"""Shared indicator and data-assembly code used by both replay and live paths.

Everything here is deterministic pandas/numpy. The same ``compute_indicators``
function feeds the Nautilus replay strategy (via injected feature frames) and
the live decision path, so the two cannot drift apart.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

from getagent import backtest, data

HOUR_MS = 3_600_000
INTERVAL = "1h"
KLINE_CHUNK_DAYS = 90  # hard per-request cap of the managed kline endpoint
KLINE_LIMIT = 1000

FEATURE_COLUMNS = (
    "ema_fast",
    "ema_slow",
    "atr",
    "adx",
    "plus_di",
    "minus_di",
    "atr_pct_rank",
    "funding_rate",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Indicators
# --------------------------------------------------------------------------- #
def _wilder(series: pd.Series, period: int) -> pd.Series:
    # Wilder smoothing == EMA with alpha = 1/period, seeded by the simple mean.
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def compute_indicators(frame: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """Append indicator columns to an OHLCV frame indexed by UTC bar open time.

    Required input columns: open, high, low, close. Output adds
    ema_fast, ema_slow, atr, adx, plus_di, minus_di, atr_pct, atr_pct_rank.
    Rows inside the warm-up window carry NaN and must be treated as
    "signal invalid -> no trade" by callers.
    """
    df = frame.copy()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)

    ema_fast_n = int(params["ema_fast_period"])
    ema_slow_n = int(params["ema_slow_period"])
    atr_n = int(params["atr_period"])
    adx_n = int(params["adx_period"])
    rank_n = int(params["atr_rank_window"])

    df["ema_fast"] = close.ewm(span=ema_fast_n, adjust=False, min_periods=ema_fast_n).mean()
    df["ema_slow"] = close.ewm(span=ema_slow_n, adjust=False, min_periods=ema_slow_n).mean()

    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = _wilder(tr, atr_n)
    df["atr"] = atr

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index)
    atr_adx = _wilder(tr, adx_n)
    plus_di = 100.0 * _wilder(plus_dm, adx_n) / atr_adx
    minus_di = 100.0 * _wilder(minus_dm, adx_n) / atr_adx
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    df["plus_di"] = plus_di
    df["minus_di"] = minus_di
    df["adx"] = _wilder(dx.fillna(0.0), adx_n)

    atr_pct = atr / close
    df["atr_pct"] = atr_pct
    # Percentile rank of the current ATR% inside the trailing window (0..1).
    df["atr_pct_rank"] = (
        atr_pct.rolling(rank_n, min_periods=max(adx_n * 4, 48))
        .apply(lambda window: float((window[:-1] <= window[-1]).mean()), raw=True)
    )
    return df


# --------------------------------------------------------------------------- #
# Data assembly
# --------------------------------------------------------------------------- #
def _frame_from_obb(obj: Any) -> pd.DataFrame:
    if obj is None:
        return pd.DataFrame()
    try:
        df = data.to_dataframe(obj)
    except Exception:  # noqa: BLE001 - empty / malformed response
        return pd.DataFrame()
    if df is None or len(df) == 0:
        return pd.DataFrame()
    return df


def _normalize_bars(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    prepared = backtest.prepare_frame(df)
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in prepared.columns]
    prepared = prepared[keep].astype(float)
    prepared = prepared[~prepared.index.duplicated(keep="last")].sort_index()
    return prepared


def fetch_klines_window(
    symbol: str,
    *,
    exchange: str,
    start: datetime,
    end: datetime,
    deadline: datetime | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch closed 1h bars for [start, end) in 90-day chunks, newest first.

    Stops early when ``deadline`` passes so a slow data path degrades to a
    shorter, honestly reported window instead of a sandbox timeout. Returns the
    frame plus a coverage report.
    """
    chunks: list[pd.DataFrame] = []
    requests = 0
    cursor_end = end
    truncated_by_deadline = False
    while cursor_end > start:
        if deadline is not None and utc_now() >= deadline:
            truncated_by_deadline = True
            break
        cursor_start = max(start, cursor_end - timedelta(days=KLINE_CHUNK_DAYS))
        bars = data.crypto.futures.kline(
            symbol=symbol,
            interval=INTERVAL,
            exchange=exchange,
            limit=KLINE_LIMIT,
            start_time=int(cursor_start.timestamp() * 1000),
            end_time=int(cursor_end.timestamp() * 1000),
            closed_only=True,
        )
        requests += 1
        df = _normalize_bars(_frame_from_obb(bars))
        if df.empty:
            break
        chunks.append(df)
        earliest = df.index.min().to_pydatetime()
        if earliest >= cursor_end:
            break
        cursor_end = earliest  # next page ends where this one began
    if chunks:
        frame = pd.concat(chunks).sort_index()
        frame = frame[~frame.index.duplicated(keep="last")]
        frame = frame[(frame.index >= pd.Timestamp(start)) & (frame.index < pd.Timestamp(end))]
    else:
        frame = pd.DataFrame()
    report = {
        "symbol": symbol,
        "requests": requests,
        "rows": int(len(frame)),
        "first_bar": frame.index.min().isoformat() if len(frame) else None,
        "last_bar": frame.index.max().isoformat() if len(frame) else None,
        "truncated_by_deadline": truncated_by_deadline,
    }
    return frame, report


def fetch_funding_window(
    symbol: str,
    *,
    exchange: str,
    start: datetime,
    end: datetime,
    deadline: datetime | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch historical funding rates for [start, end) in 90-day chunks.

    Returns a frame indexed by UTC time with a single ``funding_rate`` column,
    or an empty frame when the endpoint has no coverage (reported, not hidden).
    """
    chunks: list[pd.DataFrame] = []
    requests = 0
    cursor_end = end
    truncated_by_deadline = False
    while cursor_end > start:
        if deadline is not None and utc_now() >= deadline:
            truncated_by_deadline = True
            break
        cursor_start = max(start, cursor_end - timedelta(days=KLINE_CHUNK_DAYS))
        try:
            raw = data.crypto.futures.funding_rate(
                symbol=symbol,
                exchange=exchange,
                interval="4h",
                limit=1000,
                start_time=int(cursor_start.timestamp() * 1000),
                end_time=int(cursor_end.timestamp() * 1000),
            )
        except Exception:  # noqa: BLE001 - endpoint failure is reported below
            raw = None
        requests += 1
        df = _frame_from_obb(raw)
        if df.empty or "funding_rate" not in df.columns:
            break
        time_col = "timestamp" if "timestamp" in df.columns else "date"
        prepared = backtest.prepare_frame(df, datetime_index=time_col)
        prepared = prepared[["funding_rate"]].astype(float)
        prepared = prepared[~prepared.index.duplicated(keep="last")].sort_index()
        chunks.append(prepared)
        earliest = prepared.index.min().to_pydatetime()
        if earliest >= cursor_end:
            break
        cursor_end = earliest
    if chunks:
        frame = pd.concat(chunks).sort_index()
        frame = frame[~frame.index.duplicated(keep="last")]
        frame = frame[(frame.index >= pd.Timestamp(start)) & (frame.index < pd.Timestamp(end))]
    else:
        frame = pd.DataFrame(columns=["funding_rate"])
    report = {
        "symbol": symbol,
        "requests": requests,
        "rows": int(len(frame)),
        "first": frame.index.min().isoformat() if len(frame) else None,
        "last": frame.index.max().isoformat() if len(frame) else None,
        "truncated_by_deadline": truncated_by_deadline,
    }
    return frame, report


def build_replay_frame(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    params: dict[str, Any],
) -> pd.DataFrame:
    """OHLCV + indicators + as-of aligned funding_rate, ready for backtest.run."""
    enriched = compute_indicators(bars, params)
    if funding is not None and len(funding):
        enriched = backtest.build_feature_frame(
            enriched,
            features=[
                backtest.FeatureSource(
                    data=funding,
                    include_columns=("funding_rate",),
                    mode="asof",
                    direction="backward",
                )
            ],
        )
    else:
        # Funding coverage missing: keep the column so the engine contract holds,
        # but the run reports funding_degraded=True and the funding gate is off.
        enriched["funding_rate"] = np.nan
    return enriched


def latest_closed_bar_is_fresh(index: pd.DatetimeIndex, now: datetime, interval_ms: int = HOUR_MS) -> bool:
    """SDK freshness rule: refuse when now - (last_open + interval) > 2 x interval."""
    if len(index) == 0:
        return False
    last_open_ms = int(index.max().timestamp() * 1000)
    now_ms = int(now.timestamp() * 1000)
    return (now_ms - (last_open_ms + interval_ms)) <= 2 * interval_ms
