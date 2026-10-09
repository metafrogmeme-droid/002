"""Live isolated-limit execution. Mutations run only inside emit_signal_or_follow."""
from decimal import Decimal
from typing import Any

from . import risk


def _quantize(price: float, step: Decimal) -> str:
    if step <= 0:
        return str(price)
    quant = (Decimal(str(price)) / step).to_integral_value() * step
    return format(quant, "f")


def cancel_stale_limits(*, symbol: str, now_ms: int, ttl_hours: int, state: dict[str, Any]) -> list[dict[str, Any]]:
    from getagent import trade

    logs: list[dict[str, Any]] = []
    pending = trade.contract.pending_orders(symbol=symbol)
    if not trade.is_success(pending):
        return [{"reason_code": "pending_orders_failed", "symbol": symbol, "result": pending}]
    records = []
    raw = pending.get("data") if isinstance(pending, dict) else None
    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        records = raw.get("entrustedList") or raw.get("list") or []
    for item in records if isinstance(records, list) else []:
        if not isinstance(item, dict):
            continue
        order_id = str(item.get("orderId") or item.get("order_id") or "")
        if not order_id:
            continue
        placed = int(state.get("open_orders", {}).get(order_id, {}).get("ts") or 0)
        if placed and now_ms - placed < ttl_hours * 3600 * 1000:
            continue
        cancelled = trade.contract.cancel_order(symbol=symbol, order_id=order_id)
        logs.append(
            {
                "reason_code": "limit_ttl_cancel" if trade.is_success(cancelled) else "limit_cancel_failed",
                "symbol": symbol,
                "order_id": order_id,
                "result": cancelled,
            }
        )
    return logs


def place_isolated_long(
    *,
    symbol: str,
    limit_price: float,
    qty: float,
    leverage: int,
    sl_price: float,
    tp_price: float,
    margin_budget: str,
) -> dict[str, Any]:
    from getagent import trade

    leverage = risk.cap_leverage(leverage, 5)
    rules = trade.helpers.contract_rules(symbol)
    step = Decimal(str(getattr(rules, "price_step", "0.01") or "0.01"))
    sl = _quantize(sl_price, step)
    tp = _quantize(tp_price, step)
    limit = _quantize(limit_price, step)
    margin = risk.margin_for_qty(qty=qty, price=limit_price, leverage=leverage)
    budget = min(float(margin_budget), margin) if margin_budget else margin
    qty_plan = trade.helpers.compute_qty(
        symbol=symbol,
        market="contract",
        budget_amount=str(budget),
        leverage=leverage,
        price=limit,
    )
    tpsl = trade.helpers.resolve_contract_tpsl(
        symbol=symbol,
        side="long",
        leverage=leverage,
        tp_trigger_price=tp,
        sl_trigger_price=sl,
        reference_price=limit,
    )
    changed = trade.contract.change_leverage(symbol=symbol, leverage=leverage)
    if not trade.is_success(changed):
        return {"status": "leverage_failed", "result": changed}
    placed = trade.contract.place_order(
        symbol=symbol,
        side="buy",
        order_type="limit",
        qty=qty_plan.qty,
        price=limit,
        margin_mode="isolated",
        margin_coin="USDT",
        trade_side="open",
        pos_side="long",
        tp_trigger_price=tpsl.tp_trigger_price,
        sl_trigger_price=tpsl.sl_trigger_price,
    )
    if not trade.is_success(placed):
        raise RuntimeError(f"isolated limit open failed: {placed}")
    return {
        "status": "submitted",
        "qty": str(qty_plan.qty),
        "intended_price": limit,
        "sl": tpsl.sl_trigger_price,
        "tp": tpsl.tp_trigger_price,
        "result": placed,
    }


def alien_positions(*, opened_symbols: set[str]) -> list[str]:
    from getagent import trade

    current = trade.contract.current_position(symbol="")
    live_symbols = set(trade.helpers.contract_open_symbols(current) or [])
    return sorted(sym for sym in live_symbols if sym not in opened_symbols)
