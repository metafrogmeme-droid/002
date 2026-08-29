# Trade Contract Reference

USDT futures query, leverage, order, TP/SL, and close flows.

These signatures are written against the `getagent.trade` public contract.
Runner-managed identity kwargs (`user_id`, `channel`, `trace_id`) are
intentionally omitted from the author-facing signatures below.

## Contents
- [`trade.contract.pending_orders`](#tradecontractpending-orders)
- [`trade.contract.plan_pending_orders`](#tradecontractplan-pending-orders)
- [`trade.contract.current_position`](#tradecontractcurrent-position)
- [`trade.contract.fills`](#tradecontractfills)
- [`trade.contract.change_leverage`](#tradecontractchange-leverage)
- [`trade.contract.place_order`](#tradecontractplace-order)
- [`trade.contract.cancel_order`](#tradecontractcancel-order)
- [`trade.contract.modify_limit_order`](#tradecontractmodify-limit-order)
- [`trade.contract.close_position`](#tradecontractclose-position)
- [`trade.contract.modify_take_profit`](#tradecontractmodify-take-profit)
- [`trade.contract.modify_stop_loss`](#tradecontractmodify-stop-loss)
- [`trade.contract.open_long_market`](#tradecontractopen-long-market)
- [`trade.contract.open_short_market`](#tradecontractopen-short-market)
- [`trade.contract.open_long_limit`](#tradecontractopen-long-limit)
- [`trade.contract.open_short_limit`](#tradecontractopen-short-limit)

## Method reference

### `trade.contract.pending_orders`

```python
trade.contract.pending_orders(symbol="", limit=None, product_type='USDT-FUTURES')
```

Summary: List live (unfilled) contract orders, optionally filtered by ``symbol``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `no` | `str` | `""` |
| `limit` | `no` | `int | None` | `None` |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `ContractPendingOrdersResult`

---

### `trade.contract.plan_pending_orders`

```python
trade.contract.plan_pending_orders(symbol="", limit=None, product_type='USDT-FUTURES')
```

Summary: List live TP/SL (plan) orders, optionally filtered by ``symbol``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `no` | `str` | `""` |
| `limit` | `no` | `int | None` | `None` |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `PlanPendingOrdersResult`

---

### `trade.contract.current_position`

```python
trade.contract.current_position(symbol="", product_type='USDT-FUTURES')
```

Summary: Query live contract positions, optionally filtered by ``symbol``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `no` | `str` | `""` |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `ContractCurrentPositionResult`

---

### `trade.contract.fills`

```python
trade.contract.fills(symbol="", order_id="", limit=None, product_type='USDT-FUTURES')
```

Summary: List recent contract trade fills, optionally scoped to one order.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `no` | `str` | `""` |
| `order_id` | `no` | `str` | `""` |
| `limit` | `no` | `int | None` | `None` |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `ContractFillsResult`

---

### `trade.contract.change_leverage`

```python
trade.contract.change_leverage(symbol, leverage, product_type='USDT-FUTURES', margin_coin='USDT')
```

Summary: Change the contract leverage for ``symbol`` before opening a position.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `leverage` | `yes` | `Any` | - |
| `product_type` | `no` | `str` | `USDT-FUTURES` |
| `margin_coin` | `no` | `str` | `USDT` |

Returns: `ChangeLeverageResult`

---

### `trade.contract.place_order`

```python
trade.contract.place_order(symbol, side, order_type, qty, price="", product_type='USDT-FUTURES', margin_mode='crossed', margin_coin='USDT', pos_side="", trade_side="", tp_trigger_price="", sl_trigger_price="")
```

Summary: Place a contract order with full parameter control.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `side` | `yes` | `SideLiteral` | - |
| `order_type` | `yes` | `OrderTypeLiteral` | - |
| `qty` | `yes` | `Any` | - |
| `price` | `no` | `Any` | `""` |
| `product_type` | `no` | `str` | `USDT-FUTURES` |
| `margin_mode` | `no` | `MarginModeLiteral` | `crossed` |
| `margin_coin` | `no` | `str` | `USDT` |
| `pos_side` | `no` | `PosSideOrEmptyLiteral` | `""` |
| `trade_side` | `no` | `TradeSideOrEmptyLiteral` | `""` |
| `tp_trigger_price` | `no` | `Any` | `""` |
| `sl_trigger_price` | `no` | `Any` | `""` |

Returns: `OrderPlacedResult`

---

### `trade.contract.cancel_order`

```python
trade.contract.cancel_order(symbol, order_id, product_type='USDT-FUTURES')
```

Summary: Cancel a live contract order by ``order_id``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `order_id` | `yes` | `str` | - |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `OrderPlacedResult`

---

### `trade.contract.modify_limit_order`

```python
trade.contract.modify_limit_order(symbol, order_id, price, qty, tp_trigger_price, sl_trigger_price)
```

Summary: Modify a live contract limit order's price/qty/TP/SL atomically.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `order_id` | `yes` | `str` | - |
| `price` | `yes` | `Any` | - |
| `qty` | `yes` | `Any` | - |
| `tp_trigger_price` | `yes` | `Any` | - |
| `sl_trigger_price` | `yes` | `Any` | - |

Returns: `OrderPlacedResult`

---

### `trade.contract.close_position`

```python
trade.contract.close_position(symbol, hold_side, product_type='USDT-FUTURES')
```

Summary: Fully close the ``hold_side`` contract position for ``symbol``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `hold_side` | `yes` | `HoldSideLiteral` | - |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `ClosePositionResult`

---

### `trade.contract.modify_take_profit`

```python
trade.contract.modify_take_profit(symbol, order_id, trigger_price, product_type='USDT-FUTURES')
```

Summary: Modify an existing take-profit plan order's ``trigger_price``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `order_id` | `yes` | `str` | - |
| `trigger_price` | `yes` | `Any` | - |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `ModifyPlanOrderResult`

---

### `trade.contract.modify_stop_loss`

```python
trade.contract.modify_stop_loss(symbol, order_id, trigger_price, product_type='USDT-FUTURES')
```

Summary: Modify an existing stop-loss plan order's ``trigger_price``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `order_id` | `yes` | `str` | - |
| `trigger_price` | `yes` | `Any` | - |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `ModifyPlanOrderResult`

---

### `trade.contract.open_long_market`

```python
trade.contract.open_long_market(symbol, qty, leverage, tp_trigger_price="", sl_trigger_price="")
```

Summary: Composite open-long market order: change leverage + place order.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `qty` | `yes` | `Any` | - |
| `leverage` | `yes` | `Any` | - |
| `tp_trigger_price` | `no` | `Any` | `""` |
| `sl_trigger_price` | `no` | `Any` | `""` |

Returns: `OpenPositionResult`

TP/SL trigger prices must align with the contract instrument price step. Do not
use fixed decimal rounding such as `str(round(price, 2))`; use
`trade.helpers.resolve_contract_tpsl(...)` or quantize custom trigger prices with
`trade.helpers.contract_rules(symbol).price_step` before calling this method.

---

### `trade.contract.open_short_market`

```python
trade.contract.open_short_market(symbol, qty, leverage, tp_trigger_price="", sl_trigger_price="")
```

Summary: Composite open-short market order: change leverage + place order.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `qty` | `yes` | `Any` | - |
| `leverage` | `yes` | `Any` | - |
| `tp_trigger_price` | `no` | `Any` | `""` |
| `sl_trigger_price` | `no` | `Any` | `""` |

Returns: `OpenPositionResult`

TP/SL trigger prices must align with the contract instrument price step. Do not
use fixed decimal rounding such as `str(round(price, 2))`; use
`trade.helpers.resolve_contract_tpsl(...)` or quantize custom trigger prices with
`trade.helpers.contract_rules(symbol).price_step` before calling this method.

---

### `trade.contract.open_long_limit`

```python
trade.contract.open_long_limit(symbol, qty, price, leverage, tp_trigger_price="", sl_trigger_price="")
```

Summary: Composite open-long limit order: change leverage + place limit order.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `qty` | `yes` | `Any` | - |
| `price` | `yes` | `Any` | - |
| `leverage` | `yes` | `Any` | - |
| `tp_trigger_price` | `no` | `Any` | `""` |
| `sl_trigger_price` | `no` | `Any` | `""` |

Returns: `OpenPositionResult`

---

### `trade.contract.open_short_limit`

```python
trade.contract.open_short_limit(symbol, qty, price, leverage, tp_trigger_price="", sl_trigger_price="")
```

Summary: Composite open-short limit order: change leverage + place limit order.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `qty` | `yes` | `Any` | - |
| `price` | `yes` | `Any` | - |
| `leverage` | `yes` | `Any` | - |
| `tp_trigger_price` | `no` | `Any` | `""` |
| `sl_trigger_price` | `no` | `Any` | `""` |

Returns: `OpenPositionResult`

---
