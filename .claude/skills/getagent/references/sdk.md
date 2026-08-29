# GetAgent SDK

This is the stable authoring entrypoint for the Python SDK surface available to
Playbook code. Use this file before writing `src/main.py`.

This folder separates:

- `sdk/` — Python modules imported by Playbook code
- `api/` — HTTP control plane used to upload, publish, run, and manage Playbooks

## Read order

1. Start with `[package-schema.md](package-schema.md)` to understand the package
  contract.
2. Read the relevant SDK section below:
  - market data → `[sdk/data/catalog.md](sdk/data/catalog.md)` (domain index) →
    domain files: `[crypto.md](sdk/data/crypto.md)`, `[equity.md](sdk/data/equity.md)`,
    `[economy.md](sdk/data/economy.md)`, `[derivatives.md](sdk/data/derivatives.md)`,
    `[etf.md](sdk/data/etf.md)`, `[fixedincome.md](sdk/data/fixedincome.md)`,
    `[currency.md](sdk/data/currency.md)`, `[commodity.md](sdk/data/commodity.md)`,
    `[sentiment.md](sdk/data/sentiment.md)`, `[index.md](sdk/data/index.md)`,
    `[news.md](sdk/data/news.md)`, `[regulators.md](sdk/data/regulators.md)`,
    `[uscongress.md](sdk/data/uscongress.md)`, `[arxiv.md](sdk/data/arxiv.md)`,
    `[web_search.md](sdk/data/web_search.md)`, `[wikipedia.md](sdk/data/wikipedia.md)`,
    `[famafrench.md](sdk/data/famafrench.md)`, `[imf_utils.md](sdk/data/imf_utils.md)`,
    `[coverage.md](sdk/data/coverage.md)`
    - replay / charting → `[sdk/backtest/catalog.md](sdk/backtest/catalog.md)`
  - trading → `[sdk/trade/patterns.md](sdk/trade/patterns.md)`; Grid bot
    lifecycle → `[strategy-bot-orchestration.md](strategy-bot-orchestration.md)`
    → `[sdk/trade/grid.md](sdk/trade/grid.md)`
  - runtime protocol / signal output → `[sdk/runtime/catalog.md](sdk/runtime/catalog.md)`
  - bounded LLM/live-only logic → `[sdk/llm/catalog.md](sdk/llm/catalog.md)`
3. Read `[backtest-engine.md](backtest-engine.md)` for replay and metrics rules.
4. Read `[sandbox-runtime.md](sandbox-runtime.md)` for execution limits and
  blocked imports.

## Quick start

```python
from getagent import backtest, data, runtime

# kline drops the currently-forming candle by default (closed_only=True).
bars = data.crypto.futures.kline(symbol="BTCUSDT", interval="1h", exchange="binance")
taker_volume = data.crypto.futures.taker_volume(symbol="BTCUSDT", interval="1h")
replay_frame = backtest.build_feature_frame(
    bars,
    base_datetime_index="date",
    features=[
        backtest.FeatureSource(
            data=taker_volume,
            datetime_index="timestamp",
            include_columns=("buy_vol", "sell_vol"),
            rename_columns={
                "buy_vol": "taker_buy_volume",
                "sell_vol": "taker_sell_volume",
            },
        )
    ],
)
result = backtest.run(
    ohlcv_data={"BTCUSDT.BINANCE": replay_frame},
    spec=runtime.backtest_spec,
)
summary = result.summary
# Author code emits raw account-level numbers; the platform rewrites
# total_return_pct / max_drawdown_pct to per-strategy basis
# (net_pnl / margin_budget) before persisting them.
runtime.emit_signal(
    action="long" if float(summary.get("net_pnl", 0) or 0) > 0 else "hold",
    symbol="BTCUSDT",
    confidence=result.win_rate,
    metrics={
        "total_return_pct": result.total_return_pct,
        "net_pnl": float(summary.get("net_pnl", 0) or 0),
        "starting_balance": summary.get("starting_balance"),
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown_pct": result.max_drawdown_pct,
        "win_rate": result.win_rate,
        "total_trades": result.total_trades,
        "profit_factor": result.profit_factor,
    },
)
```

## Modules

Use this file and the linked catalogs as the SDK source of truth. Do not invent
modules, namespaces, methods, endpoint ids, or keyword arguments by combining
plausible names. If the needed capability is absent from the listed surfaces,
report missing SDK coverage instead of importing a direct client or guessing a
fallback.

Authoritative public surfaces:

- DataSDK: `getagent.data` generated endpoint methods listed under
  `sdk/data/`
- TradeSDK: `getagent.trade` namespaces and helpers listed under `sdk/trade/`
- BacktestSDK: `getagent.backtest` helpers listed in `sdk/backtest/catalog.md`
- RuntimeSDK: `getagent.runtime` context and signal helpers listed in
  `sdk/runtime/catalog.md`
- LLMSDK: `getagent.llm` bounded `chat` / `complete` surface listed in
  `sdk/llm/catalog.md`

### `getagent.data`

The only supported market data module.

Read order:

1. `[sdk/data/catalog.md](sdk/data/catalog.md)` — full domain index with all
  Playbook-callable `getagent.data` endpoints organised by domain
2. domain files under `[sdk/data/](sdk/data/catalog.md)` — exact signatures,
  defaults, enums, and parameter notes

Hard rules:

- Never import direct clients such as `ccxt`, `httpx`, `requests`,
`yfinance`, or `akshare`
- Convert `OBBject` responses with `data.to_dataframe()`, `data.to_dict()`, or
`data.to_records()`
- When several endpoints need to land in one replay frame, normalize them first
and join them through `backtest.prepare_frame()` / `backtest.build_feature_frame()`
- Treat all generated `getagent.data` endpoints as callable from Playbooks; for
backtests, verify the response fields and time axis match the replay contract
before declaring required fields in `backtest.yaml`

### `getagent.trade`

The managed trading surface. Playbook code must import `getagent.trade`, not
`trade_sdk`.

Read order:

1. `[sdk/trade/patterns.md](sdk/trade/patterns.md)` — safe execution flows
2. `[sdk/trade/catalog.md](sdk/trade/catalog.md)` — namespace index
3. namespace files under `[sdk/trade/](sdk/trade/catalog.md)` — exact method
  signatures and parameters

Hard rules:

- Never hardcode runner-managed identity such as `user_id`, `base_url`, or
`channel`
- Always size quote or margin budgets via `trade.helpers.compute_qty(...)`
- For contract opens, derive TP/SL via `trade.helpers.resolve_contract_tpsl(...)`
- Do not pass percentage override kwargs to `resolve_contract_tpsl(...)`; compute
concrete `tp_trigger_price` / `sl_trigger_price` values first
- For cancel / close / modify flows, follow `PRE-CHECK -> EXECUTE -> POST-CHECK`
- Always check envelopes with `trade.is_success(result)`
- Grid Playbooks use `trade.grid` and route each mutation through
  `runtime.execute_strategy_bot_action(...)`; read the orchestration contract
  before authoring Grid lifecycle code, then read
  `[sdk/trade/grid.md](sdk/trade/grid.md)` for exact Spot, directional-contract,
  and neutral-contract parameters

### `getagent.backtest`

Backtest and charting helpers for replayable strategies.

Read `[sdk/backtest/catalog.md](sdk/backtest/catalog.md)` for the concrete
author-facing API surface, result shape, and basic examples.

- `backtest.run(...)`
- `backtest.prepare_frame(...)`
- `backtest.FeatureSource(...)`
- `backtest.build_feature_frame(...)`
- `backtest.generate_chart(...)`

Read `[backtest-engine.md](backtest-engine.md)` for Nautilus spec shape, replay
assumptions, and diagnostics.

Extra replay columns declared in `backtest.yaml` are preserved and can be read
through strategy feature-frame injection. Use the feature-frame helpers above to
align arbitrary `getagent.data` endpoints onto your base bar series before
calling `backtest.run(...)`; see the backtest docs above.

### `getagent.runtime`

Managed runtime protocol for Playbooks.

Read `[sdk/runtime/catalog.md](sdk/runtime/catalog.md)` for the concrete context
surface, signal output contract, and examples.

- context:
  - `runtime.manifest`
  - `runtime.backtest_spec`
  - `runtime.run_id`
- output:
  - `runtime.emit_signal(...)`
  - `runtime.get_emitted_signals()`
  - `runtime.execute_strategy_bot_action(...)` for Strategy Bot lifecycle
  - `runtime.list_strategy_bots(...)` for the current authoritative bot inventory

Use `runtime` for runner-injected context and signal output. Do not expect a
built-in planner, memory loop, or general agent runtime from this module.

### `getagent.llm`

Managed bounded model access for live-only Playbooks.

Read `[sdk/llm/catalog.md](sdk/llm/catalog.md)` for the concrete call surface,
runtime limits, typed errors, and examples.

- Available only when `manifest.yaml` sets `runtime_profile: llm_bounded`
- `llm.is_available()` reflects whether the runner injected bounded LLM access
- `llm.complete(...)` and `llm.chat(...)` run against one runner-managed model
- Call count, prompt size, output tokens, and timeout are all capped by the
deployment runtime
- Tool calls, free model switching, and arbitrary HTTP clients are not exposed

Use `getagent.llm` only for unreplayable/live-only logic. Historical backtest
still requires `runtime_profile: deterministic`.

## See also

- `[sandbox-runtime.md](sandbox-runtime.md)` — runtime contract
- `[package-schema.md](package-schema.md)` — package structure and manifest
- `[api/index.md](api/index.md)` — HTTP control plane, not Python imports
