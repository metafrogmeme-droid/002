"""Live order management through ``getagent.trade`` (imported by main_live only).

Mutations here are only ever reached from the ``execute_trade`` callback of
``runtime.emit_signal_or_follow(...)`` in ``main_live.run``. Every mutation
follows PRE-CHECK -> EXECUTE -> POST-CHECK.
"""
from decimal import Decimal
from typing import Any

from getagent import trade

try:
    from . import logic
except ImportError:  # loaded as a top-level module
    import logic  # type: ignore[no-redef]

RC = logic.ReasonCode


def read_snapshot() -> dict[str, Any]:
    """Read-only account state for the whole sub-account (all symbols)."""
    positions = trade.contract.current_position()
    orders = trade.contract.pending_orders()
    fills = trade.contract.fills(limit=100)
    for name, res in (("positions", positions), ("orders", orders), ("fills", fills)):
        if not trade.is_success(res):
            raise RuntimeError(f"snapshot read failed: {name}")
    pos = [logic.normalize_position(r) for r in trade.helpers.contract_position_records(positions)]
    return {
        "positions": [r for r in pos if r["size"] > 0],
        "orders": logic.extract_records(orders),
        "fills": logic.extract_records(fills),
    }


def verify_rules(symbol: str, spec: Any) -> tuple[bool, str]:
    """Cross-check the live exchange tick against the authoring-time contract config."""
    rules = trade.helpers.contract_rules(symbol)
    step = getattr(rules, "price_step", None)
    if step is None:
        return False, "contract_rules.price_step unavailable"
    if Decimal(str(step)) != spec.tick:
        return False, f"price_step {step} != verified tick {spec.tick}"
    return True, "ok"


def place_entry(symbol: str, plan: Any, leverage: int) -> dict[str, Any]:
    """Isolated-margin limit buy with exchange-side preset SL and TP on the order."""
    held = trade.contract.current_position(symbol=symbol)
    if trade.helpers.find_contract_position(held, symbol=symbol) is not None:
        return {"ok": False, "reason": RC.SKIP_SYMBOL_OCCUPIED.value}
    if logic.extract_records(trade.contract.pending_orders(symbol=symbol)):
        return {"ok": False, "reason": RC.SKIP_SYMBOL_OCCUPIED.value}

    tpsl = trade.helpers.resolve_contract_tpsl(
        symbol=symbol, side="long", leverage=leverage,
        tp_trigger_price=str(plan.take_profit), sl_trigger_price=str(plan.stop),
        reference_price=str(plan.entry),
    )
    if (Decimal(str(tpsl.sl_trigger_price)) != plan.stop
            or Decimal(str(tpsl.tp_trigger_price)) != plan.take_profit):
        return {"ok": False, "reason": RC.SKIP_CONFIG_MISMATCH.value, "detail": "tp/sl changed by tick alignment"}

    lev = trade.contract.change_leverage(symbol=symbol, leverage=leverage)
    if not trade.is_success(lev):
        return {"ok": False, "reason": RC.ORDER_REJECTED.value, "detail": "change_leverage failed"}
    placed = trade.contract.place_order(
        symbol=symbol, side="buy", order_type="limit", qty=str(plan.qty), price=str(plan.entry),
        margin_mode="isolated", trade_side="open",
        tp_trigger_price=str(tpsl.tp_trigger_price), sl_trigger_price=str(tpsl.sl_trigger_price),
    )
    if not trade.is_success(placed):
        return {"ok": False, "reason": RC.ORDER_REJECTED.value, "detail": logic.to_plain(placed)}
    order_id = str(logic.deep_find(placed, ("orderId", "order_id")) or "")

    out: dict[str, Any] = {"ok": True, "order_id": order_id, "sl_attached": "unverified"}
    resting = logic.extract_records(trade.contract.pending_orders(symbol=symbol))
    mine = next((r for r in resting if not order_id or str(logic.pick(r, "orderId", "order_id", default="")) == order_id), None)
    if mine is not None:
        for key in ("presetStopLossPrice", "presetStopLoss", "sl_trigger_price"):
            if key in mine:
                attached = mine[key] not in (None, "", "0")
                out["sl_attached"] = "yes" if attached else "no"
                break
        if out["sl_attached"] == "no":
            trade.contract.cancel_order(symbol=symbol, order_id=str(logic.pick(mine, "orderId", "order_id", default=order_id)))
            return {"ok": False, "reason": RC.SKIP_SL_NOT_ATTACHED.value, "order_id": order_id}
        mode = str(logic.pick(mine, "marginMode", "margin_mode", default="")).lower()
        out["margin_mode_seen"] = mode or "unverified"
        if mode and mode not in ("isolated", "isolation"):
            trade.contract.cancel_order(symbol=symbol, order_id=str(logic.pick(mine, "orderId", "order_id", default=order_id)))
            return {"ok": False, "reason": RC.HALT_MARGIN_MODE_MISMATCH.value, "order_id": order_id}
    else:
        out["post_check"] = "order not visible yet (may have filled immediately)"
    return out


def cancel_entry(symbol: str) -> dict[str, Any]:
    """Cancel the resting entry for ``symbol`` (unfilled expiry / funding window)."""
    resting = logic.extract_records(trade.contract.pending_orders(symbol=symbol))
    if not resting:
        return {"ok": True, "cancelled": 0, "detail": "nothing resting"}
    cancelled = 0
    for rec in resting:
        oid = str(logic.pick(rec, "orderId", "order_id", default=""))
        if oid and trade.is_success(trade.contract.cancel_order(symbol=symbol, order_id=oid)):
            cancelled += 1
    left = logic.extract_records(trade.contract.pending_orders(symbol=symbol))
    return {"ok": not left, "cancelled": cancelled, "still_resting": len(left)}


def time_stop_close(symbol: str) -> dict[str, Any]:
    """Close one Playbook-owned long after the time stop. Never touches other symbols."""
    held = trade.contract.current_position(symbol=symbol)
    position = trade.helpers.find_contract_position(held, symbol=symbol, hold_side="long")
    if position is None:
        return {"ok": True, "detail": "already flat"}
    closed = trade.contract.close_position(symbol=symbol, hold_side=position.hold_side)
    if not trade.is_success(closed):
        return {"ok": False, "detail": logic.to_plain(closed)}
    after = trade.contract.current_position(symbol=symbol)
    flat = trade.helpers.find_contract_position(after, symbol=symbol, hold_side="long") is None
    leftovers = len(logic.extract_records(trade.contract.plan_pending_orders(symbol=symbol)))
    return {"ok": True, "flat_after": flat, "leftover_plan_orders": leftovers}
