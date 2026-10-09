"""Nautilus replay strategy for the crypto-majors trend-pullback sleeve.

Execution mirrors the live contract: one limit entry at a time across the
crypto-majors cluster, stop and 2R target attached on fill, 4-bar entry TTL,
8-bar time stop. Every action is written to a JSON ledger that
``main_backtest`` turns into net-of-cost R metrics.
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
    from .signals import Params, evaluate_setup, expected_funding_usdt, in_funding_blackout, size_order
except ImportError:
    try:
        from signals import Params, evaluate_setup, expected_funding_usdt, in_funding_blackout, size_order
    except ImportError:
        from src.signals import Params, evaluate_setup, expected_funding_usdt, in_funding_blackout, size_order

HOUR_NS = 3_600_000_000_000


class TrendPullbackConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    symbols_csv: str = "BTCUSDT,ETHUSDT,SOLUSDT"
    venue_name: str = "BITGET"
    params_json: str = "{}"
    trade_start_ms: int = 0
    trade_end_ms: int = 0
    min_notional_usdt: float = 5.0
    ledger_path: str = "output/trades_ledger.json"


class TrendPullbackStrategy(Strategy):
    def __init__(self, config: TrendPullbackConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self.p = Params.from_config(json.loads(config.params_json or "{}"))
        self._ids: list[InstrumentId] = []
        self._bar_types: list[BarType] = []
        self._ind: dict[str, Any] = {}
        self._feature: dict[str, Any] = {}
        self._open_time_index: dict[str, set] = {}
        self._funding_by_ts: dict[str, dict[int, float]] = {}
        self._pending_ts: Optional[int] = None
        self._candidates: list[dict] = []
        self._seen_this_ts: set[str] = set()

        self._active: Optional[dict] = None
        self._trades: list[dict] = []
        self._events: list[dict] = []
        self._skips: dict[str, int] = {}
        self._day: Optional[int] = None
        self._day_pnl = 0.0
        self._day_paused = False
        self._consec_losses = 0
        self._halt_events: list[dict] = []
        self._needs_exit_bar: Optional[dict] = None

    def set_feature_frames(self, feature_frames: dict) -> None:
        self.feature_frames = feature_frames
        for key, frame in (feature_frames or {}).items():
            sym = str(key).split(".")[0]
            idx_ns = [int(ts.value) for ts in frame.index]
            self._open_time_index[sym] = set(idx_ns)
            if "funding_rate" in frame.columns:
                rates = frame["funding_rate"].tolist()
                self._funding_by_ts[sym] = {
                    ts: float(r) for ts, r in zip(idx_ns, rates) if r is not None and math.isfinite(float(r))
                }

    def on_start(self) -> None:
        ids = list(self.cfg.instrument_ids)
        bts = list(self.cfg.bar_types)
        if not ids:
            if self.cfg.instrument_id is not None and self.cfg.bar_type is not None and len(self.p.symbols) == 1:
                ids, bts = [self.cfg.instrument_id], [self.cfg.bar_type]
            else:
                syms = [s.strip() for s in self.cfg.symbols_csv.split(",") if s.strip()]
                ids = [InstrumentId.from_str(f"{s}.{self.cfg.venue_name}") for s in syms]
                bts = [BarType.from_str(f"{s}.{self.cfg.venue_name}-1-HOUR-LAST-EXTERNAL") for s in syms]
        self._ids, self._bar_types = ids, bts
        for iid in ids:
            self._ind[iid.symbol.value] = self.p.new_indicator_state()
        for bt in bts:
            self.subscribe_bars(bt)

    def on_bar(self, bar: Bar) -> None:
        iid = bar.bar_type.instrument_id
        sym = iid.symbol.value
        ts = int(bar.ts_event)
        open_ns = ts - HOUR_NS if ts not in self._open_time_index.get(sym, ()) else ts
        close_ms = (open_ns + HOUR_NS) // 1_000_000

        if self._pending_ts is not None and ts != self._pending_ts:
            self._flush_candidates()
        self._pending_ts = ts
        self._seen_this_ts.add(sym)

        high, low, close = float(bar.high), float(bar.low), float(bar.close)
        snap = self._ind[sym].update(high, low, close, float(bar.volume))

        rec = self._needs_exit_bar
        if rec is not None and rec["symbol"] == sym:
            # The matching engine fills on this bar before the strategy sees it.
            if low <= rec["stop"] and high >= rec["tp"]:
                rec["exit_bar_both_touched"] = True
            if rec["bars_held"] == 0 and low <= rec["stop"]:
                rec["entry_bar_stop_touched"] = True
            self._needs_exit_bar = None

        self._roll_day(close_ms)
        self._manage_active(sym, iid, high, low, close_ms)

        if self.cfg.trade_start_ms <= close_ms and (self.cfg.trade_end_ms == 0 or close_ms <= self.cfg.trade_end_ms):
            self._consider(sym, iid, snap, close_ms, open_ns)

        if len(self._seen_this_ts) >= len(self._ids):
            self._flush_candidates()

    def _skip(self, reason: str) -> None:
        self._skips[reason] = self._skips.get(reason, 0) + 1

    def _consider(self, sym: str, iid: InstrumentId, snap: Any, close_ms: int, open_ns: int) -> None:
        setup = evaluate_setup(snap, self.p)
        if not setup.ok:
            self._skip(setup.reason)
            return
        if self._active is not None:
            self._skip("SKIP_CLUSTER_BUSY")
            return
        if self._day_paused:
            self._skip("PAUSE_DAILY_LOSS")
            return
        if in_funding_blackout(close_ms, self.p):
            self._skip("SKIP_FUNDING_WINDOW")
            return
        instrument = self.cache.instrument(iid)
        tick = float(instrument.price_increment)
        step = float(instrument.size_increment)
        limit = math.floor(setup.limit / tick + 1e-9) * tick
        stop = math.floor(setup.stop / tick + 1e-9) * tick
        tp = math.floor(setup.take_profit / tick + 1e-9) * tick
        qty, size_reason = size_order(limit, stop, self.p, step, step, self.cfg.min_notional_usdt)
        if qty <= 0:
            self._skip(size_reason)
            return
        rate = self._funding_by_ts.get(sym, {}).get(open_ns)
        fund = expected_funding_usdt(rate, qty * limit, close_ms, self.p)
        if fund is None:
            self._skip("SKIP_FUNDING_UNKNOWN")
            return
        if fund > self.p.max_funding_r * self.p.risk_usdt:
            self._skip("SKIP_FUNDING_COST")
            return
        self._candidates.append(
            {
                "symbol": sym,
                "iid": iid,
                "adx": setup.adx,
                "atr": setup.atr,
                "limit": limit,
                "stop": stop,
                "tp": tp,
                "qty": qty,
                "tick": tick,
                "signal_close_ms": close_ms,
                "funding_rate_at_signal": rate,
            }
        )

    def _flush_candidates(self) -> None:
        cands, self._candidates = self._candidates, []
        self._seen_this_ts = set()
        if not cands or self._active is not None:
            return
        best = max(cands, key=lambda c: c["adx"])
        for c in cands:
            if c is not best:
                self._skip("SKIP_CLUSTER_RANKED_OUT")
        self._submit_entry(best)

    def _submit_entry(self, c: dict) -> None:
        instrument = self.cache.instrument(c["iid"])
        order = self.order_factory.limit(
            instrument_id=c["iid"],
            order_side=OrderSide.BUY,
            quantity=instrument.make_qty(c["qty"]),
            price=instrument.make_price(c["limit"]),
            time_in_force=TimeInForce.GTC,
        )
        self._active = {
            **{k: v for k, v in c.items() if k != "iid"},
            "iid": c["iid"],
            "state": "PENDING",
            "entry_order_id": order.client_order_id,
            "bars_pending": 0,
            "bars_held": 0,
            "fill_price": None,
            "fill_bar_close_ms": None,
            "sl_order_id": None,
            "tp_order_id": None,
            "exit_order_id": None,
            "exit_reason": None,
            "entry_bar_stop_touched": False,
            "exit_bar_both_touched": False,
        }
        self._log("ENTRY_LIMIT_PLACED", c["symbol"], c["signal_close_ms"], price=c["limit"], qty=c["qty"])
        self.submit_order(order)

    def _manage_active(self, sym: str, iid: InstrumentId, high: float, low: float, close_ms: int) -> None:
        a = self._active
        if a is None or a["symbol"] != sym:
            return
        if a["state"] == "PENDING":
            a["bars_pending"] += 1
            if a["bars_pending"] >= self.p.entry_ttl_hours:
                order = self.cache.order(a["entry_order_id"])
                if order is not None and not order.is_closed:
                    self.cancel_order(order)
                self._log("ENTRY_CANCEL_TTL", sym, close_ms, price=a["limit"])
                self._active = None
            return
        if a["state"] == "OPEN":
            a["bars_held"] += 1
            if a["bars_held"] == 1 and low <= a["stop"]:
                a["entry_bar_stop_touched"] = True
            if low <= a["stop"] and high >= a["tp"]:
                a["exit_bar_both_touched"] = True
            a["last_bar_close_ms"] = close_ms
            if a["bars_held"] >= self.p.time_stop_hours and a["state"] == "OPEN":
                self._time_stop(a, close_ms)

    def _time_stop(self, a: dict, close_ms: int) -> None:
        for key in ("sl_order_id", "tp_order_id"):
            oid = a.get(key)
            order = self.cache.order(oid) if oid is not None else None
            if order is not None and not order.is_closed:
                self.cancel_order(order)
        instrument = self.cache.instrument(a["iid"])
        order = self.order_factory.market(
            instrument_id=a["iid"],
            order_side=OrderSide.SELL,
            quantity=instrument.make_qty(a["qty"]),
            reduce_only=True,
        )
        a["exit_order_id"] = order.client_order_id
        a["exit_reason"] = "EXIT_TIME_STOP"
        a["state"] = "CLOSING"
        self.submit_order(order)

    def on_order_rejected(self, event: Any) -> None:
        # A sell stop is rejected when price is already through it at fill time;
        # Bitget's attached stop would trigger immediately, so exit at market.
        a = self._active
        self._log("ORDER_REJECTED", a["symbol"] if a else "", int(event.ts_event) // 1_000_000,
                  order=str(event.client_order_id), why=str(getattr(event, "reason", "")))
        if a is None or a["state"] != "OPEN" or event.client_order_id != a.get("sl_order_id"):
            return
        tp_id = a.get("tp_order_id")
        tp_order = self.cache.order(tp_id) if tp_id is not None else None
        if tp_order is not None and not tp_order.is_closed:
            self.cancel_order(tp_order)
        instrument = self.cache.instrument(a["iid"])
        order = self.order_factory.market(
            instrument_id=a["iid"],
            order_side=OrderSide.SELL,
            quantity=instrument.make_qty(a["qty"]),
            reduce_only=True,
        )
        a["exit_order_id"] = order.client_order_id
        a["exit_reason"] = "EXIT_SL_IMMEDIATE"
        a["state"] = "CLOSING"
        self.submit_order(order)

    def on_order_denied(self, event: Any) -> None:
        a = self._active
        self._log("ORDER_DENIED", a["symbol"] if a else "", int(event.ts_event) // 1_000_000,
                  order=str(event.client_order_id), why=str(getattr(event, "reason", "")))

    def on_order_filled(self, event: Any) -> None:
        a = self._active
        if a is None:
            return
        coid = event.client_order_id
        px = float(event.last_px)
        ts_ms = int(event.ts_event) // 1_000_000
        if coid == a["entry_order_id"] and a["state"] == "PENDING":
            a["state"] = "OPEN"
            a["fill_price"] = px
            a["fill_ts_ms"] = ts_ms
            self._log("ENTRY_FILLED", a["symbol"], ts_ms, price=px, qty=a["qty"])
            instrument = self.cache.instrument(a["iid"])
            qty = instrument.make_qty(a["qty"])
            sl = self.order_factory.stop_market(
                instrument_id=a["iid"],
                order_side=OrderSide.SELL,
                quantity=qty,
                trigger_price=instrument.make_price(a["stop"]),
                reduce_only=True,
            )
            tp = self.order_factory.limit(
                instrument_id=a["iid"],
                order_side=OrderSide.SELL,
                quantity=qty,
                price=instrument.make_price(a["tp"]),
                reduce_only=True,
            )
            a["sl_order_id"], a["tp_order_id"] = sl.client_order_id, tp.client_order_id
            self.submit_order(sl)
            # A rejected stop is handled synchronously and moves the trade to CLOSING.
            if self._active is a and a["state"] == "OPEN":
                self.submit_order(tp)
            return
        if a["state"] not in ("OPEN", "CLOSING"):
            return
        if coid == a.get("sl_order_id"):
            reason, other = "EXIT_SL", a.get("tp_order_id")
        elif coid == a.get("tp_order_id"):
            reason, other = "EXIT_TP", a.get("sl_order_id")
        elif coid == a.get("exit_order_id"):
            reason, other = a.get("exit_reason") or "EXIT_TIME_STOP", None
        else:
            return
        if other is not None:
            order = self.cache.order(other)
            if order is not None and not order.is_closed:
                self.cancel_order(order)
        self._close_trade(a, reason, px, ts_ms)

    def _close_trade(self, a: dict, reason: str, px: float, ts_ms: int) -> None:
        entry = float(a["fill_price"])
        qty = float(a["qty"])
        gross = (px - entry) * qty
        approx_cost = entry * qty * 0.0002 + px * qty * 0.0006 + 2 * a["tick"] * qty
        net = gross - approx_cost
        rec = {
            "symbol": a["symbol"],
            "side": "long",
            "signal_close_ms": a["signal_close_ms"],
            "limit": a["limit"],
            "stop": a["stop"],
            "tp": a["tp"],
            "qty": qty,
            "atr": a["atr"],
            "adx": a["adx"],
            "tick": a["tick"],
            "funding_rate_at_signal": a.get("funding_rate_at_signal"),
            "fill_price": entry,
            "fill_ts_ms": a.get("fill_ts_ms"),
            "exit_price": px,
            "exit_ts_ms": ts_ms,
            "exit_reason": reason,
            "bars_held": a["bars_held"],
            "entry_bar_stop_touched": a["entry_bar_stop_touched"],
            "exit_bar_both_touched": a["exit_bar_both_touched"],
            "approx_net_usdt": net,
        }
        self._trades.append(rec)
        if reason != "EXIT_TIME_STOP":
            self._needs_exit_bar = rec
        self._log(reason, a["symbol"], ts_ms, price=px, qty=qty)
        self._active = None
        self._day_pnl += net
        if net < 0:
            self._consec_losses += 1
        else:
            self._consec_losses = 0
        if self._day_pnl <= -self.p.daily_stop_usdt:
            self._halt_events.append({"ts_ms": ts_ms, "code": "HALT_DAILY_STOP", "day_pnl": self._day_pnl})
            self._day_paused = True
        elif self._day_pnl <= -self.p.daily_pause_usdt:
            self._day_paused = True
        if self._consec_losses >= self.p.max_consecutive_losses:
            self._halt_events.append({"ts_ms": ts_ms, "code": "HALT_CONSEC_LOSSES", "count": self._consec_losses})
            self._consec_losses = 0

    def _roll_day(self, close_ms: int) -> None:
        day = close_ms // 86_400_000
        if day != self._day:
            self._day = day
            self._day_pnl = 0.0
            self._day_paused = False

    def _log(self, code: str, sym: str, ts_ms: int, **kw: Any) -> None:
        self._events.append({"ts_ms": ts_ms, "symbol": sym, "code": code, **kw})

    def on_stop(self) -> None:
        for iid in self._ids:
            self.cancel_all_orders(iid)
            self.close_all_positions(iid)
        out = {
            "trades": self._trades,
            "events": self._events,
            "skips": self._skips,
            "halt_events": self._halt_events,
            "open_at_end": None if self._active is None else {
                k: (str(v) if k.endswith("_id") or k == "iid" else v) for k, v in self._active.items()
            },
        }
        path = Path(self.cfg.ledger_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, default=str))
