"""Pure risk helpers for the USDT-M Trend v1 Playbook.

No SDK imports. All money math lives here so backtest and live
paths size identically.
"""

from decimal import Decimal, InvalidOperation


def to_decimal(value, default=None):
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def position_qty(risk_usdt, stop_distance_price, size_increment="0.0001",
                min_qty="0", max_qty=None):
    """Size = fixed loss budget / stop distance, floored to size increment."""
    risk = to_decimal(risk_usdt)
    dist = to_decimal(stop_distance_price)
    step = to_decimal(size_increment) or Decimal("0.0001")
    if risk is None or dist is None or risk <= 0 or dist <= 0 or step <= 0:
        return {"ok": False, "qty": "0", "reason": "invalid sizing inputs"}
    raw = risk / dist
    floored = (raw // step) * step
    if floored <= 0:
        return {"ok": False, "qty": "0", "reason": "qty below minimum increment"}
    min_q = to_decimal(min_qty) or Decimal("0")
    if floored < min_q:
        return {"ok": False, "qty": "0", "reason": "qty below exchange minimum"}
    if max_qty is not None:
        cap = to_decimal(max_qty)
        if cap is not None and floored > cap:
            floored = (cap // step) * step
    return {"ok": True, "qty": str(floored.normalize()), "reason": "ok"}


def stop_take_prices(entry_price, atr_value, atr_mult=1.5, tp_r_mult=2.0, side="long"):
    """Return (stop_price, take_price) for a long; R = stop distance."""
    entry = to_decimal(entry_price)
    atr = to_decimal(atr_value)
    mult = to_decimal(atr_mult)
    tp_r = to_decimal(tp_r_mult)
    if entry is None or atr is None or mult is None or tp_r is None:
        return {"ok": False, "reason": "invalid stop inputs"}
    if entry <= 0 or atr <= 0 or mult <= 0 or tp_r <= 0:
        return {"ok": False, "reason": "non-positive stop inputs"}
    risk_dist = atr * mult
    if side == "long":
        stop = entry - risk_dist
        take = entry + risk_dist * tp_r
        if stop <= 0:
            return {"ok": False, "reason": "stop below zero"}
    else:
        return {"ok": False, "reason": "shorts disabled (long-only playbook)"}
    return {"ok": True, "stop": stop, "take": take, "risk_dist": risk_dist}


def leverage_for(notional_usdt, margin_usdt, cap=5):
    """Leverage implied by notional vs margin, hard-capped."""
    notional = to_decimal(notional_usdt)
    margin = to_decimal(margin_usdt)
    if notional is None or margin is None or margin <= 0 or notional <= 0:
        return {"ok": False, "leverage": 1, "reason": "invalid leverage inputs"}
    implied = notional / margin
    lev = int(implied.to_integral_value(rounding="ROUND_CEILING"))
    lev = max(1, min(lev, int(cap)))
    return {"ok": True, "leverage": lev, "capped": implied > int(cap)}


def in_funding_blackout(now_utc, blackout_minutes=15):
    """True within +/-blackout of 00:00, 08:00, 16:00 UTC funding."""
    minute_of_day = now_utc.hour * 60 + now_utc.minute + now_utc.second / 60.0
    for funding_hour in (0, 8, 16):
        funding_min = funding_hour * 60
        if abs(minute_of_day - funding_min) <= blackout_minutes:
            return True
        if abs(minute_of_day - (funding_min + 1440)) <= blackout_minutes:
            return True
    return False


def funding_blocks_long(funding_rate_decimal, guard_pct=0.03):
    """Longs pay positive funding; skip when rate exceeds the guard."""
    rate = to_decimal(funding_rate_decimal)
    guard = to_decimal(guard_pct)
    if rate is None or guard is None:
        return {"block": True, "reason": "funding rate unavailable -> fail closed"}
    rate_pct = rate * Decimal("100")
    if rate_pct > guard:
        return {"block": True, "reason": "funding above guard",
                "rate_pct": str(rate_pct)}
    return {"block": False, "reason": "funding within guard",
            "rate_pct": str(rate_pct)}


def check_portfolio_guards(daily_realised_usdt, consec_losses,
                           daily_pause=-30, daily_stop=-40, max_consec=5):
    """Return (allow_new_entries, halt_playbook, reason_code)."""
    pnl = to_decimal(daily_realised_usdt)
    if pnl is None:
        return {"allow": False, "halt": False, "code": "NO_TRADE_PNL_UNKNOWN",
                "note": "daily PnL untracked -> fail closed on new entries"}
    if pnl <= Decimal(str(daily_stop)):
        return {"allow": False, "halt": True, "code": "HALT_DAILY_STOP",
                "note": "daily stop hit; stop Playbook"}
    if pnl <= Decimal(str(daily_pause)):
        return {"allow": False, "halt": False, "code": "NO_TRADE_DAILY_PAUSE",
                "note": "daily pause level hit; no new entries today"}
    if int(consec_losses or 0) >= int(max_consec):
        return {"allow": False, "halt": True, "code": "HALT_CONSEC_LOSS",
                "note": "consecutive-loss halt"}
    return {"allow": True, "halt": False, "code": "OK",
            "note": "portfolio guards pass"}
