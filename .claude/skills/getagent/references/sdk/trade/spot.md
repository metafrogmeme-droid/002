# Trade Spot Reference

Spot query, place, cancel, and modify flows.

These signatures are written against the `getagent.trade` public contract.
Runner-managed identity kwargs (`user_id`, `channel`, `trace_id`) are
intentionally omitted from the author-facing signatures below.

## Contents
- [`trade.spot.pending_orders`](#tradespotpending-orders)
- [`trade.spot.fills`](#tradespotfills)
- [`trade.spot.place_order`](#tradespotplace-order)
- [`trade.spot.market_buy`](#tradespotmarket-buy)
- [`trade.spot.market_sell`](#tradespotmarket-sell)
- [`trade.spot.limit_order`](#tradespotlimit-order)
- [`trade.spot.cancel_order`](#tradespotcancel-order)
- [`trade.spot.modify_limit_order`](#tradespotmodify-limit-order)

## Method reference

### `trade.spot.pending_orders`

```python
trade.spot.pending_orders(symbol="", limit=None)
```

Summary: List live (unfilled) spot orders, optionally filtered by ``symbol``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `no` | `str` | `""` |
| `limit` | `no` | `int | None` | `None` |

Returns: `SpotPendingOrdersResult`

---

### `trade.spot.fills`

```python
trade.spot.fills(symbol="", order_id="", limit=None)
```

Summary: List recent spot trade fills, optionally scoped to one order.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `no` | `str` | `""` |
| `order_id` | `no` | `str` | `""` |
| `limit` | `no` | `int | None` | `None` |

Returns: `SpotFillsResult`

---

### `trade.spot.place_order`

```python
trade.spot.place_order(symbol, side, order_type, qty, price="", time_in_force='GTC')
```

Summary: Place a spot order with an explicit base-asset ``qty``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `side` | `yes` | `SideLiteral` | - |
| `order_type` | `yes` | `OrderTypeLiteral` | - |
| `qty` | `yes` | `Any` | - |
| `price` | `no` | `Any` | `""` |
| `time_in_force` | `no` | `TimeInForceLiteral` | `GTC` |

Returns: `OrderPlacedResult`

---

### `trade.spot.market_buy`

```python
trade.spot.market_buy(symbol, qty)
```

Summary: Spot market buy with base-asset ``qty`` (shorthand for place_order).

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `qty` | `yes` | `Any` | - |

Returns: `OrderPlacedResult`

---

### `trade.spot.market_sell`

```python
trade.spot.market_sell(symbol, qty)
```

Summary: Spot market sell with base-asset ``qty`` (shorthand for place_order).

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `qty` | `yes` | `Any` | - |

Returns: `OrderPlacedResult`

---

### `trade.spot.limit_order`

```python
trade.spot.limit_order(symbol, side, qty, price, time_in_force='GTC')
```

Summary: Spot limit order (shorthand for place_order with order_type='limit').

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `side` | `yes` | `SideLiteral` | - |
| `qty` | `yes` | `Any` | - |
| `price` | `yes` | `Any` | - |
| `time_in_force` | `no` | `TimeInForceLiteral` | `GTC` |

Returns: `OrderPlacedResult`

---

### `trade.spot.cancel_order`

```python
trade.spot.cancel_order(symbol, order_id)
```

Summary: Cancel a live spot order by ``order_id``.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `order_id` | `yes` | `str` | - |

Returns: `OrderPlacedResult`

---

### `trade.spot.modify_limit_order`

```python
trade.spot.modify_limit_order(symbol, order_id, price, qty)
```

Summary: Modify a live spot limit order's ``price`` and ``qty`` atomically.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `str` | - |
| `order_id` | `yes` | `str` | - |
| `price` | `yes` | `Any` | - |
| `qty` | `yes` | `Any` | - |

Returns: `OrderPlacedResult`

---
