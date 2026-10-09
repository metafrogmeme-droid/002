"""Risk, halt, and funding-clock helpers. Values are read from strategy_config."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def cfg(manifest: dict[str, Any]) -> dict[str, Any]:
    return dict(manifest.get("strategy_config") or {})


def as_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def cap_leverage(raw: object, hard_cap: int = 5) -> int:
    return max(1, min(hard_cap, as_int(raw, hard_cap)))


def near_funding(ts_ms: int, blackout_minutes: int = 15) -> bool:
    """True when [bar_open, bar_open+1h) intersects ±blackout around 00/08/16 UTC."""
    open_s = ts_ms / 1000.0
    close_s = open_s + 3600.0
    base = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    pad = blackout_minutes * 60
    for hour in (0, 8, 16):
        center = base.replace(hour=hour, minute=0, second=0, microsecond=0).timestamp()
        for shift in (-86400, 0, 86400):
            mid = center + shift
            if open_s < mid + pad and close_s > mid - pad:
                return True
    return False


def funding_blocks_long(rate: float | None, skip_rate: float) -> bool:
    if rate is None:
        return False
    return rate > skip_rate


def position_qty(*, risk_usdt: float, stop_distance: float, lot: float) -> float:
    if stop_distance <= 0 or lot <= 0:
        return 0.0
    raw = risk_usdt / stop_distance
    stepped = (raw // lot) * lot
    return float(stepped) if stepped > 0 else 0.0


def margin_for_qty(*, qty: float, price: float, leverage: int) -> float:
    if leverage <= 0:
        return 0.0
    return abs(qty * price) / leverage
