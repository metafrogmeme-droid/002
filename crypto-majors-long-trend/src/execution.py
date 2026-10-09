"""Live isolated-margin limit entry and manage/exit helpers."""

from typing import Any

from getagent import trade

from . import spec
from .risk import quantize_price


def _success(result: object) -> bool:
    return bool(trade.is_success(result))


def _raw_price(position: Any) -> str:
    raw = getattr(position, "raw", None) or {}
    if not isinstance(raw, dict):
        return ""
    for key in ("openPriceAvg", "openPrice", "averageOpenPrice", "avgPrice"):
        value = raw.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def current_position(symbol: str):
    snapshot = trade.contract.current_position(symbol=symbol)
    return trade.helpers.find_contract_position(snapshot, symbol=symbol, hold_side="long")


def all_open_symbols():
    snapshot = trade.contract.current_position()
    return trade.helpers.contract_open_symbols(snapshot)


def pending_entry(symbol: str):
    pending = trade.contract.pending_orders(symbol=symbol)
    try:
        return trade.helpers.select_contract_order(
            pending,
            symbol=symbol,
            prefer_first=True,
        )
    except Exception:
        return None


def place_isolated_long(
    *,
    symbol: str,
    qty: str,
    price: str,
    leverage: int,
    tp_price: str,
    sl_price: str,
) -> dict[str, Any]:
    support = trade.market.check_symbol_support([symbol])
    if not trade.is_success(support):
        raise RuntimeError(f"symbol support check failed: {support}")

    ticked = trade.helpers.resolve_contract_tpsl(
        symbol=symbol,
        side="long",
        leverage=leverage,
        tp_trigger_price=tp_price,
        sl_trigger_price=sl_price,
        reference_price=price,
        product_type=spec.PRODUCT_TYPE,
    )
    levered = trade.contract.change_leverage(symbol=symbol, leverage=leverage)
    if not _success(levered):
        raise RuntimeError(f"change_leverage failed: {levered}")

    placed = trade.contract.place_order(
        symbol=symbol,
        side="buy",
        order_type="limit",
        qty=qty,
        price=price,
        product_type=spec.PRODUCT_TYPE,
        margin_mode="isolated",
        margin_coin="USDT",
        pos_side="long",
        trade_side="open",
        tp_trigger_price=ticked.tp_trigger_price,
        sl_trigger_price=ticked.sl_trigger_price,
    )
    if not _success(placed):
        raise RuntimeError(f"isolated limit open failed: {placed}")
    return {
        "status": "limit_placed",
        "qty": qty,
        "price": price,
        "tp_trigger_price": str(ticked.tp_trigger_price),
        "sl_trigger_price": str(ticked.sl_trigger_price),
        "leverage": leverage,
        "margin_mode": "isolated",
        "result": placed,
    }


def cancel_pending(symbol: str, order_id: str) -> dict[str, Any]:
    pending = trade.contract.pending_orders(symbol=symbol)
    selected = None
    if order_id:
        try:
            selected = trade.helpers.find_contract_order(pending, order_id)
        except Exception:
            selected = None
    if selected is None:
        selected = pending_entry(symbol)
    if selected is None:
        return {"status": "already_gone"}
    target_id = getattr(selected, "order_id", None) or order_id
    cancelled = trade.contract.cancel_order(symbol=symbol, order_id=target_id)
    if not _success(cancelled):
        raise RuntimeError(f"cancel failed: {cancelled}")
    return {"status": "cancelled", "order_id": str(target_id), "result": cancelled}


def close_long(symbol: str) -> dict[str, Any]:
    snapshot = trade.contract.current_position(symbol=symbol)
    position = trade.helpers.find_contract_position(snapshot, symbol=symbol, hold_side="long")
    if position is None:
        return {"status": "flat"}
    closed = trade.contract.close_position(symbol=symbol, hold_side="long")
    if not _success(closed):
        raise RuntimeError(f"close failed: {closed}")
    return {
        "status": "closed",
        "entry_price": _raw_price(position),
        "result": closed,
    }


def levels_from_entry(symbol: str, entry: float, stop_distance: float, tp_r: float) -> tuple[str, str]:
    tick = spec.tick_size(symbol)
    sl = quantize_price(symbol, entry - stop_distance - tick)
    tp = quantize_price(symbol, entry + tp_r * stop_distance)
    return str(tp), str(sl)
