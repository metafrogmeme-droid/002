"""Historical bar and funding fetch for the replay path.

The managed client is getagent.data. This module does not set a provider.
Kline requests stay inside the documented 1000-bar cap and are stitched by
`time`. A symbol with no Bitget market row, or a funding series that cannot
be read, is reported. Callers must not replace a missing series with zeros.
"""

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from getagent import backtest, data

try:
    from .reasons import INVALID_SIGNAL
except ImportError:
    from reasons import INVALID_SIGNAL


HOUR_MS = 60 * 60 * 1000
# Stay under the 1000-row cap and the 90-day window. A full 1000-row
# request is end-anchored, so a 900-hour page keeps the first bar.
KLINE_CHUNK_MS = 900 * HOUR_MS
FUNDING_CHUNK_MS = 900 * HOUR_MS


class DataCoverageError(RuntimeError):
    """Raised when a required replay series is missing or not identifiable."""


def resolve_bitget_perpetual(symbol: str) -> str:
    """Confirm a Bitget perpetual row and return the exchange-native symbol."""
    base = symbol[:-4] if symbol.endswith("USDT") else symbol
    markets = data.crypto.market(
        symbol=f"{base}/USDT",
        market_type="perpetual",
        exchange="bitget",
    )
    rows = data.to_records(markets)
    for row in rows:
        exchange = str(row.get("exchange") or "").lower()
        if exchange != "bitget":
            continue
        active = row.get("active")
        status = str(row.get("status") or "").lower()
        if active is False:
            continue
        if active is not True and status not in {"", "online", "normal"}:
            continue
        exchange_id = str(row.get("exchange_id") or "").upper()
        if exchange_id and exchange_id.isalnum():
            return exchange_id
        return symbol
    raise DataCoverageError(
        f"{symbol}: no active Bitget perpetual row from data.crypto.market"
    )


def _chunk_bounds(start_ms: int, end_ms: int, step_ms: int) -> list[tuple[int, int]]:
    bounds: list[tuple[int, int]] = []
    cursor = start_ms
    while cursor < end_ms:
        nxt = min(cursor + step_ms, end_ms)
        bounds.append((cursor, nxt))
        cursor = nxt
    return bounds


def _time_ms(row: dict[str, Any]) -> int | None:
    for key in ("time", "timestamp", "date"):
        raw = row.get(key)
        if raw is None or raw == "":
            continue
        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            parsed = _parse_datetime(raw)
            if parsed is None:
                continue
            return int(parsed.timestamp() * 1000)
        if value < 10_000_000_000:
            value *= 1000
        return value
    return None


def _parse_datetime(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stitch(pages: list[Any]) -> list[dict[str, Any]]:
    merged: dict[int, dict[str, Any]] = {}
    for page in pages:
        for row in data.to_records(page):
            stamp = _time_ms(row)
            if stamp is None:
                continue
            merged[stamp] = row
    return [merged[stamp] for stamp in sorted(merged)]


def fetch_klines(symbol: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    pages = []
    for chunk_start, chunk_end in _chunk_bounds(start_ms, end_ms, KLINE_CHUNK_MS):
        pages.append(
            data.crypto.futures.kline(
                symbol=symbol,
                interval="1h",
                exchange="bitget",
                start_time=chunk_start,
                end_time=chunk_end,
                limit=1000,
                closed_only=True,
            )
        )
    rows = [
        row
        for row in _stitch(pages)
        if (stamp := _time_ms(row)) is not None and start_ms <= stamp < end_ms
    ]
    if not rows:
        raise DataCoverageError(f"{symbol}: Bitget 1H kline stitch returned no rows")
    return rows


def fetch_funding(symbol: str, start_ms: int, end_ms: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return decimal funding rows and the walk that produced them.

    Pages move the request end backward. A page that does not start earlier
    than the end it was given is a stalled window: those rows are kept, and
    the gap back to `start_ms` is left empty. Missing rates are not filled
    with zero. The pair symbol is tried before the base asset. Among
    non-empty walks, the earliest series wins, then the one with more rows.

    Measured on 2026-10-10: `crypto.futures.funding_rate` (bitget_data) ignores
    a 2024 start and its earliest row is 2026-07-12T00:00:00Z.
    `crypto.futures.funding_weighted` (coinglass, base symbol, interval 1d,
    weight_type volume) does honor that start: BTC, ETH, and SOL each returned
    730 daily rows from 2024-10-09 through 2026-10-08 with no gap above 36h.
    That series is a cross-exchange volume-weighted rate, not Bitget's own
    settlement print. Its percent display is divided by 100, the same unit
    conversion as bitget_data (BTC 2026-10-08 weighted 0.003811 versus the
    public Bitget print 0.00004). A 4h weighted request did not start on
    2024-10-09, so the daily series is the one used.
    """
    try:
        from .risk import funding_rate_from_managed
    except ImportError:
        from risk import funding_rate_from_managed

    base = symbol[:-4] if symbol.endswith("USDT") else symbol
    attempts: list[dict[str, Any]] = []
    best_rows: list[dict[str, Any]] | None = None
    best_info: dict[str, Any] | None = None
    weighted_rows, weighted_info = _walk_weighted_funding(base, start_ms, end_ms)
    attempts.append(weighted_info)
    if weighted_rows and not weighted_info.get("stalled"):
        best_rows = _scale_funding_rows(weighted_rows, funding_rate_from_managed)
        best_info = weighted_info
    else:
        best_rank: tuple[int, int] | None = None
        for candidate in (symbol, base):
            for interval in ("4h", "1d", "1h"):
                rows, info = _walk_funding(candidate, interval, start_ms, end_ms)
                attempts.append(info)
                if not rows:
                    continue
                scaled = _scale_funding_rows(rows, funding_rate_from_managed)
                earliest = int(info.get("earliest_ms") or 0)
                rank = (earliest, -len(scaled))
                if best_rank is None or rank < best_rank:
                    best_rank = rank
                    best_rows = scaled
                    best_info = info
    if not best_rows or best_info is None:
        raise DataCoverageError(
            f"{symbol}: funding_rate unavailable ({_attempt_summary(attempts)})"
        )
    best_info = dict(best_info)
    best_info["attempts"] = [
        {
            "symbol": item.get("symbol"),
            "interval": item.get("interval"),
            "rows": item.get("rows"),
            "earliest_ms": item.get("earliest_ms"),
            "latest_ms": item.get("latest_ms"),
            "stalled": item.get("stalled"),
        }
        for item in attempts
    ]
    return best_rows, best_info


def _attempt_summary(attempts: list[dict[str, Any]]) -> str:
    if not attempts:
        return "no requests"
    parts = []
    for item in attempts:
        parts.append(
            f"{item.get('symbol')}/{item.get('interval')}:{item.get('stalled') or item.get('rows')}"
        )
    return "; ".join(parts)


def _scale_funding_rows(rows: list[dict[str, Any]], scaler: Any) -> list[dict[str, Any]]:
    scaled: list[dict[str, Any]] = []
    for row in rows:
        try:
            rate = scaler(float(row.get("funding_rate")))
        except (TypeError, ValueError):
            continue
        if rate != rate or rate in (float("inf"), float("-inf")):
            continue
        copied = dict(row)
        copied["funding_rate"] = rate
        scaled.append(copied)
    return scaled


def _walk_weighted_funding(
    base: str, start_ms: int, end_ms: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Forward-page the daily cross-exchange series. Do not fill holes."""
    try:
        from .risk import funding_series_gap_ms
    except ImportError:
        from risk import funding_series_gap_ms

    page_span = 80 * 24 * HOUR_MS
    max_gap = 36 * HOUR_MS
    collected: dict[int, dict[str, Any]] = {}
    cursor = start_ms
    stalled = ""
    pages = 0
    first_request: dict[str, Any] | None = None
    while cursor < end_ms and pages < 16:
        chunk_end = min(end_ms, cursor + page_span)
        pages += 1
        try:
            page = data.crypto.futures.funding_weighted(
                symbol=base,
                interval="1d",
                start_time=cursor,
                end_time=chunk_end,
                limit=1000,
                weight_type="volume",
            )
        except Exception as exc:
            stalled = type(exc).__name__
            if first_request is None:
                first_request = {"start_time": cursor, "end_time": chunk_end, "error": stalled}
            break
        page_rows: list[dict[str, Any]] = []
        for row in data.to_records(page):
            stamp = _time_ms(row)
            raw = row.get("weighted_funding_rate")
            if stamp is None or raw is None or stamp < start_ms or stamp > end_ms:
                continue
            if stamp < cursor or stamp > chunk_end:
                continue
            copied = dict(row)
            copied["funding_rate"] = raw
            page_rows.append(copied)
        if first_request is None:
            first_request = {
                "start_time": cursor,
                "end_time": chunk_end,
                "rows": len(page_rows),
            }
        if not page_rows:
            stalled = "empty"
            break
        earliest = min(_time_ms(row) or 0 for row in page_rows)
        if earliest > chunk_end:
            stalled = "window_ignored"
            break
        for row in page_rows:
            stamp = _time_ms(row)
            if stamp is not None:
                collected[stamp] = row
        cursor = chunk_end
    rows = [collected[stamp] for stamp in sorted(collected)]
    earliest_ms = min(collected) if collected else None
    latest_ms = max(collected) if collected else None
    gap_ms = funding_series_gap_ms(list(collected), max_gap) if collected else None
    if gap_ms is not None and not stalled:
        stalled = "gap"
    if rows and earliest_ms is not None and earliest_ms > start_ms and not stalled:
        stalled = "short_of_start"
    return rows, {
        "symbol": base,
        "interval": "1d",
        "source": "crypto.futures.funding_weighted",
        "rows": len(rows),
        "earliest_ms": earliest_ms,
        "latest_ms": latest_ms,
        "stalled": stalled,
        "gap_ms": gap_ms,
        "pages": pages,
        "first_request": first_request or {},
    }


def _walk_funding(
    candidate: str, interval: str, start_ms: int, end_ms: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Walk `end_time` backward until the series reaches `start_ms` or stalls."""
    try:
        from .risk import funding_page_ignores_window
    except ImportError:
        from risk import funding_page_ignores_window

    interval_ms = {"1h": HOUR_MS, "4h": 4 * HOUR_MS, "1d": 24 * HOUR_MS}[interval]
    page_span = min(80 * 24 * HOUR_MS, 900 * interval_ms)
    collected: dict[int, dict[str, Any]] = {}
    cursor_end = end_ms
    stalled = ""
    pages = 0
    first_request: dict[str, Any] | None = None
    while cursor_end > start_ms and pages < 24:
        cursor_start = max(start_ms, cursor_end - page_span)
        pages += 1
        try:
            page = data.crypto.futures.funding_rate(
                symbol=candidate,
                exchange="bitget",
                interval=interval,
                start_time=cursor_start,
                end_time=cursor_end,
                limit=1000,
            )
        except Exception as exc:
            stalled = type(exc).__name__
            if first_request is None:
                first_request = {
                    "start_time": cursor_start,
                    "end_time": cursor_end,
                    "error": stalled,
                }
            break
        page_rows = _stitch([page])
        times = [stamp for stamp in (_time_ms(row) for row in page_rows) if stamp is not None]
        if not times:
            stalled = "empty"
            if first_request is None:
                first_request = {
                    "start_time": cursor_start,
                    "end_time": cursor_end,
                    "rows": 0,
                }
            break
        earliest, latest = min(times), max(times)
        if first_request is None:
            first_request = {
                "start_time": cursor_start,
                "end_time": cursor_end,
                "rows": len(page_rows),
                "earliest_ms": earliest,
                "latest_ms": latest,
            }
        for row in page_rows:
            stamp = _time_ms(row)
            if stamp is not None and stamp <= end_ms:
                collected[stamp] = row
        if funding_page_ignores_window(earliest, latest, cursor_end, interval_ms):
            stalled = "window_ignored"
            break
        if earliest <= start_ms:
            break
        if earliest >= cursor_end:
            stalled = "window_ignored"
            break
        cursor_end = earliest
    rows = [collected[stamp] for stamp in sorted(collected)]
    earliest_ms = min(collected) if collected else None
    latest_ms = max(collected) if collected else None
    if rows and earliest_ms is not None and earliest_ms > start_ms and not stalled:
        stalled = "short_of_start"
    return rows, {
        "symbol": candidate,
        "interval": interval,
        "rows": len(rows),
        "earliest_ms": earliest_ms,
        "latest_ms": latest_ms,
        "stalled": stalled,
        "pages": pages,
        "first_request": first_request or {},
    }


def _bars_for_replay(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Kline rows indexed by `time`. Drop `timestamp` so the joiner can create it."""
    normalized: list[dict[str, Any]] = []
    for row in rows:
        stamp = _time_ms(row)
        if stamp is None:
            continue
        copied = {key: value for key, value in row.items() if key != "timestamp"}
        copied["time"] = stamp
        normalized.append(copied)
    return normalized


def _funding_for_replay(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Funding rows indexed by `funding_ts`, not the reserved name `timestamp`."""
    normalized: list[dict[str, Any]] = []
    for row in rows:
        stamp = _time_ms(row)
        if stamp is None:
            continue
        try:
            rate = float(row.get("funding_rate"))
        except (TypeError, ValueError):
            continue
        if rate != rate or rate in (float("inf"), float("-inf")):
            continue
        normalized.append({"funding_ts": stamp, "funding_rate": rate})
    return normalized


def build_replay_frame(symbol: str, start_ms: int, end_ms: int) -> tuple[Any, dict[str, Any]]:
    native = resolve_bitget_perpetual(symbol)
    bars = fetch_klines(native, start_ms, end_ms)
    funding_rows, funding_info = fetch_funding(native, start_ms, end_ms)
    funding_symbol = str(funding_info.get("symbol") or native)
    frame = backtest.build_feature_frame(
        _bars_for_replay(bars),
        base_datetime_index="time",
        features=[
            backtest.FeatureSource(
                data=_funding_for_replay(funding_rows),
                datetime_index="funding_ts",
                include_columns=("funding_rate",),
                mode="asof",
                direction="backward",
            )
        ],
    )
    if "funding_rate" not in getattr(frame, "columns", []):
        raise DataCoverageError(f"{symbol}: replay frame is missing funding_rate")
    frame = _restore_utc_index(frame)
    index_min = frame.index.min()
    index_max = frame.index.max()
    if int(index_max.year) < 2000:
        raise DataCoverageError(
            f"{symbol}: replay index stayed in {index_min.isoformat()} .. {index_max.isoformat()}"
        )
    coverage = {
        "symbol": native,
        "requested_symbol": symbol,
        "funding_symbol_argument": funding_symbol,
        "funding_source": funding_info.get("source") or "crypto.futures.funding_rate",
        "funding_interval": funding_info.get("interval"),
        "funding_stalled": funding_info.get("stalled"),
        "funding_gap_ms": funding_info.get("gap_ms"),
        "funding_pages": funding_info.get("pages"),
        "funding_first_request": funding_info.get("first_request"),
        "funding_scale": "percent_display_divided_by_100",
        "kline_rows": len(bars),
        "funding_rows": len(funding_rows),
        "kline_first_ms": _time_ms(bars[0]),
        "kline_last_ms": _time_ms(bars[-1]),
        "funding_first_ms": _time_ms(funding_rows[0]),
        "funding_last_ms": _time_ms(funding_rows[-1]),
        "invalid_signal_code": INVALID_SIGNAL,
        "index_first": index_min.isoformat(),
        "index_last": index_max.isoformat(),
    }
    return frame, coverage


def _restore_utc_index(frame: Any) -> Any:
    """Put bar opens on a real UTC timeline.

    Millisecond epochs are sometimes read as nanoseconds, which lands the
    whole sample in 1970 and then the execution window drops every bar.
    """
    index = frame.index
    if not isinstance(index, pd.DatetimeIndex):
        numbers = pd.to_numeric(pd.Index(index), errors="coerce")
        sample = float(numbers[0])
        unit = "ms" if sample >= 10**11 else "s"
        restored = frame.copy()
        restored.index = pd.to_datetime(numbers, unit=unit, utc=True)
        return restored
    if len(index) and int(index.max().year) < 2000:
        restored = frame.copy()
        restored.index = pd.to_datetime(index.asi8 * 1_000_000, utc=True)
        return restored
    if index.tz is None:
        restored = frame.copy()
        restored.index = index.tz_localize("UTC")
        return restored
    return frame
