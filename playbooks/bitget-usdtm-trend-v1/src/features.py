"""Market-data access shared by the backtest and live paths (no trade imports).

All calls go through ``getagent.data`` with ``exchange="bitget"`` and
exchange-native symbols. No ``provider=`` argument is ever passed.
"""
from typing import Any, Optional

import pandas as pd
from getagent import backtest, data

try:
    from .logic import HOUR_MS, DAY_MS, to_float, to_ms
except ImportError:  # loaded as a top-level module by the replay runner
    from logic import HOUR_MS, DAY_MS, to_float, to_ms  # type: ignore[no-redef]

EXCHANGE = "bitget"
# The kline endpoint caps `limit` at 1000 and truncates silently toward the
# window END, so every request stays below the cap to make truncation impossible.
KLINE_CHUNK_BARS = 960
FUNDING_CHUNK_MS = 40 * DAY_MS
SETTLEMENT_HOURS = (0, 8, 16)


class DataError(RuntimeError):
    pass


def _frame_from(obb: Any) -> pd.DataFrame:
    if not data.to_records(obb):
        return pd.DataFrame()
    frame = backtest.prepare_frame(obb, datetime_index="date")
    return frame


def fetch_klines(symbol: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Closed 1h bars in [start_ms, end_ms), stitched from <=960-bar chunks."""
    frames: list[pd.DataFrame] = []
    cursor = start_ms
    while cursor < end_ms:
        chunk_end = min(cursor + KLINE_CHUNK_BARS * HOUR_MS, end_ms)
        bars = data.crypto.futures.kline(
            symbol=symbol, interval="1h", exchange=EXCHANGE, limit=1000,
            start_time=cursor, end_time=chunk_end, closed_only=True,
        )
        frame = _frame_from(bars)
        if not frame.empty:
            frames.append(frame)
        cursor = chunk_end
    if not frames:
        raise DataError(f"{symbol}: kline returned no rows for the requested window")
    out = pd.concat(frames)
    out = out[~out.index.duplicated(keep="first")].sort_index()
    lo = pd.Timestamp(start_ms, unit="ms", tz="UTC")
    hi = pd.Timestamp(end_ms, unit="ms", tz="UTC")
    return out[(out.index >= lo) & (out.index < hi)]


def check_coverage(symbol: str, frame: pd.DataFrame, start_ms: int, end_ms: int, max_gap_bars: int = 6) -> dict[str, Any]:
    """Raise if the replay frame does not honestly cover the requested window."""
    if frame.empty:
        raise DataError(f"{symbol}: empty replay frame")
    first = int(frame.index[0].timestamp() * 1000)
    last = int(frame.index[-1].timestamp() * 1000)
    expected = (end_ms - start_ms) // HOUR_MS
    gaps = frame.index.to_series().diff().dropna()
    biggest_gap = int(gaps.max().total_seconds() // 3600) if len(gaps) else 0
    report = {
        "symbol": symbol, "rows": len(frame), "expected_rows": int(expected),
        "first_ts_ms": first, "last_ts_ms": last, "largest_gap_hours": biggest_gap,
        "columns": list(frame.columns),
    }
    if first - start_ms > 48 * HOUR_MS:
        raise DataError(f"{symbol}: history starts {first} well after requested {start_ms}: {report}")
    if len(frame) < 0.97 * expected or biggest_gap > max_gap_bars:
        raise DataError(f"{symbol}: coverage too thin or gapped: {report}")
    return report


def _settlement_rows(records: list[dict[str, Any]]) -> list[tuple[int, float]]:
    rows: dict[int, float] = {}
    for rec in records:
        ts = to_ms(rec.get("timestamp") if rec.get("timestamp") not in (None, "") else rec.get("date"))
        if ts is None:
            try:
                ts = int(pd.to_datetime(str(rec.get("timestamp") or rec.get("date")), utc=True).timestamp() * 1000)
            except (ValueError, TypeError):
                continue
        rate = to_float(rec.get("funding_rate"))
        if rate is None:
            continue
        hour, rem = divmod(ts % DAY_MS, HOUR_MS)
        if hour in SETTLEMENT_HOURS and rem == 0:
            rows[ts] = rate
    return sorted(rows.items())


def fetch_funding(symbol: str, start_ms: int, end_ms: int) -> Optional[pd.DataFrame]:
    """Settlement-time funding rates indexed by UTC time, or None if unavailable.

    The funding endpoint's docs say some providers want a base-asset symbol, so
    the exchange-native symbol is tried first and the base asset second. Which
    candidate worked is returned in the frame's ``attrs``.
    """
    base = symbol[:-4] if symbol.endswith("USDT") else symbol
    for candidate in (symbol, base):
        collected: list[tuple[int, float]] = []
        try:
            cursor = start_ms
            while cursor < end_ms:
                chunk_end = min(cursor + FUNDING_CHUNK_MS, end_ms)
                resp = data.crypto.futures.funding_rate(
                    symbol=candidate, exchange=EXCHANGE, interval="1h", limit=1000,
                    start_time=cursor, end_time=chunk_end,
                )
                collected.extend(_settlement_rows(data.to_records(resp)))
                cursor = chunk_end
        except Exception:  # noqa: BLE001 - probing candidates; failure is reported, not hidden
            collected = []
        if collected:
            uniq = dict(collected)
            idx = pd.to_datetime(sorted(uniq), unit="ms", utc=True)
            frame = pd.DataFrame({"funding_rate": [uniq[k] for k in sorted(uniq)]}, index=idx)
            frame.attrs["symbol_used"] = candidate
            return frame
    return None


def build_replay_frame(bars: pd.DataFrame, funding: Optional[pd.DataFrame]) -> pd.DataFrame:
    if funding is None:
        return bars
    return backtest.build_feature_frame(
        bars,
        features=[
            backtest.FeatureSource(
                data=funding, include_columns=("funding_rate",), mode="asof",
            )
        ],
    )


# ---------------------------------------------------------------------------
# Live helpers
# ---------------------------------------------------------------------------


def latest_closed_bar_open_ms(symbol: str) -> Optional[int]:
    bars = data.crypto.futures.kline(
        symbol=symbol, interval="1h", exchange=EXCHANGE, limit=3, closed_only=True,
    )
    frame = _frame_from(bars)
    if frame.empty:
        return None
    return int(frame.index.max().timestamp() * 1000)


def mark_snapshot(symbol: str) -> dict[str, Optional[float]]:
    resp = data.crypto.futures.mark_price(symbol=symbol, exchange=EXCHANGE)
    rows = data.to_records(resp)
    rec = next((r for r in rows if str(r.get("symbol", symbol)).upper() == symbol), rows[0] if rows else {})
    return {
        "mark_price": to_float(rec.get("mark_price")),
        "last_funding_rate": to_float(rec.get("last_funding_rate")),
        "next_funding_time_ms": to_ms(rec.get("next_funding_time")),
    }
