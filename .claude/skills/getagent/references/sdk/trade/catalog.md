# Trade Reference Catalog

This catalog is the self-contained authoring index for `getagent.trade`.
Use it instead of reading the vendored `trade_sdk` implementation directly.

## Read order

1. Start with [`patterns.md`](patterns.md) for safe end-to-end flows.
2. Use the namespace files below for exact method signatures.
3. Always call `trade.is_success(result)` after mutations or live queries
   that return envelopes.

## Namespace index

| Namespace | File | Methods | Use for |
|---|---|---:|---|
| `trade.account` | [account.md](account.md) | 4 | Account queries and internal balance transfers. |
| `trade.market` | [market.md](market.md) | 1 | Market capability checks before order placement. |
| `trade.spot` | [spot.md](spot.md) | 8 | Spot query, place, cancel, and modify flows. |
| `trade.contract` | [contract.md](contract.md) | 15 | USDT futures query, leverage, order, TP/SL, and close flows. |
| `trade.grid` | [grid.md](grid.md) | 8 | Grid validation, lifecycle mutations, and bot/order details for Spot plus USDT contracts. |
| `trade.helpers` | [helpers.md](helpers.md) | 19 | Deterministic symbol, qty, TP/SL, and selector helpers. |

## Contract notes

- Playbook code must import `getagent.trade`, not `trade_sdk`.
- Runner-managed identity parameters are hidden from author-facing
  examples and should not be hardcoded.
- For budget-based orders, use `trade.helpers.compute_qty(...)` instead
  of mental math.
- For contract opens, keep one `leverage` variable across qty sizing,
  TP/SL planning, and the final open call.
- For live position checks, `select_contract_position(...)` raises when the
  account is flat and does not expose `.found`. Use
  `find_contract_position(...)` or `contract_position_records(...)` for normal
  empty-account branches.
- Grid mutations must run inside
  `runtime.execute_strategy_bot_action(..., execute=...)`. The `shutdown`
  lifecycle action maps to `trade.grid.close_bot(...)`; there is no
  `shutdown_bot` method.
- Grid creation uses scalar `investment_amount` with `investment_coin` and
  `funds_source`, or a list of `coin` / `amount` investment entries. Contract
  creation requires `grid_type: long`, `short`, or `neutral`, plus `leverage`,
  `take_profit`, and `stop_loss`; `funds_source` is fixed to `["funding"]`.
  Neutral routing uses the same public methods with a restricted field set.
  Martingale is not available.
