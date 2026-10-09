"""Position sizing, tick quantization, funding clock, and net-of-cost math.

Sizing targets a fixed USDT loss at the stop. Quantity is floored to the
exchange size step so the loss at the stop is not larger than that fixed loss.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from typing import Sequence


FUNDING_HOURS = (0, 8, 16)
# bitget_data funding_rate is the percent display of the decimal rate.
# Public BTCUSDT settlement 0.00004 at 2026-10-09T16:00:00Z matched managed
# funding_rate 0.004 on the bar whose funding_timestamp is that instant.
MANAGED_FUNDING_PERCENT_SCALE = 100.0


def funding_rate_from_managed(raw: float) -> float:
    """Convert a managed funding_rate percent display into a decimal rate."""
    return raw / MANAGED_FUNDING_PERCENT_SCALE


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
    )


def _reject(reason: str) -> SizePlan:
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
        if self.side != "long":
            return 0.0
        return (self.exit_price - self.entry_price) * self.qty

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
