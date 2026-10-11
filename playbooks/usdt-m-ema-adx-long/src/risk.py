"""Position sizing, tick quantization, funding clock, and net-of-cost math.

Sizing targets a fixed USDT loss at the stop. Quantity is floored to the
exchange size step so the loss at the stop is not larger than that fixed loss.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from typing import Any, Sequence


FUNDING_HOURS = (0, 8, 16)
HOUR_MS = 60 * 60 * 1000
# bitget_data funding_rate is the percent display of the decimal rate.
# Public BTCUSDT settlement 0.00004 at 2026-10-09T16:00:00Z matched managed
# funding_rate 0.004 on the bar whose funding_timestamp is that instant.
MANAGED_FUNDING_PERCENT_SCALE = 100.0


def coverage_tail_allowance_ms(bar_hours: int) -> int:
    """How old the last closed bar may be at the window end.

    One bar interval plus one hour. On 1H that is two hours, the same tail
    the v2.1 coverage check used. A 4H bar that closed four hours before the
    window end is still a complete bar for that window.
    """
    if bar_hours not in (1, 4):
        raise ValueError("bar_hours must be 1 or 4")
    return (bar_hours + 1) * HOUR_MS


def kline_tail_covers(last_ms: int, end_ms: int, bar_hours: int) -> bool:
    """True when the last kline timestamp sits inside the interval-sized tail."""
    return last_ms >= end_ms - coverage_tail_allowance_ms(bar_hours)


def four_hour_open(open_ts: datetime) -> datetime:
    """Start of the 4H window that contains this 1H bar open."""
    hour = open_ts.hour - (open_ts.hour % 4)
    return open_ts.replace(hour=hour, minute=0, second=0, microsecond=0)


def fold_hour_bar(
    bucket: dict[str, Any] | None,
    open_ts: datetime,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Fold one 1H bar into a 4H bucket.

    The completed bucket is returned only when it holds four hourly bars.
    A short bucket at a gap is dropped rather than treated as a 4H bar.
    """
    start = four_hour_open(open_ts)
    fresh = {
        "start": start,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "hours": 1,
    }
    if bucket is None or bucket.get("start") != start:
        completed = bucket if bucket is not None and bucket.get("hours") == 4 else None
        return completed, fresh
    bucket["high"] = max(float(bucket["high"]), high)
    bucket["low"] = min(float(bucket["low"]), low)
    bucket["close"] = close
    bucket["volume"] = float(bucket["volume"]) + volume
    bucket["hours"] = int(bucket["hours"]) + 1
    return None, bucket


def funding_rate_from_managed(raw: float) -> float:
    """Convert a managed funding_rate percent display into a decimal rate."""
    return raw / MANAGED_FUNDING_PERCENT_SCALE


def millis_from_bar_clock(ns_value: int, year: int) -> int:
    """Millisecond epoch for a replay index.

    A millisecond epoch read as nanoseconds still sits in 1970, and the
    nanosecond field is the original millisecond number.
    """
    if year < 2000 and ns_value >= 10**11:
        return int(ns_value)
    return int(ns_value / 1_000_000)


def ohlc_is_valid(open_: float, high: float, low: float, close: float) -> bool:
    """True when a bar can be replayed without inventing a price."""
    values = (open_, high, low, close)
    for value in values:
        if value != value or value in (float("inf"), float("-inf")) or value <= 0:
            return False
    return low <= high and low <= open_ and low <= close and high >= open_ and high >= close


def align_ohlc_to_tick(
    open_: float, high: float, low: float, close: float, tick: float
) -> tuple[float, float, float, float] | None:
    """Return a bar on the exchange increment, or None when it is not a price.

    Every price is moved to the nearest tick. If that would put low above
    open or close, low and high are pulled back onto the same grid. The
    returned floats are then checked the way the replay engine rounds a
    float onto the instrument precision (half away from zero). That second
    rounding is what aborted the pullback replay with ``high was < open``
    (and the cross replay with ``low was > open``): open can round up while
    high rounds down. High is lifted and low is dropped to the extreme of
    those integer units before the bar is emitted. Off-tick prints are not
    passed through. Nothing is interpolated and no strategy threshold changes.
    """
    if not ohlc_is_valid(open_, high, low, close) or tick <= 0:
        return None
    step = _decimal(tick)
    places = _tick_places(step)
    o = quantize_nearest(open_, tick)
    h = quantize_nearest(high, tick)
    l = quantize_nearest(low, tick)
    c = quantize_nearest(close, tick)
    l = min(l, o, c)
    h = max(h, o, c)
    if l <= 0 or h < l:
        return None
    emitted = tuple(_emit_tick(value, places) for value in (o, h, l, c))
    return _clamp_engine_bar(emitted, step, places)


def expand_bar_to_prior_close(
    open_: float,
    high: float,
    low: float,
    close: float,
    prior_close: float,
    tick: float,
) -> tuple[float, float, float, float] | None:
    """Keep a one-tick rounding gap from the previous close inside the bar.

    A larger gap is a real print and is left unchanged. The close is not
    rewritten.
    """
    if not ohlc_is_valid(open_, high, low, close) or tick <= 0:
        return None
    if prior_close != prior_close or prior_close in (float("inf"), float("-inf")) or prior_close <= 0:
        return (open_, high, low, close)
    if prior_close < low and (low - prior_close) <= tick + tick * 1e-9:
        low = prior_close
    elif prior_close > high and (prior_close - high) <= tick + tick * 1e-9:
        high = prior_close
    if not ohlc_is_valid(open_, high, low, close):
        return None
    return (open_, high, low, close)


def _tick_places(step: Decimal) -> int:
    exponent = step.as_tuple().exponent
    if not isinstance(exponent, int):
        return 0
    return max(0, -exponent)


def _emit_tick(value: Decimal, places: int) -> float:
    return float(f"{value:.{places}f}")


def _engine_units(value: float, places: int) -> int:
    """Match Rust ``f64::round``: half away from zero, at the instrument precision."""
    scaled = float(value) * float(10 ** places)
    if scaled >= 0:
        return int(math.floor(scaled + 0.5))
    return int(math.ceil(scaled - 0.5))


def _clamp_engine_bar(
    bar: tuple[float, float, float, float], step: Decimal, places: int
) -> tuple[float, float, float, float] | None:
    """Expand high and low onto the same units the engine will compare."""
    units = [_engine_units(value, places) for value in bar]
    units[2] = min(units)
    units[1] = max(units)
    if units[2] <= 0 or units[1] < units[2]:
        return None
    emitted = tuple(_emit_tick(Decimal(unit) * step, places) for unit in units)
    checked = [_engine_units(value, places) for value in emitted]
    if checked != units:
        return None
    if not ohlc_is_valid(*emitted):
        return None
    return emitted


def funding_series_gap_ms(stamps: Sequence[int], max_gap_ms: int) -> int | None:
    """Largest hole between stamps, or None when every step is inside the cap.

    A hole is left empty. Callers must not fill it with zero or with the
    previous rate.
    """
    ordered = sorted({int(stamp) for stamp in stamps})
    worst: int | None = None
    for prev, nxt in zip(ordered, ordered[1:]):
        gap = nxt - prev
        if gap > max_gap_ms and (worst is None or gap > worst):
            worst = gap
    return worst


def funding_page_ignores_window(
    earliest_ms: int, latest_ms: int, cursor_end_ms: int, interval_ms: int
) -> bool:
    """True when a page did not start earlier than the end it was given.

    A historical request that comes back as the latest page is not coverage.
    Callers keep the rows they already have and leave the older gap empty.
    """
    if earliest_ms >= cursor_end_ms:
        return True
    return latest_ms > cursor_end_ms and earliest_ms >= cursor_end_ms - interval_ms


def _decimal(value: float | Decimal | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def quantize(value: float, tick: float, rounding: str) -> Decimal:
    step = _decimal(tick)
    if step <= 0:
        raise ValueError("tick must be positive")
    amount = _decimal(value)
    units = (amount / step).to_integral_value(rounding=rounding)
    return units * step


def quantize_floor(value: float, tick: float) -> Decimal:
    return quantize(value, tick, ROUND_FLOOR)


def quantize_ceil(value: float, tick: float) -> Decimal:
    return quantize(value, tick, ROUND_CEILING)


def quantize_nearest(value: float, tick: float) -> Decimal:
    return quantize(value, tick, ROUND_HALF_UP)


@dataclass(frozen=True)
class SizePlan:
    qty: Decimal
    entry: Decimal
    stop: Decimal
    take_profit: Decimal
    stop_distance: Decimal
    risk_usdt: Decimal
    notional: Decimal
    margin: Decimal
    reason: str
    detail: str = ""


def plan_long_size(
    *,
    close: float,
    atr: float,
    atr_stop_mult: float,
    reward_r: float,
    fixed_loss_usdt: float,
    price_tick: float,
    size_step: float,
    min_qty: float,
    min_notional_usdt: float,
    leverage: int,
    margin_remaining: float,
) -> SizePlan:
    """Build a long limit plan or a rejected plan with a reason code."""
    if close <= 0 or atr <= 0 or atr_stop_mult <= 0 or reward_r <= 0:
        return _reject("INVALID_SIGNAL")
    if leverage < 1:
        return _reject("SKIP_LEVERAGE_CAP")
    entry = quantize_nearest(close, price_tick)
    raw_stop = float(entry) - atr_stop_mult * atr
    stop = quantize_floor(raw_stop, price_tick)
    distance = entry - stop
    if distance <= 0 or entry <= 0:
        return _reject("INVALID_SIGNAL")
    # Optimistic isolated long liquidation ignores maintenance: adverse move of 1/leverage.
    # The public contract payload has no keepMarginRate, so that rate is not invented.
    # Real liquidation is closer to entry when maintenance is positive, so equality skips too.
    liquidation_fraction = Decimal(1) / Decimal(leverage)
    stop_fraction = distance / entry
    if stop_fraction >= liquidation_fraction:
        return _reject(
            "SKIP_LIQUIDATION_INSIDE_STOP",
            (
                f"stop_fraction={stop_fraction} liquidation_fraction={liquidation_fraction} "
                f"leverage={leverage}; isolated liquidation is inside the 1.5 ATR stop"
            ),
        )
    risk_budget = _decimal(fixed_loss_usdt)
    raw_qty = risk_budget / distance
    qty = quantize_floor(float(raw_qty), size_step)
    min_size = _decimal(min_qty)
    if qty < min_size:
        return _reject("SKIP_SIZE")
    actual_risk = qty * distance
    if actual_risk > risk_budget:
        return _reject("SKIP_SIZE")
    notional = qty * entry
    if notional < _decimal(min_notional_usdt):
        return _reject("SKIP_MIN_NOTIONAL")
    margin = notional / Decimal(leverage)
    if margin > _decimal(margin_remaining):
        return _reject("SKIP_MARGIN")
    take_profit = quantize_nearest(float(entry + distance * _decimal(reward_r)), price_tick)
    if take_profit <= entry:
        return _reject("INVALID_SIGNAL")
    return SizePlan(
        qty=qty,
        entry=entry,
        stop=stop,
        take_profit=take_profit,
        stop_distance=distance,
        risk_usdt=actual_risk,
        notional=notional,
        margin=margin,
        reason="TRIGGER_LONG",
        detail="",
    )


def plan_short_size(
    *,
    close: float,
    atr: float,
    atr_stop_mult: float,
    reward_r: float,
    fixed_loss_usdt: float,
    price_tick: float,
    size_step: float,
    min_qty: float,
    min_notional_usdt: float,
    leverage: int,
    margin_remaining: float,
) -> SizePlan:
    """Mirror of the long plan. The stop is above entry. Size is not raised."""
    if close <= 0 or atr <= 0 or atr_stop_mult <= 0 or reward_r <= 0:
        return _reject("INVALID_SIGNAL")
    if leverage < 1:
        return _reject("SKIP_LEVERAGE_CAP")
    entry = quantize_nearest(close, price_tick)
    raw_stop = float(entry) + atr_stop_mult * atr
    stop = quantize_ceil(raw_stop, price_tick)
    distance = stop - entry
    if distance <= 0 or entry <= 0:
        return _reject("INVALID_SIGNAL")
    liquidation_fraction = Decimal(1) / Decimal(leverage)
    stop_fraction = distance / entry
    if stop_fraction >= liquidation_fraction:
        return _reject(
            "SKIP_LIQUIDATION_INSIDE_STOP",
            (
                f"stop_fraction={stop_fraction} liquidation_fraction={liquidation_fraction} "
                f"leverage={leverage}; isolated liquidation is inside the stop"
            ),
        )
    risk_budget = _decimal(fixed_loss_usdt)
    qty = quantize_floor(float(risk_budget / distance), size_step)
    if qty < _decimal(min_qty):
        return _reject("SKIP_SIZE")
    actual_risk = qty * distance
    if actual_risk > risk_budget:
        return _reject("SKIP_SIZE")
    notional = qty * entry
    if notional < _decimal(min_notional_usdt):
        return _reject("SKIP_MIN_NOTIONAL")
    margin = notional / Decimal(leverage)
    if margin > _decimal(margin_remaining):
        return _reject("SKIP_MARGIN")
    take_profit = quantize_nearest(float(entry - distance * _decimal(reward_r)), price_tick)
    if take_profit >= entry or take_profit <= 0:
        return _reject("INVALID_SIGNAL")
    return SizePlan(
        qty=qty,
        entry=entry,
        stop=stop,
        take_profit=take_profit,
        stop_distance=distance,
        risk_usdt=actual_risk,
        notional=notional,
        margin=margin,
        reason="TRIGGER_SHORT",
        detail="",
    )


def _reject(reason: str, detail: str = "") -> SizePlan:
    zero = Decimal("0")
    return SizePlan(
        qty=zero,
        entry=zero,
        stop=zero,
        take_profit=zero,
        stop_distance=zero,
        risk_usdt=zero,
        notional=zero,
        margin=zero,
        reason=reason,
        detail=detail,
    )


def in_funding_blackout(ts: datetime, minutes: int) -> bool:
    """True when `ts` is within `minutes` of 00:00, 08:00, or 16:00 UTC."""
    moment = ts.astimezone(timezone.utc)
    second_of_day = moment.hour * 3600 + moment.minute * 60 + moment.second
    window = minutes * 60
    day = 24 * 3600
    for hour in FUNDING_HOURS:
        funding = hour * 3600
        delta = min((second_of_day - funding) % day, (funding - second_of_day) % day)
        if delta <= window:
            return True
    return False


def next_blackout_start(ts: datetime, minutes: int) -> datetime:
    """UTC timestamp when the next funding blackout begins, strictly after `ts`."""
    moment = ts.astimezone(timezone.utc).replace(microsecond=0)
    day = moment.date()
    candidates: list[datetime] = []
    for offset in range(3):
        base = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(days=offset)
        for hour in FUNDING_HOURS:
            candidates.append(base + timedelta(hours=hour) - timedelta(minutes=minutes))
    for candidate in candidates:
        if candidate > moment:
            return candidate
    raise RuntimeError("no future funding blackout")


def exposure_hits_blackout(start: datetime, end: datetime, minutes: int) -> bool:
    """True when (start, end] overlaps a funding blackout."""
    begin = start.astimezone(timezone.utc)
    finish = end.astimezone(timezone.utc)
    if finish <= begin:
        return False
    origin = begin.date()
    for offset in range(-1, 3):
        base = datetime(origin.year, origin.month, origin.day, tzinfo=timezone.utc) + timedelta(
            days=offset
        )
        for hour in FUNDING_HOURS:
            funding = base + timedelta(hours=hour)
            blackout_start = funding - timedelta(minutes=minutes)
            blackout_end = funding + timedelta(minutes=minutes)
            if blackout_start < finish and blackout_end > begin:
                return True
    return False


def is_funding_settlement(ts: datetime) -> bool:
    moment = ts.astimezone(timezone.utc)
    return (
        moment.minute == 0
        and moment.second == 0
        and moment.microsecond == 0
        and moment.hour in FUNDING_HOURS
    )


@dataclass(frozen=True)
class ClosedTrade:
    symbol: str
    entry_ts: str
    exit_ts: str
    side: str
    qty: float
    entry_price: float
    exit_price: float
    entry_fee_rate: float
    exit_fee_rate: float
    slippage_usdt: float
    funding_usdt: float
    funding_known: bool
    risk_usdt: float
    reason_code: str

    def gross(self) -> float:
        if self.side == "long":
            return (self.exit_price - self.entry_price) * self.qty
        if self.side == "short":
            return (self.entry_price - self.exit_price) * self.qty
        return 0.0

    def fee_usdt(self) -> float:
        return (self.entry_price * self.qty * self.entry_fee_rate) + (
            self.exit_price * self.qty * self.exit_fee_rate
        )

    def net(self, cost_multiplier: float) -> float | None:
        if not self.funding_known:
            return None
        return (
            self.gross()
            - cost_multiplier * self.fee_usdt()
            - cost_multiplier * self.slippage_usdt
            - self.funding_usdt
        )


def expectancy_r(trades: Sequence[ClosedTrade], cost_multiplier: float) -> float | None:
    if not trades:
        return None
    nets: list[float] = []
    for trade in trades:
        net = trade.net(cost_multiplier)
        if net is None or trade.risk_usdt <= 0:
            return None
        nets.append(net / trade.risk_usdt)
    return sum(nets) / len(nets)
