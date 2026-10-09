"""Nautilus replay strategy for the sleeve-A playbook (long-only, bracket orders, single correlation cluster).

Signals, sizing and gates come from rules.py; the replay frames carry the pre-computed causal columns
(atr, sig_trend, sig_mr, sig_break, quote_vol_24h) built in main_backtest.py.
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
FEATURE_COLS = ("atr", "sig_trend", "sig_mr", "sig_break", "quote_vol_24h")


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
        self.rcfg = rules.Config.from_mapping(json.loads(config.rules_json))
        self.rules_ticks = json.loads(config.tick_json)
        self.frames = {}
        self._rows = {}
        self._instruments = {}
        self._pending = None
        self._open = {}
        self._day_pnl = {}
        self._total_pnl = 0.0
        self._streak = 0
        self._stopped = False
        self.log_rows = []

    def set_feature_frames(self, feature_frames) -> None:
        self.frames = feature_frames

    def on_start(self) -> None:
        for sym in self.cfg.symbols:
            iid = InstrumentId.from_str(f"{sym}.{self.cfg.venue}")
            self._instruments[sym] = self.cache.instrument(iid)
            if self._instruments[sym] is None:
                raise RuntimeError(f"instrument not found: {iid}")
            frame = self._frame_for(iid)
            if frame is None:
                raise RuntimeError(f"feature frame missing for {iid}")
            self._rows[sym] = {
                "ts": {int(t.value): i for i, t in enumerate(frame.index)},
                "cols": {c: frame[c].to_numpy() for c in FEATURE_COLS},
                "close": frame["close"].to_numpy(),
            }
            self.subscribe_bars(BarType.from_str(f"{iid}-1-HOUR-LAST-EXTERNAL"))

    def _frame_for(self, iid: InstrumentId):
        for key in (str(iid), iid.value, iid.symbol.value):
            if key in self.frames:
                return self.frames[key]
        return None

    def on_bar(self, bar: Bar) -> None:
        sym = bar.bar_type.instrument_id.symbol.value
        if sym not in self._rows:
            return
        rows = self._rows[sym]
        i = rows["ts"].get(int(bar.ts_event))
        if i is None:
            return
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
        c = rows["cols"]
        module = "trend" if c["sig_trend"][i] > 0.5 else "break" if c["sig_break"][i] > 0.5 else "mr" if c["sig_mr"][i] > 0.5 else None
        if module is None:
            return
        if not (c["quote_vol_24h"][i] >= self.rcfg.min_volume_24h_usdt):
            return
        tick = self.rules_ticks[sym]
        plan = rules.build_plan(
            module=module,
            close=float(rows["close"][i]),
            atr=float(c["atr"][i]),
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
            rows = self._rows[sym]
            fill_i = rows["ts"].get(int(self.clock.timestamp_ns()) // HOUR_NS * HOUR_NS, pend["i"] + 1)
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
