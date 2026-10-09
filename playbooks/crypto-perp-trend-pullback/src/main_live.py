"""Live hourly cycle: reconcile -> halts -> manage -> scan -> filter -> order -> log.

Runs at HH:16 UTC so every new entry is placed outside the +/-15 minute window
around 00/08/16 UTC funding settlements. State lives in ``.state/`` (the only
persisted path); if state is missing while positions exist, those positions are
treated as foreign and the Playbook halts without touching them.
"""

import json
import math
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any, Callable, Optional

from getagent import data, runtime

from .market_data import _ts_ms, funding_rows, kline_rows
from .signals import HOUR_MS, Params, evaluate_setup, expected_funding_usdt, in_funding_blackout

STATE_PATH = Path(".state") / "crypto_majors_trend_pullback.json"
DAY_MS = 86_400_000
MAX_LOG = 1000

# Bitget USDT-FUTURES public contract config (fallback if trade.helpers rules lack a field).
SPEC_FALLBACK = {
    "BTCUSDT": {"tick": "0.1", "step": "0.0001", "min_qty": "0.0001", "min_notional": "5"},
    "ETHUSDT": {"tick": "0.01", "step": "0.01", "min_qty": "0.01", "min_notional": "5"},
    "SOLUSDT": {"tick": "0.001", "step": "0.1", "min_qty": "0.1", "min_notional": "5"},
}


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _iso(ms: Optional[int]) -> Optional[str]:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(value: Any) -> Optional[float]:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (ValueError, OSError):
            pass
    return {"version": "v1", "orders": {}, "positions": {}, "closed": [], "halt": None, "log": []}


def _save_state(state: dict) -> None:
    state["log"] = state.get("log", [])[-MAX_LOG:]
    state["closed"] = state.get("closed", [])[-500:]
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, default=str))


def _rows(result: Any) -> list[dict]:
    """First list of dict rows found in a trade envelope."""
    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict)]
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    elif hasattr(result, "dict") and callable(result.dict):
        result = result.dict()
    if isinstance(result, dict):
        for key in ("data", "list", "entrustedList", "fillList", "orderList", "result", "rows"):
            if key in result:
                found = _rows(result[key])
                if found:
                    return found
    return []


def _first(row: dict, *keys: str) -> Any:
    for key in keys:
        if row.get(key) not in (None, ""):
            return row[key]
    return None


def _order_id(result: Any) -> Optional[str]:
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    if isinstance(result, dict):
        for key in ("orderId", "order_id", "id"):
            if result.get(key):
                return str(result[key])
        for key in ("data", "result", "order"):
            if key in result:
                found = _order_id(result[key])
                if found:
                    return found
    return None


def _fill_summary(trade: Any, symbol: str, order_id: str = "", since_ms: int = 0) -> dict:
    res = trade.contract.fills(symbol=symbol, order_id=order_id, limit=100)
    rows = [r for r in _rows(res) if (_f(_first(r, "cTime", "ctime", "ts")) or 0) >= since_ms]
    qty = px_qty = fees = profit = 0.0
    last_ts = None
    for r in rows:
        q = _f(_first(r, "baseVolume", "size", "fillQty", "qty")) or 0.0
        px = _f(_first(r, "price", "priceAvg", "fillPrice")) or 0.0
        qty += q
        px_qty += q * px
        fee = 0.0
        details = r.get("feeDetail")
        if isinstance(details, list):
            fee = sum(_f(_first(d, "totalFee", "fee")) or 0.0 for d in details if isinstance(d, dict))
        else:
            fee = _f(_first(r, "fee", "totalFee")) or 0.0
        fees += -abs(fee)
        profit += _f(_first(r, "profit", "pnl")) or 0.0
        ts = _f(_first(r, "cTime", "ctime", "ts"))
        if ts is not None:
            last_ts = int(max(last_ts or 0, ts))
    return {"qty": qty, "avg_price": (px_qty / qty) if qty else None, "fees": fees,
            "profit": profit, "last_ts": last_ts, "rows": len(rows)}


def _rules(trade: Any, symbol: str) -> dict:
    fb = SPEC_FALLBACK.get(symbol, {})
    out = {k: Decimal(v) for k, v in fb.items()}
    try:
        r = trade.helpers.contract_rules(symbol)
    except Exception:  # noqa: BLE001
        return out
    for key, names in (("tick", ("price_step", "tick_size")),
                       ("step", ("qty_step", "size_step", "quantity_step", "lot_size")),
                       ("min_qty", ("min_qty", "min_trade_qty", "min_order_qty")),
                       ("min_notional", ("min_notional", "min_trade_usdt", "min_order_notional"))):
        for name in names:
            value = getattr(r, name, None)
            if value not in (None, "") and Decimal(str(value)) > 0:
                out[key] = Decimal(str(value))
                break
    return out


def _q(value: float, step: Decimal) -> Decimal:
    return (Decimal(str(value)) / step).to_integral_value(rounding=ROUND_DOWN) * step


class Cycle:
    def __init__(self) -> None:
        self.cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
        self.p = Params.from_config(self.cfg)
        self.now = _now_ms()
        self.state = _load_state()
        self.actions: list[dict] = []
        self.entries_blocked: list[str] = []

    def log(self, code: str, symbol: str = "", **kw: Any) -> dict:
        entry = {"timestamp": _iso(self.now), "symbol": symbol, "side": kw.pop("side", "long" if symbol else ""),
                 "intended_price": kw.pop("intended_price", None), "filled_price": kw.pop("filled_price", None),
                 "fees": kw.pop("fees", None), "funding": kw.pop("funding", None), "reason_code": code, **kw}
        self.actions.append(entry)
        self.state.setdefault("log", []).append(entry)
        return entry

    def act(self, action: str, symbol: str, code: str, execute: Callable[[], Any], **meta: Any) -> Any:
        holder: dict[str, Any] = {}

        def _run() -> Any:
            holder["result"] = execute()
            return holder["result"]

        runtime.emit_signal_or_follow(
            action=action,
            symbol=symbol,
            confidence=1.0,
            metrics={},
            meta={"reason_code": code, **meta},
            execute_trade=_run,
            reason_code=code,
        )
        return holder.get("result")

    def run(self) -> None:
        from getagent import trade

        self.trade = trade
        pos_res = trade.contract.current_position()
        pend_res = trade.contract.pending_orders()
        plan_res = trade.contract.plan_pending_orders()
        if not (trade.is_success(pos_res) and trade.is_success(pend_res) and trade.is_success(plan_res)):
            self.log("HALT_ACCOUNT_QUERY_FAILED")
            self.finish("HALT_ACCOUNT_QUERY_FAILED")
            return
        open_syms = set(trade.helpers.contract_open_symbols(pos_res))
        pending = {str(_first(r, "orderId", "order_id")): r for r in _rows(pend_res)}
        plan_rows = _rows(plan_res)

        self.reconcile_orders(open_syms, pending)
        self.reconcile_positions(open_syms, plan_rows)

        foreign_pos = sorted(s for s in open_syms if s not in self.state["positions"])
        foreign_ord = sorted(oid for oid in pending if oid and oid not in self.state["orders"])
        if foreign_pos or foreign_ord:
            self.log("HALT_FOREIGN_POSITION", positions=foreign_pos, orders=foreign_ord[:20])
            self.entries_blocked.append("HALT_FOREIGN_POSITION")

        self.check_loss_limits()
        if self.state.get("halt"):
            self.entries_blocked.append(self.state["halt"]["code"])

        busy = len(self.state["positions"]) + len(self.state["orders"])
        if busy >= self.p.max_concurrent:
            self.entries_blocked.append("SKIP_CLUSTER_BUSY")

        if not self.entries_blocked:
            self.scan()
        self.finish(self.entries_blocked[0] if self.entries_blocked else "CYCLE_OK")

    def reconcile_orders(self, open_syms: set, pending: dict) -> None:
        for oid, o in list(self.state["orders"].items()):
            sym = o["symbol"]
            if oid in pending:
                if self.now - int(o["placed_ms"]) >= self.p.entry_ttl_hours * HOUR_MS:
                    res = self.act("close", sym, "ENTRY_CANCEL_4H",
                                   lambda s=sym, i=oid: self.trade.contract.cancel_order(symbol=s, order_id=i),
                                   order_id=oid)
                    check = self.trade.contract.pending_orders(symbol=sym)
                    still = any(str(_first(r, "orderId", "order_id")) == oid for r in _rows(check))
                    if res is not None and not still:
                        self.log("ENTRY_CANCEL_4H", sym, intended_price=o["limit"], order_id=oid)
                        del self.state["orders"][oid]
                    else:
                        self.log("ENTRY_CANCEL_PENDING", sym, intended_price=o["limit"], order_id=oid)
                continue
            if sym in open_syms:
                fill = _fill_summary(self.trade, sym, order_id=oid)
                self.state["positions"][sym] = {
                    **o,
                    "entry_order_id": oid,
                    "fill_price": fill["avg_price"] or o["limit"],
                    "fill_ms": fill["last_ts"] or self.now,
                    "entry_fees": fill["fees"],
                }
                self.log("ENTRY_FILLED", sym, intended_price=o["limit"], filled_price=fill["avg_price"],
                         fees=fill["fees"], order_id=oid)
            else:
                self.log("ENTRY_ORDER_GONE", sym, intended_price=o["limit"], order_id=oid)
            del self.state["orders"][oid]

    def reconcile_positions(self, open_syms: set, plan_rows: list[dict]) -> None:
        for sym, pos in list(self.state["positions"].items()):
            if sym not in open_syms:
                fill = _fill_summary(self.trade, sym, since_ms=int(pos["fill_ms"]) + 1)
                exit_px = fill["avg_price"]
                code = "EXIT_UNKNOWN"
                if exit_px is not None:
                    code = "EXIT_TP" if exit_px >= float(pos["tp"]) * 0.999 else (
                        "EXIT_SL" if exit_px <= float(pos["stop"]) * 1.001 else pos.get("pending_exit", "EXIT_OTHER"))
                net = fill["profit"] + fill["fees"] + float(pos.get("entry_fees") or 0.0)
                self.state["closed"].append({"symbol": sym, "ts": fill["last_ts"] or self.now, "net": net,
                                             "r": net / self.p.risk_usdt, "code": code})
                self.log(code, sym, side="sell", intended_price=pos.get("tp") if code == "EXIT_TP" else pos.get("stop"),
                         filled_price=exit_px, fees=fill["fees"], funding="PENDING_NOT_IN_FILLS",
                         net_usdt=round(net, 4))
                del self.state["positions"][sym]
                continue
            if self.now - int(pos["fill_ms"]) >= self.p.time_stop_hours * HOUR_MS:
                self.close(sym, "EXIT_TIME_STOP")
                continue
            has_sl = any(
                str(_first(r, "symbol")).upper() == sym
                and "loss" in str(_first(r, "planType", "plan_type") or "").lower()
                for r in plan_rows
            )
            if not has_sl:
                self.close(sym, "EXIT_SAFETY_NO_SL")

    def close(self, sym: str, code: str) -> None:
        self.state["positions"][sym]["pending_exit"] = code
        res = self.act("close", sym, code,
                       lambda s=sym: self.trade.contract.close_position(symbol=s, hold_side="long"))
        self.log(code + ("_SENT" if res is not None else "_NOT_EXECUTED"), sym, side="sell")

    def check_loss_limits(self) -> None:
        day0 = self.now - self.now % DAY_MS
        day_pnl = sum(c["net"] for c in self.state["closed"] if int(c["ts"]) >= day0)
        streak = 0
        for c in reversed(self.state["closed"]):
            if c["net"] < 0:
                streak += 1
            else:
                break
        if self.state.get("halt") is None:
            if day_pnl <= -self.p.daily_stop_usdt:
                self.state["halt"] = {"code": "HALT_DAILY_STOP", "ts": self.now, "day_pnl": day_pnl}
                self.log("HALT_DAILY_STOP", day_pnl=round(day_pnl, 4),
                         note="Stop this Playbook in the GetAgent page; it will not open new trades.")
            elif streak >= self.p.max_consecutive_losses:
                self.state["halt"] = {"code": "HALT_CONSEC_LOSSES", "ts": self.now, "streak": streak}
                self.log("HALT_CONSEC_LOSSES", streak=streak,
                         note="Review required; restart the Playbook instance to resume.")
        if day_pnl <= -self.p.daily_pause_usdt:
            self.entries_blocked.append("PAUSE_DAILY_LOSS")

    def scan(self) -> None:
        cands = []
        stale = 0
        for sym in self.p.symbols:
            c = self.evaluate(sym)
            if c.get("stale"):
                stale += 1
            if c.get("ok"):
                cands.append(c)
        if stale == len(self.p.symbols):
            self.log("HALT_STALE_DATA")
            return
        if not cands:
            return
        best = max(cands, key=lambda c: c["adx"])
        for c in cands:
            if c is not best:
                self.log("SKIP_CLUSTER_RANKED_OUT", c["symbol"])
        self.place(best)

    def evaluate(self, sym: str) -> dict:
        try:
            tick_rows = data.to_records(data.crypto.futures.ticker(symbol=sym, exchange="bitget")) or []
        except Exception as exc:  # noqa: BLE001
            self.log("NO_TRADE_DATA_ERROR", sym, error=str(exc)[:200])
            return {"stale": True}
        t = tick_rows[0] if tick_rows else {}
        tick_ts = _ts_ms(t, "timestamp")
        if tick_ts is None or self.now - tick_ts > self.p.max_data_age_seconds * 1000:
            self.log("HALT_STALE_DATA", sym, age_s=None if tick_ts is None else round((self.now - tick_ts) / 1000, 1))
            return {"stale": True}
        bid, ask = _f(t.get("bid")), _f(t.get("ask"))
        if not bid or not ask or ask < bid:
            self.log("NO_TRADE_SIGNAL_INVALID", sym, why="bad bid/ask")
            return {}
        spread_bps = (ask - bid) / ((ask + bid) / 2) * 10_000
        if spread_bps > self.p.max_spread_bps:
            self.log("SKIP_SPREAD", sym, spread_bps=round(spread_bps, 3))
            return {}
        qv = _f(t.get("quote_volume"))
        if qv is None or qv < self.p.min_quote_volume_usd:
            self.log("SKIP_VOLUME", sym, quote_volume=qv)
            return {}

        last_closed_open = self.now - self.now % HOUR_MS - HOUR_MS
        bars = kline_rows(sym, last_closed_open - 999 * HOUR_MS, last_closed_open + HOUR_MS)
        if len(bars) < self.p.warmup_bars or bars[-1]["ts"] != last_closed_open:
            self.log("NO_TRADE_SIGNAL_INVALID", sym, bars=len(bars),
                     last_bar=_iso(bars[-1]["ts"]) if bars else None)
            return {}
        ind = self.p.new_indicator_state()
        snap = None
        for b in bars:
            snap = ind.update(b["high"], b["low"], b["close"], b["volume"])
        setup = evaluate_setup(snap, self.p)
        if not setup.ok:
            self.log(setup.reason, sym)
            return {}
        signal_close = last_closed_open + HOUR_MS
        if in_funding_blackout(signal_close, self.p):
            self.log("SKIP_FUNDING_WINDOW", sym)
            return {}

        rules = _rules(self.trade, sym)
        limit = _q(setup.limit, rules["tick"])
        stop = _q(setup.stop, rules["tick"])
        tp = _q(setup.take_profit, rules["tick"])
        dist = limit - stop
        if dist <= 0:
            self.log("NO_TRADE_SIGNAL_INVALID", sym)
            return {}
        qty = _q(float(Decimal(str(self.p.risk_usdt)) / dist), rules["step"])
        notional = qty * limit
        if qty < rules["min_qty"] or notional < rules["min_notional"]:
            self.log("SKIP_SIZE_MIN", sym, qty=str(qty))
            return {}
        if notional > Decimal(str(self.p.leverage * self.p.margin_budget)):
            self.log("SKIP_SIZE_CAP", sym, notional=str(notional))
            return {}

        frows = funding_rows(sym, self.now - 2 * DAY_MS, self.now)
        rate = frows[-1]["funding_rate"] if frows else None
        fund = expected_funding_usdt(rate, float(notional), self.now, self.p)
        if fund is None:
            self.log("SKIP_FUNDING_UNKNOWN", sym)
            return {}
        if fund > self.p.max_funding_r * self.p.risk_usdt:
            self.log("SKIP_FUNDING_COST", sym, expected_funding=round(fund, 4))
            return {}
        return {"ok": True, "symbol": sym, "adx": setup.adx, "atr": setup.atr, "limit": limit, "stop": stop,
                "tp": tp, "qty": qty, "signal_close_ms": signal_close, "funding_rate": rate,
                "expected_funding": fund, "spread_bps": spread_bps}

    def place(self, c: dict) -> None:
        sym = c["symbol"]
        lev = self.p.leverage
        plan = self.trade.helpers.resolve_contract_tpsl(
            symbol=sym, side="long", leverage=lev, tp_trigger_price=str(c["tp"]),
            sl_trigger_price=str(c["stop"]), reference_price=str(c["limit"]),
        )
        tp_px = str(getattr(plan, "tp_trigger_price", "") or c["tp"])
        sl_px = str(getattr(plan, "sl_trigger_price", "") or c["stop"])

        def execute() -> Any:
            lev_res = self.trade.contract.change_leverage(symbol=sym, leverage=lev)
            if not self.trade.is_success(lev_res):
                raise RuntimeError(f"change_leverage failed: {lev_res}")
            res = self.trade.contract.place_order(
                symbol=sym, side="buy", order_type="limit", qty=str(c["qty"]), price=str(c["limit"]),
                margin_mode=str(self.cfg.get("margin_mode", "isolated")), trade_side="open",
                tp_trigger_price=tp_px, sl_trigger_price=sl_px,
            )
            if not self.trade.is_success(res):
                raise RuntimeError(f"place_order failed: {res}")
            return res

        res = self.act("long", sym, "ENTRY_LIMIT_PLACED", execute, limit=str(c["limit"]), stop=sl_px, tp=tp_px,
                       qty=str(c["qty"]), adx=round(c["adx"], 2))
        oid = _order_id(res) if res is not None else None
        if oid:
            self.state["orders"][oid] = {"symbol": sym, "limit": float(c["limit"]), "stop": float(sl_px),
                                         "tp": float(tp_px), "qty": float(c["qty"]), "placed_ms": self.now,
                                         "signal_close_ms": c["signal_close_ms"]}
            self.log("ENTRY_LIMIT_PLACED", sym, intended_price=float(c["limit"]), order_id=oid,
                     stop=float(sl_px), tp=float(tp_px), qty=float(c["qty"]),
                     expected_funding=round(c["expected_funding"], 4), spread_bps=round(c["spread_bps"], 3))
        else:
            self.log("ENTRY_SIGNAL_ONLY", sym, intended_price=float(c["limit"]),
                     note="signal emitted; no order placed (not follow-trade or order rejected)")

    def finish(self, status: str) -> None:
        _save_state(self.state)
        runtime.emit_signal(
            action="watch",
            symbol=self.p.symbols[0],
            confidence=0.0,
            metrics={"open_positions": len(self.state["positions"]), "pending_orders": len(self.state["orders"]),
                     "closed_trades": len(self.state["closed"])},
            meta={"status": status, "halt": self.state.get("halt"), "actions": self.actions[-50:],
                  "version": self.state.get("version", "v1")},
        )


def run() -> None:
    Cycle().run()
