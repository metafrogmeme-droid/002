# Trade Helpers Reference

Deterministic symbol, qty, TP/SL, and selector helpers.

These signatures are written against the `getagent.trade` public contract.
Runner-managed identity kwargs (`user_id`, `channel`, `trace_id`) are
intentionally omitted from the author-facing signatures below.

## Contents
- [`trade.helpers.normalize_trading_symbol`](#tradehelpersnormalize-trading-symbol)
- [`trade.helpers.normalize_trading_symbols`](#tradehelpersnormalize-trading-symbols)
- [`trade.helpers.parse_budget`](#tradehelpersparse-budget)
- [`trade.helpers.spot_price_quote`](#tradehelpersspot-price-quote)
- [`trade.helpers.spot_price`](#tradehelpersspot-price)
- [`trade.helpers.contract_price_quote`](#tradehelperscontract-price-quote)
- [`trade.helpers.contract_price`](#tradehelperscontract-price)
- [`trade.helpers.spot_rules`](#tradehelpersspot-rules)
- [`trade.helpers.contract_rules`](#tradehelperscontract-rules)
- [`trade.helpers.compute_qty`](#tradehelperscompute-qty)
- [`trade.helpers.resolve_contract_tpsl`](#tradehelpersresolve-contract-tpsl)
- [`trade.helpers.select_spot_order`](#tradehelpersselect-spot-order)
- [`trade.helpers.select_contract_order`](#tradehelpersselect-contract-order)
- [`trade.helpers.select_tp_plan_order`](#tradehelpersselect-tp-plan-order)
- [`trade.helpers.select_sl_plan_order`](#tradehelpersselect-sl-plan-order)
- [`trade.helpers.select_contract_position`](#tradehelpersselect-contract-position)
- [`trade.helpers.find_contract_position`](#tradehelpersfind-contract-position)
- [`trade.helpers.contract_position_records`](#tradehelperscontract-position-records)
- [`trade.helpers.count_open_contract_positions`](#tradehelperscount-open-contract-positions)
- [`trade.helpers.contract_open_symbols`](#tradehelperscontract-open-symbols)
- [`trade.helpers.find_spot_order`](#tradehelpersfind-spot-order)
- [`trade.helpers.find_contract_order`](#tradehelpersfind-contract-order)

## Method reference

### `trade.helpers.normalize_trading_symbol`

```python
trade.helpers.normalize_trading_symbol(symbol, quote='USDT')
```

Summary: -

Normalizes simple asset inputs into exchange-native quote pairs. This helper is
safe for crypto shortcuts such as `BTC -> BTCUSDT`. For Bitget RWA markets,
choose the market namespace before normalizing:

- RWA spot Apple: pass `RAAPL` or `RAAPLUSDT`
- RWA contract Apple: pass `AAPL` or `AAPLUSDT`
- RWA contract gold: pass `XAU` or `XAUUSDT`

Do not pass the result to a different market type than the one implied by the
symbol. In particular, `normalize_trading_symbol("AAPL")` produces `AAPLUSDT`,
which is the RWA contract namespace, not the RWA spot namespace.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |
| `quote` | `no` | `str` | `USDT` |

Returns: `str`

---

### `trade.helpers.normalize_trading_symbols`

```python
trade.helpers.normalize_trading_symbols(symbols, quote='USDT')
```

Summary: -

Applies `normalize_trading_symbol(...)` to each item. The same RWA namespace
rule applies: use `R`-prefixed inputs for RWA spot and non-prefixed inputs for
RWA contracts.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbols` | `yes` | `list[Any] | tuple[Any, ...]` | - |
| `quote` | `no` | `str` | `USDT` |

Returns: `list[str]`

---

### `trade.helpers.parse_budget`

```python
trade.helpers.parse_budget(value, default_quote='USDT')
```

Summary: -

| Param | Required | Type | Default |
|---|---|---|---|
| `value` | `yes` | `Any` | - |
| `default_quote` | `no` | `str` | `USDT` |

Returns: `ParsedBudget`

---

### `trade.helpers.spot_price_quote`

```python
trade.helpers.spot_price_quote(symbol)
```

Summary: -

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |

Returns: `PriceQuote`

---

### `trade.helpers.spot_price`

```python
trade.helpers.spot_price(symbol)
```

Summary: Return the latest Bitget spot price as a Decimal.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |

Returns: `Decimal`

---

### `trade.helpers.contract_price_quote`

```python
trade.helpers.contract_price_quote(symbol, product_type='USDT-FUTURES')
```

Summary: -

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `PriceQuote`

---

### `trade.helpers.contract_price`

```python
trade.helpers.contract_price(symbol, product_type='USDT-FUTURES')
```

Summary: Return the latest Bitget contract last price as a Decimal.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `Decimal`

---

### `trade.helpers.spot_rules`

```python
trade.helpers.spot_rules(symbol)
```

Summary: Load normalized Bitget spot instrument rules for a symbol.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |

Returns: `InstrumentRules`

---

### `trade.helpers.contract_rules`

```python
trade.helpers.contract_rules(symbol, product_type='USDT-FUTURES')
```

Summary: Load normalized Bitget contract instrument rules for a symbol.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `InstrumentRules`

---

### `trade.helpers.compute_qty`

```python
trade.helpers.compute_qty(symbol, market, budget_amount, leverage=None, price="", product_type='USDT-FUTURES')
```

Summary: Convert a quote budget into executable spot or contract qty.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |
| `market` | `yes` | `MarketLiteral` | - |
| `budget_amount` | `yes` | `Any` | - |
| `leverage` | `no` | `Any` | `None` |
| `price` | `no` | `Any` | `""` |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `QtyPlan`

---

### `trade.helpers.resolve_contract_tpsl`

```python
trade.helpers.resolve_contract_tpsl(*, symbol, side, leverage, tp_trigger_price="", sl_trigger_price="", reference_price="", product_type='USDT-FUTURES')
```

Summary: Validate or auto-fill contract TP/SL using live price and instrument rules.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbol` | `yes` | `Any` | - |
| `side` | `yes` | `TpSlSideLiteral` | - |
| `leverage` | `yes` | `Any` | - |
| `tp_trigger_price` | `no` | `Any` | `""` |
| `sl_trigger_price` | `no` | `Any` | `""` |
| `reference_price` | `no` | `Any` | `""` |
| `product_type` | `no` | `str` | `USDT-FUTURES` |

Returns: `ContractTpslPlan`

Live contract order rule: never pass `str(round(price, 2))` or any other fixed
decimal precision directly to `tp_trigger_price` / `sl_trigger_price`. Bitget
contract trigger prices must align with the instrument `price_step` / tick size
(for example BTCUSDT may require `0.1` increments). Use
`trade.helpers.resolve_contract_tpsl(...)` when possible, or load
`trade.helpers.contract_rules(symbol)` and quantize custom ATR/indicator trigger
prices to `rules.price_step` before calling `trade.contract.open_long_market(...)`
or `trade.contract.open_short_market(...)`.

`resolve_contract_tpsl` is keyword-only and accepts only the parameters listed
above. It does **not** accept percentage override kwargs such as
`tp_pct_override`, `sl_pct_override`, `take_profit_pct`, or `stop_loss_pct`. If a
strategy exposes percentage-based TP/SL tunables, compute concrete
`tp_trigger_price` and `sl_trigger_price` values first, then pass those prices to
this helper for validation and tick-size alignment.

---

### `trade.helpers.select_spot_order`

```python
trade.helpers.select_spot_order(pending_orders_result, symbol="", prefer_first=False)
```

Summary: -

| Param | Required | Type | Default |
|---|---|---|---|
| `pending_orders_result` | `yes` | `dict[str, Any]` | - |
| `symbol` | `no` | `str` | `""` |
| `prefer_first` | `no` | `bool` | `false` |

Returns: `OrderSelection`

---

### `trade.helpers.select_contract_order`

```python
trade.helpers.select_contract_order(pending_orders_result, symbol="", prefer_first=False)
```

Summary: -

| Param | Required | Type | Default |
|---|---|---|---|
| `pending_orders_result` | `yes` | `dict[str, Any]` | - |
| `symbol` | `no` | `str` | `""` |
| `prefer_first` | `no` | `bool` | `false` |

Returns: `OrderSelection`

---

### `trade.helpers.select_tp_plan_order`

```python
trade.helpers.select_tp_plan_order(plan_orders_result, symbol="", prefer_first=False)
```

Summary: Pick a take-profit plan order candidate from a live plan-order payload.

| Param | Required | Type | Default |
|---|---|---|---|
| `plan_orders_result` | `yes` | `dict[str, Any]` | - |
| `symbol` | `no` | `str` | `""` |
| `prefer_first` | `no` | `bool` | `false` |

Returns: `PlanOrderSelection`

---

### `trade.helpers.select_sl_plan_order`

```python
trade.helpers.select_sl_plan_order(plan_orders_result, symbol="", prefer_first=False)
```

Summary: Pick a stop-loss plan order candidate from a live plan-order payload.

| Param | Required | Type | Default |
|---|---|---|---|
| `plan_orders_result` | `yes` | `dict[str, Any]` | - |
| `symbol` | `no` | `str` | `""` |
| `prefer_first` | `no` | `bool` | `false` |

Returns: `PlanOrderSelection`

---

### `trade.helpers.select_contract_position`

```python
trade.helpers.select_contract_position(current_position_result, symbol, hold_side="", prefer_first=False)
```

Summary: Pick a contract position candidate from a live current-position payload.
Raises when the account is flat for the requested symbol or when multiple
positions match without a tiebreaker. Do not use `.found`; `PositionSelection`
does not expose that field. For first live tick / empty account checks, prefer
`trade.helpers.find_contract_position(...)` or `contract_position_records(...)`.

| Param | Required | Type | Default |
|---|---|---|---|
| `current_position_result` | `yes` | `dict[str, Any]` | - |
| `symbol` | `yes` | `str` | - |
| `hold_side` | `no` | `str` | `""` |
| `prefer_first` | `no` | `bool` | `false` |

Returns: `PositionSelection`

`PositionSelection` exposes only:

- `symbol`
- `hold_side`
- `size`
- `leverage`
- `candidate_count`
- `raw`

Do not access convenience fields such as `.open_price`, `.entry_price`,
`.avg_price`, or `.average_open_price`; they are not part of the helper return
contract. If live logic needs an exchange-specific entry/open price, read it
from `selection.raw` with explicit fallback keys, or use
`contract_position_records(...)` and parse the normalized position dictionaries.

---

### `trade.helpers.find_contract_position`

```python
trade.helpers.find_contract_position(current_position_result, symbol, hold_side="", prefer_first=False)
```

Summary: Return a matching open contract position, or `None` when the account is
flat for the requested symbol. Still raises on ambiguous multiple matches unless
`hold_side` is specific or `prefer_first=True` is intentional.

| Param | Required | Type | Default |
|---|---|---|---|
| `current_position_result` | `yes` | `Any` | - |
| `symbol` | `yes` | `str` | - |
| `hold_side` | `no` | `str` | `""` |
| `prefer_first` | `no` | `bool` | `false` |

Returns: `PositionSelection | None`

When a position is found, the returned `PositionSelection` has the same field
contract as `select_contract_position(...)`: `symbol`, `hold_side`, `size`,
`leverage`, `candidate_count`, and `raw` only. Do not access `.open_price`,
`.entry_price`, `.avg_price`, or `.average_open_price`; parse
exchange-specific price fields from `.raw` instead.

---

### `trade.helpers.contract_position_records`

```python
trade.helpers.contract_position_records(current_position_result, symbol="")
```

Summary: Normalize varied live `current_position(...)` response shapes into a
list of position dictionaries, optionally filtered by symbol.

| Param | Required | Type | Default |
|---|---|---|---|
| `current_position_result` | `yes` | `Any` | - |
| `symbol` | `no` | `str` | `""` |

Returns: `list[dict[str, Any]]`

---

### `trade.helpers.count_open_contract_positions`

```python
trade.helpers.count_open_contract_positions(current_position_result, symbol="")
```

Summary: Count non-zero contract positions from a live `current_position(...)`
payload. Handles direct list payloads and nested `data.list` / `positions`
payloads.

| Param | Required | Type | Default |
|---|---|---|---|
| `current_position_result` | `yes` | `Any` | - |
| `symbol` | `no` | `str` | `""` |

Returns: `int`

---

### `trade.helpers.contract_open_symbols`

```python
trade.helpers.contract_open_symbols(current_position_result)
```

Summary: Return sorted unique symbols that have a non-zero contract position.

| Param | Required | Type | Default |
|---|---|---|---|
| `current_position_result` | `yes` | `Any` | - |

Returns: `list[str]`

---

### `trade.helpers.find_spot_order`

```python
trade.helpers.find_spot_order(pending_orders_result, order_id)
```

Summary: Locate a spot order by exact ``order_id`` (bypasses multi-candidate raise).

| Param | Required | Type | Default |
|---|---|---|---|
| `pending_orders_result` | `yes` | `dict[str, Any]` | - |
| `order_id` | `yes` | `str` | - |

Returns: `OrderSelection`

---

### `trade.helpers.find_contract_order`

```python
trade.helpers.find_contract_order(pending_orders_result, order_id)
```

Summary: Locate a contract order by exact ``order_id`` (bypasses multi-candidate raise).

| Param | Required | Type | Default |
|---|---|---|---|
| `pending_orders_result` | `yes` | `dict[str, Any]` | - |
| `order_id` | `yes` | `str` | - |

Returns: `OrderSelection`

---
