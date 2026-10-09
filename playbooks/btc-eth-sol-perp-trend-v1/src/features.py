"""Shared, replayable feature engineering for the perp trend Playbook.

Everything here is pure arithmetic on closed bars so the exact same code path
is used by the Nautilus replay strategy and by the live scheduler. No data,
trade, or runtime SDK calls live in this module.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional, Sequence


def bisect_left(values: Sequence[float], x: float) -> int:
    lo, hi = 0, len(values)
    while lo < hi:
        mid = (lo + hi) // 2
        if values[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def bisect_right(values: Sequence[float], x: float) -> int:
    lo, hi = 0, len(values)
    while lo < hi:
        mid = (lo + hi) // 2
        if x < values[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


def insort(values: list, x: float) -> None:
    values.insert(bisect_right(values, x), x)

INTERVAL_SECONDS = 3600
FUNDING_SETTLEMENT_MINUTES = (0, 8 * 60, 16 * 60)

# Reason codes shared by backtest trade log and live decision log.
RC_ENTRY_SUBMIT = "ENTRY_SUBMIT"
RC_ENTRY_FILL = "ENTRY_FILL"
RC_ENTRY_EXPIRED = "ENTRY_EXPIRED"
RC_EXIT_TP = "EXIT_TAKE_PROFIT"
RC_EXIT_SL = "EXIT_STOP_LOSS"
RC_EXIT_TIME = "EXIT_TIME_STOP"
RC_EXIT_DAILY_STOP = "EXIT_DAILY_STOP"
RC_EXIT_END = "EXIT_END_OF_DATA"
RC_SKIP_REGIME = "SKIP_REGIME"
RC_SKIP_FUNDING_WINDOW = "SKIP_FUNDING_WINDOW"
RC_SKIP_FUNDING_RATE = "SKIP_FUNDING_RATE"
RC_SKIP_VOLUME = "SKIP_VOLUME"
RC_SKIP_MAX_POSITIONS = "SKIP_MAX_POSITIONS"
RC_SKIP_DAILY_PAUSE = "SKIP_DAILY_PAUSE"
RC_SKIP_HALTED = "SKIP_HALTED"
RC_SKIP_SIZE = "SKIP_SIZE_BELOW_MIN"
RC_SKIP_STALE = "SKIP_STALE_DATA"
RC_SKIP_PENDING = "SKIP_PENDING_ENTRY"
RC_HALT_CONSEC_LOSS = "HALT_CONSECUTIVE_LOSSES"
RC_HALT_DAILY_STOP = "HALT_DAILY_STOP"
RC_HALT_STALE = "HALT_STALE_DATA"
RC_ALERT_FOREIGN_POSITION = "ALERT_FOREIGN_POSITION"
RC_WATCH = "WATCH_NO_SIGNAL"


@dataclass
class StrategyParams:
    """Decision parameters. Defaults mirror manifest strategy_config and are
    always overridden by the manifest values at runtime."""

    adx_period: int = 14
    adx_min: float = 25.0
    atr_period: int = 14
    atr_pct_lookback_bars: int = 720
    atr_pct_min: float = 20.0
    atr_pct_max: float = 90.0
    ema_fast: int = 20
    ema_slow: int = 50
    volume_avg_bars: int = 20
    volume_multiple: float = 1.5
    stop_atr_multiple: float = 1.5
    take_profit_r: float = 2.0
    entry_ttl_hours: int = 4
    time_stop_hours: int = 8
    max_concurrent_positions: int = 3
    risk_per_trade_usdt: float = 15.0
    leverage: int = 5
    margin_budget: float = 1500.0
    daily_pause_loss_usdt: float = 30.0
    daily_stop_loss_usdt: float = 40.0
    max_consecutive_losses: int = 5
    funding_window_minutes: int = 15
    max_funding_rate_pct: float = 0.03
    slippage_ticks: int = 1
    side_mode: str = "long_only"

    @classmethod
    def from_config(cls, cfg: dict) -> "StrategyParams":
        params = cls()
        for name in params.__dataclass_fields__:
            if name in cfg and cfg[name] is not None:
                current = getattr(params, name)
                raw = cfg[name]
                if isinstance(current, bool):
                    setattr(params, name, bool(raw))
                elif isinstance(current, int):
                    setattr(params, name, int(raw))
                elif isinstance(current, float):
                    setattr(params, name, float(raw))
                else:
                    setattr(params, name, str(raw))
        return params

    def warmup_bars(self) -> int:
        return max(
            self.atr_pct_lookback_bars + self.atr_period + 1,
            self.ema_slow * 3,
            self.adx_period * 3 + 1,
            self.volume_avg_bars + 1,
        )


class Ema:
    def __init__(self, period: int) -> None:
        self.alpha = 2.0 / (period + 1)
        self.value: Optional[float] = None

    def update(self, x: float) -> float:
        self.value = x if self.value is None else self.alpha * x + (1 - self.alpha) * self.value
        return self.value


class WilderAtrAdx:
    """Incremental Wilder ATR, +DI, -DI and ADX."""

    def __init__(self, atr_period: int, adx_period: int) -> None:
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.prev_high: Optional[float] = None
        self.prev_low: Optional[float] = None
        self.prev_close: Optional[float] = None
        self.atr: Optional[float] = None
        self.sm_plus: Optional[float] = None
        self.sm_minus: Optional[float] = None
        self.adx: Optional[float] = None
        self.plus_di: Optional[float] = None
        self.minus_di: Optional[float] = None
        self._tr_seed: list[float] = []
        self._plus_seed: list[float] = []
        self._minus_seed: list[float] = []
        self._dx_seed: list[float] = []
        self.count = 0

    def update(self, high: float, low: float, close: float) -> None:
        self.count += 1
        if self.prev_close is None:
            self.prev_high, self.prev_low, self.prev_close = high, low, close
            return
        tr = max(high - low, abs(high - self.prev_close), abs(low - self.prev_close))
        up = high - self.prev_high
        down = self.prev_low - low
        plus_dm = up if (up > down and up > 0) else 0.0
        minus_dm = down if (down > up and down > 0) else 0.0
        self.prev_high, self.prev_low, self.prev_close = high, low, close

        n = self.atr_period
        if self.atr is None:
            self._tr_seed.append(tr)
            self._plus_seed.append(plus_dm)
            self._minus_seed.append(minus_dm)
            if len(self._tr_seed) == n:
                self.atr = sum(self._tr_seed) / n
                self.sm_plus = sum(self._plus_seed)
                self.sm_minus = sum(self._minus_seed)
            else:
                return
        else:
            self.atr = (self.atr * (n - 1) + tr) / n
            self.sm_plus = self.sm_plus - self.sm_plus / n + plus_dm  # type: ignore[operator]
            self.sm_minus = self.sm_minus - self.sm_minus / n + minus_dm  # type: ignore[operator]

        atr_sum = self.atr * n
        if atr_sum <= 0:
            return
        self.plus_di = 100.0 * self.sm_plus / atr_sum  # type: ignore[operator]
        self.minus_di = 100.0 * self.sm_minus / atr_sum  # type: ignore[operator]
        di_sum = self.plus_di + self.minus_di
        dx = 0.0 if di_sum <= 0 else 100.0 * abs(self.plus_di - self.minus_di) / di_sum
        m = self.adx_period
        if self.adx is None:
            self._dx_seed.append(dx)
            if len(self._dx_seed) == m:
                self.adx = sum(self._dx_seed) / m
        else:
            self.adx = (self.adx * (m - 1) + dx) / m


class RollingPercentile:
    """Percentile rank (0-100) of the newest value within a rolling window."""

    def __init__(self, window: int) -> None:
        self.window = window
        self._values: Deque[float] = deque()
        self._sorted: list[float] = []

    def update(self, x: float) -> Optional[float]:
        self._values.append(x)
        insort(self._sorted, x)
        if len(self._values) > self.window:
            old = self._values.popleft()
            idx = bisect_left(self._sorted, old)
            del self._sorted[idx]
        if len(self._values) < self.window:
            return None
        rank = bisect_left(self._sorted, x)
        return 100.0 * rank / (len(self._sorted) - 1) if len(self._sorted) > 1 else 50.0


@dataclass
class BarSnapshot:
    close_ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    ema_fast: Optional[float] = None
    ema_slow: Optional[float] = None
    atr: Optional[float] = None
    adx: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None
    atr_pct_rank: Optional[float] = None
    volume_ratio: Optional[float] = None
    prev_close: Optional[float] = None
    prev_ema_fast: Optional[float] = None
    warmed: bool = False
    regime: str = "warming"
    long_trigger: bool = False
    short_trigger: bool = False
    skip_reason: str = ""


@dataclass
class FeatureEngine:
    """Per-symbol incremental feature state. Feed closed bars in order."""

    params: StrategyParams
    ema_fast: Ema = field(init=False)
    ema_slow: Ema = field(init=False)
    dmi: WilderAtrAdx = field(init=False)
    atr_rank: RollingPercentile = field(init=False)
    volumes: Deque[float] = field(default_factory=deque)
    bars_seen: int = 0
    last: Optional[BarSnapshot] = None

    def __post_init__(self) -> None:
        p = self.params
        self.ema_fast = Ema(p.ema_fast)
        self.ema_slow = Ema(p.ema_slow)
        self.dmi = WilderAtrAdx(p.atr_period, p.adx_period)
        self.atr_rank = RollingPercentile(p.atr_pct_lookback_bars)

    def update(self, close_ts: int, o: float, h: float, l: float, c: float, v: float) -> BarSnapshot:
        p = self.params
        prev = self.last
        snap = BarSnapshot(close_ts=close_ts, open=o, high=h, low=l, close=c, volume=v)
        snap.prev_close = prev.close if prev else None
        snap.prev_ema_fast = prev.ema_fast if prev else None

        snap.ema_fast = self.ema_fast.update(c)
        snap.ema_slow = self.ema_slow.update(c)
        self.dmi.update(h, l, c)
        snap.atr = self.dmi.atr
        snap.adx = self.dmi.adx
        snap.plus_di = self.dmi.plus_di
        snap.minus_di = self.dmi.minus_di
        if snap.atr is not None and c > 0:
            snap.atr_pct_rank = self.atr_rank.update(snap.atr / c)

        if len(self.volumes) >= p.volume_avg_bars:
            avg = sum(self.volumes) / len(self.volumes)
            snap.volume_ratio = (v / avg) if avg > 0 else None
        self.volumes.append(v)
        if len(self.volumes) > p.volume_avg_bars:
            self.volumes.popleft()

        self.bars_seen += 1
        snap.warmed = (
            self.bars_seen >= p.warmup_bars()
            and snap.adx is not None
            and snap.atr_pct_rank is not None
            and snap.volume_ratio is not None
            and snap.prev_close is not None
            and snap.prev_ema_fast is not None
        )
        if snap.warmed:
            self._classify(snap)
        self.last = snap
        return snap

    def _classify(self, s: BarSnapshot) -> None:
        p = self.params
        assert s.adx is not None and s.atr_pct_rank is not None
        if s.adx < p.adx_min:
            s.regime = "range"
        elif s.atr_pct_rank < p.atr_pct_min:
            s.regime = "trend_lowvol"
        elif s.atr_pct_rank > p.atr_pct_max:
            s.regime = "trend_blowoff"
        else:
            s.regime = "trend_tradable"
        if s.regime != "trend_tradable":
            s.skip_reason = RC_SKIP_REGIME
            return
        assert s.ema_fast is not None and s.ema_slow is not None
        assert s.plus_di is not None and s.minus_di is not None
        up_trend = s.ema_fast > s.ema_slow and s.plus_di > s.minus_di
        down_trend = s.ema_fast < s.ema_slow and s.minus_di > s.plus_di
        pullback_resume_long = (
            s.prev_close is not None
            and s.prev_ema_fast is not None
            and s.prev_close <= s.prev_ema_fast
            and s.close > s.ema_fast
        )
        pullback_resume_short = (
            s.prev_close is not None
            and s.prev_ema_fast is not None
            and s.prev_close >= s.prev_ema_fast
            and s.close < s.ema_fast
        )
        volume_ok = s.volume_ratio is not None and s.volume_ratio >= p.volume_multiple
        if up_trend and pullback_resume_long:
            if volume_ok:
                s.long_trigger = True
            else:
                s.skip_reason = RC_SKIP_VOLUME
        elif down_trend and pullback_resume_short:
            if volume_ok:
                s.short_trigger = True
            else:
                s.skip_reason = RC_SKIP_VOLUME


def minute_of_day_utc(ts_seconds: int) -> int:
    return int((ts_seconds % 86400) // 60)


def in_funding_window(ts_seconds: int, window_minutes: int) -> bool:
    mod = minute_of_day_utc(ts_seconds)
    for settle in FUNDING_SETTLEMENT_MINUTES:
        diff = abs(mod - settle)
        diff = min(diff, 1440 - diff)
        if diff <= window_minutes:
            return True
    return False


def is_funding_settlement(ts_seconds: int) -> bool:
    return ts_seconds % 86400 in (0, 8 * 3600, 16 * 3600)


def funding_blocks_entry(side: str, funding_rate: Optional[float], max_rate_pct: float) -> bool:
    """Skip when funding is charged *against* the intended side above the cap.

    Longs pay when funding is positive, shorts pay when it is negative.
    A missing funding value is treated as blocking (fail closed).
    """
    if funding_rate is None:
        return True
    cap = max_rate_pct / 100.0
    if side == "long":
        return funding_rate > cap
    return funding_rate < -cap


def quantize_down(value: float, step: float) -> float:
    if step <= 0:
        return value
    return int(value / step + 1e-9) * step


def quantize_nearest(value: float, step: float) -> float:
    if step <= 0:
        return value
    return round(value / step) * step


def size_position(
    *,
    risk_usdt: float,
    stop_distance: float,
    price: float,
    leverage: int,
    margin_cap_usdt: float,
    size_step: float,
    min_qty: float,
) -> dict:
    """Fixed-USDT-risk sizing with a leverage/margin cap.

    qty = risk / stop_distance, floored to the exchange size step. If the
    required isolated margin (notional / leverage) exceeds the per-position
    margin cap, qty is reduced so the leverage hard cap is never exceeded.
    """
    out = {
        "qty": 0.0,
        "notional_usdt": 0.0,
        "margin_usdt": 0.0,
        "risk_usdt": 0.0,
        "size_reduced": False,
        "sizing_ok": False,
        "min_open_notional_usdt": min_qty * price,
    }
    if stop_distance <= 0 or price <= 0:
        return out
    qty = quantize_down(risk_usdt / stop_distance, size_step)
    margin = qty * price / leverage
    if margin > margin_cap_usdt:
        qty = quantize_down(margin_cap_usdt * leverage / price, size_step)
        out["size_reduced"] = True
    if qty < min_qty or qty <= 0:
        return out
    out["qty"] = qty
    out["notional_usdt"] = qty * price
    out["margin_usdt"] = qty * price / leverage
    out["risk_usdt"] = qty * stop_distance
    out["sizing_ok"] = True
    return out


def utc_day(ts_seconds: int) -> int:
    return int(ts_seconds // 86400)
