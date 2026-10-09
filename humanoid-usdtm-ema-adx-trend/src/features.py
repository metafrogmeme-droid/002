"""Feature assembly for live scans and historical replay frames."""
from __future__ import annotations

import math
from typing import Any

from . import indicators


def extract_series(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    volumes: list[float] = []
    times: list[int] = []
    for row in rows:
        close = row.get("close")
        if close in (None, ""):
            continue
        highs.append(float(row.get("high") or close))
        lows.append(float(row.get("low") or close))
        closes.append(float(close))
        volumes.append(float(row.get("volume") or 0.0))
        stamp = row.get("time") or row.get("timestamp")
        times.append(int(stamp) if stamp not in (None, "") else 0)
    return {"high": highs, "low": lows, "close": closes, "volume": volumes, "time": times}


def build_indicator_pack(rows: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, Any] | None:
    series = extract_series(rows)
    closes = series["close"]
    if len(closes) < 80:
        return None
    fast = int(cfg.get("fast_period") or 12)
    slow = int(cfg.get("slow_period") or 26)
    adx_period = int(cfg.get("adx_period") or 14)
    atr_period = int(cfg.get("atr_period") or 14)
    vol_period = int(cfg.get("volume_avg_period") or 20)
    lookback = int(cfg.get("atr_percentile_lookback") or 500)
    atr_vals = indicators.atr(series["high"], series["low"], closes, atr_period)
    atr_pct = [
        (atr_vals[i] / closes[i] * 100.0) if closes[i] else math.nan
        for i in range(len(closes))
    ]
    return {
        "close": closes,
        "volume": series["volume"],
        "time": series["time"],
        "ema_fast": indicators.ema(closes, fast),
        "ema_slow": indicators.ema(closes, slow),
        "adx": indicators.adx(series["high"], series["low"], closes, adx_period),
        "atr": atr_vals,
        "atr_pctile": indicators.rolling_percentile(atr_pct, lookback),
        "vol_sma": indicators.sma(series["volume"], vol_period),
    }


def latest_snapshot(pack: dict[str, Any]) -> dict[str, Any] | None:
    i = len(pack["close"]) - 1
    if i < 1:
        return None
    needed = (
        pack["ema_fast"][i],
        pack["ema_slow"][i],
        pack["adx"][i],
        pack["adx"][i - 1],
        pack["atr"][i],
        pack["atr_pctile"][i],
        pack["vol_sma"][i],
    )
    if any(isinstance(v, float) and math.isnan(v) for v in needed):
        return None
    return {
        "index": i,
        "close": pack["close"][i],
        "volume": pack["volume"][i],
        "time": pack["time"][i],
        "ema_fast": pack["ema_fast"][i],
        "ema_slow": pack["ema_slow"][i],
        "adx": pack["adx"][i],
        "adx_prev": pack["adx"][i - 1],
        "atr": pack["atr"][i],
        "atr_pctile": pack["atr_pctile"][i],
        "vol_sma": pack["vol_sma"][i],
    }


def setup_ready(snap: dict[str, Any], cfg: dict[str, Any]) -> bool:
    return (
        snap["ema_fast"] > snap["ema_slow"]
        and snap["adx"] >= float(cfg.get("adx_min") or 25)
        and float(cfg.get("atr_pct_lo") or 20) <= snap["atr_pctile"] <= float(cfg.get("atr_pct_hi") or 90)
    )


def volume_confirms(snap: dict[str, Any], cfg: dict[str, Any]) -> bool:
    avg = snap["vol_sma"]
    if not avg:
        return False
    return snap["volume"] >= float(cfg.get("volume_mult") or 1.5) * avg
