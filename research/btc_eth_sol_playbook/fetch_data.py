"""Download the historical inputs for the local research backtest.

Sources (public, no credentials):
  * 1H USDT-M perpetual candles: Bitget v2 `mix/market/history-candles`.
  * Funding settlements, recent ~90 days: Bitget v2 `mix/market/history-fund-rate`
    (Bitget's public endpoint does not page further back than that).
  * Funding settlements, older history: Binance USDT-M monthly archive on
    data.binance.vision, used as a PROXY for Bitget funding. Every row keeps a
    `source` column so results can state which engine/data produced them.

Output: CSV files under ./data/ (gitignored; rerun this script to rebuild).

Usage:
  python3 fetch_data.py --start 2023-08-01 --end 2026-10-01
"""
from __future__ import annotations

import argparse
import io
import json
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
DATA_DIR = Path(__file__).resolve().parent / "data"
BITGET = "https://api.bitget.com"
BINANCE_ARCHIVE = "https://data.binance.vision/data/futures/um/monthly/fundingRate"
HOUR_MS = 3_600_000


def _get(url: str, retries: int = 4) -> bytes:
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-backtest/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception:
            if attempt == retries:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def _ms(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def fetch_candles(symbol: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    rows: dict[int, list] = {}
    cursor = end_ms
    while cursor > start_ms:
        window_start = max(start_ms, cursor - 200 * HOUR_MS)
        url = (
            f"{BITGET}/api/v2/mix/market/history-candles?symbol={symbol}"
            f"&productType=USDT-FUTURES&granularity=1H&startTime={window_start}"
            f"&endTime={cursor}&limit=200"
        )
        payload = json.loads(_get(url))
        if payload.get("code") != "00000":
            raise RuntimeError(f"bitget candles error {symbol}: {payload}")
        batch = payload.get("data") or []
        for r in batch:
            ts = int(r[0])
            if start_ms <= ts < end_ms:
                rows[ts] = r
        cursor = window_start
        time.sleep(0.07)
    df = pd.DataFrame(
        [rows[k] for k in sorted(rows)],
        columns=["ts", "open", "high", "low", "close", "volume", "quote_volume"],
    )
    df = df.astype({"ts": "int64", "open": float, "high": float, "low": float,
                    "close": float, "volume": float, "quote_volume": float})
    return df


def fetch_bitget_funding(symbol: str) -> pd.DataFrame:
    out = []
    for page in range(1, 30):
        url = (
            f"{BITGET}/api/v2/mix/market/history-fund-rate?symbol={symbol}"
            f"&productType=USDT-FUTURES&pageSize=100&pageNo={page}"
        )
        payload = json.loads(_get(url))
        batch = payload.get("data") or []
        if not batch:
            break
        out.extend(batch)
        time.sleep(0.1)
    df = pd.DataFrame(out)
    if df.empty:
        return pd.DataFrame(columns=["ts", "rate", "source"])
    df = pd.DataFrame({
        "ts": df["fundingTime"].astype("int64"),
        "rate": df["fundingRate"].astype(float),
        "source": "bitget",
    })
    return df


def fetch_binance_funding(symbol: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    frames = []
    month = pd.Timestamp(start_ms, unit="ms").to_period("M")
    last = pd.Timestamp(end_ms, unit="ms").to_period("M")
    while month <= last:
        url = f"{BINANCE_ARCHIVE}/{symbol}/{symbol}-fundingRate-{month.strftime('%Y-%m')}.zip"
        try:
            blob = _get(url, retries=2)
        except Exception:
            month += 1
            continue
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            raw = pd.read_csv(zf.open(zf.namelist()[0]))
        frames.append(pd.DataFrame({
            "ts": raw["calc_time"].astype("int64"),
            "rate": raw["last_funding_rate"].astype(float),
            "source": "binance_proxy",
        }))
        month += 1
    if not frames:
        return pd.DataFrame(columns=["ts", "rate", "source"])
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-08-01")
    ap.add_argument("--end", default="2026-10-01")
    args = ap.parse_args()
    start_ms, end_ms = _ms(args.start), _ms(args.end)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"start": args.start, "end": args.end, "symbols": {}}
    for sym in SYMBOLS:
        candles = fetch_candles(sym, start_ms, end_ms)
        candles.to_csv(DATA_DIR / f"{sym}_1h.csv", index=False)

        bg = fetch_bitget_funding(sym)
        bn = fetch_binance_funding(sym, start_ms, end_ms)
        # Normalise settlement timestamps to the hour so both sources align.
        for f in (bg, bn):
            if not f.empty:
                f["ts"] = (f["ts"] // HOUR_MS) * HOUR_MS
        overlap = None
        if not bg.empty and not bn.empty:
            m = bg.merge(bn, on="ts", suffixes=("_bg", "_bn"))
            if len(m) > 5:
                overlap = {
                    "rows": int(len(m)),
                    "corr": float(m["rate_bg"].corr(m["rate_bn"])),
                    "mean_abs_diff": float((m["rate_bg"] - m["rate_bn"]).abs().mean()),
                    "mean_bitget": float(m["rate_bg"].mean()),
                    "mean_binance": float(m["rate_bn"].mean()),
                }
        bitget_start = int(bg["ts"].min()) if not bg.empty else end_ms
        funding = pd.concat([bn[bn["ts"] < bitget_start], bg], ignore_index=True)
        funding = funding[(funding["ts"] >= start_ms) & (funding["ts"] < end_ms)]
        funding = funding.drop_duplicates("ts", keep="last").sort_values("ts")
        funding.to_csv(DATA_DIR / f"{sym}_funding.csv", index=False)

        manifest["symbols"][sym] = {
            "candles": int(len(candles)),
            "candles_first": pd.Timestamp(candles["ts"].min(), unit="ms", tz="UTC").isoformat(),
            "candles_last": pd.Timestamp(candles["ts"].max(), unit="ms", tz="UTC").isoformat(),
            "missing_hours": int((end_ms - start_ms) // HOUR_MS - len(candles)),
            "funding_rows": int(len(funding)),
            "funding_rows_bitget": int((funding["source"] == "bitget").sum()),
            "funding_rows_binance_proxy": int((funding["source"] == "binance_proxy").sum()),
            "bitget_funding_first": pd.Timestamp(bitget_start, unit="ms", tz="UTC").isoformat(),
            "funding_overlap_bitget_vs_binance": overlap,
        }
        print(sym, json.dumps(manifest["symbols"][sym]))
    (DATA_DIR / "data_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
