# `getagent.runtime`

Author-facing runtime protocol for Playbooks.

## When to use

Use `getagent.runtime` whenever Playbook code needs runner-injected context or
needs to emit managed signal output back to the platform.

Typical fit:

- read package metadata from `manifest.yaml`
- read the explicit Nautilus replay spec from `backtest.yaml`
- branch between historical and live execution
- access the current run ID
- emit one or more signals in the platform format

`getagent.runtime` is the boundary between strategy code and the managed runner.
It is not a planner, memory system, trading client, or persistence layer.

## Public API

### Context

- `runtime.manifest`
  - lazy mapping backed by `/workspace/manifest.yaml`
  - use for package fields such as symbols, schedule, metadata, and `strategy_config`

- `runtime.backtest_spec`
  - lazy mapping backed by `/workspace/backtest.yaml`
  - only meaningful when `manifest.yaml` sets `backtest_support: full`
  - carries the explicit Nautilus replay spec: `venue`, `instrument` or
    `instruments`, `strategy`, optional `execution`, and optional
    `data_requirements`

- `runtime.run_id`
  - runner-injected identifier for the current execution

- `runtime.list_strategy_bots(status="running") -> list[StrategyBotSnapshot]`
  - lists bots belonging to the current Playbook instance
  - `status` is `running`, `closed`, or `all`
  - snapshots expose `strategy_bot_id`, `kind`, `symbol`, `status`, and
    structured `params`
  - query failure raises; never replace failure with an empty list

- `runtime.evaluation_mode`
  - runner-injected execution mode
  - currently `"historical"` for `POST /api/v1/playbook/run`
  - currently `"live"` for follow/subscription schedule executions

- `runtime.is_historical() -> bool`
  - true when this execution should use historical/backtest semantics

- `runtime.is_live() -> bool`
  - true when this execution should use live market/trading semantics

- `runtime.execution_mode() -> str`
  - returns the injected trading mode (`"follow_trade"` or `"grid"`) or an
    empty string for non-trading packages / missing runtime context

- `runtime.is_follow_trade() -> bool`
  - true when live execution may place orders after emitting the signal

- `runtime.is_actionable_signal(signal_or_action) -> bool`
  - true when the signal action is not `watch`, `hold`, `noop`, `none`, or empty

- `runtime.should_follow_trade(signal_or_action) -> bool`
  - true only for an actionable signal in an authorized live `"follow_trade"`
    execution

- `runtime.emit_signal_or_follow(..., execute_trade=None, *, reason_code=None, reason_text=None, reason_locale=None) -> FollowTradeResult`
  - emits a managed signal and automatically decides whether to call the
    `execute_trade` callback based on `execution_mode` and signal action
  - optional keyword-only `reason_code` / `reason_text` / `reason_locale`
    persist Creator source reasons into follow-trade artifacts for product
    decision logs; omit all three for legacy-compatible calls
  - `emit_signal()` does not accept reason fields and does not write decision
    logs; use `emit_signal_or_follow(action="watch", reason_*=...)` when watch
    rows should appear in the decision log

### Output

- `runtime.emit_signal(action, symbol="", confidence=0.0, metrics=None, meta=None) -> SignalPayload`
- `runtime.get_emitted_signals() -> list[SignalPayload]`

`emit_signal(...)` does three things:

1. returns a typed `SignalPayload`
2. prints one JSON record to stdout
3. appends the record to `/workspace/output/signal.json`

### Progress / Strategy Bot actions

- `runtime.emit_progress(blocks) -> bool`
- `runtime.emit_decision(action, params=None, *, sub_action=None, reason_code=None, reason_text=None, reason_locale=None) -> bool`
- `runtime.execute_strategy_bot_action(action, *, params=None, execute=None, sub_action=None, reason_code=None, reason_text=None, reason_locale=None) -> StrategyBotActionResult`

`emit_progress` is observability-only scheduling output.
`emit_decision` is a low-level observation helper and never executes a Trade
SDK operation. Playbook code must not use it for `create`, `modify`, or
`shutdown`. Optional `reason_text` / `reason_locale` carry a natural-language
source reason for product display; omit both when no AI reason is available.

`execute_strategy_bot_action` is the lifecycle boundary for Strategy Bot
Orchestration Playbooks. It validates the action, executes one supplied Trade
SDK mutation when required, returns the real bot ID, and reports the action
outcome without retrying the mutation. See
[`strategy-bot-orchestration.md`](../../strategy-bot-orchestration.md).

`emit_progress(blocks)` reports one scheduling step using the block protocol
(2026-07-20 revision: three block types, markdown string bodies):

- `blocks` is a list of 1–8 dicts, each `{"type": ..., "ctx": ...}`
- `type` is one of `title` / `subTitle` / `content`
- `ctx` is a non-empty **markdown string**; tabular data goes into a
  `content` block as a markdown table (the legacy `text`/`table` span
  protocol was removed and now raises `ValueError`)
- limits: single serialized block ≤ 4 KB, calls closer than 100 ms apart are
  dropped, at most 200 progress events per run (drops are silent, returns False)

`execute_strategy_bot_action(...)` rules:

- `create`, `modify`, and `shutdown` require `execute=` with exactly one
  matching Trade SDK mutation.
- `execute` must be a synchronous callback; async callbacks and awaitable
  return values are not supported.
- `watch` forbids `execute=` and requires `sub_action` equal to `watch.ok`,
  `watch.warn`, or `watch.action`.
- `modify` and `shutdown` require the same real `bot_id` in `params` and the
  Trade call.
- `params` must be JSON-serializable structured data.
- `reason_code` is an optional stable machine-readable key.
- Optional `reason_text` / `reason_locale` carry display copy; the SDK does
  not translate them.
- `watch` with a real `bot_id` must use `execute_strategy_bot_action(...)`.
  `emit_decision(action="watch")` is allowed only for a terminal round patrol
  when the cycle had no mutation and no bot-scoped watch.
- The result exposes `action_id`, `action`, `strategy_bot_kind`,
  `strategy_bot_id`, `executed`, `succeeded`, `operation_result`, and
  `decision_emitted`.
- Strategy Bot orchestrators must call `list_strategy_bots(status="running")`
  before planning mutations. Local state may supplement but never replace this
  inventory.

## Historical / Live Split

Do not put `run_mode` in `manifest.yaml`. A package is immutable and should run
both modes from the same uploaded version. Branch on `runtime.evaluation_mode` in
`src/main.py`:

```python
from getagent import runtime
from . import main_backtest, main_live

if runtime.is_historical():
    main_backtest.run()
elif runtime.is_live():
    main_live.run()
else:
    raise ValueError(f"unsupported evaluation_mode={runtime.evaluation_mode!r}")
```

Keep shared feature engineering in a neutral module like `features.py`.
`main_backtest.py` must not import live trading code or call `getagent.trade`.
`main_live.py` may call `getagent.trade` and can place real orders when the
current subscription is in follow-trade mode.

Live code must separate decision output from trade execution:

```python
from getagent import runtime, trade


def run() -> None:
    decision = build_live_decision()

    runtime.emit_signal_or_follow(
        action=decision.action,
        symbol=decision.symbol,
        confidence=decision.confidence,
        metrics=decision.metrics,
        meta=decision.meta,
        execute_trade=lambda: execute_trade(decision),
    )
```

Non-trading packages should use `runtime.emit_signal(...)`. Trading packages
must put mutations inside the callback passed to
`runtime.emit_signal_or_follow(...)`; the SDK still fails closed if live trade
permission is absent.

## Output Contract

Use `runtime.emit_signal(...)` for strategy conclusions that should be persisted
as managed Playbook output.

Arguments:

- `action` — signal action such as `long`, `short`, `close`, `hold`, or `watch`
- `symbol` — target instrument, usually something like `BTCUSDT`
- `confidence` — float confidence score
- `metrics` — structured numeric summary
- `meta` — extra non-core context for downstream inspection

The runner collects `/workspace/output/signal.json` automatically. Do not write
that file yourself unless you are debugging the runtime contract.

If a live run emits an actionable trade signal and then emits a `watch` summary,
the platform treats the last actionable signal as primary. Use `watch` for final
summary context, not as a replacement for `long`, `short`, or `close`.

## Example

```python
from getagent import runtime

primary_symbol = runtime.manifest.get("trading_symbols", ["BTCUSDT"])[0]
config = runtime.manifest.get("strategy_config", {})

if runtime.is_historical():
    runtime.emit_signal(
        action="watch",
        symbol=primary_symbol,
        confidence=0.5,
        metrics={"mode": "historical", "lookback_hours": config.get("lookback_hours", 360)},
        meta={"run_id": runtime.run_id},
    )
else:
    runtime.emit_signal(
        action="long",
        symbol=primary_symbol,
        confidence=0.72,
        metrics={"mode": "live"},
        meta={"run_id": runtime.run_id},
    )
```

## Hard Rules

- Treat `runtime.manifest` as the source of truth for package contract fields.
- Read every user-editable strategy parameter from
  `runtime.manifest.get("strategy_config", {})`; do not hardcode values that
  appear in `user_config_schema`.
- Treat `runtime.backtest_spec` as optional; do not assume it exists.
- Use `runtime.evaluation_mode` / `runtime.is_historical()` / `runtime.is_live()` for mode routing.
- Prefer `runtime.emit_signal_or_follow(...)` for live follow-trade routing.
- Use `runtime.emit_signal(...)` instead of inventing your own signal schema.
- Emit the signal before placing follow-trade orders. Non-trading packages use
  `emit_signal(...)` and never call trade mutation APIs.
- Do not expect `runtime` to expose trading, data, or LLM clients.
- Do not use `runtime` as a hidden persistence layer beyond emitted signals.

## Related Docs

- [`../../package-schema.md`](../../package-schema.md)
- [`../../sandbox-runtime.md`](../../sandbox-runtime.md)
- [`../../backtest-engine.md`](../../backtest-engine.md)
- [`../../strategy-bot-orchestration.md`](../../strategy-bot-orchestration.md)
- [`../trade/grid.md`](../trade/grid.md)
- [`../llm/catalog.md`](../llm/catalog.md)
