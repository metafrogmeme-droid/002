"""Shared risk, halt, funding, and sizing gates."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Any

from . import spec


def _dec(value: object, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except Exception:
        return Decimal(default)


def quantize_price(symbol: str, price: float) -> Decimal:
    tick = _dec(spec.tick_size(symbol))
    raw = _dec(price)
    if tick <= 0:
        return raw
    steps = (raw / tick).to_integral_value(rounding=ROUND_DOWN)
    return steps * tick


def quantize_qty(symbol: str, qty: float) -> Decimal:
    step = _dec(spec.min_size(symbol))
    raw = _dec(qty)
    if step <= 0:
        return raw
    steps = (raw / step).to_integral_value(rounding=ROUND_DOWN)
    return steps * step


def spread_bps(bid: object, ask: object) -> float | None:
    bid_d = _dec(bid)
    ask_d = _dec(ask)
    if bid_d <= 0 or ask_d <= 0 or ask_d < bid_d:
        return None
    mid = (bid_d + ask_d) / Decimal("2")
    if mid <= 0:
        return None
    return float((ask_d - bid_d) / mid * Decimal("10000"))


def ticker_stale(ts_ms: object, now: datetime, max_age_sec: int) -> bool:
    try:
        stamp = int(ts_ms)
    except (TypeError, ValueError):
        return True
    now_ms = int(now.timestamp() * 1000)
    return now_ms - stamp > max_age_sec * 1000


def bar_feed_stale(last_open_ms: int | None, now: datetime, interval_ms: int) -> bool:
    if last_open_ms is None:
        return True
    last_close_ms = last_open_ms + interval_ms
    now_ms = int(now.timestamp() * 1000)
    return now_ms - last_close_ms > 2 * interval_ms


def seconds_to_funding(now: datetime, next_funding_ms: object, interval_hours: int) -> float:
    try:
        next_ms = int(next_funding_ms)
        return (next_ms - int(now.timestamp() * 1000)) / 1000.0
    except (TypeError, ValueError):
        hour = now.astimezone(timezone.utc).hour
        elapsed = (hour % interval_hours) * 3600 + now.minute * 60 + now.second
        return float(interval_hours * 3600 - elapsed)


def in_funding_blackout(
    now: datetime,
    next_funding_ms: object,
    interval_hours: int,
    blackout_min: int,
    limit_ttl_hours: int,
) -> bool:
    seconds = seconds_to_funding(now, next_funding_ms, interval_hours)
    blackout = blackout_min * 60
    # A resting limit can live through the next settlement.
    if 0 <= seconds <= limit_ttl_hours * 3600 + blackout:
        return True
    if seconds < 0 and abs(seconds) <= blackout:
        return True
    return False


def expected_funding_r(
    funding_rate: object,
    notional: float,
    planned_hold_hours: int,
    interval_hours: int,
    risk_usdt: float,
) -> float:
    rate = float(_dec(funding_rate))
    periods = max(planned_hold_hours / max(interval_hours, 1), 1.0)
    cost = abs(rate) * notional * periods
    if risk_usdt <= 0:
        return 0.0
    return cost / risk_usdt


def size_from_risk(
    symbol: str,
    *,
    price: float,
    stop_distance: float,
    risk_usdt: float,
    leverage_cap: int,
    margin_budget: float,
) -> dict[str, Any]:
    if price <= 0 or stop_distance <= 0 or risk_usdt <= 0:
        return {"sizing_ok": False, "reason": "SIZING_REJECT", "qty": "0"}
    raw_qty = risk_usdt / stop_distance
    qty = quantize_qty(symbol, raw_qty)
    min_qty = _dec(spec.min_size(symbol))
    if qty < min_qty:
        return {
            "sizing_ok": False,
            "reason": "SIZING_REJECT",
            "qty": str(qty),
            "min_qty": str(min_qty),
        }
    notional = float(qty) * price
    max_notional = margin_budget * max(leverage_cap, 1)
    if notional > max_notional and price > 0:
        qty = quantize_qty(symbol, max_notional / price)
        notional = float(qty) * price
    if qty < min_qty or notional < 5:
        return {
            "sizing_ok": False,
            "reason": "SIZING_REJECT",
            "qty": str(qty),
            "notional_usdt": notional,
            "min_open_notional_usdt": 5.0,
        }
    leverage = min(leverage_cap, max(1, int((notional / max(margin_budget, 1.0)) + 0.999)))
    margin = notional / leverage
    return {
        "sizing_ok": True,
        "qty": str(qty),
        "notional_usdt": notional,
        "min_open_notional_usdt": 5.0,
        "leverage": leverage,
        "margin_usdt": margin,
        "stop_distance": stop_distance,
    }


@dataclass
class HaltState:
    halted: bool = False
    halt_reason: str = ""
    daily_realized_usdt: float = 0.0
    daily_date_utc: str = ""
    consecutive_losses: int = 0
    opened_symbols: tuple[str, ...] = ()
    pending_order_id: str = ""
    pending_symbol: str = ""
    pending_submitted_ms: int = 0
    last_entry_price: str = ""
    last_stop_price: str = ""
    last_tp_price: str = ""


def utc_date(now: datetime) -> str:
    return now.astimezone(timezone.utc).date().isoformat()


def apply_day_rollover(state: HaltState, now: datetime) -> HaltState:
    today = utc_date(now)
    if state.daily_date_utc != today:
        state.daily_realized_usdt = 0.0
        state.daily_date_utc = today
        if state.halt_reason in {"HALT_DAILY_PAUSE"}:
            state.halted = False
            state.halt_reason = ""
    return state


def register_realized(state: HaltState, pnl_usdt: float, pause_usdt: float, stop_usdt: float) -> HaltState:
    state.daily_realized_usdt += pnl_usdt
    if pnl_usdt < 0:
        state.consecutive_losses += 1
    elif pnl_usdt > 0:
        state.consecutive_losses = 0
    if state.daily_realized_usdt <= -abs(stop_usdt):
        state.halted = True
        state.halt_reason = "HALT_PLAYBOOK_STOP"
    elif state.daily_realized_usdt <= -abs(pause_usdt) and state.halt_reason != "HALT_PLAYBOOK_STOP":
        state.halt_reason = "HALT_DAILY_PAUSE"
    return state
