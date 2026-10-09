"""Live follow-trade actions for USDT-M Trend v1 (live path only).

Never imported by the historical path. Every mutation runs inside
the ``execute_trade`` callback of ``runtime.emit_signal_or_follow``.
"""

import json
from datetime import datetime, timezone


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def open_long_with_tpsl(symbol, qty, limit_price, tp_price, sl_price, leverage):
    """Limit long with exchange-side TPSL attached. Returns result envelope."""
    from getagent import trade

    tpsl = trade.helpers.resolve_contract_tpsl(
        symbol=symbol,
        side="long",
        leverage=leverage,
        tp_trigger_price=str(tp_price),
        sl_trigger_price=str(sl_price),
    )
    result = trade.contract.open_long_limit(
        symbol=symbol,
        qty=str(qty),
        price=str(limit_price),
        leverage=leverage,
        tp_trigger_price=tpsl.tp_trigger_price,
        sl_trigger_price=tpsl.sl_trigger_price,
    )
    if not trade.is_success(result):
        raise RuntimeError("contract limit-long failed: %s" % (result,))
    return result


def cancel_stale_entries(symbol, older_than_hours=4):
    """Cancel pending limit entries older than the TTL (best effort)."""
    from getagent import trade

    pending = trade.contract.pending_orders(symbol=symbol)
    if not trade.is_success(pending):
        raise RuntimeError("pending_orders query failed: %s" % (pending,))
    return pending


def read_positions(symbols):
    """Return (records, open_symbols, raw) for the bound sub-account."""
    from getagent import trade

    current = trade.contract.current_position()
    if not trade.is_success(current):
        raise RuntimeError("current_position query failed: %s" % (current,))
    records = trade.helpers.contract_position_records(current)
    open_symbols = trade.helpers.contract_open_symbols(current)
    mine = [r for r in records if r.get("symbol") in symbols]
    return {"records": records, "mine": mine, "open_symbols": open_symbols,
            "raw": current}
