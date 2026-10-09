"""Live execution for the BTC/ETH/SOL regime-filtered long Playbook.

Every scheduled tick (every 15 minutes):
  scan -> reconcile account vs persisted state -> risk/halt checks -> manage
  (entry TTL cancel, time stop) -> filter + trigger on the just-closed 1H bar ->
  order (isolated limit with exchange-side TP/SL attached) -> log.

All trade mutations run inside the callback passed to
``runtime.emit_signal_or_follow``. Positions not opened by this Playbook are
never touched: they raise an alert and block new entries.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

from getagent import data, runtime, trade

from .action_log import ActionLog
from .features import (
    cfg_value,
    compute_indicators,
    compute_signals,
    funding_blocks,
    in_funding_window,
    validate_signal,
)
from .risk import RiskState, leverage_cap, plan_entry, rv

HOUR_MS = 3_600_000
DAY_MS = 86_400_000
STATE_DIR = Path(".state")
STATE_PATH = STATE_DIR / "regime_long_state.json"
LOG_PATH = STATE_DIR / "action_log.jsonl"
OUT_DIR = Path("/workspace/output")
MAX_LOG_LINES = 5000
STATE_VERSION = 1

FALLBACK_RULES = {
    "BTCUSDT": {"tick": 0.1, "size_step": 0.0001, "min_qty": 0.0001},
    "ETHUSDT": {"tick": 0.01, "size_step": 0.01, "min_qty": 0.01},
    "SOLUSDT": {"tick": 0.001, "size_step": 0.1, "min_qty": 0.1},
}


# ---------------------------------------------------------------- utilities
def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _f(value: Any) -> Optional[float]:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _first(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def _records(result: Any) -> list[dict[str, Any]]:
    """Find the first list of dict rows inside an SDK envelope (dict, object, or list)."""
    if result is None:
        return []
    if isinstance(result, list):
        if all(isinstance(x, dict) for x in result):
            return result
        return []
    if not isinstance(result, dict):
        for attr in ("data", "raw"):
            inner = getattr(result, attr, None)
            if inner is not None:
                return _records(inner)
        return []
    for key in ("entrustedList", "fillList", "list", "orders", "fills", "positions", "data"):
        if key in result:
            found = _records(result[key])
            if found:
                return found
    return []


def _ms_field(record: dict[str, Any], *keys: str) -> Optional[int]:
    value = _first(record, *keys)
    if value is None:
        return None
    num = _f(value)
    if num is not None:
        return int(num if num > 1e12 else num * 1000)
    try:
        return int(pd.Timestamp(value).tz_convert("UTC").timestamp() * 1000)
    except Exception:
        try:
            return int(pd.Timestamp(value, tz="UTC").timestamp() * 1000)
        except Exception:
            return None


def _order_id(result: Any) -> str:
    if isinstance(result, dict):
        for key in ("orderId", "order_id", "id"):
            if result.get(key):
                return str(result[key])
        for key in ("data", "result"):
            if key in result:
                found = _order_id(result[key])
                if found:
                    return found
    for attr in ("order_id", "orderId", "data"):
        inner = getattr(result, attr, None)
        if inner:
            return inner if isinstance(inner, str) else _order_id(inner)
    return ""


# ---------------------------------------------------------------- state
def _load_state() -> tuple[dict[str, Any], Optional[str]]:
    empty = {"version": STATE_VERSION, "orders": {}, "positions": {}, "risk": RiskState().to_dict(),
             "last_eval_bar": {}, "log_seq": 0, "closing": {}}
    if not STATE_PATH.exists():
        return empty, None
    try:
        state = json.loads(STATE_PATH.read_text())
        if int(state.get("version", 0)) != STATE_VERSION:
            return empty, "HALT_STATE_UNREADABLE"
        for key, default in empty.items():
            state.setdefault(key, default)
        return state, None
    except Exception:
        return empty, "HALT_STATE_UNREADABLE"


def _save(state: dict[str, Any], log: ActionLog) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["log_seq"] = log.seq
    STATE_PATH.write_text(json.dumps(state, default=str))
    old = LOG_PATH.read_text().splitlines() if LOG_PATH.exists() else []
    new = [json.dumps(r, default=str) for r in log.rows]
    LOG_PATH.write_text("\n".join((old + new)[-MAX_LOG_LINES:]) + "\n")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "action_log.json").write_text(json.dumps(log.rows, default=str))


# ---------------------------------------------------------------- market data
def _fetch_bars(symbol: str) -> pd.DataFrame:
    bars = data.crypto.futures.kline(symbol=symbol, interval="1h", exchange="bitget", limit=1000, closed_only=True)
    df = pd.DataFrame(data.to_records(bars))
    if df.empty:
        return df
    col = "time" if "time" in df.columns else "date"
    s = df[col]
    idx = pd.to_datetime(s.astype("int64"), unit="ms", utc=True) if pd.api.types.is_numeric_dtype(s) \
        else pd.to_datetime(s, utc=True)
    df.index = pd.DatetimeIndex(idx)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def _ticker_age_seconds(symbol: str, now_ms: int) -> Optional[float]:
    rows = data.to_records(data.crypto.futures.ticker(symbol=symbol, exchange="bitget"))
    if not rows:
        return None
    ts = _ms_field(rows[-1], "timestamp")
    if ts is None:
        return None
    return (now_ms - ts) / 1000.0


def _funding_8h(symbol: str, interval_hours: float) -> Optional[float]:
    rows = data.to_records(data.crypto.futures.funding_rate(symbol=symbol, exchange="bitget", interval="1h", days=1))
    if not rows:
        return None
    last = rows[-1]
    rate = _f(last.get("estimated_rate"))
    if rate is None:
        rate = _f(last.get("funding_rate"))
    return None if rate is None else rate * 8.0 / interval_hours


# ---------------------------------------------------------------- trade callbacks (run only via emit_signal_or_follow)
def _rules(symbol: str) -> dict[str, float]:
    fb = FALLBACK_RULES[symbol]
    try:
        rules = trade.helpers.contract_rules(symbol)
        tick = _f(getattr(rules, "price_step", None)) or fb["tick"]
        step = _f(getattr(rules, "qty_step", None)) or _f(getattr(rules, "size_step", None)) or fb["size_step"]
        min_qty = _f(getattr(rules, "min_qty", None)) or fb["min_qty"]
        return {"tick": tick, "size_step": step, "min_qty": min_qty}
    except Exception:
        return dict(fb)


def _place_entry(symbol: str, plan: Any, cfg: dict[str, Any], sink: dict[str, Any]) -> dict[str, Any]:
    lev = int(leverage_cap(cfg))
    lev_res = trade.contract.change_leverage(symbol=symbol, leverage=lev)
    if not trade.is_success(lev_res):
        raise RuntimeError(f"change_leverage failed: {lev_res}")
    qty_plan = trade.helpers.compute_qty(symbol=symbol, market="contract", budget_amount=str(round(plan.margin, 4)),
                                         leverage=lev, price=str(plan.limit))
    qty = _f(qty_plan.qty) or 0.0
    loss_at_stop = qty * plan.risk_px
    if qty <= 0 or loss_at_stop > float(rv(cfg, "risk_per_trade_usdt")) * 1.02:
        raise RuntimeError(f"qty {qty} breaks the fixed-risk cap (loss at stop {loss_at_stop:.2f})")
    tpsl = trade.helpers.resolve_contract_tpsl(symbol=symbol, side=plan.side, leverage=lev,
                                               tp_trigger_price=str(plan.tp), sl_trigger_price=str(plan.stop),
                                               reference_price=str(plan.limit))
    result = trade.contract.place_order(
        symbol=symbol, side="buy" if plan.side == "long" else "sell", order_type="limit", qty=qty_plan.qty,
        price=str(plan.limit), margin_mode="isolated",
        tp_trigger_price=tpsl.tp_trigger_price, sl_trigger_price=tpsl.sl_trigger_price,
    )
    if not trade.is_success(result):
        raise RuntimeError(f"place_order failed: {result}")
    sink.update({"executed": True, "order_id": _order_id(result), "qty": qty,
                 "tp": _f(tpsl.tp_trigger_price), "sl": _f(tpsl.sl_trigger_price)})
    return {"order_id": sink["order_id"], "qty": str(qty_plan.qty)}


def _cancel_entry(symbol: str, order_id: str, sink: dict[str, Any]) -> dict[str, Any]:
    pre = trade.contract.pending_orders(symbol=symbol)
    if order_id not in {str(_first(r, "orderId", "order_id")) for r in _records(pre)}:
        sink.update({"executed": True, "already_gone": True})
        return {"status": "not_pending"}
    res = trade.contract.cancel_order(symbol=symbol, order_id=order_id)
    if not trade.is_success(res):
        raise RuntimeError(f"cancel_order failed: {res}")
    post = trade.contract.pending_orders(symbol=symbol)
    still = order_id in {str(_first(r, "orderId", "order_id")) for r in _records(post)}
    sink.update({"executed": not still})
    return {"status": "cancelled" if not still else "still_pending"}


def _time_stop_close(symbol: str, hold_side: str, sink: dict[str, Any]) -> dict[str, Any]:
    pre = trade.contract.current_position(symbol=symbol)
    pos = trade.helpers.find_contract_position(pre, symbol=symbol, hold_side=hold_side)
    if pos is None:
        sink.update({"executed": True, "already_flat": True})
        return {"status": "flat"}
    res = trade.contract.close_position(symbol=symbol, hold_side=hold_side)
    if not trade.is_success(res):
        raise RuntimeError(f"close_position failed: {res}")
    post = trade.contract.current_position(symbol=symbol)
    sink.update({"executed": trade.helpers.find_contract_position(post, symbol=symbol, hold_side=hold_side) is None})
    return {"status": "closed" if sink["executed"] else "still_open"}


def _follow(action: str, symbol: str, reason: str, meta: dict[str, Any], fn: Callable[[dict[str, Any]], Any],
            log: ActionLog, now_ms: int) -> dict[str, Any]:
    sink: dict[str, Any] = {"executed": False}

    def _execute() -> Any:
        return fn(sink)

    try:
        runtime.emit_signal_or_follow(action=action, symbol=symbol, confidence=1.0, metrics={}, meta=meta,
                                      execute_trade=_execute, reason_code=reason)
    except Exception as exc:
        log.add(now_ms, symbol, "ALERT", "ORDER_REJECTED", detail={"error": str(exc)[:500], "meta": meta})
        sink["error"] = str(exc)
    return sink


# ---------------------------------------------------------------- reconciliation
def _fills(symbol: str, order_id: str = "") -> list[dict[str, Any]]:
    return _records(trade.contract.fills(symbol=symbol, order_id=order_id, limit=100))


def _fee(record: dict[str, Any]) -> float:
    detail = record.get("feeDetail")
    if isinstance(detail, list):
        return sum(_f(_first(d, "totalFee", "fee")) or 0.0 for d in detail if isinstance(d, dict))
    return _f(_first(record, "fee", "totalFee")) or 0.0


def _is_close_fill(record: dict[str, Any]) -> bool:
    ts = str(_first(record, "tradeSide", "trade_side") or "").lower()
    return "close" in ts or ts in ("sell_single", "buy_single") and _f(record.get("profit")) not in (None, 0.0)


def _estimate_funding(symbol: str, qty: float, price: float, start_ms: int, end_ms: int, side: str) -> Optional[float]:
    try:
        rows = data.to_records(data.crypto.futures.funding_rate(symbol=symbol, exchange="bitget", interval="1h",
                                                                start_time=start_ms, end_time=end_ms))
    except Exception:
        return None
    total = 0.0
    seen: set[int] = set()
    for r in rows:
        ts = _ms_field(r, "timestamp", "date")
        rate = _f(r.get("funding_rate"))
        if ts is None or rate is None:
            continue
        settle = (ts // HOUR_MS) * HOUR_MS
        hour = (settle // HOUR_MS) % 24
        if hour in (0, 8, 16) and start_ms < settle <= end_ms and settle not in seen:
            seen.add(settle)
            total += (1.0 if side == "long" else -1.0) * qty * price * rate
    return total


def _resolve_close(symbol: str, pos: dict[str, Any], cfg: dict[str, Any]) -> Optional[dict[str, Any]]:
    fills = [f for f in _fills(symbol) if (_ms_field(f, "cTime", "ctime", "time") or 0) >= int(pos["fill_ms"])]
    closes = [f for f in fills if _is_close_fill(f)]
    if not closes:
        return None
    qty = sum(_f(_first(f, "baseVolume", "size", "qty")) or 0.0 for f in closes)
    if qty <= 0:
        return None
    exit_px = sum((_f(_first(f, "price", "priceAvg")) or 0.0) * (_f(_first(f, "baseVolume", "size", "qty")) or 0.0)
                  for f in closes) / qty
    profits = [_f(f.get("profit")) for f in closes]
    if any(p is None for p in profits):
        return None
    close_fees = sum(_fee(f) for f in closes)
    exit_ms = max(_ms_field(f, "cTime", "ctime", "time") or 0 for f in closes)
    funding = _estimate_funding(symbol, float(pos["qty"]), float(pos["entry_filled"]), int(pos["fill_ms"]), exit_ms,
                                pos["side"])
    fees = float(pos.get("entry_fee", 0.0)) + close_fees
    net = sum(p for p in profits if p is not None) + fees - (funding or 0.0)
    r_unit = float(rv(cfg, "risk_per_trade_usdt"))
    if pos.get("time_stop_sent"):
        reason = "TIME_STOP"
    elif abs(exit_px - float(pos["tp"])) <= 0.25 * abs(float(pos["entry_filled"]) - float(pos["sl"])):
        reason = "EXIT_TP"
    elif abs(exit_px - float(pos["sl"])) <= 0.25 * abs(float(pos["entry_filled"]) - float(pos["sl"])):
        reason = "EXIT_SL"
    else:
        reason = "EXIT_OTHER"
    return {"exit_px": exit_px, "exit_ms": exit_ms, "fees": fees, "funding": funding, "net": net,
            "r": net / r_unit, "reason": reason, "intended": float(pos["tp"]) if reason == "EXIT_TP"
            else float(pos["sl"]) if reason == "EXIT_SL" else None}


def _position_rows() -> list[dict[str, Any]]:
    res = trade.contract.current_position()
    rows = trade.helpers.contract_position_records(res)
    out = []
    for r in rows:
        size = _f(_first(r, "total", "size", "available", "qty")) or 0.0
        if size > 0:
            out.append({"symbol": str(_first(r, "symbol") or ""), "size": size,
                        "hold_side": str(_first(r, "holdSide", "hold_side", "side") or ""),
                        "open_price": _f(_first(r, "openPriceAvg", "open_price", "averageOpenPrice"))})
    return out


# ---------------------------------------------------------------- main tick
def run() -> None:
    cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    symbols = [str(s) for s in (cfg.get("trading_symbols") or ["BTCUSDT", "ETHUSDT", "SOLUSDT"])]
    now_ms = _now_ms()
    day = now_ms // DAY_MS
    state, state_err = _load_state()
    log = ActionLog(run_id=str(runtime.run_id or ""), mode="live", start_seq=int(state.get("log_seq", 0)))
    risk = RiskState.from_dict(state["risk"])
    risk.roll(day)
    allowed = ("long", "short") if bool(rv(cfg, "allow_short")) else ("long",)
    block_min = int(rv(cfg, "funding_block_minutes"))
    intervals = cfg.get("funding_interval_hours") or {}
    run_blocks: list[str] = []

    if state_err:
        log.add(now_ms, "*", "HALT", state_err)
        runtime.emit_signal(action="watch", symbol=symbols[0], confidence=0.0, metrics={},
                            meta={"halt": state_err, "log": log.rows})
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "action_log.json").write_text(json.dumps(log.rows, default=str))
        return

    # 1) scan market data + staleness
    market: dict[str, dict[str, Any]] = {}
    stale = False
    for sym in symbols:
        info: dict[str, Any] = {}
        try:
            age = _ticker_age_seconds(sym, now_ms)
            bars = _fetch_bars(sym)
        except Exception as exc:
            age, bars = None, pd.DataFrame()
            info["error"] = str(exc)[:300]
        last_open = int(bars.index[-1].timestamp() * 1000) if len(bars) else None
        bar_stale = last_open is None or now_ms - (last_open + HOUR_MS) > 2 * HOUR_MS
        if age is None or age > float(rv(cfg, "stale_data_seconds")) or bar_stale:
            stale = True
            log.add(now_ms, sym, "HALT", "HALT_STALE_DATA",
                    detail={"ticker_age_s": age, "last_bar_open_ms": last_open, **info})
        info.update({"bars": bars, "last_open": last_open, "ticker_age_s": age})
        market[sym] = info
    if stale:
        run_blocks.append("HALT_STALE_DATA")

    # 2) reconcile account vs state
    try:
        positions = _position_rows()
        pending_ids = {str(_first(r, "orderId", "order_id")) for r in _records(trade.contract.pending_orders())}
    except Exception as exc:
        log.add(now_ms, "*", "HALT", "HALT_STATE_UNREADABLE", detail={"error": str(exc)[:300]})
        state["risk"] = risk.to_dict()
        _save(state, log)
        runtime.emit_signal(action="watch", symbol=symbols[0], confidence=0.0, metrics={},
                            meta={"halt": "account_read_failed"})
        return
    live_by_sym = {p["symbol"]: p for p in positions}

    for sym, od in list(state["orders"].items()):
        oid = str(od.get("order_id", ""))
        if oid and oid in pending_ids:
            continue
        entry_fills = [f for f in _fills(sym, oid)] if oid else []
        if entry_fills:
            qty = sum(_f(_first(f, "baseVolume", "size", "qty")) or 0.0 for f in entry_fills)
            px = sum((_f(_first(f, "price", "priceAvg")) or 0.0) * (_f(_first(f, "baseVolume", "size", "qty")) or 0.0)
                     for f in entry_fills) / qty if qty > 0 else float(od["limit"])
            fill_ms = min(_ms_field(f, "cTime", "ctime", "time") or now_ms for f in entry_fills)
            fee = sum(_fee(f) for f in entry_fills)
            state["positions"][sym] = {**od, "qty": qty or od["qty"], "entry_filled": px, "fill_ms": fill_ms,
                                       "entry_fee": fee}
            log.add(fill_ms, sym, "ENTRY_FILLED", "ENTRY_SIGNAL", side=od["side"], intended_price=od["limit"],
                    filled_price=px, qty=qty, fee_usdt=fee, order_id=oid)
        else:
            log.add(now_ms, sym, "ORDER_CANCELLED", "ENTRY_TTL_EXPIRED" if od.get("cancel_sent") else "ORDER_GONE_UNFILLED",
                    side=od["side"], intended_price=od["limit"], qty=od["qty"], order_id=oid,
                    detail={"note": "order no longer pending and no fills found"})
        del state["orders"][sym]

    for sym, pos in list(state["positions"].items()):
        if sym in live_by_sym:
            continue
        closed = _resolve_close(sym, pos, cfg)
        if closed is None:
            risk.latched_halt = risk.latched_halt or "PNL_UNRESOLVED"
            log.add(now_ms, sym, "HALT", "PNL_UNRESOLVED", side=pos["side"], detail={"position": pos})
            continue
        log.add(closed["exit_ms"], sym, "EXIT", closed["reason"], side=pos["side"],
                intended_price=closed["intended"], filled_price=closed["exit_px"], qty=pos["qty"],
                fee_usdt=closed["fees"], funding_usdt=closed["funding"], realized_pnl_usdt=closed["net"],
                r_multiple=closed["r"], detail={"funding_is_estimate": True})
        new_state = risk.record_close(closed["exit_ms"] // DAY_MS, closed["net"], cfg)
        if new_state:
            log.add(now_ms, sym, "HALT", new_state, detail=risk.to_dict())
        del state["positions"][sym]

    foreign = [p for p in positions if p["symbol"] not in state["positions"]]
    for p in foreign:
        log.add(now_ms, p["symbol"], "ALERT", "HALT_FOREIGN_POSITION", side=p["hold_side"], qty=p["size"],
                detail={"open_price": p["open_price"], "action": "not touched"})
    if foreign:
        run_blocks.append("HALT_FOREIGN_POSITION")

    # 3) manage: entry TTL / pause cancels, time stops
    block = risk.entry_block_reason(day)
    for sym, od in list(state["orders"].items()):
        expired = now_ms - int(od["placed_ms"]) >= int(rv(cfg, "entry_ttl_hours")) * HOUR_MS
        if not (expired or block):
            continue
        reason = "ENTRY_TTL_EXPIRED" if expired else "PAUSE_CANCEL"
        sink = _follow("close", sym, reason, {"op": "cancel_entry", "order_id": od["order_id"]},
                       lambda s, _sym=sym, _oid=str(od["order_id"]): _cancel_entry(_sym, _oid, s), log, now_ms)
        if sink.get("executed"):
            od["cancel_sent"] = True
            log.add(now_ms, sym, "ORDER_CANCELLED", reason, side=od["side"], intended_price=od["limit"],
                    qty=od["qty"], order_id=str(od["order_id"]))

    for sym, pos in state["positions"].items():
        if pos.get("time_stop_sent"):
            continue
        if now_ms - int(pos["fill_ms"]) < int(rv(cfg, "time_stop_hours")) * HOUR_MS:
            continue
        if in_funding_window(now_ms, block_min):
            log.add(now_ms, sym, "NO_TRADE", "FUNDING_WINDOW", detail={"deferred": "time_stop"})
            continue
        sink = _follow("close", sym, "TIME_STOP", {"op": "time_stop"},
                       lambda s, _sym=sym, _side=pos["side"]: _time_stop_close(_sym, _side, s), log, now_ms)
        if sink.get("executed"):
            pos["time_stop_sent"] = True

    # 4) filter + trigger + order on the just-closed bar
    if block:
        run_blocks.append(block)
    for sym in symbols:
        info = market[sym]
        last_open = info.get("last_open")
        if last_open is None:
            continue
        bar_close = last_open + HOUR_MS
        if state["last_eval_bar"].get(sym) == last_open or now_ms - bar_close >= 15 * 60_000:
            continue
        state["last_eval_bar"][sym] = last_open
        bars = info["bars"]
        if len(bars) < int(cfg_value(cfg, "atr_rank_window")) + 50:
            log.add(now_ms, sym, "NO_TRADE", "NO_SIGNAL", detail={"bars": len(bars), "note": "insufficient history"})
            continue
        sig = compute_signals(compute_indicators(bars, cfg), cfg).iloc[-1]
        raw_action = "long" if bool(sig["signal_long"]) else ("short" if bool(sig["signal_short"]) else None)
        snapshot = {k: (None if not isinstance(sig[k], (int, float)) or not math.isfinite(float(sig[k]))
                        else round(float(sig[k]), 6))
                    for k in ("close", "adx", "atr", "atr_rank", "vol_ratio", "ema_fast", "ema_slow")}
        snapshot["regime"] = str(sig["regime"])
        if raw_action is None:
            code = "REGIME_SIT_OUT" if snapshot["regime"] == "SIT_OUT" else "NO_SIGNAL"
            log.add(now_ms, sym, "NO_TRADE", code, detail=snapshot)
            continue
        action = validate_signal(raw_action, allowed)
        if action is None:
            log.add(now_ms, sym, "NO_TRADE", "INVALID_SIGNAL", side=str(raw_action), detail=snapshot)
            continue
        reason = None
        if run_blocks:
            reason = run_blocks[0]
        elif sym in state["orders"] or sym in state["positions"] or sym in live_by_sym:
            reason = "SYMBOL_BUSY"
        elif len(state["orders"]) + len(state["positions"]) >= int(rv(cfg, "max_concurrent")):
            reason = "MAX_CONCURRENT"
        elif in_funding_window(now_ms, block_min):
            reason = "FUNDING_WINDOW"
        if reason is None:
            try:
                f8h = _funding_8h(sym, float(intervals.get(sym, 8)))
            except Exception:
                f8h = None
            snapshot["funding_8h"] = f8h
            if funding_blocks(action, f8h, float(rv(cfg, "funding_max_against_8h"))):
                reason = "FUNDING_UNKNOWN" if f8h is None else "FUNDING_AGAINST"
        if reason:
            log.add(now_ms, sym, "NO_TRADE", reason, side=action, detail=snapshot)
            continue
        rules = _rules(sym)
        plan = plan_entry(side=action, close=float(sig["close"]), atr=float(sig["atr"]), tick=rules["tick"],
                          size_step=rules["size_step"], min_qty=rules["min_qty"], cfg=cfg)
        if not plan.ok:
            log.add(now_ms, sym, "NO_TRADE", plan.reason_code, side=action, intended_price=plan.limit, qty=plan.qty,
                    detail={**snapshot, "notional": plan.notional, "margin": plan.margin})
            continue
        log.add(now_ms, sym, "SIGNAL", "ENTRY_SIGNAL", side=action, intended_price=plan.limit, qty=plan.qty,
                detail={**snapshot, "stop": plan.stop, "tp": plan.tp, "notional": plan.notional,
                        "leverage": leverage_cap(cfg)})
        meta = {"op": "open_entry", "limit": plan.limit, "stop": plan.stop, "tp": plan.tp, "qty": plan.qty,
                "regime": snapshot["regime"], "margin_mode": "isolated", "leverage": leverage_cap(cfg)}
        sink = _follow(action, sym, "ENTRY_SIGNAL", meta,
                       lambda s, _sym=sym, _plan=plan: _place_entry(_sym, _plan, cfg, s), log, now_ms)
        if sink.get("executed") and sink.get("order_id"):
            state["orders"][sym] = {"order_id": sink["order_id"], "side": action, "limit": plan.limit,
                                    "sl": sink.get("sl") or plan.stop, "tp": sink.get("tp") or plan.tp,
                                    "qty": sink.get("qty") or plan.qty, "placed_ms": now_ms,
                                    "signal_bar_open": last_open}
            log.add(now_ms, sym, "ORDER_PLACED", "ENTRY_SIGNAL", side=action, intended_price=plan.limit,
                    qty=sink.get("qty"), order_id=sink["order_id"],
                    detail={"sl": sink.get("sl"), "tp": sink.get("tp"), "margin_mode": "isolated"})
        elif not sink.get("error"):
            log.add(now_ms, sym, "NO_TRADE", "FOLLOW_NOT_EXECUTED", side=action, intended_price=plan.limit)

    state["risk"] = risk.to_dict()
    _save(state, log)
    runtime.emit_signal(
        action="watch", symbol=symbols[0], confidence=0.0,
        metrics={"open_orders": len(state["orders"]), "open_positions": len(state["positions"]),
                 "daily_realized_usdt": round(risk.daily_realized, 4),
                 "consecutive_losses": risk.consecutive_losses},
        meta={"blocks": run_blocks, "latched_halt": risk.latched_halt,
              "actions": [{k: r[k] for k in ("symbol", "action", "reason_code", "side")} for r in log.rows][-30:]},
    )
