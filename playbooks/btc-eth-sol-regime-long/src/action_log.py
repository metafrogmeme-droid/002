"""Per-action log schema used by live execution and the replay ledger.

Every row has the same keys so live and backtest logs can be compared directly.
"""
from datetime import datetime, timezone
from typing import Any, Optional

LOG_FIELDS = (
    "ts_utc",
    "ts_ms",
    "run_id",
    "mode",
    "seq",
    "symbol",
    "action",
    "side",
    "intended_price",
    "filled_price",
    "qty",
    "fee_usdt",
    "funding_usdt",
    "realized_pnl_usdt",
    "r_multiple",
    "order_id",
    "reason_code",
    "detail",
)

ACTIONS = (
    "SIGNAL",
    "NO_TRADE",
    "ORDER_PLACED",
    "ORDER_CANCELLED",
    "ENTRY_FILLED",
    "EXIT",
    "HALT",
    "ALERT",
    "STATE",
)

REASON_CODES = {
    "ENTRY_SIGNAL": "Valid long entry signal on the closed 1H bar",
    "NO_SIGNAL": "No entry condition met on the closed bar",
    "INVALID_SIGNAL": "Signal layer returned a missing or invalid action; no trade",
    "REGIME_SIT_OUT": "Regime filter says sit out (transitional ADX or extreme/dead volatility)",
    "FUNDING_WINDOW": "Inside +/- funding block window around 00/08/16 UTC",
    "FUNDING_AGAINST": "Funding more than the cap against the position side",
    "FUNDING_UNKNOWN": "Funding rate unavailable; fail closed",
    "SYMBOL_BUSY": "Symbol already has a Playbook order or position",
    "MAX_CONCURRENT": "Max concurrent orders/positions reached",
    "DAILY_PAUSE": "Daily realised loss reached the pause level; no new entries today",
    "PLAYBOOK_STOP_DAILY_LOSS": "Daily realised loss reached the stop level; Playbook halted",
    "HALT_CONSECUTIVE_LOSSES": "Consecutive-loss limit reached; Playbook halted",
    "HALT_STALE_DATA": "Market data older than the staleness limit; no actions this run",
    "HALT_FOREIGN_POSITION": "Position not opened by this Playbook found; alert only, not touched",
    "HALT_STATE_UNREADABLE": "Persisted state unreadable; fail closed",
    "PNL_UNRESOLVED": "Could not resolve realised PnL of a closed trade; fail closed",
    "SIZE_EXCEEDS_LEVERAGE_CAP": "Required notional exceeds slot margin x leverage cap; skipped",
    "QTY_BELOW_MIN": "Risk-based size below the exchange minimum; skipped",
    "ENTRY_TTL_EXPIRED": "Entry limit not filled within the entry TTL; cancelled",
    "ORDER_GONE_UNFILLED": "Entry order no longer pending and no fills found (cancelled outside the Playbook)",
    "PAUSE_CANCEL": "Pending entry cancelled because new entries are paused/halted",
    "TIME_STOP": "Position reached the time stop; closed at market",
    "EXIT_TP": "Exchange-side take profit filled",
    "EXIT_SL": "Exchange-side stop loss filled",
    "EXIT_OTHER": "Position closed by an unclassified fill",
    "ORDER_REJECTED": "Exchange rejected or SDK failed the order call",
    "FOLLOW_NOT_EXECUTED": "Signal emitted but runtime did not execute the trade callback",
}


def iso(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).isoformat()


def make_row(
    *,
    ts_ms: int,
    run_id: str,
    mode: str,
    seq: int,
    symbol: str,
    action: str,
    reason_code: str,
    side: str = "",
    intended_price: Optional[float] = None,
    filled_price: Optional[float] = None,
    qty: Optional[float] = None,
    fee_usdt: Optional[float] = None,
    funding_usdt: Optional[float] = None,
    realized_pnl_usdt: Optional[float] = None,
    r_multiple: Optional[float] = None,
    order_id: str = "",
    detail: Any = None,
) -> dict[str, Any]:
    if action not in ACTIONS:
        raise ValueError(f"unknown log action {action!r}")
    if reason_code not in REASON_CODES:
        raise ValueError(f"unknown reason code {reason_code!r}")
    return {
        "ts_utc": iso(ts_ms),
        "ts_ms": int(ts_ms),
        "run_id": run_id,
        "mode": mode,
        "seq": int(seq),
        "symbol": symbol,
        "action": action,
        "side": side,
        "intended_price": intended_price,
        "filled_price": filled_price,
        "qty": qty,
        "fee_usdt": fee_usdt,
        "funding_usdt": funding_usdt,
        "realized_pnl_usdt": realized_pnl_usdt,
        "r_multiple": r_multiple,
        "order_id": order_id,
        "reason_code": reason_code,
        "detail": detail,
    }


class ActionLog:
    def __init__(self, run_id: str, mode: str, start_seq: int = 0) -> None:
        self.run_id = run_id
        self.mode = mode
        self.seq = start_seq
        self.rows: list[dict[str, Any]] = []

    def add(self, ts_ms: int, symbol: str, action: str, reason_code: str, **kw: Any) -> dict[str, Any]:
        self.seq += 1
        row = make_row(ts_ms=ts_ms, run_id=self.run_id, mode=self.mode, seq=self.seq,
                       symbol=symbol, action=action, reason_code=reason_code, **kw)
        self.rows.append(row)
        return row
