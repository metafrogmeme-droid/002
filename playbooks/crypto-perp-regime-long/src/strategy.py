"""Nautilus replay strategy for the sleeve-A playbook (long-only, bracket orders, single correlation cluster).

Self-contained: features, signals, sizing and gates come from rules.py (FeatureStream is the incremental twin of the
batch research code), so it runs on plain OHLCV replay frames supplied by the managed runner.
Configuration is read from the package manifest (single source of truth) with static yaml values as fallback.
"""
import json
from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

try:
    from . import rules
except ImportError:
    import rules

HOUR_NS = 3_600_000_000_000
HOUR_MS = 3_600_000
DEFAULT_TICKS = {
    "BTCUSDT": {"tick": 0.1, "step": 0.0001, "min_qty": 0.0001},
    "ETHUSDT": {"tick": 0.01, "step": 0.01, "min_qty": 0.01},
    "SOLUSDT": {"tick": 0.001, "step": 0.1, "min_qty": 0.1},
}


def _manifest_strategy_config() -> dict:
    try:
        from getagent import runtime

        return dict(runtime.manifest.get("strategy_config", {}) or {})
    except Exception:  # noqa: BLE001 - not running inside the managed sandbox
        return {}


class RegimeLongStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    order_id_tag: str = "001"
    symbols: tuple[str, ...] = ()
    venue: str = "BITGET"
    rules_json: str = "{}"
    enforce_halts: bool = False
    tick_json: str = "{}"


class RegimeLongStrategy(Strategy):
    def __init__(self, config: RegimeLongStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        mf = _manifest_strategy_config() or json.loads(config.rules_json)
        mf["margin_cap_usdt"] = mf.get("margin_budget", mf.get("margin_cap_usdt", 500))
        self.rcfg = rules.Config.from_mapping(mf)
        self.rules_ticks = mf.get("contract_specs") or json.loads(config.tick_json) or DEFAULT_TICKS
        self._streams = {}
        self._bar_i = {}
        self._instruments = {}
        self._pending = None
        self._open = {}
        self._day_pnl = {}
        self._total_pnl = 0.0
        self._streak = 0
        self._stopped = False
        self.log_rows = []

    def on_start(self) -> None:
        for sym in self.cfg.symbols:
            iid = InstrumentId.from_str(f"{sym}.{self.cfg.venue}")
            self._instruments[sym] = self.cache.instrument(iid)
            if self._instruments[sym] is None:
                raise RuntimeError(f"instrument not found: {iid}")
            self._streams[sym] = rules.FeatureStream(self.rcfg)
            self._bar_i[sym] = -1
            self.subscribe_bars(BarType.from_str(f"{iid}-1-HOUR-LAST-EXTERNAL"))

    def on_bar(self, bar: Bar) -> None:
        sym = bar.bar_type.instrument_id.symbol.value
        if sym not in self._streams:
            return
        feat = self._streams[sym].push(float(bar.open), float(bar.high), float(bar.low), float(bar.close), float(bar.volume))
        self._bar_i[sym] += 1
        i = self._bar_i[sym]
        ts_ms = int(bar.ts_event) // 1_000_000
        inst = self._instruments[sym]

        pend = self._pending
        if pend is not None and pend["sym"] == sym:
            nxt_blackout = rules.blackout_for_order_bar(ts_ms + HOUR_MS, self.rcfg)
            if i + 1 > pend["last"] or nxt_blackout:
                self.cancel_all_orders(inst.id)
                self._pending = None

        if sym in self._open:
            held = i - self._open[sym]["fill_i"]
            if held >= self._open[sym]["hold"] - 1 and not self._open[sym].get("closing"):
                self._open[sym]["closing"] = True
                self.close_all_positions(inst.id)
            return

        if self._pending is not None or self._open or self._stopped:
            return
        if self._day_pnl.get((ts_ms + HOUR_MS) // (24 * HOUR_MS), 0.0) <= -self.rcfg.daily_pause_usdt:
            return
        module = "trend" if feat["sig_trend"] else "break" if feat["sig_break"] else "mr" if feat["sig_mr"] else None
        if module is None:
            return
        if not (feat["quote_vol_24h"] >= self.rcfg.min_volume_24h_usdt):
            return
        tick = self.rules_ticks[sym]
        plan = rules.build_plan(
            module=module,
            close=feat["close"],
            atr=feat["atr"],
            decision_ts_ms=ts_ms + HOUR_MS,
            cfg=self.rcfg,
            tick=tick["tick"],
            size_step=tick["step"],
            min_qty=tick["min_qty"],
            min_notional=5.0,
            funding_rate=self.rcfg.funding_rate_assumed,
        )
        if not plan.ok:
            return
        if rules.blackout_for_order_bar(ts_ms + HOUR_MS, self.rcfg):
            return
        orders = self.order_factory.bracket(
            instrument_id=inst.id,
            order_side=OrderSide.BUY,
            quantity=inst.make_qty(Decimal(str(plan.qty))),
            entry_order_type=OrderType.LIMIT,
            entry_price=inst.make_price(Decimal(str(plan.limit_price))),
            time_in_force=TimeInForce.GTC,
            tp_price=inst.make_price(Decimal(str(plan.tp_price))),
            tp_post_only=False,
            sl_trigger_price=inst.make_price(Decimal(str(plan.stop_price))),
        )
        self.submit_order_list(orders)
        self._pending = {"sym": sym, "last": i + self.rcfg.entry_cancel_hours, "hold": plan.time_stop_hours, "module": module, "i": i,
                         "entry_id": orders.orders[0].client_order_id}

    def on_order_filled(self, event) -> None:
        pend = self._pending
        if pend is not None and event.client_order_id == pend["entry_id"]:
            sym = pend["sym"]
            fill_i = self._bar_i[sym]
            self._open[sym] = {"fill_i": fill_i, "hold": pend["hold"], "module": pend["module"]}
            self._pending = None

    def on_position_closed(self, position) -> None:
        sym = position.instrument_id.symbol.value
        self._open.pop(sym, None)
        pnl = float(position.realized_pnl.as_decimal())
        ts_ms = int(self.clock.timestamp_ns()) // 1_000_000
        day = ts_ms // (24 * HOUR_MS)
        self._day_pnl[day] = self._day_pnl.get(day, 0.0) + pnl
        self._total_pnl += pnl
        self._streak = self._streak + 1 if pnl < 0 else 0
        if self.cfg.enforce_halts and (
            self._total_pnl <= -self.rcfg.stop_playbook_usdt or self._streak >= self.rcfg.max_consecutive_losses
        ):
            self._stopped = True

    def on_stop(self) -> None:
        for sym, inst in self._instruments.items():
            self.cancel_all_orders(inst.id)
            self.close_all_positions(inst.id)
