"""Nautilus replay strategy for the Bitget USDT-M trend Playbook (long-only, v1).

One strategy instance handles all declared instruments. Indicator, sizing, gate
and cost rules come from ``logic`` (pure Python, unit-tested). Every action is
recorded as a structured log record with a ``ReasonCode``.
"""
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy

try:
    from . import logic
except ImportError:  # loaded as a top-level module by the replay runner
    import logic  # type: ignore[no-redef]

RC = logic.ReasonCode
HOUR_MS = logic.HOUR_MS
NS_PER_MS = 1_000_000
MAX_LOG_RECORDS = 25_000

# Hand-off to main_backtest in case the runner imports this module in-process.
RESULTS: dict[str, Any] = {}


class TrendStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    params_json: str = "{}"


class _SymbolState:
    def __init__(self, symbol: str, iid: InstrumentId, spec: Any, p: Any) -> None:
        self.symbol = symbol
        self.iid = iid
        self.spec = spec
        self.ind = logic.IndicatorEngine(
            ema_fast=p.ema_fast, ema_slow=p.ema_slow, adx_period=p.adx_period,
            atr_period=p.atr_period, atr_pct_lookback=p.atr_pct_lookback_bars,
            atr_pct_min_history=p.atr_pct_min_history_bars, volume_lookback=p.volume_lookback_bars,
        )
        self.pending: Optional[dict[str, Any]] = None
        self.trade: Optional[dict[str, Any]] = None
        self.time_stop_sent = False
        self.funding: dict[int, float] = {}


class TrendStrategy(Strategy):
    def __init__(self, config: TrendStrategyConfig) -> None:
        super().__init__(config)
        self.p = logic.load_params(json.loads(config.params_json or "{}"))
        self.states: dict[str, _SymbolState] = {}
        self.feature_frames: dict[str, Any] = {}
        self.funding_ready = False
        self.funding_modelled = False
        self.stopping = False
        resume = float(self.p.backtest_halt_resume_hours)
        self.risk = logic.RiskState(self.p, resume_after_hours=resume if resume > 0 else None)
        self.trades: list[dict[str, Any]] = []
        self.logs: list[dict[str, Any]] = []
        self.logs_dropped = 0
        self.reason_counts: dict[str, int] = {}
        self.regime_counts: dict[str, dict[str, int]] = {}
        self.cost_mult = float(self.p.cost_multiplier)
        self.start_ms = logic.parse_iso_ms(self.p.trade_start) if self.p.trade_start else 0
        self.end_ms = logic.parse_iso_ms(self.p.trade_end) if self.p.trade_end else 2**62
        self.bar_shift_ms = HOUR_MS if self.p.bar_ts_convention == "open" else 0

    # -- lifecycle ---------------------------------------------------------

    def set_feature_frames(self, feature_frames: dict[str, Any]) -> None:
        self.feature_frames = feature_frames

    def on_start(self) -> None:
        ids = list(self.config.instrument_ids) or ([self.config.instrument_id] if self.config.instrument_id else [])
        types = list(self.config.bar_types) or ([self.config.bar_type] if self.config.bar_type else [])
        if not ids or len(ids) != len(types):
            raise RuntimeError("instrument_ids and bar_types must be set and aligned")
        for raw_id, raw_type in zip(ids, types):
            iid = InstrumentId.from_str(str(raw_id))
            btype = BarType.from_str(str(raw_type))
            symbol = iid.symbol.value
            spec = logic.CONTRACT_SPECS[symbol]
            instrument = self.cache.instrument(iid)
            if instrument is None:
                raise RuntimeError(f"instrument {iid} not found in cache")
            if Decimal(str(instrument.price_increment)) != spec.tick:
                raise RuntimeError(f"{symbol}: price_increment {instrument.price_increment} != verified tick {spec.tick}")
            if Decimal(str(instrument.size_increment)) != spec.qty_step:
                raise RuntimeError(f"{symbol}: size_increment {instrument.size_increment} != verified step {spec.qty_step}")
            self.states[symbol] = _SymbolState(symbol, iid, spec, self.p)
            self.regime_counts[symbol] = {"bars_ready": 0, "bars_regime_ok": 0, "adx_low": 0, "atr_pct_low": 0, "atr_pct_high": 0}
            self.subscribe_bars(btype)

    def _load_funding(self) -> None:
        self.funding_ready = True
        missing = []
        for key, frame in (self.feature_frames or {}).items():
            symbol = str(key).split(".")[0]
            if symbol in self.states and "funding_rate" in getattr(frame, "columns", []):
                series = frame["funding_rate"].dropna()
                self.states[symbol].funding = {
                    int(ts.timestamp() * 1000): float(v) for ts, v in series.items()
                }
        for symbol, st in self.states.items():
            if not st.funding:
                missing.append(symbol)
        self.funding_modelled = not missing
        if missing and self.p.require_funding_data:
            raise RuntimeError(f"funding_rate feature missing for {missing}; refusing to produce results without funding")

    # -- helpers -----------------------------------------------------------

    def _count(self, reason: Any) -> None:
        self.reason_counts[reason.value] = self.reason_counts.get(reason.value, 0) + 1

    def _log(self, ts_ms: int, symbol: str, action: str, reason: Any, **kw: Any) -> None:
        if len(self.logs) >= MAX_LOG_RECORDS:
            self.logs_dropped += 1
            return
        self.logs.append(logic.make_log(ts_ms, symbol, action, reason, **kw))

    def _slots_used(self) -> int:
        return sum(1 for s in self.states.values() if s.trade is not None or s.pending is not None)

    def _open_notional(self) -> float:
        total = 0.0
        for s in self.states.values():
            if s.trade is not None:
                total += s.trade["qty"] * s.trade["entry_px"]
            elif s.pending is not None:
                total += s.pending["notional"]
        return total

    def _rate_at(self, st: _SymbolState, bar_open_ms: int) -> Optional[float]:
        return st.funding.get(bar_open_ms)

    # -- bar handling ------------------------------------------------------

    def on_bar(self, bar: Bar) -> None:
        if not self.funding_ready:
            self._load_funding()
        symbol = bar.bar_type.instrument_id.symbol.value
        st = self.states[symbol]
        ts_ms = bar.ts_event // NS_PER_MS
        decision_ms = ts_ms + self.bar_shift_ms
        bar_open_ms = decision_ms - HOUR_MS
        feats = st.ind.update(float(bar.high), float(bar.low), float(bar.close), float(bar.volume))

        if st.trade is not None:
            self._accrue_funding(st, bar_open_ms, float(bar.open))
            self._manage_time_stop(st, bar_open_ms, decision_ms)

        if decision_ms < self.start_ms or decision_ms > self.end_ms:
            return
        rc = self.regime_counts[symbol]
        if feats.ready:
            rc["bars_ready"] += 1
            ok, why = logic.regime_ok(feats, self.p)
            if ok:
                rc["bars_regime_ok"] += 1
            else:
                key = {RC.REGIME_ADX_LOW: "adx_low", RC.REGIME_ATR_PCT_LOW: "atr_pct_low", RC.REGIME_ATR_PCT_HIGH: "atr_pct_high"}[why]
                rc[key] += 1
        self._evaluate_entry(st, feats, decision_ms, bar_open_ms)

    def _accrue_funding(self, st: _SymbolState, bar_open_ms: int, open_px: float) -> None:
        hour, rem = divmod(bar_open_ms % (24 * HOUR_MS), HOUR_MS)
        if rem != 0 or hour not in self.p.funding_hours_utc:
            return
        trade = st.trade
        if trade is None or trade["entry_ts_ms"] >= bar_open_ms:
            return
        rate = self._rate_at(st, bar_open_ms)
        if rate is None:
            trade["funding_missing"] += 1
            return
        trade["funding_paid"] += rate * trade["qty"] * open_px

    def _manage_time_stop(self, st: _SymbolState, bar_open_ms: int, decision_ms: int) -> None:
        trade = st.trade
        if trade is None or st.time_stop_sent or self.stopping:
            return
        if bar_open_ms - trade["entry_ts_ms"] >= int(self.p.time_stop_hours * HOUR_MS):
            st.time_stop_sent = True
            self.cancel_all_orders(st.iid)
            order = self.order_factory.market(
                instrument_id=st.iid, order_side=OrderSide.SELL,
                quantity=Quantity.from_str(str(trade["qty_dec"])), time_in_force=TimeInForce.GTC,
                tags=["TIME"],
            )
            self.submit_order(order)

    def _evaluate_entry(self, st: _SymbolState, feats: Any, decision_ms: int, bar_open_ms: int) -> None:
        p = self.p
        reason = logic.evaluate_signal(feats, p)
        if reason == RC.NO_SIGNAL or reason == RC.REGIME_WARMUP:
            return
        self._count(reason)
        if reason != RC.SIGNAL_LONG_ENTRY:
            self._log(decision_ms, st.symbol, "no_trade", reason, adx=feats.adx, atr_pct_rank=feats.atr_pct_rank, vol_ratio=feats.vol_ratio)
            return

        def skip(why: Any, **detail: Any) -> None:
            self._count(why)
            self._log(decision_ms, st.symbol, "no_trade", why, intended_price=feats.close, **detail)

        if st.trade is not None or st.pending is not None:
            return skip(RC.SKIP_SYMBOL_OCCUPIED)
        if self._slots_used() >= p.max_concurrent:
            return skip(RC.SKIP_MAX_CONCURRENT)
        gate = self.risk.entry_gate(decision_ms)
        if gate is not None:
            return skip(gate)
        if logic.in_funding_window(decision_ms, int(p.funding_window_minutes), p.funding_hours_utc):
            return skip(RC.NO_TRADE_FUNDING_WINDOW)
        rate = self._rate_at(st, bar_open_ms)
        if rate is None:
            if p.require_funding_data:
                return skip(RC.SKIP_FUNDING_UNAVAILABLE)
        elif logic.funding_adverse(rate, "long", p.funding_adverse_max):
            return skip(RC.SKIP_FUNDING_RATE_ADVERSE, funding_rate=rate)
        plan, why = logic.plan_long_entry(
            close=feats.close, atr=feats.atr, spec=st.spec, p=p,
            equity=p.equity_basis, open_notional=self._open_notional(),
        )
        if plan is None:
            return skip(why, atr=feats.atr)
        self._submit_entry(st, plan, decision_ms)

    def _submit_entry(self, st: _SymbolState, plan: Any, decision_ms: int) -> None:
        expire_ms = logic.entry_expiry_ms(decision_ms, self.p)
        bracket = self.order_factory.bracket(
            instrument_id=st.iid,
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str(str(plan.qty)),
            entry_order_type=OrderType.LIMIT,
            entry_price=Price.from_str(str(plan.entry)),
            time_in_force=TimeInForce.GTD,
            expire_time=pd.Timestamp(expire_ms, unit="ms", tz="UTC"),
            entry_tags=["ENTRY"],
            tp_order_type=OrderType.MARKET_IF_TOUCHED,
            tp_trigger_price=Price.from_str(str(plan.take_profit)),
            tp_tags=["TP"],
            sl_order_type=OrderType.STOP_MARKET,
            sl_trigger_price=Price.from_str(str(plan.stop)),
            sl_tags=["SL"],
        )
        st.pending = {"plan": plan, "notional": plan.notional, "placed_ms": decision_ms, "expire_ms": expire_ms}
        st.time_stop_sent = False
        self._count(RC.ORDER_PLACED)
        self.submit_order_list(bracket)
        self._log(
            decision_ms, st.symbol, "place_entry", RC.ORDER_PLACED, intended_price=plan.entry,
            qty=plan.qty, stop=float(plan.stop), take_profit=float(plan.take_profit),
            risk_at_stop_usdt=plan.risk_at_stop_usdt, required_leverage=plan.required_leverage,
            expire=logic.iso(expire_ms),
        )

    # -- order events ------------------------------------------------------

    def _tag(self, client_order_id: Any) -> str:
        order = self.cache.order(client_order_id)
        tags = getattr(order, "tags", None) or []
        return str(tags[0]) if tags else ""

    def on_order_filled(self, event: Any) -> None:
        if self.stopping:
            return
        st = self.states.get(event.instrument_id.symbol.value)
        if st is None:
            return
        tag = self._tag(event.client_order_id)
        ts_ms = event.ts_event // NS_PER_MS
        px, qty = float(event.last_px), float(event.last_qty)
        if tag == "ENTRY":
            plan = st.pending["plan"] if st.pending else None
            if plan is None:
                return
            st.trade = {
                "entry_px": px, "qty": qty, "qty_dec": plan.qty, "entry_ts_ms": ts_ms,
                "plan_entry": float(plan.entry), "stop": float(plan.stop), "tp": float(plan.take_profit),
                "r_usdt": plan.risk_at_stop_usdt, "funding_paid": 0.0, "funding_missing": 0,
            }
            st.pending = None
            self._count(RC.ORDER_FILLED)
            self._log(ts_ms, st.symbol, "entry_fill", RC.ORDER_FILLED, intended_price=plan.entry, filled_price=px, qty=qty,
                      fee_usdt=px * qty * float(st.spec.maker_fee) * self.cost_mult)
        elif tag in ("SL", "TP", "TIME") and st.trade is not None:
            reason = {"SL": RC.EXIT_STOP_LOSS, "TP": RC.EXIT_TAKE_PROFIT, "TIME": RC.EXIT_TIME_STOP}[tag]
            self._finish_trade(st, px, ts_ms, reason)

    def _finish_trade(self, st: _SymbolState, exit_px: float, ts_ms: int, reason: Any) -> None:
        t = st.trade
        if t is None:
            return
        spec = st.spec
        costs = logic.trade_costs_1x(
            entry_px=t["entry_px"], exit_px=exit_px, qty=t["qty"], tick=float(spec.tick),
            maker_fee=float(spec.maker_fee), taker_fee=float(spec.taker_fee),
            slippage_ticks=float(self.p.slippage_ticks), funding_paid=t["funding_paid"],
        )
        gross = (exit_px - t["entry_px"]) * t["qty"]
        net = gross - self.cost_mult * costs["total"]
        record = {
            "symbol": st.symbol, "entry_ts_ms": t["entry_ts_ms"], "exit_ts_ms": ts_ms,
            "entry_px": t["entry_px"], "exit_px": exit_px, "qty": t["qty"],
            "stop": t["stop"], "tp": t["tp"], "r_usdt": t["r_usdt"],
            "gross_pnl": gross, "costs_1x_total": costs["total"], "costs_1x": costs,
            "net_pnl": net, "net_r": net / t["r_usdt"], "exit_reason": reason.value,
            "hold_hours": (ts_ms - t["entry_ts_ms"]) / HOUR_MS,
            "funding_missing_settlements": t["funding_missing"],
        }
        self.trades.append(record)
        self.risk.record_trade(ts_ms, net)
        self._count(reason)
        self._log(
            ts_ms, st.symbol, "exit", reason, intended_price=(t["stop"] if reason == RC.EXIT_STOP_LOSS else t["tp"] if reason == RC.EXIT_TAKE_PROFIT else None),
            filled_price=exit_px, qty=t["qty"],
            fee_usdt=(costs["fee_entry"] + costs["fee_exit"]) * self.cost_mult,
            funding_usdt=costs["funding"] * self.cost_mult, pnl_usdt=net, net_r=record["net_r"],
        )
        st.trade = None
        st.time_stop_sent = False

    def _entry_ended(self, event: Any, reason: Any) -> None:
        st = self.states.get(event.instrument_id.symbol.value)
        if st is None or self.stopping or self._tag(event.client_order_id) != "ENTRY":
            return
        st.pending = None
        self._count(reason)
        self._log(event.ts_event // NS_PER_MS, st.symbol, "entry_ended", reason)

    def on_order_expired(self, event: Any) -> None:
        self._entry_ended(event, RC.ORDER_EXPIRED_UNFILLED)

    def on_order_canceled(self, event: Any) -> None:
        self._entry_ended(event, RC.ORDER_EXPIRED_UNFILLED)

    def on_order_rejected(self, event: Any) -> None:
        self._entry_ended(event, RC.ORDER_REJECTED)

    def on_order_denied(self, event: Any) -> None:
        self._entry_ended(event, RC.ORDER_REJECTED)

    # -- shutdown ----------------------------------------------------------

    def on_stop(self) -> None:
        self.stopping = True
        open_at_end = [s.symbol for s in self.states.values() if s.trade is not None]
        payload = {
            "param_hash": logic.param_hash(self.p),
            "trades": self.trades,
            "logs": self.logs,
            "logs_dropped": self.logs_dropped,
            "reason_counts": self.reason_counts,
            "regime_counts": self.regime_counts,
            "risk_events": [{"timestamp": logic.iso(t), "reason_code": c.value, "detail": d} for t, c, d in self.risk.events],
            "halts": self.risk.halts,
            "open_at_end_excluded": open_at_end,
            "funding_modelled": self.funding_modelled,
            "cost_multiplier": self.cost_mult,
        }
        RESULTS.clear()
        RESULTS.update(payload)
        try:
            out = Path("output")
            out.mkdir(parents=True, exist_ok=True)
            (out / "playbook_raw.json").write_text(json.dumps(payload, default=str), encoding="utf-8")
        except OSError:
            pass
        for st in self.states.values():
            self.cancel_all_orders(st.iid)
            self.close_all_positions(st.iid)
