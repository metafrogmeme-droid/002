"""Bitget-native data loading shared by the replay and live paths."""

import asyncio
import math
from typing import Any, Callable, Optional

import pandas as pd

from getagent import data

HOUR_MS = 3_600_000
DAY_MS = 86_400_000
KLINE_CHUNK_MS = 40 * DAY_MS
FUNDING_CHUNK_MS = 85 * DAY_MS


def _ts_ms(row: dict, *keys: str) -> Optional[int]:
    for key in keys:
        value = row.get(key)
        if value in (None, ""):
            continue
        if isinstance(value, str) and value.strip().isdigit():
            value = int(value.strip())
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            v = int(value)
            return v * 1000 if v < 10_000_000_000 else v
        try:
            ts = pd.Timestamp(value)
        except (ValueError, TypeError):
            continue
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        return int(ts.value // 1_000_000)
    return None


def kline_rows(symbol: str, start_ms: int, end_ms: int, closed_only: bool = True) -> list[dict]:
    obb = data.crypto.futures.kline(
        symbol=symbol,
        interval="1h",
        exchange="bitget",
        limit=1000,
        start_time=int(start_ms),
        end_time=int(end_ms),
        closed_only=closed_only,
    )
    out = []
    for r in data.to_records(obb) or []:
        ts = _ts_ms(r, "time", "date")
        if ts is None:
            continue
        try:
            out.append({
                "ts": ts,
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r.get("volume") or 0.0),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return out


def funding_rows(symbol: str, start_ms: int, end_ms: int, interval: str = "4h",
                 exchange: str = "bitget") -> list[dict]:
    obb = data.crypto.futures.funding_rate(
        symbol=symbol,
        exchange=exchange,
        interval=interval,
        limit=1000,
        start_time=int(start_ms),
        end_time=int(end_ms),
    )
    out = []
    for r in data.to_records(obb) or []:
        ts = _ts_ms(r, "timestamp", "date")
        rate = r.get("funding_rate")
        if ts is None or rate in (None, ""):
            continue
        try:
            rate_f = float(rate)
        except (TypeError, ValueError):
            continue
        if math.isfinite(rate_f):
            out.append({"ts": ts, "funding_rate": rate_f})
    return out


def _chunks(start_ms: int, end_ms: int, size: int) -> list[tuple[int, int]]:
    out, cur = [], start_ms
    while cur < end_ms:
        out.append((cur, min(cur + size, end_ms)))
        cur += size
    return out


def _gather(jobs: list[tuple[Callable[..., list], tuple]], concurrency: int) -> list[Any]:
    async def runner() -> list[Any]:
        sem = asyncio.Semaphore(max(1, concurrency))

        async def one(fn: Callable[..., list], args: tuple) -> Any:
            async with sem:
                try:
                    return await asyncio.to_thread(fn, *args)
                except Exception as exc:  # noqa: BLE001
                    return exc

        return await asyncio.gather(*(one(fn, args) for fn, args in jobs))

    if concurrency <= 1:
        results = []
        for fn, args in jobs:
            try:
                results.append(fn(*args))
            except Exception as exc:  # noqa: BLE001
                results.append(exc)
        return results
    try:
        return asyncio.run(runner())
    except RuntimeError:
        return _gather(jobs, 1)


def load_history(symbols: list[str], start_ms: int, end_ms: int, funding_interval: str,
                 concurrency: int) -> tuple[dict[str, pd.DataFrame], dict[str, list[tuple[int, float]]], dict]:
    jobs: list[tuple[Callable[..., list], tuple]] = []
    tags: list[tuple[str, str]] = []
    for sym in symbols:
        for lo, hi in _chunks(start_ms, end_ms, KLINE_CHUNK_MS):
            jobs.append((kline_rows, (sym, lo, hi)))
            tags.append((sym, "kline"))
        for ex in ("bitget", "binance"):
            for lo, hi in _chunks(start_ms, end_ms, FUNDING_CHUNK_MS):
                jobs.append((funding_rows, (sym, lo, hi, funding_interval, ex)))
                tags.append((sym, f"funding_{ex}"))
    results = _gather(jobs, concurrency)

    bars: dict[str, dict[int, dict]] = {s: {} for s in symbols}
    fund: dict[str, dict[str, dict[int, float]]] = {s: {"bitget": {}, "binance": {}} for s in symbols}
    errors: list[str] = []
    for (sym, kind), res in zip(tags, results):
        if isinstance(res, Exception):
            errors.append(f"{sym}:{kind}:{type(res).__name__}:{str(res)[:120]}")
            continue
        if kind == "kline":
            for r in res:
                if start_ms <= r["ts"] < end_ms:
                    bars[sym][r["ts"]] = r
        else:
            ex = kind.split("_", 1)[1]
            for r in res:
                fund[sym][ex][r["ts"]] = r["funding_rate"]

    frames: dict[str, pd.DataFrame] = {}
    funding: dict[str, list[tuple[int, float]]] = {}
    coverage: dict[str, Any] = {"errors": errors[:20], "symbols": {}}
    for sym in symbols:
        rows = [bars[sym][k] for k in sorted(bars[sym])]
        native = sorted(fund[sym]["bitget"].items())
        proxy = sorted(fund[sym]["binance"].items())
        # Bitget funding where the SDK has it; Binance funding as a labelled proxy before that.
        cut = native[0][0] if native else end_ms
        fl = [x for x in proxy if x[0] < cut] + native
        funding[sym] = fl
        info = {
            "bars": len(rows),
            "funding_rows": len(fl),
            "funding_rows_bitget": len(native),
            "funding_rows_binance_proxy": sum(1 for x in proxy if x[0] < cut),
            "funding_bitget_from": pd.Timestamp(cut, unit="ms", tz="UTC").isoformat() if native else None,
            "funding_sample_bitget": native[-3:],
            "funding_sample_binance": proxy[-3:],
        }
        if rows:
            info["first_bar"] = pd.Timestamp(rows[0]["ts"], unit="ms", tz="UTC").isoformat()
            info["last_bar"] = pd.Timestamp(rows[-1]["ts"], unit="ms", tz="UTC").isoformat()
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
            frames[sym] = df[["date", "open", "high", "low", "close", "volume"]]
        if fl:
            info["first_funding"] = pd.Timestamp(fl[0][0], unit="ms", tz="UTC").isoformat()
        coverage["symbols"][sym] = info
    return frames, funding, coverage
