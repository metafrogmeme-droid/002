"""Indicator, regime, and signal definitions shared by live, backtest, and research code.

Pure pandas/numpy. Every value at bar ``t`` uses only bars ``<= t`` (closed bars),
so the same function is safe for replay and for live decisions.
"""
from typing import Any, Mapping

import numpy as np
import pandas as pd

REGIME_TREND = "TREND"
REGIME_RANGE = "RANGE"
REGIME_SIT_OUT = "SIT_OUT"

BASE_TREND = "ema_adx_trend"
BASE_MEAN_REVERSION = "mean_reversion"
VALID_BASES = (BASE_TREND, BASE_MEAN_REVERSION)

VALID_SIGNAL_ACTIONS = ("long", "short")

FUNDING_HOURS_UTC = (0, 8, 16)

DEFAULTS: dict[str, Any] = {
    "base_strategy": BASE_TREND,
    "ema_fast": 20,
    "ema_slow": 50,
    "adx_period": 14,
    "atr_period": 14,
    "adx_trend_min": 25.0,
    "adx_range_max": 20.0,
    "atr_rank_window": 720,
    "atr_rank_min": 20.0,
    "atr_rank_max": 90.0,
    "volume_avg_period": 20,
    "volume_mult": 1.5,
    "breakout_lookback": 20,
    "rsi_period": 14,
    "rsi_oversold": 30.0,
    "rsi_overbought": 70.0,
    "bb_period": 20,
    "bb_std": 2.0,
}


def cfg_value(cfg: Mapping[str, Any], key: str) -> Any:
    value = cfg.get(key)
    return DEFAULTS[key] if value is None else value


def _wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def compute_indicators(bars: pd.DataFrame, cfg: Mapping[str, Any]) -> pd.DataFrame:
    """Return a copy of ``bars`` (open/high/low/close/volume, time-indexed) plus indicators."""
    df = bars[["open", "high", "low", "close", "volume"]].astype(float).copy()
    high, low, close, volume = df["high"], df["low"], df["close"], df["volume"]

    df["ema_fast"] = close.ewm(span=int(cfg_value(cfg, "ema_fast")), adjust=False).mean()
    df["ema_slow"] = close.ewm(span=int(cfg_value(cfg, "ema_slow")), adjust=False).mean()

    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = _wilder(tr, int(cfg_value(cfg, "atr_period")))
    df["atr"] = atr
    df["atr_pct"] = atr / close
    window = int(cfg_value(cfg, "atr_rank_window"))
    df["atr_rank"] = df["atr_pct"].rolling(window, min_periods=window).rank(pct=True) * 100.0

    adx_n = int(cfg_value(cfg, "adx_period"))
    up = high.diff()
    down = -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    atr_adx = _wilder(tr, adx_n)
    plus_di = 100.0 * _wilder(plus_dm, adx_n) / atr_adx
    minus_di = 100.0 * _wilder(minus_dm, adx_n) / atr_adx
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    df["plus_di"] = plus_di
    df["minus_di"] = minus_di
    df["adx"] = _wilder(dx, adx_n)

    vol_n = int(cfg_value(cfg, "volume_avg_period"))
    df["vol_avg"] = volume.shift(1).rolling(vol_n, min_periods=vol_n).mean()
    df["vol_ratio"] = volume / df["vol_avg"]

    look = int(cfg_value(cfg, "breakout_lookback"))
    df["donchian_high"] = high.shift(1).rolling(look, min_periods=look).max()
    df["donchian_low"] = low.shift(1).rolling(look, min_periods=look).min()

    rsi_n = int(cfg_value(cfg, "rsi_period"))
    delta = close.diff()
    gain = _wilder(delta.clip(lower=0.0), rsi_n)
    loss = _wilder((-delta).clip(lower=0.0), rsi_n)
    rs = gain / loss.replace(0.0, np.nan)
    df["rsi"] = 100.0 - 100.0 / (1.0 + rs)

    bb_n = int(cfg_value(cfg, "bb_period"))
    bb_k = float(cfg_value(cfg, "bb_std"))
    mid = close.rolling(bb_n, min_periods=bb_n).mean()
    sd = close.rolling(bb_n, min_periods=bb_n).std(ddof=0)
    df["bb_mid"] = mid
    df["bb_lower"] = mid - bb_k * sd
    df["bb_upper"] = mid + bb_k * sd
    return df


def classify_regime(df: pd.DataFrame, cfg: Mapping[str, Any]) -> pd.Series:
    """TREND: ADX >= adx_trend_min and ATR%-rank inside [min, max].
    RANGE: ADX < adx_range_max and ATR%-rank <= max.
    Everything else (transitional ADX, extreme or dead volatility, warm-up) is SIT_OUT."""
    adx = df["adx"]
    rank = df["atr_rank"]
    rank_ok_trend = (rank >= float(cfg_value(cfg, "atr_rank_min"))) & (rank <= float(cfg_value(cfg, "atr_rank_max")))
    rank_ok_range = rank <= float(cfg_value(cfg, "atr_rank_max"))
    trend = (adx >= float(cfg_value(cfg, "adx_trend_min"))) & rank_ok_trend
    rng = (adx < float(cfg_value(cfg, "adx_range_max"))) & rank_ok_range
    regime = pd.Series(REGIME_SIT_OUT, index=df.index, dtype=object)
    regime[rng.fillna(False)] = REGIME_RANGE
    regime[trend.fillna(False)] = REGIME_TREND
    return regime


def compute_signals(df: pd.DataFrame, cfg: Mapping[str, Any]) -> pd.DataFrame:
    """Add ``regime``, ``signal_long`` and ``signal_short`` for the configured base strategy."""
    out = df.copy()
    out["regime"] = classify_regime(out, cfg)
    vol_ok = out["vol_ratio"] >= float(cfg_value(cfg, "volume_mult"))
    base = str(cfg_value(cfg, "base_strategy"))
    if base == BASE_TREND:
        in_regime = out["regime"] == REGIME_TREND
        long_sig = (
            in_regime
            & (out["ema_fast"] > out["ema_slow"])
            & (out["plus_di"] > out["minus_di"])
            & (out["close"] > out["donchian_high"])
            & vol_ok
        )
        short_sig = (
            in_regime
            & (out["ema_fast"] < out["ema_slow"])
            & (out["minus_di"] > out["plus_di"])
            & (out["close"] < out["donchian_low"])
            & vol_ok
        )
    elif base == BASE_MEAN_REVERSION:
        in_regime = out["regime"] == REGIME_RANGE
        long_sig = (
            in_regime
            & (out["close"] < out["bb_lower"])
            & (out["rsi"] < float(cfg_value(cfg, "rsi_oversold")))
            & vol_ok
        )
        short_sig = (
            in_regime
            & (out["close"] > out["bb_upper"])
            & (out["rsi"] > float(cfg_value(cfg, "rsi_overbought")))
            & vol_ok
        )
    else:
        raise ValueError(f"unknown base_strategy={base!r}")
    out["signal_long"] = long_sig.fillna(False).astype(bool)
    out["signal_short"] = short_sig.fillna(False).astype(bool)
    return out


REGIME_CODES = {REGIME_SIT_OUT: 0.0, REGIME_TREND: 1.0, REGIME_RANGE: 2.0}


def warmup_bars(cfg: Mapping[str, Any]) -> int:
    """Closed bars needed before the regime filter can classify anything but SIT_OUT."""
    return int(cfg_value(cfg, "atr_rank_window")) + int(cfg_value(cfg, "atr_period")) + 1


def entry_candidate(highs: list[float], lows: list[float], closes: list[float], vols: list[float],
                    cfg: Mapping[str, Any], want_short: bool = False) -> bool:
    """Cheap necessary condition for an entry signal on the last bar (volume, plus breakout for trend).

    Slightly looser than ``compute_signals`` so it never rejects a bar that the full
    computation would accept; the full computation still decides.
    """
    look = int(cfg_value(cfg, "breakout_lookback"))
    vol_n = int(cfg_value(cfg, "volume_avg_period"))
    if len(closes) < max(look, vol_n) + 1:
        return False
    vol_avg = sum(vols[-vol_n - 1:-1]) / vol_n
    if not vols[-1] >= 0.999 * float(cfg_value(cfg, "volume_mult")) * vol_avg:
        return False
    if str(cfg_value(cfg, "base_strategy")) != BASE_TREND:
        return True
    if closes[-1] >= max(highs[-look - 1:-1]):
        return True
    return bool(want_short and closes[-1] <= min(lows[-look - 1:-1]))


def last_signal_row(bars: pd.DataFrame, cfg: Mapping[str, Any]) -> dict[str, float]:
    """``compute_signals`` on a trailing bar window; returns the last (just-closed) bar's values."""
    sig = compute_signals(compute_indicators(bars, cfg), cfg)
    last = sig.iloc[-1]
    return {
        "close": float(last["close"]),
        "atr": float(last["atr"]),
        "adx": float(last["adx"]),
        "regime_code": REGIME_CODES.get(str(last["regime"]), 0.0),
        "signal_long": 1.0 if bool(last["signal_long"]) else 0.0,
        "signal_short": 1.0 if bool(last["signal_short"]) else 0.0,
    }


FUNDING_PERCENT_MEDIAN_MIN = 0.001


def funding_unit_scale(rates: Any) -> tuple[float, str]:
    """Multiplier that converts a series of SDK funding rates to decimals, plus the detected unit.

    ``getagent.data.crypto.futures.funding_rate`` returned percent values for Bitget
    (BTC 0.01 == 0.01% per 8h) in a sandbox run on 2026-10-09, although its docs say
    decimal. Bitget 8h rates sit near 0.0001 as decimals and near 0.01 as percent, so
    a median magnitude above 0.001 is read as percent. Decided per fetched series.
    """
    vals = sorted(abs(float(r)) for r in rates if r is not None and np.isfinite(float(r)))
    if not vals:
        return 1.0, "unknown"
    if vals[len(vals) // 2] > FUNDING_PERCENT_MEDIAN_MIN:
        return 0.01, "percent"
    return 1.0, "decimal"


class FundingLookup:
    """Point-in-time funding rates for one symbol (timestamps in ms, UTC).

    ``rate_8h_at(t)``: latest rate published at or before ``t``, scaled to 8h, or None
    when no rate younger than ``max_age_hours`` exists (unknown).
    ``settle_rate(t)``: rate charged at a 00/08/16 UTC settlement at ``t``, else 0.
    """

    def __init__(self, ts_ms: list[int], rates: list[float], interval_hours: float = 8.0,
                 max_age_hours: float = 24.0) -> None:
        pairs = sorted({int(t): float(r) for t, r in zip(ts_ms, rates) if r is not None and np.isfinite(r)}.items())
        self.ts = [p[0] for p in pairs]
        self.rates = [p[1] for p in pairs]
        self.interval_ms = int(float(interval_hours) * 3_600_000)
        self.scale = 8.0 / float(interval_hours)
        self.max_age_ms = int(float(max_age_hours) * 3_600_000)

    def __len__(self) -> int:
        return len(self.ts)

    def _at(self, ts_ms: int) -> int:
        lo, hi = 0, len(self.ts)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.ts[mid] <= ts_ms:
                lo = mid + 1
            else:
                hi = mid
        return lo - 1

    def rate_8h_at(self, ts_ms: int) -> float | None:
        k = self._at(ts_ms)
        if k < 0 or ts_ms - self.ts[k] > self.max_age_ms:
            return None
        return self.rates[k] * self.scale

    def settle_rate(self, ts_ms: int) -> float:
        if (ts_ms // 60_000) % 1440 not in tuple(h * 60 for h in FUNDING_HOURS_UTC):
            return 0.0
        k = self._at(ts_ms)
        if k < 0 or ts_ms - self.ts[k] > self.interval_ms:
            return 0.0
        return self.rates[k]

    def known_share(self, start_ms: int, end_ms: int, step_ms: int = 3_600_000) -> float:
        points = range(int(start_ms) + step_ms, int(end_ms) + 1, step_ms)
        if not len(points):
            return 0.0
        return sum(1 for t in points if self.rate_8h_at(t) is not None) / len(points)

    def to_dict(self) -> dict[str, Any]:
        return {"ts": self.ts, "rate": self.rates, "interval_hours": self.interval_ms / 3_600_000}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FundingLookup":
        return cls(list(payload.get("ts") or []), list(payload.get("rate") or []),
                   float(payload.get("interval_hours") or 8.0))


def validate_signal(action: Any, allowed_actions: tuple[str, ...]) -> str | None:
    """Return a normalised action only when it is explicitly valid; otherwise None (NO TRADE).

    There is no default direction: anything missing, malformed, or not in
    ``allowed_actions`` yields None.
    """
    if not isinstance(action, str):
        return None
    norm = action.strip().lower()
    if norm in VALID_SIGNAL_ACTIONS and norm in allowed_actions:
        return norm
    return None


def in_funding_window(ts_ms: int, block_minutes: int) -> bool:
    """True when ``ts_ms`` is within +/- block_minutes of a 00/08/16 UTC funding settlement."""
    minute_of_day = (ts_ms // 60_000) % 1440
    for h in FUNDING_HOURS_UTC:
        center = h * 60
        diff = abs(minute_of_day - center)
        diff = min(diff, 1440 - diff)
        if diff <= block_minutes:
            return True
    return False


def funding_blocks(side: str, funding_rate_8h: float | None, max_against: float) -> bool:
    """True when the current 8h-equivalent funding is more than ``max_against`` against ``side``.

    Longs pay positive funding; shorts pay negative funding. Unknown funding blocks the trade.
    """
    if funding_rate_8h is None or not np.isfinite(funding_rate_8h):
        return True
    if side == "long":
        return funding_rate_8h > max_against
    return funding_rate_8h < -max_against
