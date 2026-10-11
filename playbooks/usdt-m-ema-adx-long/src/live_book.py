"""Pure live-state rules. This module does not import getagent or place orders."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any


def book_realised(state: dict[str, Any], net: float, day: str) -> dict[str, Any]:
    """Apply one closed-trade net to the persisted halt counters."""
    daily = state.setdefault("daily", {})
    if not isinstance(daily, dict):
        daily = {}
        state["daily"] = daily
    daily[day] = float(daily.get(day) or 0.0) + float(net)
    state["cumulative_realised"] = float(state.get("cumulative_realised") or 0.0) + float(net)
    if net < 0:
        state["consecutive_losses"] = int(state.get("consecutive_losses") or 0) + 1
    elif net > 0:
        state["consecutive_losses"] = 0
    return state


def mark_filled(item: dict[str, Any], filled_at: str) -> dict[str, Any]:
    """Start the 8h clock at the fill, not at the limit submit."""
    item["status"] = "open"
    item["filled_at"] = filled_at
    return item


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def time_stop_due(filled_at: Any, now: datetime, hours: int) -> bool:
    """True only after `hours` from the fill. A missing fill time does not fire."""
    anchor = parse_utc(filled_at)
    if anchor is None:
        return False
    return now >= anchor + timedelta(hours=hours)


def choose_order_qty(planned: Decimal, helper: Decimal, distance: Decimal, max_loss: Decimal) -> Decimal | None:
    """Keep the pre-sized quantity. A helper result must not increase it."""
    if distance <= 0 or planned <= 0:
        return None
    qty = planned
    if helper > 0 and helper < planned:
        qty = helper
    if qty * distance > max_loss + Decimal("0.01"):
        return None
    return qty


def bars_are_stale(last_open_ms: int | None, now: datetime, bar_hours: int) -> bool:
    """True when the newest closed bar is older than two intervals."""
    if last_open_ms is None:
        return True
    interval_ms = bar_hours * 60 * 60 * 1000
    return (now.timestamp() * 1000) - (last_open_ms + interval_ms) > 2 * interval_ms


def net_from_fill_rows(rows: list[Any], after_ms: int | None = None) -> float | None:
    """Sum a documented profit field. Missing or non-numeric profit stays unknown."""
    if not isinstance(rows, list) or not rows:
        return None
    total = 0.0
    found = 0
    for row in rows:
        if not isinstance(row, dict):
            return None
        stamp = row.get("time") or row.get("cTime") or row.get("fillTime") or row.get("ts")
        if after_ms is not None and stamp not in (None, ""):
            try:
                stamp_ms = int(float(stamp))
            except (TypeError, ValueError):
                return None
            if stamp_ms < 10_000_000_000:
                stamp_ms *= 1000
            if stamp_ms < after_ms:
                continue
        raw = None
        for key in ("profit", "achievedProfits", "totalProfits"):
            if key in row and row[key] not in (None, ""):
                raw = row[key]
                break
        if raw is None:
            continue
        try:
            total += float(raw)
        except (TypeError, ValueError):
            return None
        found += 1
    if found == 0:
        return None
    return total
