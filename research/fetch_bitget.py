"""Local-only research helper: pull Bitget USDT-M 1H candles and funding history.

Not part of the uploaded Playbook package. Used to develop and cross-check the
strategy locally before running the official sandbox backtest.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://api.bitget.com"
OUT = Path(__file__).resolve().parent / "data"
HOUR_MS = 3_600_000


def _get(path: str) -> dict:
    for attempt in range(5):
        try:
            with urllib.request.urlopen(BASE + path, timeout=20) as resp:
                return json.loads(resp.read())
        except Exception:  # noqa: BLE001
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {path}")


def candles(symbol: str, start_ms: int, end_ms: int) -> list[list]:
    rows: dict[int, list] = {}
    cursor = end_ms
    while cursor > start_ms:
        q = (
            f"/api/v2/mix/market/history-candles?symbol={symbol}&productType=USDT-FUTURES"
            f"&granularity=1H&endTime={cursor}&limit=200"
        )
        data = _get(q).get("data") or []
        if not data:
            break
        for r in data:
            rows[int(r[0])] = r
        oldest = min(int(r[0]) for r in data)
        if oldest >= cursor:
            break
        cursor = oldest
        time.sleep(0.12)
    return [rows[k] for k in sorted(rows) if start_ms <= k < end_ms]


def funding(symbol: str, start_ms: int) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        q = (
            f"/api/v2/mix/market/history-fund-rate?symbol={symbol}&productType=USDT-FUTURES"
            f"&pageSize=100&pageNo={page}"
        )
        data = _get(q).get("data") or []
        if not data:
            break
        out.extend(data)
        if min(int(r["fundingTime"]) for r in data) < start_ms:
            break
        page += 1
        time.sleep(0.12)
    return sorted((r for r in out if int(r["fundingTime"]) >= start_ms), key=lambda r: int(r["fundingTime"]))


def main() -> None:
    start_ms = int(sys.argv[1]) if len(sys.argv) > 1 else 1_722_470_400_000  # 2024-08-01
    end_ms = int(sys.argv[2]) if len(sys.argv) > 2 else 1_790_812_800_000  # 2026-10-01
    OUT.mkdir(exist_ok=True)
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        c = candles(sym, start_ms, end_ms)
        (OUT / f"{sym}_1h.json").write_text(json.dumps(c))
        f = funding(sym, start_ms)
        (OUT / f"{sym}_funding.json").write_text(json.dumps(f))
        print(sym, len(c), "bars", len(f), "funding rows",
              c[0][0] if c else None, c[-1][0] if c else None)


if __name__ == "__main__":
    main()
