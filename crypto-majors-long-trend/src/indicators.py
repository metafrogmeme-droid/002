"""Deterministic Wilder / EMA helpers shared by live and replay paths."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BarWindow:
    high: list[float]
    low: list[float]
    close: list[float]


def ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    out = [values[0]]
    for value in values[1:]:
        out.append(alpha * value + (1.0 - alpha) * out[-1])
    return out


def _true_ranges(high: list[float], low: list[float], close: list[float]) -> list[float]:
    trs: list[float] = []
    for index, (hi, lo) in enumerate(zip(high, low)):
        if index == 0:
            trs.append(hi - lo)
            continue
        prev_close = close[index - 1]
        trs.append(max(hi - lo, abs(hi - prev_close), abs(lo - prev_close)))
    return trs


def _wilder(values: list[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    for index in range(period, len(values)):
        prev = out[index - 1]
        if prev is None:
            continue
        out[index] = (prev * (period - 1) + values[index]) / period
    return out


def atr(high: list[float], low: list[float], close: list[float], period: int) -> list[float | None]:
    return _wilder(_true_ranges(high, low, close), period)


def adx_bundle(
    high: list[float],
    low: list[float],
    close: list[float],
    period: int,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    length = len(close)
    plus_dm = [0.0] * length
    minus_dm = [0.0] * length
    for index in range(1, length):
        up_move = high[index] - high[index - 1]
        down_move = low[index - 1] - low[index]
        if up_move > down_move and up_move > 0:
            plus_dm[index] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[index] = down_move
    tr_s = _wilder(_true_ranges(high, low, close), period)
    plus_s = _wilder(plus_dm, period)
    minus_s = _wilder(minus_dm, period)
    plus_di: list[float | None] = [None] * length
    minus_di: list[float | None] = [None] * length
    dx: list[float | None] = [None] * length
    for index in range(length):
        tr_val = tr_s[index]
        p_val = plus_s[index]
        m_val = minus_s[index]
        if tr_val in (None, 0) or p_val is None or m_val is None:
            continue
        p_di = 100.0 * p_val / tr_val
        m_di = 100.0 * m_val / tr_val
        plus_di[index] = p_di
        minus_di[index] = m_di
        denom = p_di + m_di
        if denom > 0:
            dx[index] = 100.0 * abs(p_di - m_di) / denom
    adx_vals = _wilder([0.0 if item is None else item for item in dx], period)
    for index, item in enumerate(dx):
        if item is None:
            adx_vals[index] = None
    return adx_vals, plus_di, minus_di


def percentile_rank(window: list[float], value: float) -> float | None:
    if not window:
        return None
    below = sum(1 for item in window if item <= value)
    return 100.0 * below / len(window)
