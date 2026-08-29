# Grid Playbooks

Grid Playbooks are Strategy Bot Orchestration Playbooks specialized for Grid
bots. Read [`strategy-bot-orchestration.md`](strategy-bot-orchestration.md)
first for lifecycle, callback, bot identity, and error semantics. This document
contains only Grid-specific parameters and `getagent.trade.grid` mappings.

## Package contract

Grid packages keep the following manifest values:

```yaml
output_kind: grid
execution_mode: grid
backtest_support: none
follow_trade_supported: false
```

They require a recurring `schedule.cron` and `schedule.tz`. Both
`strategy_config` and `user_config_schema` must contain these seven product
fields:

| Field | Contract |
|---|---|
| `trade_type` | `spot` or `contract` |
| `style` | `balanced` or `aggressive` |
| `leverage` | integer `1..100`; futures only |
| `capital_pct` | number `1..100`; per-symbol cap based on current Funding equity |
| `max_bots` | integer `1..8`; concurrent bot limit |
| `trading_symbols` | exchange-native symbol array |
| `auto_follow_new_coins` | boolean |

Additional strategy settings may live in `strategy_config`, but expose only
product-supported settings in `user_config_schema`. Read editable values from
`runtime.manifest["strategy_config"]`.

## Grid lifecycle mapping

| Public action | Required Trade call inside `execute=` |
|---|---|
| `create` | `trade.grid.create_bot(...)` after `trade.grid.validate(...)` |
| `modify` | `trade.grid.modify_bot(...)`, `modify_grid_interval(...)`, or `add_investment(...)` |
| `watch` | No mutation callback; use `bot_detail(...)` and `list_details(...)` before the action when needed |
| `shutdown` | `trade.grid.close_bot(...)` |

There is no `trade.grid.shutdown_bot`. The orchestration action named
`shutdown` always maps to `trade.grid.close_bot`.

`trade.grid.validate(...)`, `bot_detail(...)`, and `list_details(...)` are
non-mutating calls. All five Grid mutations must run only inside the
`execute=` callback of `runtime.execute_strategy_bot_action(...)`. Grid
Playbooks must not call `trade.spot`, `trade.contract`, or `trade.account`
mutation methods.

See [`sdk/trade/grid.md`](sdk/trade/grid.md) for exact signatures.

## Grid parameters

The Trade SDK uses these names:

- `category`: `spot`, `futures`, or `usdt-futures`; map manifest
  `trade_type: contract` to `category="futures"`, which defaults to
  `usdt-futures`.
- `grid_type`: `long`, `short`, or `neutral`; required for futures. Neutral
  Grid uses the same eight public `trade.grid` methods, selected by
  `grid_type="neutral"` where the method exposes that argument.
- `min_price` / `max_price`: positive decimal strings with
  `min_price < max_price`.
- `grid_num`: positive integer or integer string.
- `grid_order_mode`: `arithmetic` or `geometric`.
- `investment_amount`: positive decimal string plus `investment_coin`, or an
  investment list containing `coin` / `amount` entries. The list form supports
  Spot left-coin plus right-coin funding.
- `investment_coin`: `USDT` for contracts.
- `funds_source`: fixed to `["funding"]` for validation, creation, investment
  modification, and added investment. Do not use UTA as a Grid funding source.
- `slippage`: optional `1%`, `2%`, or `none` for Spot and directional
  contracts; omit it for neutral Grid.
- `auto_transfer_profits`: boolean or `yes` / `no`.
- `take_profit` / `stop_loss`: required for creation and modification.
- `leverage`: required for contract creation, rejected for Spot, and cannot be
  modified.
- `termination_sell`: platform-owned. Spot and directional validate/create
  send `terminationSell=yes`; neutral calls omit it. Playbook input is accepted
  for backward compatibility but ignored. Do not expose it in
  `user_config_schema`.
- `bot_id`: the real ID returned by successful creation, never a symbol.

Call `trade.grid.validate(...)` before creation when a plan is newly computed.
Treat a failed envelope or `data.valid != "true"` as a rejected plan; do not
silently adjust funds, range, or grid count.

Advanced parameters include trigger/termination indicator blocks, leverage,
automatic or reserved margin, moving Grid controls, Spot `hodl_mode`, contract
directional `market_open` / `loss_reserve`, and profit auto-transfer. Follow
the exact signatures and conditional rules in
[`sdk/trade/grid.md`](sdk/trade/grid.md). Do not enable Spot `hodl_mode`
together with `auto_transfer_profits`.
Neutral Grid rejects slippage, trigger/termination indicator blocks, moving
Grid controls, reserve-margin fields, `hodl_mode`, `market_open`, and
`loss_reserve`; its modify surface is limited to TP/SL and optional profit
auto-transfer.

## Risk rules

- Enforce `max_bots` against bot IDs, not distinct symbols. One instance may
  manage several bots for the same symbol.
- Read `trade.account.funding_assets(coin="USDT")` once per cycle. Use
  `available + frozen + locked` as the Funding-equity basis for `capital_pct`,
  and never substitute `trade.account.total_value()` or a launch-time config
  snapshot.
- `capital_pct` is a per-symbol aggregate cap, not a fresh allowance for every
  bot. Before each create, sum `occupied_usdt` across every running bot for that
  symbol plus earlier create plans in the current cycle. The new bot may use at
  most the remaining symbol allowance and current Funding `available`,
  whichever is lower. Reduce the in-memory available balance after each
  successful create in the same cycle.
- Parse `data.minInvestment` from `trade.grid.validate(...)`. Do not call
  `create_bot(...)` when the planned amount is below the minimum accepted by
  every permitted Grid count.
- Read occupied funds from `StrategyBotSnapshot.params["occupied_usdt"]`.
  When absent, query `trade.grid.bot_detail(...)` and use its investment fact.
  Missing or invalid funds must stop creation; never assume zero.
- Do not use a symbol as a bot key. Persist the real create result ID when a P0
  package needs cross-run continuity.
- Call `runtime.list_strategy_bots(status="running")` every cycle and reconcile
  local supplemental metadata against those snapshots. A failed list query
  must stop the cycle, and a missing state file is rebuilt only from a
  successful platform response.
- Local `.state/` is not an authoritative bot inventory. Persist it atomically
  immediately after each successful create, modify, or shutdown so later
  failures cannot lose the mutation's supplemental record.
- Before modifying or closing a remembered bot, query
  `trade.grid.bot_detail(bot_id=..., grid_type="neutral")` for a neutral bot
  (omit `grid_type` otherwise). When order state matters, neutral bots require
  `trade.grid.list_details(category=..., bot_id=..., grid_type="neutral")`;
  non-neutral bots may omit `grid_type` and normally omit `category`.
- For every existing bot, derive `category` from that bot's authoritative
  snapshot `params.trade_type` and Grid type from `params.grid_type`. Spot
  snapshots require `grid_type: spot`; contract snapshots require `long`,
  `short`, or `neutral`. Never reuse the instance's current
  `strategy_config.trade_type` after a configuration switch. Missing, invalid,
  or detail-conflicting contract facts must stop the cycle. Do not compare a
  Spot snapshot's synthetic `grid_type: spot` with bot-detail `gridType`, which
  may report `long` for a Spot bot.
- `shutdown` stops the bot through `close_bot`; it does not mean deleting its
  identity or historical results.

## Reason codes and display text

Use stable Grid-specific keys, for example:

- `grid.create.volatility_fit`
- `grid.modify.range_rebalanced`
- `grid.watch.healthy`
- `grid.watch.warning`
- `grid.watch.round_complete`
- `grid.shutdown.risk_limit`

`reason_code` is the machine-readable label. Keep structured facts in `params`.

Optional `reason_text` / `reason_locale` on
`execute_strategy_bot_action(...)` or terminal `emit_decision(watch)` carry
human-readable copy for product display. The SDK forwards them unchanged; it
does not translate or generate prose. Omit both when no display text is needed.

Do not put localized sentences only inside `params`.

## Related docs

- [`strategy-bot-orchestration.md`](strategy-bot-orchestration.md)
- [`package-schema.md`](package-schema.md)
- [`sdk/runtime/catalog.md`](sdk/runtime/catalog.md)
- [`sdk/trade/grid.md`](sdk/trade/grid.md)
