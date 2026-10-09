"""EMA, Wilder ATR, and Wilder ADX used by v1.

Definitions (locked for v1, not optimized):

- EMA seed is the simple average of the first `period` closes. After that,
  alpha = 2 / (period + 1).
- True range and directional movement follow Wilder. The first smoothed value
  is the simple average of the first `period` observations. Later values use
  Wilder smoothing: ((prior * (period - 1)) + current) / period.
- The first ADX is the simple average of the first `period` DX values, then
  the same Wilder smoothing.
- ATR percentile is the percent of the last `lookback` ATR/close ratios that
  are less than or equal to the current ratio. It is undefined until that
  window is full.
- Volume ratio uses the current bar divided by the mean of the previous
  `volume_avg_bars` bars, excluding the current bar.
"""

from collections import deque
from typing import Sequence


def _wilder_series(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    for index in range(period, len(values)):
        prior = out[index - 1]
        if prior is None:
            return out
        out[index] = ((prior * (period - 1)) + values[index]) / period
    return out


def ema_series(closes: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(closes)
    if period <= 0 or len(closes) < period:
        return out
    seed = sum(closes[:period]) / period
    out[period - 1] = seed
    alpha = 2.0 / (period + 1)
    for index in range(period, len(closes)):
        prior = out[index - 1]
        if prior is None:
            return out
        out[index] = alpha * closes[index] + (1.0 - alpha) * prior
    return out


def _true_ranges(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]
) -> list[float]:
    ranges: list[float] = []
    for index in range(1, len(closes)):
        high = highs[index]
        low = lows[index]
        prev_close = closes[index - 1]
        ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    return ranges


def _directional_moves(
    highs: Sequence[float], lows: Sequence[float]
) -> tuple[list[float], list[float]]:
    plus: list[float] = []
    minus: list[float] = []
    for index in range(1, len(highs)):
        up = highs[index] - highs[index - 1]
        down = lows[index - 1] - lows[index]
        plus.append(up if up > down and up > 0 else 0.0)
        minus.append(down if down > up and down > 0 else 0.0)
    return plus, minus


def atr_series(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int
) -> list[float | None]:
    """ATR aligned to the original bar index. Index 0 is always None."""
    aligned: list[float | None] = [None] * len(closes)
    if len(closes) < 2:
        return aligned
    smoothed = _wilder_series(_true_ranges(highs, lows, closes), period)
    for offset, value in enumerate(smoothed):
        aligned[offset + 1] = value
    return aligned


def adx_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    """Return ADX, +DI, -DI aligned to the original bar index."""
    size = len(closes)
    adx: list[float | None] = [None] * size
    plus_di: list[float | None] = [None] * size
    minus_di: list[float | None] = [None] * size
    if size < 2 or period <= 0:
        return adx, plus_di, minus_di
    tr_s = _wilder_series(_true_ranges(highs, lows, closes), period)
    plus_raw, minus_raw = _directional_moves(highs, lows)
    plus_s = _wilder_series(plus_raw, period)
    minus_s = _wilder_series(minus_raw, period)
    dx_values: list[float] = []
    dx_index: list[int] = []
    for offset, tr_value in enumerate(tr_s):
        plus_value = plus_s[offset]
        minus_value = minus_s[offset]
        bar_index = offset + 1
        if tr_value is None or plus_value is None or minus_value is None or tr_value == 0:
            continue
        pdi = 100.0 * plus_value / tr_value
        mdi = 100.0 * minus_value / tr_value
        plus_di[bar_index] = pdi
        minus_di[bar_index] = mdi
        denom = pdi + mdi
        if denom == 0:
            continue
        dx_values.append(100.0 * abs(pdi - mdi) / denom)
        dx_index.append(bar_index)
    smoothed_dx = _wilder_series(dx_values, period)
    for offset, value in enumerate(smoothed_dx):
        if value is not None:
            adx[dx_index[offset]] = value
    return adx, plus_di, minus_di


def percentile_rank(window: Sequence[float], value: float) -> float:
    if not window:
        raise ValueError("percentile window is empty")
    less_or_equal = sum(1 for item in window if item <= value)
    return 100.0 * less_or_equal / len(window)


class _Wilder:
    def __init__(self, period: int) -> None:
        self.period = period
        self._seed: list[float] = []
        self.value: float | None = None

    def update(self, value: float) -> float | None:
        if self.value is None:
            self._seed.append(value)
            if len(self._seed) == self.period:
                self.value = sum(self._seed) / self.period
            return self.value
        self.value = ((self.value * (self.period - 1)) + value) / self.period
        return self.value


class _Ema:
    def __init__(self, period: int) -> None:
        self.period = period
        self._seed: list[float] = []
        self.value: float | None = None
        self.alpha = 2.0 / (period + 1)

    def update(self, close: float) -> float | None:
        if self.value is None:
            self._seed.append(close)
            if len(self._seed) == self.period:
                self.value = sum(self._seed) / self.period
            return self.value
        self.value = self.alpha * close + (1.0 - self.alpha) * self.value
        return self.value


class IndicatorBook:
    """One-pass book. The last `update` matches the batch series at that bar."""

    def __init__(
        self,
        ema_fast: int,
        ema_slow: int,
        adx_period: int,
        atr_period: int,
        atr_pct_lookback: int,
        volume_avg_bars: int,
    ) -> None:
        self.ema_fast_period = ema_fast
        self.ema_slow_period = ema_slow
        self.adx_period = adx_period
        self.atr_period = atr_period
        self.atr_pct_lookback = atr_pct_lookback
        self.volume_avg_bars = volume_avg_bars
        self._fast = _Ema(ema_fast)
        self._slow = _Ema(ema_slow)
        self._atr = _Wilder(atr_period)
        self._plus = _Wilder(adx_period)
        self._minus = _Wilder(adx_period)
        self._tr = _Wilder(adx_period)
        self._dx = _Wilder(adx_period)
        self._prev_high: float | None = None
        self._prev_low: float | None = None
        self._prev_close: float | None = None
        self._prev_fast: float | None = None
        self._prev_slow: float | None = None
        self._volumes: deque[float] = deque(maxlen=volume_avg_bars + 1)
        self._ratios: deque[float] = deque(maxlen=atr_pct_lookback)
        self.count = 0

    def update(
        self, high: float, low: float, close: float, volume: float
    ) -> dict[str, float | None]:
        prev_fast = self._fast.value
        prev_slow = self._slow.value
        fast = self._fast.update(close)
        slow = self._slow.update(close)
        atr: float | None = None
        adx: float | None = None
        plus_di: float | None = None
        minus_di: float | None = None
        if self._prev_close is not None and self._prev_high is not None and self._prev_low is not None:
            tr_value = max(
                high - low,
                abs(high - self._prev_close),
                abs(low - self._prev_close),
            )
            up = high - self._prev_high
            down = self._prev_low - low
            plus_dm = up if up > down and up > 0 else 0.0
            minus_dm = down if down > up and down > 0 else 0.0
            atr = self._atr.update(tr_value)
            tr_s = self._tr.update(tr_value)
            plus_s = self._plus.update(plus_dm)
            minus_s = self._minus.update(minus_dm)
            if (
                tr_s is not None
                and plus_s is not None
                and minus_s is not None
                and tr_s != 0
            ):
                plus_di = 100.0 * plus_s / tr_s
                minus_di = 100.0 * minus_s / tr_s
                denom = plus_di + minus_di
                if denom != 0:
                    dx = 100.0 * abs(plus_di - minus_di) / denom
                    adx = self._dx.update(dx)
        atr_pct = None
        if atr is not None and close != 0:
            ratio = atr / close
            self._ratios.append(ratio)
            if len(self._ratios) == self.atr_pct_lookback:
                atr_pct = percentile_rank(self._ratios, ratio)
        self._volumes.append(volume)
        volume_avg = None
        if len(self._volumes) == self.volume_avg_bars + 1:
            prior = list(self._volumes)[:-1]
            volume_avg = sum(prior) / len(prior)
        self._prev_high = high
        self._prev_low = low
        self._prev_close = close
        self._prev_fast = prev_fast
        self._prev_slow = prev_slow
        self.count += 1
        return {
            "fast_ema": fast,
            "slow_ema": slow,
            "prev_fast_ema": prev_fast,
            "prev_slow_ema": prev_slow,
            "atr": atr,
            "atr_pct": atr_pct,
            "adx": adx,
            "plus_di": plus_di,
            "minus_di": minus_di,
            "volume": volume,
            "volume_avg_prev": volume_avg,
            "close": close,
        }


def batch_last(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    volumes: Sequence[float],
    *,
    ema_fast: int,
    ema_slow: int,
    adx_period: int,
    atr_period: int,
    atr_pct_lookback: int,
    volume_avg_bars: int,
) -> dict[str, float | None]:
    """Oracle: full-series definitions at the final bar."""
    index = len(closes) - 1
    fast = ema_series(closes, ema_fast)
    slow = ema_series(closes, ema_slow)
    atr = atr_series(highs, lows, closes, atr_period)
    adx, plus_di, minus_di = adx_series(highs, lows, closes, adx_period)
    ratios: list[float] = []
    for atr_value, close in zip(atr, closes):
        if atr_value is not None and close != 0:
            ratios.append(atr_value / close)
    atr_pct = None
    if len(ratios) >= atr_pct_lookback and atr[index] is not None and closes[index] != 0:
        window = ratios[-atr_pct_lookback:]
        atr_pct = percentile_rank(window, ratios[-1])
    volume_avg = None
    if index >= volume_avg_bars:
        window = volumes[index - volume_avg_bars : index]
        volume_avg = sum(window) / len(window)
    prev = index - 1
    return {
        "fast_ema": fast[index],
        "slow_ema": slow[index],
        "prev_fast_ema": fast[prev] if prev >= 0 else None,
        "prev_slow_ema": slow[prev] if prev >= 0 else None,
        "atr": atr[index],
        "atr_pct": atr_pct,
        "adx": adx[index],
        "plus_di": plus_di[index],
        "minus_di": minus_di[index],
        "volume": volumes[index],
        "volume_avg_prev": volume_avg,
        "close": closes[index],
    }
