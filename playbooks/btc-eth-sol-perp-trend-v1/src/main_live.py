"""Live scheduled execution (hourly, right after the 1H bar closes).

Decision output is always emitted first through `runtime.emit_signal_or_follow`;
every Trade SDK mutation lives inside the `execute_trade` callback so the
runtime's follow-trade permission gate stays authoritative.

Flow per run: load state -> fetch closed bars + funding -> freshness gate ->
read account (positions / pending orders) -> alert on foreign positions ->
reconcile tracked positions (realised PnL ledger, consecutive losses) ->
risk gates (daily pause / stop, halts) -> time-stop & entry-TTL housekeeping ->
new entry decisions -> emit + execute -> persist state.
"""

import json
from datetime import datetime, timezone
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

from getagent import data, runtime, trade

from . import features as F

STATE_DIR = Path("/workspace/.state")
STATE_FILE = STATE_DIR / "perp_trend_state.json"
BARS_FOR_FEATURES = 1000
MAX_STALE_INTERVALS = 2
QUOTE_STALE_SECONDS = 60


# ----------------------------------------------------------------- helpers
def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _dec(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _quantize(value: float, step: Decimal, *, down: bool = True) -> Decimal:
    if step <= 0:
        return Decimal(str(value))
    units = (Decimal(str(value)) / step).to_integral_value(rounding=ROUND_DOWN if down else ROUND_HALF_UP)
    return (units * step).quantize(step)


def _load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return {"positions": {}, "daily": {"day": None, "pnl": 0.0}, "consecutive_losses": 0, "halt_until_ts": 0, "entry_block_day": -1, "log": []}


def _save_state(state: dict[str, Any]) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state["log"] = list(state.get("log", []))[-500:]
        STATE_FILE.write_text(json.dumps(state, default=str), encoding="utf-8")
    except OSError:
        pass


def _records(response: Any) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in data.to_records(response)]
    except Exception:
        return []


def _dig_list(payload: Any) -> list[dict[str, Any]]:
    """Find the first list of dicts inside a Trade SDK envelope."""
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if hasattr(payload, "raw") and not isinstance(payload, dict):
        found = _dig_list(getattr(payload, "raw"))
        if found:
            return found
    if hasattr(payload, "data") and not isinstance(payload, dict):
        found = _dig_list(getattr(payload, "data"))
        if found:
            return found
    if isinstance(payload, dict):
        for key in ("list", "data", "orderList", "fillList", "entrustedList", "positions", "result"):
            if key in payload:
                found = _dig_list(payload[key])
                if found:
                    return found
    return []


def _first_key(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def _extract_order_id(result: Any) -> str:
    for candidate in (result, getattr(result, "raw", None), getattr(result, "data", None)):
        if isinstance(candidate, dict):
            value = _first_key(candidate, ("order_id", "orderId", "clientOid", "client_oid"))
            if value:
                return str(value)
            nested = candidate.get("data")
            if isinstance(nested, dict):
                value = _first_key(nested, ("order_id", "orderId", "clientOid", "client_oid"))
                if value:
                    return str(value)
        for attr in ("order_id", "orderId"):
            value = getattr(candidate, attr, None)
            if value:
                return str(value)
    return ""


def _log_action(state: dict[str, Any], **record: Any) -> dict[str, Any]:
    record.setdefault("ts", _now_ts())
    record.setdefault("ts_iso", _iso(int(record["ts"])))
    record.setdefault("run_id", str(runtime.run_id))
    state.setdefault("log", []).append(record)
    print(json.dumps({"action_log": record}, default=str))
    return record


# -------------------------------------------------------------- market data
def _latest_funding(symbol: str) -> Optional[float]:
    base = symbol[:-4] if symbol.endswith("USDT") else symbol
    for candidate in (symbol, base):
        try:
            resp = data.crypto.futures.funding_rate(symbol=candidate, exchange="bitget", interval="4h", limit=5)
        except Exception:
            continue
        rows = _records(resp)
        values = [row.get("funding_rate") for row in rows if row.get("funding_rate") not in (None, "")]
        if values:
            try:
                return float(values[-1])
            except (TypeError, ValueError):
                continue
    return None


def _symbol_snapshot(symbol: str, params: F.StrategyParams) -> dict[str, Any]:
    fetch_started = _now_ts()
    bars = data.crypto.futures.kline(symbol=symbol, interval="1h", exchange="bitget", limit=BARS_FOR_FEATURES, closed_only=True)
    fetch_seconds = _now_ts() - fetch_started
    rows = _records(bars)

    def _open_ms(row: dict[str, Any]) -> Optional[int]:
        value = row.get("time")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
        raw_date = row.get("date")
        if raw_date:
            try:
                return int(datetime.fromisoformat(str(raw_date).replace("Z", "+00:00")).timestamp() * 1000)
            except ValueError:
                return None
        return None

    parsed = []
    for row in rows:
        open_ms = _open_ms(row)
        if open_ms is None:
            continue
        try:
            parsed.append((open_ms, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row.get("volume") or 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
    parsed.sort(key=lambda r: r[0])
    engine = F.FeatureEngine(params)
    snap = None
    for open_ms, o, h, l, c, v in parsed:
        snap = engine.update(open_ms // 1000 + F.INTERVAL_SECONDS, o, h, l, c, v)
    now = _now_ts()
    last_close_ts = snap.close_ts if snap else None
    stale = last_close_ts is None or (now - last_close_ts) > MAX_STALE_INTERVALS * F.INTERVAL_SECONDS or fetch_seconds > QUOTE_STALE_SECONDS
    return {
        "symbol": symbol,
        "rows": len(parsed),
        "snapshot": snap,
        "last_close_ts": last_close_ts,
        "stale": stale,
        "fetch_seconds": fetch_seconds,
        "funding_rate": _latest_funding(symbol),
    }


# ------------------------------------------------------------ trade reads
def _position_entry_price(selection: Any) -> Optional[float]:
    raw = getattr(selection, "raw", None)
    if isinstance(raw, dict):
        value = _first_key(raw, ("openPriceAvg", "averageOpenPrice", "avgOpenPrice", "open_avg_price", "openAvgPrice", "markPrice"))
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
    return None


def _realized_from_fills(symbol: str, rec: dict[str, Any]) -> tuple[float, bool]:
    """Best-effort realised PnL for a closed tracked position from fill history.

    Returns (pnl_usdt, is_estimate). Falls back to -risk (conservative) when
    the fill payload cannot be parsed."""
    try:
        fills = trade.contract.fills(symbol=symbol, limit=50)
    except Exception:
        return (-float(rec.get("risk_usdt", 0.0)), True)
    rows = _dig_list(fills)
    entry_ts_ms = int(rec.get("entry_ts", rec.get("signal_ts", 0))) * 1000
    pnl = 0.0
    fees = 0.0
    found = False
    for row in rows:
        ts_raw = _first_key(row, ("cTime", "ctime", "ts", "timestamp", "fillTime"))
        try:
            ts_ms = int(float(ts_raw)) if ts_raw is not None else 0
        except (TypeError, ValueError):
            ts_ms = 0
        if ts_ms and ts_ms < entry_ts_ms - 3600 * 1000:
            continue
        profit = _first_key(row, ("profit", "realizedPnl", "realized_pnl"))
        fee = _first_key(row, ("fee", "fees", "totalFee"))
        if profit is not None:
            try:
                pnl += float(profit)
                found = True
            except (TypeError, ValueError):
                pass
        if fee is not None:
            try:
                fees += abs(float(fee))
            except (TypeError, ValueError):
                pass
    if found:
        return (pnl - fees, False)
    return (-float(rec.get("risk_usdt", 0.0)), True)


# ---------------------------------------------------------- trade mutations
def _execute_entry(plan: dict[str, Any], params: F.StrategyParams, state: dict[str, Any]) -> dict[str, Any]:
    symbol = plan["symbol"]
    current = trade.contract.current_position(symbol=symbol)
    if trade.helpers.find_contract_position(current, symbol=symbol, prefer_first=True) is not None:
        return {"status": "already_positioned"}

    rules = trade.helpers.contract_rules(symbol)
    price_step = _dec(getattr(rules, "price_step", "0"), default="0")
    limit_price = _quantize(plan["intended_price"], price_step, down=True) if price_step > 0 else Decimal(str(plan["intended_price"]))
    stop_distance = Decimal(str(plan["stop_distance"]))
    sl_price = limit_price - stop_distance
    tp_price = limit_price + Decimal(str(params.take_profit_r)) * stop_distance
    if price_step > 0:
        sl_price = _quantize(float(sl_price), price_step, down=True)
        tp_price = _quantize(float(tp_price), price_step, down=True)

    # Risk-based size -> margin budget -> helper-quantised qty (never manual lot math).
    margin_needed = Decimal(str(plan["notional_usdt"])) / Decimal(params.leverage)
    qty_plan = trade.helpers.compute_qty(
        symbol=symbol,
        market="contract",
        budget_amount=str(margin_needed.quantize(Decimal("0.0001"))),
        leverage=params.leverage,
        price=str(limit_price),
    )
    tpsl = trade.helpers.resolve_contract_tpsl(
        symbol=symbol,
        side="long",
        leverage=params.leverage,
        tp_trigger_price=str(tp_price),
        sl_trigger_price=str(sl_price),
        reference_price=str(limit_price),
    )
    lev = trade.contract.change_leverage(symbol=symbol, leverage=params.leverage)
    if not trade.is_success(lev):
        raise RuntimeError(f"change_leverage failed: {lev}")
    result = trade.contract.place_order(
        symbol=symbol,
        side="buy",
        order_type="limit",
        qty=qty_plan.qty,
        price=str(limit_price),
        margin_mode="isolated",
        tp_trigger_price=tpsl.tp_trigger_price,
        sl_trigger_price=tpsl.sl_trigger_price,
    )
    if not trade.is_success(result):
        raise RuntimeError(f"contract limit open failed: {result}")
    order_id = _extract_order_id(result)
    if not order_id:
        pending = trade.contract.pending_orders(symbol=symbol)
        try:
            selection = trade.helpers.select_contract_order(pending, symbol=symbol, prefer_first=True)
            order_id = str(getattr(selection, "order_id", "") or "")
        except Exception:
            order_id = ""
    state["positions"][symbol] = {
        "symbol": symbol,
        "side": "long",
        "status": "pending",
        "order_id": order_id,
        "signal_ts": plan["signal_ts"],
        "submitted_ts": _now_ts(),
        "intended_price": str(limit_price),
        "qty": str(qty_plan.qty),
        "stop_price": str(tpsl.sl_trigger_price),
        "tp_price": str(tpsl.tp_trigger_price),
        "risk_usdt": float(plan["risk_usdt"]),
        "margin_usdt": float(plan["margin_usdt"]),
    }
    _log_action(
        state,
        symbol=symbol,
        side="long",
        action="entry_submit",
        reason_code=F.RC_ENTRY_SUBMIT,
        intended_price=str(limit_price),
        filled_price=None,
        qty=str(qty_plan.qty),
        fee_usdt=None,
        funding_usdt=None,
        order_id=order_id,
        stop_price=str(tpsl.sl_trigger_price),
        tp_price=str(tpsl.tp_trigger_price),
    )
    return {"status": "submitted", "order_id": order_id, "qty": str(qty_plan.qty)}


def _execute_cancel_entry(symbol: str, rec: dict[str, Any], state: dict[str, Any], reason_code: str) -> dict[str, Any]:
    pending = trade.contract.pending_orders(symbol=symbol)
    order_id = str(rec.get("order_id") or "")
    target = None
    try:
        target = trade.helpers.find_contract_order(pending, order_id) if order_id else trade.helpers.select_contract_order(pending, symbol=symbol, prefer_first=True)
    except Exception:
        target = None
    if target is None:
        state["positions"].pop(symbol, None)
        return {"status": "nothing_to_cancel"}
    target_id = str(getattr(target, "order_id", "") or order_id)
    result = trade.contract.cancel_order(symbol=symbol, order_id=target_id)
    if not trade.is_success(result):
        raise RuntimeError(f"cancel failed: {result}")
    after = trade.contract.pending_orders(symbol=symbol)
    still_open = False
    try:
        still_open = trade.helpers.find_contract_order(after, target_id) is not None
    except Exception:
        still_open = False
    state["positions"].pop(symbol, None)
    _log_action(state, symbol=symbol, side="long", action="entry_cancel", reason_code=reason_code, intended_price=rec.get("intended_price"), order_id=target_id, post_check_still_open=still_open)
    return {"status": "cancelled", "order_id": target_id}


def _execute_close(symbol: str, rec: dict[str, Any], state: dict[str, Any], reason_code: str) -> dict[str, Any]:
    current = trade.contract.current_position(symbol=symbol)
    position = trade.helpers.find_contract_position(current, symbol=symbol, hold_side="long", prefer_first=True)
    if position is None:
        rec["status"] = "closed_externally"
        return {"status": "flat"}
    result = trade.contract.close_position(symbol=symbol, hold_side="long")
    if not trade.is_success(result):
        raise RuntimeError(f"close_position failed: {result}")
    after = trade.contract.current_position(symbol=symbol)
    remaining = trade.helpers.count_open_contract_positions(after, symbol=symbol)
    pnl, estimated = _realized_from_fills(symbol, rec)
    _settle_closed(state, symbol, rec, pnl, estimated, reason_code)
    return {"status": "closed", "remaining_positions": remaining, "pnl_usdt": pnl, "pnl_estimated": estimated}


def _settle_closed(state: dict[str, Any], symbol: str, rec: dict[str, Any], pnl: float, estimated: bool, reason_code: str) -> None:
    day = F.utc_day(_now_ts())
    daily = state.setdefault("daily", {"day": None, "pnl": 0.0})
    if daily.get("day") != day:
        daily["day"] = day
        daily["pnl"] = 0.0
    daily["pnl"] = float(daily.get("pnl", 0.0)) + pnl
    if pnl < 0:
        state["consecutive_losses"] = int(state.get("consecutive_losses", 0)) + 1
    else:
        state["consecutive_losses"] = 0
    state["positions"].pop(symbol, None)
    _log_action(
        state,
        symbol=symbol,
        side=rec.get("side", "long"),
        action="exit",
        reason_code=reason_code,
        intended_price=rec.get("tp_price") if reason_code == F.RC_EXIT_TP else rec.get("stop_price"),
        filled_price=None,
        qty=rec.get("qty"),
        pnl_usdt=pnl,
        pnl_estimated=estimated,
        daily_pnl_usdt=daily["pnl"],
    )


# ------------------------------------------------------------------- run
def run() -> None:
    cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    params = F.StrategyParams.from_config(cfg)
    symbols = trade.helpers.normalize_trading_symbols([str(s) for s in (cfg.get("trading_symbols") or runtime.manifest.get("trading_symbols") or [])])
    state = _load_state()
    now = _now_ts()
    day = F.utc_day(now)
    daily = state.setdefault("daily", {"day": None, "pnl": 0.0})
    if daily.get("day") != day:
        daily["day"] = day
        daily["pnl"] = 0.0

    support = trade.market.check_symbol_support(symbols)
    if not trade.is_success(support):
        runtime.emit_signal_or_follow(action="watch", symbol=symbols[0], confidence=0.0, metrics={"supported": False}, meta={"support": str(support)}, reason_code=F.RC_SKIP_HALTED, reason_text="symbol support check failed for the bound sub-account; no trading this run")
        _save_state(state)
        return

    # ---- market data + features
    snapshots = {symbol: _symbol_snapshot(symbol, params) for symbol in symbols}

    # ---- account reads (no mutations)
    positions_result = trade.contract.current_position()
    open_symbols = set(trade.helpers.contract_open_symbols(positions_result))
    tracked: dict[str, dict[str, Any]] = state.setdefault("positions", {})

    foreign = sorted(open_symbols - set(tracked))
    for symbol in foreign:
        _log_action(state, symbol=symbol, side="", action="alert", reason_code=F.RC_ALERT_FOREIGN_POSITION, intended_price=None, filled_price=None)
        runtime.emit_signal_or_follow(
            action="watch",
            symbol=symbol,
            confidence=0.0,
            metrics={"foreign_position": True},
            meta={"note": "position not opened by this Playbook; left untouched"},
            reason_code=F.RC_ALERT_FOREIGN_POSITION,
            reason_text="A position exists in the sub-account that this Playbook did not open. Alert only; the Playbook will not touch it.",
        )

    # ---- reconcile tracked positions
    for symbol, rec in list(tracked.items()):
        if symbol in open_symbols:
            if rec.get("status") == "pending":
                rec["status"] = "open"
                rec["entry_ts"] = now
                selection = trade.helpers.find_contract_position(positions_result, symbol=symbol, prefer_first=True)
                entry_px = _position_entry_price(selection) if selection is not None else None
                rec["entry_price"] = entry_px
                _log_action(state, symbol=symbol, side="long", action="entry_fill", reason_code=F.RC_ENTRY_FILL, intended_price=rec.get("intended_price"), filled_price=entry_px, qty=rec.get("qty"))
            continue
        if rec.get("status") == "open":
            pnl, estimated = _realized_from_fills(symbol, rec)
            reason = F.RC_EXIT_TP if pnl > 0 else F.RC_EXIT_SL
            _settle_closed(state, symbol, rec, pnl, estimated, reason)
        elif rec.get("status") == "pending" and now - int(rec.get("signal_ts", now)) >= params.entry_ttl_hours * 3600:
            pass  # handled below as cancel action

    # ---- risk gates
    halt_reason: Optional[str] = None
    if float(daily.get("pnl", 0.0)) <= -params.daily_stop_loss_usdt and int(state.get("entry_block_day", -1)) < day:
        state["entry_block_day"] = day
        halt_reason = F.RC_HALT_DAILY_STOP
    if int(state.get("consecutive_losses", 0)) >= params.max_consecutive_losses:
        state["halt_until_ts"] = now + 24 * 3600
        state["consecutive_losses"] = 0
        halt_reason = halt_reason or F.RC_HALT_CONSEC_LOSS
    if halt_reason:
        _log_action(state, symbol="*", side="", action="halt", reason_code=halt_reason, intended_price=None, filled_price=None, daily_pnl_usdt=daily.get("pnl"))
    entries_blocked = (
        now < int(state.get("halt_until_ts", 0))
        or int(state.get("entry_block_day", -1)) >= day
        or float(daily.get("pnl", 0.0)) <= -params.daily_pause_loss_usdt
    )

    emitted = 0
    # ---- daily stop: flatten tracked positions, cancel tracked pending entries
    if halt_reason == F.RC_HALT_DAILY_STOP:
        for symbol, rec in list(tracked.items()):
            if rec.get("status") == "open":
                runtime.emit_signal_or_follow(
                    action="close", symbol=symbol, confidence=1.0,
                    metrics={"daily_pnl_usdt": daily.get("pnl")}, meta={"rec": rec},
                    reason_code=F.RC_EXIT_DAILY_STOP,
                    reason_text="Daily realised loss limit hit; flattening Playbook-opened position. Stop the Playbook in GetAgent if you want a full halt.",
                    execute_trade=lambda s=symbol, r=rec: _execute_close(s, r, state, F.RC_EXIT_DAILY_STOP),
                )
            elif rec.get("status") == "pending":
                runtime.emit_signal_or_follow(
                    action="close", symbol=symbol, confidence=1.0, metrics={}, meta={"rec": rec},
                    reason_code=F.RC_EXIT_DAILY_STOP, reason_text="Daily stop: cancelling unfilled entry.",
                    execute_trade=lambda s=symbol, r=rec: _execute_cancel_entry(s, r, state, F.RC_EXIT_DAILY_STOP),
                )
            emitted += 1

    # ---- housekeeping: time stop and entry TTL
    for symbol, rec in list(tracked.items()):
        if halt_reason == F.RC_HALT_DAILY_STOP:
            break
        if rec.get("status") == "open" and now - int(rec.get("entry_ts", now)) >= params.time_stop_hours * 3600:
            runtime.emit_signal_or_follow(
                action="close", symbol=symbol, confidence=1.0,
                metrics={"held_seconds": now - int(rec.get("entry_ts", now))}, meta={"rec": rec},
                reason_code=F.RC_EXIT_TIME, reason_text="Time stop reached; closing at market.",
                execute_trade=lambda s=symbol, r=rec: _execute_close(s, r, state, F.RC_EXIT_TIME),
            )
            emitted += 1
        elif rec.get("status") == "pending" and now - int(rec.get("signal_ts", now)) >= params.entry_ttl_hours * 3600:
            runtime.emit_signal_or_follow(
                action="close", symbol=symbol, confidence=1.0, metrics={}, meta={"rec": rec},
                reason_code=F.RC_ENTRY_EXPIRED, reason_text="Entry limit unfilled past TTL; cancelling.",
                execute_trade=lambda s=symbol, r=rec: _execute_cancel_entry(s, r, state, F.RC_ENTRY_EXPIRED),
            )
            emitted += 1

    # ---- new entries
    for symbol in symbols:
        info = snapshots[symbol]
        snap: Optional[F.BarSnapshot] = info["snapshot"]
        base_metrics = {
            "rows": info["rows"],
            "last_bar_close_ts": info["last_close_ts"],
            "data_stale": info["stale"],
            "funding_rate": info["funding_rate"],
            "adx": snap.adx if snap else None,
            "atr": snap.atr if snap else None,
            "atr_pct_rank": snap.atr_pct_rank if snap else None,
            "volume_ratio": snap.volume_ratio if snap else None,
            "regime": snap.regime if snap else "no_data",
        }
        if info["stale"] or snap is None or not snap.warmed:
            _log_action(state, symbol=symbol, side="", action="skip", reason_code=F.RC_SKIP_STALE, intended_price=None, filled_price=None, **{"fetch_seconds": info["fetch_seconds"]})
            runtime.emit_signal_or_follow(action="watch", symbol=symbol, confidence=0.0, metrics=base_metrics, meta={}, reason_code=F.RC_HALT_STALE, reason_text="Market data stale or insufficient; no trading decision for this symbol.")
            emitted += 1
            continue
        if not (snap.long_trigger and params.side_mode in ("long_only", "both")):
            continue
        reason: Optional[str] = None
        if symbol in tracked or symbol in open_symbols:
            reason = F.RC_SKIP_PENDING
        elif entries_blocked:
            reason = F.RC_SKIP_HALTED if now < int(state.get("halt_until_ts", 0)) or int(state.get("entry_block_day", -1)) >= day else F.RC_SKIP_DAILY_PAUSE
        elif len(tracked) + len(foreign) >= params.max_concurrent_positions:
            reason = F.RC_SKIP_MAX_POSITIONS
        elif F.in_funding_window(now, params.funding_window_minutes) or F.in_funding_window(snap.close_ts, params.funding_window_minutes):
            reason = F.RC_SKIP_FUNDING_WINDOW
        elif info["funding_rate"] is None or F.funding_blocks_entry("long", info["funding_rate"], params.max_funding_rate_pct):
            reason = F.RC_SKIP_FUNDING_RATE  # live fails closed when funding cannot be read
        if reason:
            _log_action(state, symbol=symbol, side="long", action="skip", reason_code=reason, intended_price=snap.close, filled_price=None)
            runtime.emit_signal_or_follow(action="watch", symbol=symbol, confidence=0.0, metrics=base_metrics, meta={}, reason_code=reason, reason_text=f"Long trigger fired but blocked by {reason}.")
            emitted += 1
            continue
        stop_distance = params.stop_atr_multiple * float(snap.atr or 0.0)
        sizing = F.size_position(
            risk_usdt=params.risk_per_trade_usdt,
            stop_distance=stop_distance,
            price=snap.close,
            leverage=params.leverage,
            margin_cap_usdt=params.margin_budget / params.max_concurrent_positions,
            size_step=1e-9,
            min_qty=0.0,
        )
        if not sizing["sizing_ok"]:
            _log_action(state, symbol=symbol, side="long", action="skip", reason_code=F.RC_SKIP_SIZE, intended_price=snap.close, filled_price=None, sizing=sizing)
            continue
        plan = {
            "symbol": symbol,
            "signal_ts": snap.close_ts,
            "intended_price": snap.close,
            "stop_distance": stop_distance,
            "notional_usdt": sizing["notional_usdt"],
            "risk_usdt": sizing["risk_usdt"],
            "margin_usdt": sizing["margin_usdt"],
        }
        runtime.emit_signal_or_follow(
            action="long",
            symbol=symbol,
            confidence=0.6,
            metrics={**base_metrics, "notional_usdt": sizing["notional_usdt"], "min_open_notional_usdt": sizing["min_open_notional_usdt"], "sizing_ok": True, "risk_usdt": sizing["risk_usdt"], "leverage": params.leverage},
            meta={"plan": plan, "stop_atr_multiple": params.stop_atr_multiple, "take_profit_r": params.take_profit_r},
            reason_code=F.RC_ENTRY_SUBMIT,
            reason_text="Trend regime with pullback-resume trigger and volume confirmation; limit entry at signal close with exchange-side stop and take-profit.",
            execute_trade=lambda p=plan: _execute_entry(p, params, state),
        )
        emitted += 1

    if emitted == 0:
        runtime.emit_signal_or_follow(
            action="watch",
            symbol=symbols[0],
            confidence=0.0,
            metrics={s: (snapshots[s]["snapshot"].regime if snapshots[s]["snapshot"] else "no_data") for s in symbols},
            meta={"daily_pnl_usdt": daily.get("pnl"), "tracked": list(tracked)},
            reason_code=F.RC_WATCH,
            reason_text="No entry trigger this hour.",
        )
    _save_state(state)
