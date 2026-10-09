"""Nautilus replay strategy: long-only trend pullback on crypto major perpetuals.

One cluster slot (crypto majors) -> at most one pending entry or one open
position across all instruments at any time. Decisions are made once per bar
timestamp after every instrument has reported, choosing the strongest ADX
candidate.

The platform re-executes this class on raw OHLCV bars to produce the official
order/fill/position evidence, so every indicator is computed bar-by-bar inside
the strategy (``features.IncrementalIndicators``, parity-tested against the
vectorised ``compute_indicators`` the live path uses). Funding history is the
only external input: injected frame -> sidecar written by main_backtest ->
direct SDK fetch -> unknown (gate off, reported).
"""
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy

try:  # the replay engine may import this module as top-level ``strategy``
    from .rules import EntryPlan, InstrumentRules, Reason, RiskState, build_entry_plan
    from .features import IncrementalIndicators, fetch_funding_window
except ImportError:  # pragma: no cover - depends on how the runner imports src/**
    from rules import EntryPlan, InstrumentRules, Reason, RiskState, build_entry_plan
    from features import IncrementalIndicators, fetch_funding_window

HOUR_NS = 3_600_000_000_000
REPLAY_STATE_PATH = Path("/workspace/output/_replay_state.json")
FEATURE_SIDECAR_DIR = Path("/workspace/output/_features")
FUNDING_FETCH_BUDGET_SECONDS = 25.0


def _manifest_params() -> dict[str, Any]:
    try:
        from getagent import runtime  # noqa: PLC0415 - only needed on the fallback path

        cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    except Exception:  # noqa: BLE001 - manifest unavailable outside the sandbox
        cfg = {}
    if cfg:
        cfg["margin_budget"] = float(cfg.get("margin_budget", "500") or 500)
    return cfg


class TrendPullbackConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    # JSON-encoded strategy parameters (manifest strategy_config) and
    # per-instrument quantisation rules; strings keep the config immutable-safe.
    params_json: str = "{}"
    instrument_rules_json: str = "{}"


class TrendPullbackStrategy(Strategy):
    def __init__(self, config: TrendPullbackConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self.params: dict[str, Any] = json.loads(config.params_json or "{}")
        if not self.params:
            # Platform fallback bootstrap runs the class straight from backtest.yaml
            # without main_backtest's injected params: read the manifest instead.
            self.params = _manifest_params()
        self._rules_raw: dict[str, Any] = json.loads(config.instrument_rules_json or "{}")
        self.feature_frames: dict[str, pd.DataFrame] = {}
        self._indicators: dict[str, IncrementalIndicators] = {}
        # symbol -> (sorted settlement ts_ns array, rate array) for as-of lookup
        self._funding: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._instruments: dict[str, Instrument] = {}
        self._bar_types: list[BarType] = []
        # BarDataWrangler stamps bars with the frame index; getagent frames are
        # indexed by bar open time, so decision time = ts_event + 1h by default.
        self._ts_is_close_time: bool = bool(self.params.get("bar_ts_is_close_time", False))

        self._bucket_ts: Optional[int] = None
        self._bucket: dict[str, tuple[Bar, dict[str, Any]]] = {}

        self.slot: Optional[dict[str, Any]] = None  # pending entry or open position
        self.risk = RiskState()
        self.ledger: list[dict[str, Any]] = []       # closed trades
        self.action_log: list[dict[str, Any]] = []
        self.skip_counts: dict[str, int] = {}
        self.bars_seen = 0
        self.funding_known = False
        self.funding_source = "none"
        self._sidecars: Optional[dict[str, dict[str, Any]]] = None
        self.warmup_bars_used: dict[str, int] = {}

    # ------------------------------------------------------------------ setup
    def set_feature_frames(self, feature_frames: dict[str, pd.DataFrame]) -> None:
        self.feature_frames = dict(feature_frames or {})

    def _ingest_funding_frame(self, symbol: str, frame: pd.DataFrame) -> bool:
        if frame is None or "funding_rate" not in frame.columns:
            return False
        series = frame["funding_rate"].astype(float).dropna().sort_index()
        series = series[~series.index.duplicated(keep="last")]
        if series.empty:
            return False
        self._funding[symbol] = (
            np.asarray([int(pd.Timestamp(ts).value) for ts in series.index], dtype=np.int64),
            np.asarray(series.values, dtype=float),
        )
        return True

    def _read_sidecars(self) -> dict[str, dict[str, Any]]:
        """main_backtest writes one JSON sidecar per symbol:
        {"ts_ns": [...], "funding_rate": [...], "warmup": {"high": [...], "low": [...], "close": [...]}}."""
        if self._sidecars is None:
            self._sidecars = {}
            if FEATURE_SIDECAR_DIR.exists():
                for path in FEATURE_SIDECAR_DIR.glob("*.json"):
                    try:
                        self._sidecars[path.stem] = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:  # noqa: BLE001 - malformed sidecar is treated as absent
                        continue
        return self._sidecars

    def _load_funding_sidecars(self) -> bool:
        loaded = False
        for symbol, payload in self._read_sidecars().items():
            rates = payload.get("funding_rate")
            if not rates:
                continue
            frame = pd.DataFrame({"funding_rate": rates}, index=pd.to_datetime(payload["ts_ns"], utc=True))
            loaded = self._ingest_funding_frame(symbol, frame) or loaded
        return loaded

    def _prewarm_indicators(self) -> None:
        """Feed pre-window bars so indicators are valid from the first replayed bar,
        exactly like the live path which always sees trailing history."""
        for symbol, payload in self._read_sidecars().items():
            warm = payload.get("warmup") or {}
            ind = self._indicators.get(symbol)
            if ind is None or not warm.get("close"):
                continue
            for h, l, c in zip(warm["high"], warm["low"], warm["close"]):
                ind.update(h, l, c)
            self.warmup_bars_used[symbol] = len(warm["close"])

    def _fetch_funding_direct(self, symbols: list[str]) -> bool:
        """Last resort inside the platform re-run: pull funding history via the SDK."""
        now = datetime.now(timezone.utc)
        days = int(self.params.get("backtest_days", 730)) + int(self.params.get("warmup_days", 45))
        deadline = now + timedelta(seconds=FUNDING_FETCH_BUDGET_SECONDS)
        loaded = False
        for symbol in symbols:
            if datetime.now(timezone.utc) >= deadline:
                break
            try:
                frame, _report = fetch_funding_window(
                    symbol,
                    exchange=str(self.params.get("data_exchange", "bitget")),
                    start=now - timedelta(days=days),
                    end=now,
                    deadline=deadline,
                )
            except Exception:  # noqa: BLE001 - degrade to funding-unknown, never crash the replay
                continue
            loaded = self._ingest_funding_frame(symbol, frame) or loaded
        return loaded

    def _resolve_funding(self, symbols: list[str]) -> None:
        injected = False
        for key, frame in self.feature_frames.items():
            injected = self._ingest_funding_frame(key.split(".", 1)[0], frame) or injected
        if injected:
            self.funding_source = "injected"
        elif self._load_funding_sidecars():
            self.funding_source = "sidecar"
        elif self._fetch_funding_direct(symbols):
            self.funding_source = "sdk"
        self.funding_known = all(sym in self._funding for sym in symbols) and bool(symbols)

    def _funding_at(self, symbol: str, ts_ns: int) -> Optional[float]:
        table = self._funding.get(symbol)
        if not table:
            return None
        idx = int(np.searchsorted(table[0], ts_ns, side="right")) - 1
        return float(table[1][idx]) if idx >= 0 else None

    def on_start(self) -> None:
        instrument_ids = [
            iid if isinstance(iid, InstrumentId) else InstrumentId.from_str(str(iid))
            for iid in list(self.cfg.instrument_ids)
        ]
        if not instrument_ids and self.cfg.instrument_id is not None:
            iid = self.cfg.instrument_id
            instrument_ids = [iid if isinstance(iid, InstrumentId) else InstrumentId.from_str(str(iid))]
        if not instrument_ids:
            instrument_ids = [inst.id for inst in self.cache.instruments()]
        if not instrument_ids:
            raise RuntimeError("no instruments available for replay")
        bar_types = [
            bt if isinstance(bt, BarType) else BarType.from_str(str(bt))
            for bt in list(self.cfg.bar_types)
        ]
        if not bar_types and self.cfg.bar_type is not None:
            bt = self.cfg.bar_type
            bar_types = [bt if isinstance(bt, BarType) else BarType.from_str(str(bt))]
        if len(bar_types) != len(instrument_ids):
            bar_types = [BarType.from_str(f"{iid}-1-HOUR-LAST-EXTERNAL") for iid in instrument_ids]
        for iid in instrument_ids:
            instrument = self.cache.instrument(iid)
            if instrument is None:
                raise RuntimeError(f"instrument {iid} missing from cache")
            self._instruments[iid.symbol.value] = instrument
            self._indicators[iid.symbol.value] = IncrementalIndicators(self.params)
        self._prewarm_indicators()
        self._resolve_funding(list(self._instruments))
        self._bar_types = bar_types
        for bar_type in bar_types:
            self.subscribe_bars(bar_type)

    # -------------------------------------------------------------- utilities
    def _rules_for(self, symbol: str) -> InstrumentRules:
        raw = self._rules_raw.get(symbol) or {}
        instrument = self._instruments[symbol]
        return InstrumentRules(
            tick=float(raw.get("tick", float(instrument.price_increment))),
            size_step=float(raw.get("size_step", float(instrument.size_increment))),
            min_qty=float(raw.get("min_qty", float(instrument.size_increment))),
            min_notional=float(raw.get("min_notional", 5.0)),
            price_precision=int(raw.get("price_precision", instrument.price_precision)),
            size_precision=int(raw.get("size_precision", instrument.size_precision)),
        )

    def _feature_row(self, symbol: str, bar: Bar) -> dict[str, Any]:
        row = self._indicators[symbol].update(
            float(bar.high.as_double()), float(bar.low.as_double()), float(bar.close.as_double())
        )
        row["open"] = float(bar.open.as_double())
        row["volume"] = float(bar.volume.as_double())
        # Funding known at the bar's open (as-of), never a later settlement.
        open_ns = bar.ts_event - HOUR_NS if self._ts_is_close_time else bar.ts_event
        row["funding_rate"] = self._funding_at(symbol, open_ns)
        return row

    def _decision_time(self, ts_event: int) -> datetime:
        close_ns = ts_event if self._ts_is_close_time else ts_event + HOUR_NS
        return datetime.fromtimestamp(close_ns / 1e9, tz=timezone.utc)

    def _log(self, **entry: Any) -> None:
        entry.setdefault("mode", "backtest")
        self.action_log.append(entry)

    def _skip(self, reason: str) -> None:
        self.skip_counts[reason] = self.skip_counts.get(reason, 0) + 1

    # ----------------------------------------------------------------- events
    def on_bar(self, bar: Bar) -> None:
        self.bars_seen += 1
        symbol = bar.bar_type.instrument_id.symbol.value
        row = self._feature_row(symbol, bar)
        if self._bucket_ts is not None and bar.ts_event != self._bucket_ts:
            self._decide(self._bucket_ts)
            self._bucket = {}
        self._bucket_ts = bar.ts_event
        self._bucket[symbol] = (bar, row)
        if len(self._bucket) == len(self._instruments):
            self._decide(bar.ts_event)
            self._bucket = {}
            self._bucket_ts = None

    def _decide(self, ts_event: int) -> None:
        if not self._bucket:
            return
        now = self._decision_time(ts_event)
        self.risk.roll_day(now)
        self._manage_slot(ts_event, now)
        if self.slot is not None:
            self._skip(Reason.SLOT_OCCUPIED)
            return
        block = self.risk.entry_block_reason(now, self.params)
        if block != Reason.OK:
            self._skip(block)
            return
        best: Optional[tuple[EntryPlan, Bar]] = None
        for symbol, (bar, row) in self._bucket.items():
            funding = row.get("funding_rate")
            plan, reason = build_entry_plan(
                symbol=symbol,
                row=row,
                params=self.params,
                rules=self._rules_for(symbol),
                decision_time=now,
                funding_rate=None if funding is None or pd.isna(funding) else float(funding),
                funding_known=self.funding_known,
            )
            if plan is None:
                self._skip(reason)
                continue
            if best is None or plan.adx > best[0].adx:
                best = (plan, bar)
        if best is None:
            return
        self._place_entry(best[0], best[1], now)

    def _place_entry(self, plan: EntryPlan, bar: Bar, now: datetime) -> None:
        instrument = self._instruments[plan.symbol]
        qty = instrument.make_qty(plan.qty)
        price = instrument.make_price(plan.limit_price)
        order = self.order_factory.limit(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=qty,
            price=price,
            time_in_force=TimeInForce.GTC,
            post_only=False,
        )
        self.slot = {
            "state": "pending",
            "symbol": plan.symbol,
            "entry_client_order_id": order.client_order_id.value,
            "placed_ns": bar.ts_event,
            "placed_at": now.isoformat(),
            "plan": plan,
            "fees": 0.0,
            "fill_px": None,
            "fill_ns": None,
            "fill_qty": 0.0,
            "exit_reason": None,
            "exit_px": None,
            "exit_ns": None,
            "exit_taker": False,
            "realized_pnl": None,
        }
        self.submit_order(order)
        self._log(
            ts=now.isoformat(),
            symbol=plan.symbol,
            side="buy",
            action=Reason.ENTRY_PLACED,
            intended_price=plan.limit_price,
            filled_price=None,
            qty=plan.qty,
            stop=plan.stop_price,
            take_profit=plan.tp_price,
            notional=plan.notional,
            margin=plan.margin,
            risk_usdt=plan.risk_usdt,
            fees=0.0,
            funding=0.0,
            reason_code=";".join(plan.reasons),
            adx=round(plan.adx, 2),
            atr=round(plan.atr, 6),
            funding_rate=plan.funding_rate,
        )

    def _manage_slot(self, ts_event: int, now: datetime) -> None:
        slot = self.slot
        if slot is None:
            return
        instrument = self._instruments[slot["symbol"]]
        if slot["state"] == "pending":
            age_hours = (ts_event - slot["placed_ns"]) / HOUR_NS
            if age_hours >= float(self.params["entry_max_age_hours"]):
                for order in self.cache.orders_open(instrument_id=instrument.id):
                    self.cancel_order(order)
                self._log(
                    ts=now.isoformat(), symbol=slot["symbol"], side="buy", action=Reason.ENTRY_EXPIRED,
                    intended_price=slot["plan"].limit_price, filled_price=None, qty=slot["plan"].qty,
                    fees=0.0, funding=0.0, reason_code=Reason.ENTRY_EXPIRED,
                )
                self.slot = None
            return
        if slot["state"] == "open":
            held_hours = (ts_event - slot["fill_ns"]) / HOUR_NS
            if held_hours >= float(self.params["time_stop_hours"]):
                positions = self.cache.positions_open(instrument_id=instrument.id)
                if not positions:
                    # Position already closed by TP/SL; event handler will clear the slot.
                    return
                slot["exit_reason"] = Reason.TIME_STOP
                slot["exit_taker"] = True
                self.cancel_all_orders(instrument.id)
                for position in positions:
                    self.close_position(position)

    def on_order_filled(self, event: Any) -> None:
        slot = self.slot
        if slot is None:
            return
        symbol = event.instrument_id.symbol.value
        if symbol != slot["symbol"]:
            return
        fill_px = float(event.last_px)
        fill_qty = float(event.last_qty)
        fee = 0.0
        commission = getattr(event, "commission", None)
        if commission is not None:
            try:
                fee = float(commission.as_double())
            except Exception:  # noqa: BLE001
                try:
                    fee = float(commission)
                except Exception:  # noqa: BLE001
                    fee = 0.0
        slot["fees"] += fee
        if event.order_side == OrderSide.BUY and slot["state"] == "pending":
            slot["state"] = "open"
            slot["fill_px"] = fill_px
            slot["fill_qty"] += fill_qty
            slot["fill_ns"] = int(event.ts_event)
            plan: EntryPlan = slot["plan"]
            self._log(
                ts=datetime.fromtimestamp(int(event.ts_event) / 1e9, tz=timezone.utc).isoformat(),
                symbol=symbol, side="buy", action=Reason.ENTRY_FILLED,
                intended_price=plan.limit_price, filled_price=fill_px, qty=fill_qty,
                fees=fee, funding=0.0, reason_code=Reason.ENTRY_FILLED,
            )
            self._attach_exits(symbol, plan, fill_qty)
            return
        if event.order_side == OrderSide.SELL and slot["state"] == "open":
            slot["exit_px"] = fill_px
            slot["exit_ns"] = int(event.ts_event)
            if slot["exit_reason"] is None:
                plan = slot["plan"]
                # Distinguish stop vs target by proximity to the planned levels.
                slot["exit_reason"] = (
                    Reason.STOP_HIT if abs(fill_px - plan.stop_price) <= abs(fill_px - plan.tp_price) else Reason.TP_HIT
                )
                slot["exit_taker"] = slot["exit_reason"] == Reason.STOP_HIT

    def _attach_exits(self, symbol: str, plan: EntryPlan, qty_value: float) -> None:
        instrument = self._instruments[symbol]
        qty = instrument.make_qty(qty_value)
        stop = self.order_factory.stop_market(
            instrument_id=instrument.id,
            order_side=OrderSide.SELL,
            quantity=qty,
            trigger_price=instrument.make_price(plan.stop_price),
            time_in_force=TimeInForce.GTC,
            reduce_only=True,
        )
        take_profit = self.order_factory.limit(
            instrument_id=instrument.id,
            order_side=OrderSide.SELL,
            quantity=qty,
            price=instrument.make_price(plan.tp_price),
            time_in_force=TimeInForce.GTC,
            reduce_only=True,
        )
        self.submit_order(stop)
        self.submit_order(take_profit)

    def on_position_closed(self, event: Any) -> None:
        slot = self.slot
        if slot is None:
            return
        symbol = event.instrument_id.symbol.value
        if symbol != slot["symbol"]:
            return
        instrument = self._instruments[symbol]
        self.cancel_all_orders(instrument.id)
        realized = 0.0
        pnl_obj = getattr(event, "realized_pnl", None)
        if pnl_obj is not None:
            try:
                realized = float(pnl_obj.as_double())
            except Exception:  # noqa: BLE001
                try:
                    realized = float(pnl_obj)
                except Exception:  # noqa: BLE001
                    realized = 0.0
        exit_ns = slot.get("exit_ns") or int(event.ts_event)
        exit_time = datetime.fromtimestamp(exit_ns / 1e9, tz=timezone.utc)
        plan: EntryPlan = slot["plan"]
        fill_px = float(slot["fill_px"] or plan.limit_price)
        exit_px = float(slot["exit_px"] or fill_px)
        qty = float(slot["fill_qty"] or plan.qty)
        gross = (exit_px - fill_px) * qty
        trade = {
            "symbol": symbol,
            "side": "long",
            "entry_time": datetime.fromtimestamp(int(slot["fill_ns"]) / 1e9, tz=timezone.utc).isoformat(),
            "exit_time": exit_time.isoformat(),
            "entry_ns": int(slot["fill_ns"]),
            "exit_ns": int(exit_ns),
            "intended_entry": plan.limit_price,
            "entry_price": fill_px,
            "exit_price": exit_px,
            "qty": qty,
            "notional": round(fill_px * qty, 4),
            "stop_price": plan.stop_price,
            "tp_price": plan.tp_price,
            "risk_usdt": plan.risk_usdt,
            "gross_pnl": round(gross, 6),
            "fees": round(float(slot["fees"]), 6),
            "engine_realized_pnl": round(realized, 6),
            "exit_reason": slot.get("exit_reason") or Reason.TIME_STOP,
            "exit_taker": bool(slot.get("exit_taker")),
            "hold_hours": round((exit_ns - int(slot["fill_ns"])) / HOUR_NS, 3),
            "adx_at_signal": round(plan.adx, 2),
            "atr_at_signal": round(plan.atr, 6),
            "funding_rate_at_signal": plan.funding_rate,
            "sizing_capped": plan.sizing_capped,
        }
        self.ledger.append(trade)
        net_for_breakers = realized if realized != 0.0 else gross - float(slot["fees"])
        events = self.risk.register_close(exit_time, net_for_breakers, self.params)
        self._log(
            ts=exit_time.isoformat(), symbol=symbol, side="sell", action=trade["exit_reason"],
            intended_price=(
                plan.stop_price if trade["exit_reason"] == Reason.STOP_HIT
                else plan.tp_price if trade["exit_reason"] == Reason.TP_HIT
                else None  # time stop / end of data: market exit, no intended level
            ),
            filled_price=exit_px, qty=qty, fees=round(float(slot["fees"]), 6), funding=0.0,
            reason_code=";".join([trade["exit_reason"], *events]) if events else trade["exit_reason"],
            realized_pnl=round(net_for_breakers, 6),
        )
        self.slot = None

    def on_order_rejected(self, event: Any) -> None:
        reason = str(getattr(event, "reason", "") or "")
        symbol = event.instrument_id.symbol.value
        self._log(ts=datetime.fromtimestamp(int(event.ts_event) / 1e9, tz=timezone.utc).isoformat(),
                  symbol=symbol, side="", action="ORDER_REJECTED",
                  intended_price=None, filled_price=None, qty=None, fees=0.0, funding=0.0,
                  reason_code=f"REJECTED:{reason[:120]}")
        slot = self.slot
        if slot is None or symbol != slot["symbol"]:
            return
        if slot["state"] == "pending" and event.client_order_id.value == slot["entry_client_order_id"]:
            self.slot = None
            return
        if slot["state"] == "open" and "STOP_MARKET" in reason.upper():
            # The entry filled in a bar that already traded through the stop level, so the
            # resting stop is rejected as "in the market". Live exchange-side SL would fire
            # immediately; mirror that by closing at market now (taker, worse than planned).
            instrument = self._instruments[symbol]
            slot["exit_reason"] = Reason.STOP_HIT
            slot["exit_taker"] = True
            self.cancel_all_orders(instrument.id)
            for position in self.cache.positions_open(instrument_id=instrument.id):
                self.close_position(position)

    def on_order_denied(self, event: Any) -> None:
        self.on_order_rejected(event)

    def on_stop(self) -> None:
        if self._bucket:
            self._bucket = {}
        if self.slot is not None and self.slot["state"] == "open" and self.slot.get("exit_reason") is None:
            self.slot["exit_reason"] = "END_OF_DATA"
            self.slot["exit_taker"] = True
        for instrument in self._instruments.values():
            self.cancel_all_orders(instrument.id)
            self.close_all_positions(instrument.id)
        self._dump_state()

    def _dump_state(self) -> None:
        open_slot = None
        if self.slot is not None:
            open_slot = {k: (asdict(v) if isinstance(v, EntryPlan) else v) for k, v in self.slot.items()}
        payload = {
            "ledger": self.ledger,
            "action_log": self.action_log,
            "skip_counts": self.skip_counts,
            "risk_state": self.risk.to_dict(),
            "bars_seen": self.bars_seen,
            "funding_known": self.funding_known,
            "funding_source": self.funding_source,
            "warmup_bars_used": self.warmup_bars_used,
            "ts_is_close_time": self._ts_is_close_time,
            "unresolved_slot": open_slot,
        }
        REPLAY_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPLAY_STATE_PATH.write_text(json.dumps(payload, default=str), encoding="utf-8")
