"""Pure indicator helpers shared by live and replay paths."""
from __future__ import annotations

import math
from typing import Sequence


def ema(values: Sequence[float], period: int) -> list[float]:
    out = [math.nan] * len(values)
    if not values or period <= 0:
        return out
    alpha = 2.0 / (period + 1)
    prev = float(values[0])
    out[0] = prev
    for i, raw in enumerate(values[1:], start=1):
        prev = alpha * float(raw) + (1.0 - alpha) * prev
        out[i] = prev
    return out


def rma(values: Sequence[float], period: int) -> list[float]:
    out = [math.nan] * len(values)
    if len(values) < period or period <= 0:
        return out
    seed = sum(float(v) for v in values[:period]) / period
    out[period - 1] = seed
    for i in range(period, len(values)):
        seed = (seed * (period - 1) + float(values[i])) / period
        out[i] = seed
    return out


def true_range(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> list[float]:
    tr: list[float] = []
    prev_close = float(closes[0]) if closes else 0.0
    for high, low, close in zip(highs, lows, closes):
        tr.append(
            max(
                float(high) - float(low),
                abs(float(high) - prev_close),
                abs(float(low) - prev_close),
            )
        )
        prev_close = float(close)
    return tr


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int) -> list[float]:
    return rma(true_range(highs, lows, closes), period)


def adx(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int) -> list[float]:
    plus_dm = [0.0] * len(closes)
    minus_dm = [0.0] * len(closes)
    for i in range(1, len(closes)):
        up = float(highs[i]) - float(highs[i - 1])
        down = float(lows[i - 1]) - float(lows[i])
        plus_dm[i] = up if up > down and up > 0 else 0.0
        minus_dm[i] = down if down > up and down > 0 else 0.0
    tr_rma = rma(true_range(highs, lows, closes), period)
    plus_rma = rma(plus_dm, period)
    minus_rma = rma(minus_dm, period)
    dx = [math.nan] * len(closes)
    for i, trv in enumerate(tr_rma):
        if math.isnan(trv) or trv == 0:
            continue
        pdi = 100.0 * plus_rma[i] / trv
        mdi = 100.0 * minus_rma[i] / trv
        denom = pdi + mdi
        dx[i] = 0.0 if denom == 0 else 100.0 * abs(pdi - mdi) / denom
    clean = [0.0 if math.isnan(x) else x for x in dx]
    values = rma(clean, period)
    warmup = min(len(values), 2 * period)
    for i in range(warmup):
        values[i] = math.nan
    return values


def sma(values: Sequence[float], period: int) -> list[float]:
    out = [math.nan] * len(values)
    if period <= 0:
        return out
    acc = 0.0
    for i, raw in enumerate(values):
        acc += float(raw)
        if i >= period:
            acc -= float(values[i - period])
        if i >= period - 1:
            out[i] = acc / period
    return out


def rolling_percentile(values: Sequence[float], lookback: int) -> list[float]:
    out = [math.nan] * len(values)
    window: list[float] = []
    min_len = max(50, lookback // 5) if lookback else 50
    for i, raw in enumerate(values):
        value = float(raw)
        if math.isnan(value):
            continue
        window.append(value)
        if lookback and len(window) > lookback:
            window.pop(0)
        if len(window) < min_len:
            continue
        ranked = sorted(window)
        k = sum(1 for item in ranked if item <= value)
        out[i] = 100.0 * k / len(ranked)
    return out


def last_finite(values: Sequence[float]) -> float | None:
    for raw in reversed(values):
        value = float(raw)
        if not math.isnan(value):
            return value
    return None
