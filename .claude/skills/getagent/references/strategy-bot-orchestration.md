# Strategy Bot Orchestration Playbooks

A Strategy Bot Orchestration Playbook decides when to create, modify, observe,
or stop managed Strategy Bots. One Playbook instance may manage several bots,
including several bots for the same symbol. Bot identity is always the real
`strategy_bot_id` returned by execution; a symbol is never a bot identity.

Grid is the first supported bot kind. Grid packages continue to declare
`output_kind: grid` and `execution_mode: grid`.

## Lifecycle API

Use the single public mutation boundary:

```python
result = runtime.execute_strategy_bot_action(
    action="create",
    params={
        "symbol": "BTCUSDT",
        "trade_type": "contract",
        "grid_type": "long",
        "price_range": ["60000", "70000"],
        "grid_count": 20,
        "occupied_usdt": "500",
        "leverage": 5,
    },
    execute=lambda: trade.grid.create_bot(
        category="futures",
        symbol="BTCUSDT",
        grid_type="long",
        min_price="60000",
        max_price="70000",
        grid_num=20,
        grid_order_mode="arithmetic",
        investment_amount="500",
        investment_coin="USDT",
        funds_source=["funding"],
        slippage="none",
        auto_transfer_profits=True,
        leverage=5,
        take_profit="75000",
        stop_loss="55000",
        trigger_condition="instant",
    ),
    reason_code="grid.create.volatility_fit",
    reason_text="Open BTCUSDT long grid after volatility filter passed.",
    reason_locale="en",
)
bot_id = result.strategy_bot_id
```

Public signature:

```python
runtime.execute_strategy_bot_action(
    action,                 # create | modify | watch | shutdown
    *,
    params=None,
    execute=None,
    sub_action=None,        # watch.ok | watch.warn | watch.action
    reason_code=None,
    reason_text=None,       # optional natural-language summary for product UI
    reason_locale=None,     # optional language tag, e.g. "zh" or "en"; <=16 chars
)
```

Optional reason fields:

- `reason_code`: stable machine-readable key for analytics and i18n lookup.
- `reason_text`: optional human-readable source text for product display. The
  SDK does not translate it; pass the final language you want shown, or omit
  it when no prose is needed.
- `reason_locale`: optional language tag for `reason_text` (for example `zh`,
  `en`). Omit when `reason_text` is omitted.

Keep structured facts in `params`. Do not put localized prose only in
`params`; use `reason_text` / `reason_locale` for display copy.

The returned `StrategyBotActionResult` exposes:

- `action_id`: stable identity for this lifecycle action
- `action`
- `strategy_bot_kind`
- `strategy_bot_id`: the real bot ID when available
- `executed`
- `succeeded`
- `operation_result`
- `decision_emitted`

Current bot discovery is a separate public read:

```python
running_bots = runtime.list_strategy_bots(status="running")
```

`status` accepts `running`, `closed`, or `all`. Each
`StrategyBotSnapshot` exposes `strategy_bot_id`, `kind`, `symbol`, `status`,
and structured `params`. For Grid bots, `params` includes the creation-time
`trade_type` and `grid_type`; it may also include `occupied_usdt`.

## Action contract

| Action | `execute` | `sub_action` | Bot ID |
|---|---|---|---|
| `create` | Required; exactly one matching bot mutation | Forbidden | Extracted from successful operation result |
| `modify` | Required; exactly one matching bot mutation | Forbidden | Required in `params` and Trade call |
| `watch` | Forbidden | Required: `watch.ok`, `watch.warn`, or `watch.action` | Include when observing a specific bot |
| `shutdown` | Required; exactly one matching bot mutation | Forbidden | Required in `params` and Trade call |

The callback may mutate only the namespace matching the package bot kind. A
Grid callback therefore calls one `trade.grid` mutation. It cannot call Spot,
Contract, Account, or multiple unrelated mutations.
`execute` must be a synchronous callback; async functions and callbacks that
return awaitables are not supported.

`runtime.emit_decision(...)` remains a low-level observation helper. It does
not execute a Trade SDK operation and must never be used by Playbook code to
pretend that `create`, `modify`, or `shutdown` happened.

Use `execute_strategy_bot_action(...)` for every mutation and for bot-scoped
`watch` actions that target a real `bot_id`.

The only allowed `emit_decision(...)` case in Grid Playbooks is a terminal
round patrol when the cycle performs **no** create/modify/shutdown and there is
**no** bot-scoped watch to report. In that case emit one `action="watch"` with a
valid `sub_action` and cycle-level `params` (for example scan counts). Do not use
`emit_decision` as a shortcut for bot health checks; those must go through the
wrapper when a real bot is being observed.

## Identity and multi-bot scheduling

- Store and compare bots by real bot ID.
- Keep `symbol` as an attribute used for market selection, never as a map key
  that implies bot uniqueness.
- A successful `create` may add a new bot even when another bot already uses
  the same symbol, subject to the package's capital and bot-count rules.
- `modify`, `watch`, and `shutdown` must target one resolvable real bot ID.
- Resolve each existing Grid bot's Trade SDK `category` from its authoritative
  snapshot `params.trade_type`, and resolve its Grid type from the
  creation-time `params.grid_type`, not the instance's current configuration.
  Spot snapshots use `grid_type: spot`; contract snapshots use `long`, `short`,
  or `neutral`. Missing or invalid values must stop the cycle. If bot detail
  exposes a contract fact, it must agree with the snapshot. Do not compare a
  Spot snapshot's synthetic Grid type with bot-detail `gridType`, which may be
  reported as `long` for a Spot bot.
- At the start of every cycle, call
  `runtime.list_strategy_bots(status="running")` and use those snapshots as the
  authoritative current inventory. Query failures must stop the cycle before
  creation; never fall back to an empty list.
- Local `.state/` may keep supplemental metadata only. Reconcile it against the
  platform snapshots every cycle. A missing state file is rebuilt from the
  successful platform response, not interpreted independently as “no bots.”
- After every successful mutation, atomically persist supplemental state
  immediately, before starting another action. This preserves a newly returned
  bot ID even if a later action fails.

## Execution and failure semantics

The runtime validates the action, runs the callback once, captures the matching
Trade SDK result, normalizes the bot ID, records the action result, and reports
the decision.

- Validation errors fail before the callback.
- Trade mutations are not retried automatically.
- A Trade failure is surfaced as a failed action and re-raised; do not mark the
  bot successful in package state.
- If the Trade call succeeds but decision reporting fails, the Trade mutation
  is not repeated. `decision_emitted` reports the reporting outcome, while the
  stable `action_id` and operation result allow idempotent reconciliation.
- Reusing a stable action result must never cause another Trade mutation.

These guarantees are why package code must not split execution and decision
reporting into separate calls.

## Minimal watch

Bot-scoped watch:

```python
runtime.execute_strategy_bot_action(
    action="watch",
    params={"bot_id": bot_id, "symbol": symbol, "check_items": ["range", "pnl"]},
    sub_action="watch.ok",
    reason_code="grid.watch.healthy",
    reason_text="Grid range and PnL are within policy.",
    reason_locale="en",
)
```

Terminal patrol when the round had no mutation and no bot-scoped watch:

```python
runtime.emit_decision(
    action="watch",
    params={
        "trade_type": trade_type,
        "candidates_scanned": scanned_count,
        "actions_executed": 0,
        "patrol": True,
    },
    sub_action="watch.ok",
    reason_code="grid.watch.round_complete",
    reason_text="Patrol complete; no bot actions this round.",
    reason_locale="en",
)
```

## Related docs

- [`grid-playbook.md`](grid-playbook.md)
- [`sdk/runtime/catalog.md`](sdk/runtime/catalog.md)
- [`sdk/trade/grid.md`](sdk/trade/grid.md)
