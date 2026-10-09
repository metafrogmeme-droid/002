"""Persisted live halt / ownership state under .state/."""

import json
from pathlib import Path

from .risk import HaltState

STATE_PATH = Path("/workspace/.state/playbook_state.json")
LOG_PATH = Path("/workspace/.state/action_log.jsonl")


def load_state() -> HaltState:
    if not STATE_PATH.exists():
        return HaltState()
    try:
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return HaltState()
    opened = payload.get("opened_symbols") or []
    return HaltState(
        halted=bool(payload.get("halted", False)),
        halt_reason=str(payload.get("halt_reason") or ""),
        daily_realized_usdt=float(payload.get("daily_realized_usdt") or 0.0),
        daily_date_utc=str(payload.get("daily_date_utc") or ""),
        consecutive_losses=int(payload.get("consecutive_losses") or 0),
        opened_symbols=tuple(str(item) for item in opened),
        pending_order_id=str(payload.get("pending_order_id") or ""),
        pending_symbol=str(payload.get("pending_symbol") or ""),
        pending_submitted_ms=int(payload.get("pending_submitted_ms") or 0),
        last_entry_price=str(payload.get("last_entry_price") or ""),
        last_stop_price=str(payload.get("last_stop_price") or ""),
        last_tp_price=str(payload.get("last_tp_price") or ""),
    )


def save_state(state: HaltState) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "halted": state.halted,
        "halt_reason": state.halt_reason,
        "daily_realized_usdt": state.daily_realized_usdt,
        "daily_date_utc": state.daily_date_utc,
        "consecutive_losses": state.consecutive_losses,
        "opened_symbols": list(state.opened_symbols),
        "pending_order_id": state.pending_order_id,
        "pending_symbol": state.pending_symbol,
        "pending_submitted_ms": state.pending_submitted_ms,
        "last_entry_price": state.last_entry_price,
        "last_stop_price": state.last_stop_price,
        "last_tp_price": state.last_tp_price,
    }
    STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def append_action_log(row: dict[str, object]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False, default=str)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
