"""Historical kline / funding fetch used by the replay path."""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from getagent import backtest, data

INTERVAL = "1h"
INTERVAL_MS = 60 * 60 * 1000
CHUNK_BARS = 960


def _to_ms(stamp: datetime) -> int:
    return int(stamp.timestamp() * 1000)


def _concat(frames: list[Any]) -> Any:
    if not frames:
        return backtest.prepare_frame([])
    combined = pd.concat(frames)
    return combined[~combined.index.duplicated(keep="last")].sort_index()


def fetch_hourly_klines(symbol: str, start: datetime, end: datetime) -> Any:
    frames = []
    cursor = _to_ms(start)
    end_ms = _to_ms(end)
    chunk_ms = CHUNK_BARS * INTERVAL_MS
    while cursor < end_ms:
        chunk_end = min(cursor + chunk_ms, end_ms)
        bars = data.crypto.futures.kline(
            symbol=symbol,
            interval=INTERVAL,
            exchange="bitget",
            limit=1000,
            start_time=cursor,
            end_time=chunk_end,
            closed_only=True,
        )
        frame = backtest.prepare_frame(bars)
        if frame is not None and not getattr(frame, "empty", True):
            frames.append(frame)
        cursor = chunk_end
    return _concat(frames)


def fetch_funding(symbol: str, start: datetime, end: datetime) -> Any | None:
    frames = []
    cursor = _to_ms(start)
    end_ms = _to_ms(end)
    chunk_ms = 90 * 24 * 60 * 60 * 1000
    while cursor < end_ms:
        chunk_end = min(cursor + chunk_ms, end_ms)
        rows = data.crypto.futures.funding_rate(
            symbol=symbol,
            exchange="bitget",
            interval="4h",
            limit=1000,
            start_time=cursor,
            end_time=chunk_end,
        )
        frame = backtest.prepare_frame(rows, datetime_index="timestamp")
        if frame is not None and not getattr(frame, "empty", True):
            frames.append(frame)
        cursor = chunk_end
    if not frames:
        return None
    return _concat(frames)


def build_replay_frame(symbol: str, start: datetime, end: datetime):
    bars = fetch_hourly_klines(symbol, start, end)
    funding = fetch_funding(symbol, start, end)
    if funding is None:
        raise RuntimeError(f"funding_rate history empty for {symbol}; refuse silent fill")
    return backtest.build_feature_frame(
        bars,
        features=[
            backtest.FeatureSource(
                data=funding,
                include_columns=("funding_rate",),
                rename_columns={"funding_rate": "funding_rate"},
                mode="asof",
                join="left",
            )
        ],
    )


def warmup_start(start: datetime) -> datetime:
    return start - timedelta(days=40)
