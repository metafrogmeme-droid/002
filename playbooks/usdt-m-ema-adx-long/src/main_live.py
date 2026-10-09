"""Live path. Mutations run only inside the follow-trade callback.

An invalid, stale, or missing signal emits hold and does not place an order.
Foreign positions are logged and left untouched.
"""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from getagent import data, runtime, trade

try:
    from .action_log import action_row
    from .indicators import IndicatorBook
    from .logic import AccountState, Decision, Snapshot, decide
    from .params import Config, ConfigError, load_config
    from .reasons import (
        FILTER_FUNDING_WINDOW,
        HALT_CONSECUTIVE_LOSSES,
        HALT_DAILY_LOSS,
        HALT_FOREIGN_POSITION,
        HALT_PLAYBOOK_LOSS,
        HALT_POSITION_UNREADABLE,
        MANAGE_TIME_STOP,
        ORDER_CANCEL_UNFILLED,
        ORDER_REJECTED,
    )
    from .risk import exposure_hits_blackout, in_funding_blackout
except ImportError:
    from action_log import action_row
    from indicators import IndicatorBook
    from logic import AccountState, Decision, Snapshot, decide
    from params import Config, ConfigError, load_config
    from reasons import (
        FILTER_FUNDING_WINDOW,
        HALT_CONSECUTIVE_LOSSES,
        HALT_DAILY_LOSS,
        HALT_FOREIGN_POSITION,
        HALT_PLAYBOOK_LOSS,
        HALT_POSITION_UNREADABLE,
        MANAGE_TIME_STOP,
        ORDER_CANCEL_UNFILLED,
        ORDER_REJECTED,
    )
    from risk import exposure_hits_blackout, in_funding_blackout


STATE_PATH = Path("/workspace/.state/ema_adx_long_state.json")
OUTPUT = Path("/workspace/output/action_log.jsonl")


def run() -> None:
    try:
        cfg = load_config((runtime.manifest or {}).get("strategy_config") or {})
    except ConfigError as exc:
        runtime.emit_signal_or_follow(
            action="hold",
            symbol="BTCUSDT",
            confidence=0.0,
            reason_code="INVALID_CONFIG",
            reason_text=str(exc),
        )
        return
    now = datetime.now(timezone.utc)
    state = _load_state()
    positions, readable = _read_positions()
    if not readable:
        _emit_hold(cfg.trading_symbols[0], HALT_POSITION_UNREADABLE, now, "position query was unreadable")
        return
    _reconcile_owned(state, positions)
    foreign = _foreign_symbols(positions, state)
    plans, hold_reason = _plans(cfg, state, now, foreign)
    if not plans:
        if foreign:
            _emit_hold(
                foreign[0],
                HALT_FOREIGN_POSITION,
                now,
                "sub-account has a position this playbook did not open",
            )
            return
        _emit_hold(cfg.trading_symbols[0], hold_reason, now, "no actionable setup")
        return
    if foreign:
        _append_log(
            action_row(
                timestamp=now,
                symbol=foreign[0],
                side="none",
                reason_code=HALT_FOREIGN_POSITION,
                detail="sub-account has a position this playbook did not open",
            )
        )
    _emit_plan(cfg, state, plans[0])


def _plans(
    cfg: Config, state: dict[str, Any], now: datetime, foreign: list[str]
) -> tuple[list[dict[str, Any]], str]:
    plans: list[dict[str, Any]] = []
    hold_reason = "NO_TRADE"
    owned = {item["symbol"]: item for item in state.get("owned", []) if isinstance(item, dict)}
    for symbol, item in owned.items():
        if symbol in foreign:
            continue
        opened = _parse_ts(item.get("opened_at"))
        if item.get("status") == "pending":
            expire = _parse_ts(item.get("expire_at"))
            if expire is not None and now >= expire:
                plans.append({"kind": "cancel", "symbol": symbol, "order_id": item.get("order_id") or ""})
            elif exposure_hits_blackout(now, now + timedelta(hours=cfg.bar_hours), cfg.funding_blackout_minutes):
                plans.append({"kind": "cancel", "symbol": symbol, "order_id": item.get("order_id") or ""})
        elif item.get("status") == "open" and opened is not None:
            if now >= opened + timedelta(hours=cfg.time_stop_hours):
                plans.append({"kind": "time_stop", "symbol": symbol})
    if any(plan["kind"] == "time_stop" for plan in plans):
        return plans, hold_reason
    if _halted(state, cfg):
        return plans, hold_reason if plans else _halt_reason(state, cfg)
    for symbol in cfg.trading_symbols:
        if symbol in foreign or symbol in owned:
            continue
        decision = _live_decision(cfg, state, symbol, now)
        if decision.action == "long":
            plans.append({"kind": "entry", "symbol": symbol, "decision": decision})
            break
        hold_reason = decision.reason_code
        if decision.reason_code in {"FILTER_NO_CROSS", "INSUFFICIENT_HISTORY"}:
            continue
        _append_log(
            action_row(
                timestamp=now,
                symbol=symbol,
                side="none",
                reason_code=decision.reason_code,
            )
        )
    return plans, hold_reason


def _live_decision(cfg: Config, state: dict[str, Any], symbol: str, now: datetime):
    try:
        markets_ok = _symbol_is_bitget(symbol)
    except Exception:
        markets_ok = False
    if not markets_ok:
        return _hold_decision("INVALID_SIGNAL")
    ticker_age = _ticker_age_seconds(symbol, now)
    bars = data.crypto.futures.kline(
        symbol=symbol,
        interval="1h",
        exchange="bitget",
        limit=max(cfg.atr_pct_lookback + cfg.ema_slow + 10, 100),
        closed_only=True,
    )
    rows = data.to_records(bars)
    if not rows:
        return _hold_decision("HALT_STALE_DATA")
    book = IndicatorBook(
        ema_fast=cfg.ema_fast,
        ema_slow=cfg.ema_slow,
        adx_period=cfg.adx_period,
        atr_period=cfg.atr_period,
        atr_pct_lookback=cfg.atr_pct_lookback,
        volume_avg_bars=cfg.volume_avg_bars,
    )
    latest = None
    last_open = None
    for row in rows:
        try:
            latest = book.update(
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row["volume"]),
            )
        except (KeyError, TypeError, ValueError):
            return _hold_decision("INVALID_SIGNAL")
        last_open = row.get("time") or row.get("timestamp") or row.get("date")
    if _bars_are_stale(last_open, now, cfg.bar_hours):
        return _hold_decision("HALT_STALE_DATA")
    try:
        rules = trade.helpers.contract_rules(symbol, product_type="USDT-FUTURES")
        tick = float(rules.price_step)
    except Exception:
        tick = float(cfg.price_tick[symbol])
    if tick <= 0:
        return _hold_decision("INVALID_SIGNAL")
    step = float(cfg.size_step[symbol])
    min_qty = float(cfg.min_qty[symbol])
    snapshot = Snapshot(
        symbol=symbol,
        close_ts=now,
        close=latest.get("close") if latest else None,
        atr=latest.get("atr") if latest else None,
        atr_pct=latest.get("atr_pct") if latest else None,
        adx=latest.get("adx") if latest else None,
        plus_di=latest.get("plus_di") if latest else None,
        minus_di=latest.get("minus_di") if latest else None,
        fast_ema=latest.get("fast_ema") if latest else None,
        slow_ema=latest.get("slow_ema") if latest else None,
        prev_fast_ema=latest.get("prev_fast_ema") if latest else None,
        prev_slow_ema=latest.get("prev_slow_ema") if latest else None,
        volume=latest.get("volume") if latest else None,
        volume_avg_prev=latest.get("volume_avg_prev") if latest else None,
        funding_rate=_latest_funding(symbol),
        price_tick=tick,
        size_step=step,
        min_qty=min_qty,
    )
    account = AccountState(
        open_positions=sum(1 for item in state.get("owned", []) if item.get("status") in {"pending", "open"}),
        symbol_busy=False,
        daily_realised=float(state.get("daily", {}).get(now.date().isoformat(), 0.0)),
        cumulative_realised=float(state.get("cumulative_realised") or 0.0),
        consecutive_losses=int(state.get("consecutive_losses") or 0),
        margin_remaining=_margin_remaining(cfg, state),
        ticker_age_seconds=ticker_age,
        apply_ticker_staleness=True,
    )
    decision = decide(snapshot, cfg, account)
    if decision.action == "long" and (
        exposure_hits_blackout(
            now, now + timedelta(hours=cfg.bar_hours), cfg.funding_blackout_minutes
        )
        or in_funding_blackout(now, cfg.funding_blackout_minutes)
    ):
        return _hold_decision(FILTER_FUNDING_WINDOW)
    return decision


def _hold_decision(reason: str) -> Decision:
    return Decision(action="hold", side="none", reason_code=reason)


def _emit_plan(cfg: Config, state: dict[str, Any], plan: dict[str, Any]) -> None:
    symbol = plan["symbol"]
    kind = plan["kind"]
    if kind == "entry":
        decision = plan["decision"]
        runtime.emit_signal_or_follow(
            action="long",
            symbol=symbol,
            confidence=0.0,
            metrics={"qty": decision.qty, "entry": decision.entry, "stop": decision.stop},
            meta={"version_label": cfg.version_label},
            reason_code=decision.reason_code,
            reason_text="long limit with attached stop and target",
            execute_trade=lambda: _execute_entry(cfg, state, symbol, decision),
        )
        return
    if kind == "cancel":
        runtime.emit_signal_or_follow(
            action="close",
            symbol=symbol,
            confidence=0.0,
            reason_code=ORDER_CANCEL_UNFILLED,
            reason_text="cancel unfilled entry; do not flatten a filled position",
            execute_trade=lambda: _execute_cancel(state, symbol, str(plan.get("order_id") or "")),
        )
        return
    runtime.emit_signal_or_follow(
        action="close",
        symbol=symbol,
        confidence=0.0,
        reason_code=MANAGE_TIME_STOP,
        reason_text="time stop for a position this playbook opened",
        execute_trade=lambda: _execute_time_stop(state, symbol),
    )


def _execute_entry(cfg: Config, state: dict[str, Any], symbol: str, decision: Any) -> dict[str, Any]:
    leverage = cfg.applied_leverage
    changed = trade.contract.change_leverage(
        symbol=symbol,
        leverage=leverage,
        product_type="USDT-FUTURES",
        margin_coin="USDT",
    )
    if not trade.is_success(changed):
        _log_reject(symbol, "change_leverage failed")
        return {"status": "rejected"}
    margin = decision.margin if decision.margin else cfg.fixed_loss_usdt
    qty_plan = trade.helpers.compute_qty(
        symbol=symbol,
        market="contract",
        budget_amount=str(margin),
        leverage=leverage,
        price=str(decision.entry),
        product_type="USDT-FUTURES",
    )
    qty = Decimal(str(qty_plan.qty))
    stop_distance = Decimal(str(decision.entry)) - Decimal(str(decision.stop))
    if stop_distance <= 0 or qty * stop_distance > Decimal(str(cfg.fixed_loss_usdt)) + Decimal("0.01"):
        _log_reject(symbol, "computed qty would risk more than the fixed loss")
        return {"status": "rejected"}
    tpsl = trade.helpers.resolve_contract_tpsl(
        symbol=symbol,
        side="long",
        leverage=leverage,
        tp_trigger_price=str(decision.take_profit),
        sl_trigger_price=str(decision.stop),
        reference_price=str(decision.entry),
        product_type="USDT-FUTURES",
    )
    placed = trade.contract.place_order(
        symbol=symbol,
        side="buy",
        order_type="limit",
        qty=str(qty),
        price=str(decision.entry),
        product_type="USDT-FUTURES",
        margin_mode="isolated",
        margin_coin="USDT",
        pos_side="long",
        trade_side="open",
        tp_trigger_price=tpsl.tp_trigger_price,
        sl_trigger_price=tpsl.sl_trigger_price,
    )
    if not trade.is_success(placed):
        _log_reject(symbol, "place_order failed")
        return {"status": "rejected"}
    now = datetime.now(timezone.utc)
    state.setdefault("owned", []).append(
        {
            "symbol": symbol,
            "status": "pending",
            "order_id": _extract_order_id(placed),
            "opened_at": now.isoformat(),
            "expire_at": (now + timedelta(hours=cfg.limit_timeout_hours)).isoformat(),
            "entry": decision.entry,
            "stop": decision.stop,
            "take_profit": decision.take_profit,
            "qty": str(qty),
        }
    )
    _save_state(state)
    _append_log(
        action_row(
            timestamp=now,
            symbol=symbol,
            side="long",
            reason_code=decision.reason_code,
            intended_price=decision.entry,
        )
    )
    return {"status": "submitted", "qty": str(qty)}


def _execute_cancel(state: dict[str, Any], symbol: str, order_id: str) -> dict[str, Any]:
    if not order_id:
        _log_reject(symbol, "no owned order id; refusing to cancel an unknown order")
        return {"status": "rejected"}
    pending = trade.contract.pending_orders(symbol=symbol, product_type="USDT-FUTURES")
    if not trade.is_success(pending):
        _log_reject(symbol, "pending order pre-check failed")
        return {"status": "rejected"}
    result = trade.contract.cancel_order(
        symbol=symbol,
        order_id=order_id,
        product_type="USDT-FUTURES",
    )
    if not trade.is_success(result):
        _log_reject(symbol, "cancel failed")
        return {"status": "rejected"}
    state["owned"] = [
        item
        for item in state.get("owned", [])
        if not (item.get("symbol") == symbol and item.get("order_id") == order_id)
    ]
    _save_state(state)
    _append_log(
        action_row(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            side="none",
            reason_code=ORDER_CANCEL_UNFILLED,
        )
    )
    return {"status": "cancelled"}


def _execute_time_stop(state: dict[str, Any], symbol: str) -> dict[str, Any]:
    current = trade.contract.current_position(symbol=symbol, product_type="USDT-FUTURES")
    if not trade.is_success(current):
        _log_reject(symbol, "position pre-check failed")
        return {"status": "rejected"}
    owned = any(
        item.get("symbol") == symbol and item.get("status") == "open"
        for item in state.get("owned", [])
    )
    if not owned:
        _log_reject(symbol, "time stop refused because the position is not owned")
        return {"status": "rejected"}
    found = trade.helpers.find_contract_position(current, symbol=symbol, hold_side="long")
    if found is None:
        return {"status": "flat"}
    closed = trade.contract.close_position(
        symbol=symbol,
        hold_side="long",
        product_type="USDT-FUTURES",
    )
    if not trade.is_success(closed):
        _log_reject(symbol, "close_position failed")
        return {"status": "rejected"}
    state["owned"] = [item for item in state.get("owned", []) if item.get("symbol") != symbol]
    _save_state(state)
    _append_log(
        action_row(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            side="long",
            reason_code=MANAGE_TIME_STOP,
        )
    )
    return {"status": "closed"}


def _symbol_is_bitget(symbol: str) -> bool:
    base = symbol[:-4] if symbol.endswith("USDT") else symbol
    markets = data.crypto.market(
        symbol=f"{base}/USDT",
        market_type="perpetual",
        exchange="bitget",
    )
    for row in data.to_records(markets):
        if str(row.get("exchange") or "").lower() != "bitget":
            continue
        if row.get("active") is True or str(row.get("status") or "").lower() in {"online", "normal"}:
            return True
    return False


def _latest_funding(symbol: str) -> float | None:
    snapshot = data.crypto.futures.mark_price(symbol=symbol, exchange="bitget")
    for row in data.to_records(snapshot):
        raw = row.get("last_funding_rate")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value == value and value not in (float("inf"), float("-inf")):
            return value
    return None


def _ticker_age_seconds(symbol: str, now: datetime) -> float | None:
    snapshot = data.crypto.futures.mark_price(symbol=symbol, exchange="bitget")
    for row in data.to_records(snapshot):
        raw = row.get("time")
        stamp = _coerce_ms(raw)
        if stamp is None:
            continue
        return max(0.0, now.timestamp() - stamp / 1000.0)
    return None


def _bars_are_stale(last_open: Any, now: datetime, bar_hours: int) -> bool:
    stamp = _coerce_ms(last_open)
    if stamp is None:
        parsed = _parse_ts(last_open)
        if parsed is None:
            return True
        stamp = int(parsed.timestamp() * 1000)
    interval_ms = bar_hours * 60 * 60 * 1000
    return (now.timestamp() * 1000) - (stamp + interval_ms) > 2 * interval_ms


def _read_positions() -> tuple[list[dict[str, Any]], bool]:
    result = trade.contract.current_position(symbol="", product_type="USDT-FUTURES")
    if not trade.is_success(result):
        return [], False
    records = trade.helpers.contract_position_records(result, symbol="")
    parsed: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            return [], False
        symbol = str(record.get("symbol") or record.get("instId") or "").upper()
        size = _position_size(record)
        if size is None or not symbol:
            return [], False
        if size > 0:
            parsed.append(record)
    return parsed, True


def _position_size(record: dict[str, Any]) -> float | None:
    for key in ("size", "total", "holdSize"):
        if key not in record:
            continue
        try:
            return abs(float(record[key]))
        except (TypeError, ValueError):
            return None
    return None


def _reconcile_owned(state: dict[str, Any], records: list[dict[str, Any]]) -> None:
    """Mark our pending entry open once the exchange shows that symbol."""
    live = {
        str(record.get("symbol") or record.get("instId") or "").upper()
        for record in records
    }
    changed = False
    for item in state.get("owned", []):
        symbol = str(item.get("symbol") or "")
        if item.get("status") == "pending" and symbol in live:
            item["status"] = "open"
            item.setdefault("opened_at", datetime.now(timezone.utc).isoformat())
            changed = True
    if changed:
        _save_state(state)


def _foreign_symbols(records: list[dict[str, Any]], state: dict[str, Any]) -> list[str]:
    owned = {
        str(item.get("symbol") or "")
        for item in state.get("owned", [])
        if item.get("status") == "open"
    }
    foreign: list[str] = []
    for record in records:
        symbol = str(record.get("symbol") or record.get("instId") or "").upper()
        if symbol and symbol not in owned:
            foreign.append(symbol)
    return foreign


def _halt_reason(state: dict[str, Any], cfg: Config) -> str:
    if int(state.get("consecutive_losses") or 0) >= cfg.max_consecutive_losses:
        return HALT_CONSECUTIVE_LOSSES
    if float(state.get("cumulative_realised") or 0.0) <= cfg.playbook_stop_usdt:
        return HALT_PLAYBOOK_LOSS
    return HALT_DAILY_LOSS


def _halted(state: dict[str, Any], cfg: Config) -> bool:
    if int(state.get("consecutive_losses") or 0) >= cfg.max_consecutive_losses:
        return True
    if float(state.get("cumulative_realised") or 0.0) <= cfg.playbook_stop_usdt:
        return True
    today = datetime.now(timezone.utc).date().isoformat()
    if float(state.get("daily", {}).get(today, 0.0)) <= cfg.daily_pause_usdt:
        return True
    return False


def _margin_remaining(cfg: Config, state: dict[str, Any]) -> float:
    used = 0.0
    for item in state.get("owned", []):
        try:
            qty = float(item.get("qty") or 0)
            entry = float(item.get("entry") or 0)
        except (TypeError, ValueError):
            continue
        if qty > 0 and entry > 0:
            used += qty * entry / cfg.applied_leverage
    return cfg.margin_budget - used


def _emit_hold(symbol: str, reason: str, now: datetime, text: str) -> None:
    _append_log(action_row(timestamp=now, symbol=symbol, side="none", reason_code=reason, detail=text))
    runtime.emit_signal_or_follow(
        action="hold",
        symbol=symbol,
        confidence=0.0,
        reason_code=reason,
        reason_text=text,
    )


def _log_reject(symbol: str, detail: str) -> None:
    _append_log(
        action_row(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            side="none",
            reason_code=ORDER_REJECTED,
            detail=detail,
        )
    )


def _extract_order_id(result: Any) -> str:
    for attr in ("order_id", "orderId"):
        value = getattr(result, attr, None)
        if value:
            return str(value)
    raw = getattr(result, "raw", None)
    if isinstance(raw, dict):
        for key in ("orderId", "order_id"):
            if raw.get(key):
                return str(raw[key])
        data_row = raw.get("data")
        if isinstance(data_row, dict):
            for key in ("orderId", "order_id"):
                if data_row.get(key):
                    return str(data_row[key])
    return ""


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"owned": [], "daily": {}, "cumulative_realised": 0.0, "consecutive_losses": 0}
    loaded = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {"owned": [], "daily": {}, "cumulative_realised": 0.0, "consecutive_losses": 0}
    loaded.setdefault("owned", [])
    loaded.setdefault("daily", {})
    return loaded


def _save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state), encoding="utf-8")
    temporary.replace(STATE_PATH)


def _append_log(row: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _coerce_ms(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    if number < 10_000_000_000:
        number *= 1000
    return number
