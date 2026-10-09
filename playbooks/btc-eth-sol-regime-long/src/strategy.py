"""Nautilus replay strategy for the BTC/ETH/SOL regime-filtered long Playbook.

Signals, ATR and funding come from feature frames prepared by ``main_backtest``
with ``features.compute_signals`` (same code as live). Order handling mirrors live:
limit entry at the signal close, exchange-style stop-market + touch-triggered
take-profit attached on fill, entry TTL, time stop, portfolio/risk limits.

Replay-only simplification: a latched halt (consecutive losses / daily stop)
resumes on the next UTC day so a multi-year replay keeps producing evidence;
every occurrence is counted in the ledger summary. Live keeps it latched.
"""
import json
import math
from pathlib import Path
from typing import Any, Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

try:
    from .action_log import ActionLog
    from .features import funding_blocks, in_funding_window, validate_signal
    from .risk import RiskState, plan_entry
except ImportError:  # replay engine may import this module top-level from src/
    from action_log import ActionLog
    from features import funding_blocks, in_funding_window, validate_signal
    from risk import RiskState, plan_entry

HOUR_MS = 3_600_000
DAY_MS = 86_400_000
LEDGER_PATH = Path("/workspace/output/replay_ledger.json")


class RegimeLongConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    risk_per_trade_usdt: float = 15.0
    max_leverage: float = 5.0
    margin_budget: str = "1500"
    max_concurrent: int = 3
    stop_atr_mult: float = 1.5
    tp_r_multiple: float = 2.0
    time_stop_hours: int = 8
    entry_ttl_hours: int = 4
    daily_pause_usdt: float = 30.0
    daily_stop_usdt: float = 40.0
    max_consecutive_losses: int = 5
    funding_block_minutes: int = 15
    funding_max_against_8h: float = 0.0003
    allow_short: bool = False
    slippage_ticks: float = 1.0
    signal_start_ms: int = 0
    ledger_path: str = ""


def _money(value: Any) -> float:
    if value is None:
        return 0.0
    for attr in ("as_double", "as_decimal"):
        fn = getattr(value, attr, None)
        if callable(fn):
            try:
                return float(fn())
            except Exception:
                pass
    try:
        return float(str(value).split()[0])
    except Exception:
        return 0.0


class RegimeLongStrategy(Strategy):
    def __init__(self, config: RegimeLongConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._cfg_map = {k: getattr(config, k) for k in (
            "risk_per_trade_usdt", "max_leverage", "margin_budget", "max_concurrent", "stop_atr_mult",
            "tp_r_multiple", "time_stop_hours", "entry_ttl_hours", "daily_pause_usdt", "daily_stop_usdt",
            "max_consecutive_losses", "funding_block_minutes", "funding_max_against_8h")}
        self.feature_frames: dict[str, Any] = {}
        self._rows: dict[str, dict[int, dict[str, float]]] = {}
        self._instruments: dict[str, Any] = {}
        self._risk = RiskState()
        self._alog = ActionLog(run_id="replay", mode="historical")
        self._pending: dict[str, dict[str, Any]] = {}
        self._open: dict[str, dict[str, Any]] = {}
        self._order_role: dict[str, tuple[str, str]] = {}
        self._trades: list[dict[str, Any]] = []
        self._events = {"daily_pause": 0, "daily_stop": 0, "consecutive_loss_halt": 0}
        self._skips: dict[str, int] = {}
        self._ts_shift: Optional[int] = None

    # ---- feature frame injection -------------------------------------------------
    def set_feature_frames(self, feature_frames: Any) -> None:
        self.feature_frames = feature_frames or {}

    def _index_frames(self) -> None:
        cols = ("open", "close", "atr", "adx", "regime_code", "signal_long", "signal_short",
                "funding_rate_8h", "funding_settle_rate", "funding_known")
        for key, frame in (self.feature_frames or {}).items():
            sym = str(key).split(".")[0]
            rows: dict[int, dict[str, float]] = {}
            idx_ms = [int(ts.value // 1_000_000) for ts in frame.index]
            data = {c: frame[c].tolist() for c in cols}
            for i, ts in enumerate(idx_ms):
                rows[ts] = {c: data[c][i] for c in cols}
            self._rows[sym] = rows

    # ---- lifecycle ---------------------------------------------------------------
    def on_start(self) -> None:
        if not self.feature_frames:
            raise RuntimeError("feature frames were not injected; check data_requirements.required_bar_fields")
        self._index_frames()
        bar_types = list(self.cfg.bar_types) or ([self.cfg.bar_type] if self.cfg.bar_type else [])
        if not bar_types:
            raise RuntimeError("no bar types configured")
        for raw_bt in bar_types:
            bt = BarType.from_str(raw_bt) if isinstance(raw_bt, str) else raw_bt
            inst = self.cache.instrument(bt.instrument_id)
            if inst is None:
                raise RuntimeError(f"instrument {bt.instrument_id} missing from cache")
            self._instruments[bt.instrument_id.symbol.value] = inst
            self.subscribe_bars(bt)

    def on_stop(self) -> None:
        for inst in self._instruments.values():
            self.cancel_all_orders(inst.id)
            self.close_all_positions(inst.id)
        path = Path(self.cfg.ledger_path) if self.cfg.ledger_path else LEDGER_PATH
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "trades": self._trades, "events": self._events, "skips": self._skips,
                "action_log": self._alog.rows[-400:], "action_log_rows_total": len(self._alog.rows),
                "ts_shift_ms": self._ts_shift,
            }, default=str))
        except Exception as exc:  # pragma: no cover - surfaced in run stderr
            self._ledger_error = str(exc)

    # ---- helpers -----------------------------------------------------------------
    def _skip(self, reason: str) -> None:
        self._skips[reason] = self._skips.get(reason, 0) + 1

    def _row_for(self, sym: str, bar: Bar) -> Optional[tuple[int, dict[str, float]]]:
        rows = self._rows.get(sym)
        if not rows:
            return None
        ts = int(bar.ts_event // 1_000_000)
        close = float(bar.close)
        candidates = (self._ts_shift,) if self._ts_shift is not None else (0, -HOUR_MS)
        for shift in candidates:
            row = rows.get(ts + shift)
            if row is not None and abs(float(row["close"]) - close) <= 1e-9 * max(1.0, close) + 1e-6:
                self._ts_shift = shift
                return ts + shift, row
        return None

    def _tick(self, inst: Any) -> float:
        return float(inst.price_increment)

    def _slots_used(self) -> int:
        return len(self._pending) + len(self._open)

    # ---- bar loop ----------------------------------------------------------------
    def on_bar(self, bar: Bar) -> None:
        sym = bar.bar_type.instrument_id.symbol.value
        inst = self._instruments.get(sym)
        found = self._row_for(sym, bar)
        if inst is None or found is None:
            self._skip("feature_row_missing")
            return
        t_open, row = found
        t_close = t_open + HOUR_MS
        day = t_open // DAY_MS
        if self._risk.day != day and self._risk.latched_halt:
            self._risk.latched_halt = ""
        self._risk.roll(day)

        pos = self._open.get(sym)
        if pos is not None and pos.get("filled_bar_open", t_open) < t_open:
            rate = float(row["funding_settle_rate"] or 0.0)
            if rate:
                sgn = 1.0 if pos["side"] == "long" else -1.0
                pos["funding"] += sgn * pos["qty"] * float(row["open"]) * rate

        if pos is not None and pos.get("filled_bar_open") is not None:
            held = t_close - pos["filled_bar_open"]
            if held >= int(self.cfg.time_stop_hours) * HOUR_MS and not pos.get("closing"):
                if in_funding_window(t_close, int(self.cfg.funding_block_minutes)):
                    self._skip("time_stop_deferred_funding_window")
                else:
                    self._time_stop(sym, inst, pos, t_close)

        od = self._pending.get(sym)
        if od is not None:
            order = self.cache.order(od["client_order_id"])
            if order is not None and order.is_open and t_close - od["placed_ms"] >= int(self.cfg.entry_ttl_hours) * HOUR_MS:
                self.cancel_order(order)
                self._alog.add(t_close, sym, "ORDER_CANCELLED", "ENTRY_TTL_EXPIRED", side=od["side"],
                             intended_price=od["limit"], qty=od["qty"])
                self._pending.pop(sym, None)

        if t_close <= int(self.cfg.signal_start_ms):
            return
        block = self._risk.entry_block_reason(day)
        if block:
            for psym in list(self._pending):
                self._cancel_pending(psym, t_close, "PAUSE_CANCEL")
        self._maybe_enter(sym, inst, row, t_close, block)

    def _maybe_enter(self, sym: str, inst: Any, row: dict[str, float], t_close: int, block: Optional[str]) -> None:
        allowed = ("long", "short") if self.cfg.allow_short else ("long",)
        raw_action = "long" if row["signal_long"] >= 0.5 else ("short" if row["signal_short"] >= 0.5 else None)
        if raw_action is None:
            return
        action = validate_signal(raw_action, allowed)
        if action is None:
            self._skip("invalid_or_disallowed_signal")
            return
        if sym in self._pending or sym in self._open:
            self._skip("symbol_busy")
            return
        if block:
            self._skip("paused")
            return
        if self._slots_used() >= int(self.cfg.max_concurrent):
            self._skip("slots")
            return
        if in_funding_window(t_close, int(self.cfg.funding_block_minutes)):
            self._skip("funding_window")
            return
        f8h = float(row["funding_rate_8h"]) if row["funding_known"] >= 0.5 else None
        if funding_blocks(action, f8h, float(self.cfg.funding_max_against_8h)):
            self._skip("funding_against" if f8h is not None else "funding_unknown")
            return
        atr = float(row["atr"])
        if not (math.isfinite(atr) and atr > 0):
            self._skip("invalid_atr")
            return
        tick = self._tick(inst)
        step = float(inst.size_increment)
        plan = plan_entry(side=action, close=float(row["close"]), atr=atr, tick=tick, size_step=step,
                          min_qty=step, cfg=self._cfg_map)
        if not plan.ok:
            self._skip(plan.reason_code.lower())
            return
        order = self.order_factory.limit(
            instrument_id=inst.id,
            order_side=OrderSide.BUY if action == "long" else OrderSide.SELL,
            quantity=inst.make_qty(plan.qty),
            price=inst.make_price(plan.limit),
            time_in_force=TimeInForce.GTC,
        )
        self._pending[sym] = {"client_order_id": order.client_order_id, "side": action, "limit": plan.limit,
                             "stop": plan.stop, "tp": plan.tp, "qty": plan.qty, "placed_ms": t_close,
                             "adx": float(row["adx"]), "regime_code": float(row["regime_code"])}
        self._order_role[order.client_order_id.value] = (sym, "entry")
        self.submit_order(order)
        self._alog.add(t_close, sym, "ORDER_PLACED", "ENTRY_SIGNAL", side=action, intended_price=plan.limit,
                     qty=plan.qty, detail={"stop": plan.stop, "tp": plan.tp})

    def _cancel_pending(self, sym: str, ts: int, reason: str) -> None:
        od = self._pending.pop(sym, None)
        if od is None:
            return
        order = self.cache.order(od["client_order_id"])
        if order is not None and order.is_open:
            self.cancel_order(order)
        self._alog.add(ts, sym, "ORDER_CANCELLED", reason, side=od["side"], intended_price=od["limit"], qty=od["qty"])

    def _time_stop(self, sym: str, inst: Any, pos: dict[str, Any], ts: int) -> None:
        pos["closing"] = True
        pos["exit_reason"] = "TIME_STOP"
        for key in ("sl_id", "tp_id"):
            oid = pos.get(key)
            order = self.cache.order(oid) if oid is not None else None
            if order is not None and order.is_open:
                self.cancel_order(order)
        close_side = OrderSide.SELL if pos["side"] == "long" else OrderSide.BUY
        order = self.order_factory.market(instrument_id=inst.id, order_side=close_side,
                                          quantity=inst.make_qty(pos["qty"]), reduce_only=True)
        self._order_role[order.client_order_id.value] = (sym, "time")
        self.submit_order(order)

    # ---- events ------------------------------------------------------------------
    def on_order_filled(self, event: Any) -> None:
        role = self._order_role.get(event.client_order_id.value)
        if role is None:
            return
        sym, kind = role
        inst = self._instruments[sym]
        ts = int(event.ts_event // 1_000_000)
        if kind == "entry":
            od = self._pending.pop(sym, None)
            if od is None or sym in self._open:
                return
            fill_px = float(event.last_px)
            close_side = OrderSide.SELL if od["side"] == "long" else OrderSide.BUY
            sl = self.order_factory.stop_market(instrument_id=inst.id, order_side=close_side,
                                                quantity=inst.make_qty(od["qty"]),
                                                trigger_price=inst.make_price(od["stop"]), reduce_only=True)
            tp = self.order_factory.market_if_touched(instrument_id=inst.id, order_side=close_side,
                                                      quantity=inst.make_qty(od["qty"]),
                                                      trigger_price=inst.make_price(od["tp"]), reduce_only=True)
            self._order_role[sl.client_order_id.value] = (sym, "sl")
            self._order_role[tp.client_order_id.value] = (sym, "tp")
            self.submit_order(sl)
            self.submit_order(tp)
            bar_open = (ts // HOUR_MS) * HOUR_MS
            if self._ts_shift == -HOUR_MS and ts % HOUR_MS == 0:
                bar_open = ts - HOUR_MS
            self._open[sym] = {**od, "entry_fill": fill_px, "fill_ms": ts, "filled_bar_open": bar_open,
                              "sl_id": sl.client_order_id, "tp_id": tp.client_order_id, "funding": 0.0,
                              "fees": _money(getattr(event, "commission", None)), "exit_reason": ""}
            self._alog.add(ts, sym, "ENTRY_FILLED", "ENTRY_SIGNAL", side=od["side"], intended_price=od["limit"],
                         filled_price=fill_px, qty=od["qty"], fee_usdt=self._open[sym]["fees"],
                         order_id=event.client_order_id.value)
            return
        pos = self._open.get(sym)
        if pos is None:
            return
        if kind in ("sl", "tp"):
            pos["exit_reason"] = "EXIT_SL" if kind == "sl" else "EXIT_TP"
            other = pos.get("tp_id") if kind == "sl" else pos.get("sl_id")
            order = self.cache.order(other) if other is not None else None
            if order is not None and order.is_open:
                self.cancel_order(order)
        pos["exit_fill"] = float(event.last_px)
        pos["fees"] += _money(getattr(event, "commission", None))

    def on_position_closed(self, event: Any) -> None:
        sym = event.instrument_id.symbol.value
        pos = self._open.pop(sym, None)
        if pos is None:
            return
        inst = self._instruments[sym]
        ts = int(event.ts_event // 1_000_000)
        engine_pnl = _money(getattr(event, "realized_pnl", None))
        tick = self._tick(inst)
        slippage = float(self.cfg.slippage_ticks) * tick * pos["qty"]
        net = engine_pnl - pos["funding"] - slippage
        risk = float(self.cfg.risk_per_trade_usdt)
        exit_px = pos.get("exit_fill", float(getattr(event, "avg_px_close", 0.0) or 0.0))
        sgn = 1.0 if pos["side"] == "long" else -1.0
        gross = sgn * (exit_px - pos["entry_fill"]) * pos["qty"]
        reason = pos.get("exit_reason") or "EXIT_OTHER"
        self._trades.append({
            "symbol": sym, "side": pos["side"], "signal_close_ms": pos["placed_ms"], "fill_ms": pos["fill_ms"],
            "exit_ms": ts, "intended_entry": pos["limit"], "entry": pos["entry_fill"], "stop": pos["stop"],
            "tp": pos["tp"], "exit": exit_px, "qty": pos["qty"], "gross_pnl": gross,
            "engine_realized_pnl": engine_pnl, "fees": pos["fees"], "slippage": slippage,
            "funding": pos["funding"], "net_pnl": net, "r_gross": gross / risk, "r_net": net / risk,
            "exit_reason": reason, "adx": pos["adx"],
        })
        self._alog.add(ts, sym, "EXIT", reason, side=pos["side"], intended_price=pos["tp"] if reason == "EXIT_TP"
                     else pos["stop"] if reason == "EXIT_SL" else None, filled_price=exit_px, qty=pos["qty"],
                     fee_usdt=pos["fees"], funding_usdt=pos["funding"], realized_pnl_usdt=net, r_multiple=net / risk)
        day = ts // DAY_MS
        new_state = self._risk.record_close(day, net, self._cfg_map)
        if new_state == "HALT_CONSECUTIVE_LOSSES":
            self._events["consecutive_loss_halt"] += 1
            self._risk.consecutive_losses = 0
        elif new_state == "PLAYBOOK_STOP_DAILY_LOSS":
            self._events["daily_stop"] += 1
        elif new_state == "DAILY_PAUSE":
            self._events["daily_pause"] += 1
        if new_state:
            self._alog.add(ts, sym, "HALT", new_state, detail=self._risk.to_dict())
            for psym in list(self._pending):
                self._cancel_pending(psym, ts, "PAUSE_CANCEL")
