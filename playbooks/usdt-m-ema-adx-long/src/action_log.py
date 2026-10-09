"""Shared action-log row. Prices and costs are strings so the log does not drift."""

from datetime import datetime, timezone
from typing import Any


def action_row(
    *,
    timestamp: datetime,
    symbol: str,
    side: str,
    reason_code: str,
    intended_price: float | None = None,
    filled_price: float | None = None,
    fees: float | None = None,
    funding: float | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    moment = timestamp.astimezone(timezone.utc)
    return {
        "timestamp": moment.isoformat(),
        "symbol": symbol,
        "side": side,
        "intended_price": _num(intended_price),
        "filled_price": _num(filled_price),
        "fees": _num(fees),
        "funding": _num(funding),
        "reason_code": reason_code,
        "detail": detail or "",
    }


def _num(value: float | None) -> str | None:
    if value is None:
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return format(value, ".10g")
