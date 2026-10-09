"""Regime / trigger layer. Invalid or silent output is NO TRADE."""

from dataclasses import dataclass, field
from typing import Any

from . import indicators


@dataclass
class SignalDecision:
    valid: bool
    reason: str
    limit_price: float | None = None
    atr: float | None = None
    adx: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None
    atr_pct: float | None = None
    atr_pct_percentile: float | None = None
    ema_fast: float | None = None
    ema_slow: float | None = None
    stop_distance: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def evaluate_long(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    *,
    adx_period: int,
    atr_period: int,
    ema_fast_period: int,
    ema_slow_period: int,
    adx_min: float,
    atr_pct_lo: float,
    atr_pct_hi: float,
    percentile_lookback: int,
    stop_atr_mult: float,
) -> SignalDecision:
    need = max(adx_period * 2, atr_period * 2, ema_slow_period, percentile_lookback) + 2
    if len(closes) < need or len(highs) != len(closes) or len(lows) != len(closes):
        return SignalDecision(False, "AI_LAYER_INVALID", meta={"detail": "insufficient_bars"})

    ema_fast_series = indicators.ema(closes, ema_fast_period)
    ema_slow_series = indicators.ema(closes, ema_slow_period)
    atr_series = indicators.atr(highs, lows, closes, atr_period)
    adx_series, plus_series, minus_series = indicators.adx_bundle(highs, lows, closes, adx_period)

    close = closes[-1]
    high = highs[-1]
    low = lows[-1]
    ema_fast = ema_fast_series[-1]
    ema_slow = ema_slow_series[-1]
    atr_now = atr_series[-1]
    adx_now = adx_series[-1]
    plus_now = plus_series[-1]
    minus_now = minus_series[-1]

    if None in (atr_now, adx_now, plus_now, minus_now) or atr_now <= 0 or close <= 0:
        return SignalDecision(False, "AI_LAYER_INVALID", meta={"detail": "indicator_nan"})

    atr_pct = 100.0 * atr_now / close
    atr_pct_hist: list[float] = []
    start = max(0, len(closes) - percentile_lookback)
    for index in range(start, len(closes)):
        atr_item = atr_series[index]
        close_item = closes[index]
        if atr_item is None or close_item <= 0:
            continue
        atr_pct_hist.append(100.0 * atr_item / close_item)
    rank = indicators.percentile_rank(atr_pct_hist, atr_pct)
    if rank is None:
        return SignalDecision(False, "AI_LAYER_INVALID", meta={"detail": "percentile_unavailable"})

    tagged = low <= ema_fast <= high
    held = close > ema_fast
    trend_up = close > ema_slow and ema_fast > ema_slow
    directional = plus_now > minus_now
    trending = adx_now >= adx_min
    vol_ok = atr_pct_lo <= rank <= atr_pct_hi

    if not (trend_up and directional and trending and vol_ok):
        return SignalDecision(
            False,
            "NO_SIGNAL",
            atr=atr_now,
            adx=adx_now,
            plus_di=plus_now,
            minus_di=minus_now,
            atr_pct=atr_pct,
            atr_pct_percentile=rank,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            meta={
                "trend_up": trend_up,
                "directional": directional,
                "trending": trending,
                "vol_ok": vol_ok,
            },
        )
    if not (tagged and held):
        return SignalDecision(
            False,
            "NO_SIGNAL",
            atr=atr_now,
            adx=adx_now,
            plus_di=plus_now,
            minus_di=minus_now,
            atr_pct=atr_pct,
            atr_pct_percentile=rank,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            meta={"tagged": tagged, "held": held},
        )

    stop_distance = stop_atr_mult * atr_now
    return SignalDecision(
        True,
        "LIMIT_SETUP",
        limit_price=ema_fast,
        atr=atr_now,
        adx=adx_now,
        plus_di=plus_now,
        minus_di=minus_now,
        atr_pct=atr_pct,
        atr_pct_percentile=rank,
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        stop_distance=stop_distance,
    )
