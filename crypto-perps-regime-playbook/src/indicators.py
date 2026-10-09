"""Regime indicators for trend and volatility filtering."""

import math
from typing import List, Tuple


def compute_ema(values: List[float], period: int) -> List[float]:
    """Compute Exponential Moving Average across a series of values."""
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    ema_vals = [values[0]]
    for val in values[1:]:
        ema_vals.append(alpha * val + (1.0 - alpha) * ema_vals[-1])
    return ema_vals


def compute_atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14,
) -> List[float]:
    """Compute Average True Range (Wilder's Smoothing)."""
    n = len(closes)
    if n < 2:
        return [0.0] * n

    tr: List[float] = [highs[0] - lows[0]]
    for i in range(1, n):
        tr_val = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        tr.append(tr_val)

    if n < period:
        return tr

    atr = [sum(tr[:period]) / period]
    for i in range(period, n):
        atr_val = (atr[-1] * (period - 1) + tr[i]) / period
        atr.append(atr_val)

    # Pad prefix so atr length matches input length
    padding = [atr[0]] * (period - 1)
    return padding + atr


def compute_adx(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14,
) -> Tuple[List[float], List[float], List[float]]:
    """Compute Average Directional Index (ADX), +DI, and -DI."""
    n = len(closes)
    if n < period + 1:
        zeros = [0.0] * n
        return zeros, zeros, zeros

    tr: List[float] = [highs[0] - lows[0]]
    plus_dm: List[float] = [0.0]
    minus_dm: List[float] = [0.0]

    for i in range(1, n):
        h_diff = highs[i] - highs[i - 1]
        l_diff = lows[i - 1] - lows[i]

        p_dm = h_diff if (h_diff > l_diff and h_diff > 0.0) else 0.0
        m_dm = l_diff if (l_diff > h_diff and l_diff > 0.0) else 0.0

        plus_dm.append(p_dm)
        minus_dm.append(m_dm)

        tr_val = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        tr.append(tr_val)

    # Wilder smooth TR, +DM, -DM
    smooth_tr = [sum(tr[:period])]
    smooth_pdm = [sum(plus_dm[:period])]
    smooth_mdm = [sum(minus_dm[:period])]

    for i in range(period, n):
        smooth_tr.append(smooth_tr[-1] - (smooth_tr[-1] / period) + tr[i])
        smooth_pdm.append(smooth_pdm[-1] - (smooth_pdm[-1] / period) + plus_dm[i])
        smooth_mdm.append(smooth_mdm[-1] - (smooth_mdm[-1] / period) + minus_dm[i])

    plus_di: List[float] = []
    minus_di: List[float] = []
    dx: List[float] = []

    for s_tr, s_pdm, s_mdm in zip(smooth_tr, smooth_pdm, smooth_mdm):
        p_di = 100.0 * (s_pdm / s_tr) if s_tr > 0.0 else 0.0
        m_di = 100.0 * (s_mdm / s_tr) if s_tr > 0.0 else 0.0
        di_sum = p_di + m_di
        dx_val = 100.0 * abs(p_di - m_di) / di_sum if di_sum > 0.0 else 0.0
        plus_di.append(p_di)
        minus_di.append(m_di)
        dx.append(dx_val)

    if len(dx) < period:
        zeros = [0.0] * n
        return zeros, zeros, zeros

    adx_values = [sum(dx[:period]) / period]
    for i in range(period, len(dx)):
        adx_val = (adx_values[-1] * (period - 1) + dx[i]) / period
        adx_values.append(adx_val)

    # Pad prefix to match length n
    prefix_len = n - len(adx_values)
    padded_adx = [adx_values[0]] * prefix_len + adx_values
    padded_pdi = [plus_di[0]] * (n - len(plus_di)) + plus_di
    padded_mdi = [minus_di[0]] * (n - len(minus_di)) + minus_di

    return padded_adx, padded_pdi, padded_mdi


def compute_atr_percentile(
    atr_series: List[float],
    close_series: List[float],
    lookback: int = 100,
) -> float:
    """Compute current ATR as a percentage of price, compared to its lookback percentile."""
    if not atr_series or not close_series or len(atr_series) < 10:
        return 50.0
    atr_pct_history = [
        (a / c) * 100.0
        for a, c in zip(atr_series[-lookback:], close_series[-lookback:])
        if c > 0
    ]
    if not atr_pct_history:
        return 50.0
    current_atr_pct = atr_pct_history[-1]
    count_below = sum(1 for x in atr_pct_history if x <= current_atr_pct)
    return (count_below / len(atr_pct_history)) * 100.0
