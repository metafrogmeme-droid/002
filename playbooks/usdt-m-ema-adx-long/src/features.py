"""Historical bar and funding fetch for the replay path.

The managed client is getagent.data. This module does not set a provider.
Kline requests stay inside the documented 1000-bar cap and are stitched by
`time`. A symbol with no Bitget market row, or a funding series that cannot
be read, is reported. Callers must not replace a missing series with zeros.
"""

from datetime import datetime, timezone
from typing import Any

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


def fetch_funding(symbol: str, start_ms: int, end_ms: int) -> tuple[list[dict[str, Any]], str]:
    """Return funding rows and the symbol argument that produced them.

    The documented funding endpoint notes that some providers expect a base
    asset. Try the exchange-native pair first, then the base asset. Keep the
    first non-empty result and report which argument worked.
    """
    base = symbol[:-4] if symbol.endswith("USDT") else symbol
    last_error = "no rows"
    for candidate in (symbol, base):
        pages = []
        try:
            for chunk_start, chunk_end in _chunk_bounds(start_ms, end_ms, FUNDING_CHUNK_MS):
                pages.append(
                    data.crypto.futures.funding_rate(
                        symbol=candidate,
                        exchange="bitget",
                        interval="1h",
                        start_time=chunk_start,
                        end_time=chunk_end,
                        limit=1000,
                    )
                )
        except Exception as exc:
            last_error = f"{candidate}: {type(exc).__name__}"
            continue
        rows = _stitch(pages)
        if rows:
            return rows, candidate
        last_error = f"{candidate}: empty"
    raise DataCoverageError(f"{symbol}: funding_rate unavailable ({last_error})")


def _with_epoch_ms(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy rows so both `time` and `timestamp` are millisecond epochs."""
    normalized: list[dict[str, Any]] = []
    for row in rows:
        stamp = _time_ms(row)
        if stamp is None:
            continue
        copied = dict(row)
        copied["time"] = stamp
        copied["timestamp"] = stamp
        normalized.append(copied)
    return normalized


def build_replay_frame(symbol: str, start_ms: int, end_ms: int) -> tuple[Any, dict[str, Any]]:
    native = resolve_bitget_perpetual(symbol)
    bars = fetch_klines(native, start_ms, end_ms)
    funding_rows, funding_symbol = fetch_funding(native, start_ms, end_ms)
    frame = backtest.build_feature_frame(
        _with_epoch_ms(bars),
        base_datetime_index="time",
        features=[
            backtest.FeatureSource(
                data=_with_epoch_ms(funding_rows),
                datetime_index="timestamp",
                include_columns=("funding_rate",),
                mode="asof",
                direction="backward",
            )
        ],
    )
    if "funding_rate" not in getattr(frame, "columns", []):
        raise DataCoverageError(f"{symbol}: replay frame is missing funding_rate")
    coverage = {
        "symbol": native,
        "requested_symbol": symbol,
        "funding_symbol_argument": funding_symbol,
        "kline_rows": len(bars),
        "funding_rows": len(funding_rows),
        "kline_first_ms": _time_ms(bars[0]),
        "kline_last_ms": _time_ms(bars[-1]),
        "funding_first_ms": _time_ms(funding_rows[0]),
        "funding_last_ms": _time_ms(funding_rows[-1]),
        "invalid_signal_code": INVALID_SIGNAL,
    }
    return frame, coverage
