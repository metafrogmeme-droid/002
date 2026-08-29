# `getagent.backtest`

Author-facing replay and charting surface for backtestable Playbooks.

## When to use

Use `getagent.backtest` when the core trading decision can be fairly
reconstructed from historical data and expressed as a NautilusTrader strategy.

Typical fit:

- `runtime_profile: deterministic`
- `backtest_support: full`
- strategy logic implemented as a `nautilus_trader.trading.strategy.Strategy`
  subclass under `src/**`
- historical metrics intended for public evidence

Do not use `getagent.backtest` to justify strategies whose trade decision
depends on open-ended LLM reasoning or unreplayable live context.

## Public API

### Prepare one dataset

- `backtest.prepare_frame(source, datetime_index=None, rename_columns=None) -> pandas.DataFrame`

Behavior:

- accepts `OBBject`, `pandas.DataFrame`, one mapping, or a list of mappings
- normalizes column names to lowercase
- parses the time column into a UTC `DatetimeIndex`

### Describe one feature source

- `backtest.FeatureSource(...)`

Useful fields:

- `data` — one historical dataset returned by `getagent.data` or already prepared locally
- `datetime_index` — time field name when the source is not already indexed
- `rename_columns` — rename raw source fields into replay-field names such as
  `taker_buy_volume`
- `include_columns` — keep only the columns you want to attach to the replay frame
- `prefix` — add a prefix to every attached feature column
- `mode` — `"asof"` for time alignment or `"exact"` for exact index joins
- `join` — `"left"` (default) or `"inner"`
- `direction` / `tolerance` — `merge_asof` controls for time-series joins

### Build one replay frame

- `backtest.build_feature_frame(base, base_datetime_index=None, base_rename_columns=None, features=None) -> pandas.DataFrame`

Behavior:

- starts from a base bar dataset, usually K lines / candles
- aligns arbitrary historical feature datasets onto the base timestamps
- returns one replay-ready DataFrame that still contains core OHLCV plus your
  added feature columns

### Run a backtest

- `backtest.run(ohlcv_data, spec=None) -> BacktestResult`

Parameters:

- `ohlcv_data`
  - dict of `{instrument-key: pandas.DataFrame}`
  - each frame should have a `DatetimeIndex` plus OHLCV columns
  - additional normalized columns are preserved for strategy feature access
  - keys should match the instrument IDs or symbols declared in `backtest.yaml`

- `spec`
  - usually `runtime.backtest_spec`
  - explicit Nautilus backtest spec with:
    - `venue`
    - `instrument` or `instruments`
    - `strategy`
    - optional `execution.start` / `execution.end` bar filters (the replay
      window is the author's choice; omit to replay every fetched bar)
    - optional `data_requirements.required_bar_fields`

### Generate a chart

- `backtest.generate_chart(result, save_dir=None) -> str`

Behavior:

- writes a PNG to `/workspace/output/` by default
- returns the saved path as a string
- returns `""` when chart generation fails

## Result shape

`BacktestResult` exposes normalized account-level summary metrics directly:

- `total_return_pct` (account return, using `backtest.yaml` starting balance)
- `sharpe_ratio`
- `max_drawdown_pct`
- `win_rate`
- `profit_factor`
- `total_trades`
- `fill_count`
- `position_count`
- `summary`
- `raw`

User-facing return % is computed by the platform on a per-strategy basis
(`net_pnl / manifest.strategy_config.margin_budget`). The author should emit
the engine summary as-is; `service.build_run_record` rewrites
`total_return_pct` and `max_drawdown_pct` before storing them, preserving the
account-level numbers as `account_total_return_pct` /
`account_max_drawdown_pct` for analysts. Just remember to declare a positive
`margin_budget` in `manifest.strategy_config` (validation requires it for
`backtest_support: full` and `execution_mode: follow_trade`).

`result.raw` is Nautilus-native output with stable top-level sections:

- `summary` — normalized key metrics
- `stats` — analyzer outputs grouped by returns / general / pnls
- `reports` — account / orders / fills / positions / equity curve
- `config` — the resolved venue, instrument IDs, bar types, and strategy entry

## Example

```python
from getagent import backtest, data, runtime

bars = data.crypto.futures.kline(symbol="BTCUSDT", interval="1h", exchange="binance")
taker_volume = data.crypto.futures.taker_volume(symbol="BTCUSDT", interval="1h")
open_interest = data.crypto.futures.open_interest_history(symbol="BTCUSDT", interval="1h")

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
        ),
        backtest.FeatureSource(
            data=open_interest,
            datetime_index="date",
            include_columns=("open_interest",),
        ),
    ],
)

result = backtest.run(
    ohlcv_data={"BTCUSDT.BINANCE": replay_frame},
    spec=runtime.backtest_spec,
)

chart_path = backtest.generate_chart(result)
summary = result.summary
net_pnl = float(summary.get("net_pnl", 0) or 0)

runtime.emit_signal(
    action="long" if net_pnl > 0 else "hold",
    symbol="BTCUSDT",
    confidence=result.win_rate,
    metrics={
        "total_return_pct": result.total_return_pct,
        "net_pnl": net_pnl,
        "starting_balance": summary.get("starting_balance"),
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown_pct": result.max_drawdown_pct,
        "win_rate": result.win_rate,
        "total_trades": result.total_trades,
        "profit_factor": result.profit_factor,
    },
    meta={"chart_path": chart_path},
)
```

## Hard rules

- Use `runtime.backtest_spec` as the default source of replay configuration
- Keep public backtest claims tied to deterministic strategy logic
- Do not pass `provider=...` to `getagent.data` calls; the managed DataSDK
  provider is selected by the platform
- The `backtest.yaml.execution.start` / `execution.end` window is optional and
  entirely the author's choice — the platform never polices it. When you do
  declare one, verify the selected endpoint returns real bars inside it
- Keep `manifest.trading_symbols`, display text, README, `backtest.yaml`
  instruments, data calls, and emitted signal symbols aligned. If you correct a
  typo or replace an unavailable symbol, rename the package/title and explain
  the correction.
- Use exchange-native tradable pairs in package and replay contracts
  (`BTCUSDT`, `RAAPLUSDT`, `AAPLUSDT`), not CCXT unified symbols such as
  `BTC/USDT:USDT`.
- Before declaring `backtest_support: full`, probe the managed kline path for
  every declared symbol with `exchange="bitget"` and the intended interval and
  lookback/window. A tradable Bitget symbol is official-backtest eligible only
  when the probe returns valid JSON rows; 204/empty body and 4xx responses are
  not replay evidence.
- Declare enriched replay column dependencies in
  `backtest.yaml -> data_requirements.required_bar_fields`
- Every required replay field must be created and referenced in `src/**`; remove
  the declaration if the strategy no longer reads that feature
- Use `prepare_frame()` / `build_feature_frame()` to standardize multi-endpoint
  replay assembly instead of open-coded timestamp joins
- Expect `backtest.run()` to fail fast when declared replay columns are missing
  or all-null in the effective execution window
- Before making a backtest claim, verify the replay frame covers the claimed
  window and contains every decision feature. Record row count, first/last
  timestamp, and returned fields during probing.
- Do not silently replace missing decision features with constants such as
  `0`, `0.5`, or `False`. Missing `taker_buy_ratio`, open interest, funding, or
  liquidation data should either fail the run or be reported as degraded, not
  hidden inside the performance metrics.
- Strategy classes may import `nautilus_trader`; Playbook code must not import
  legacy backtest engines directly
- Do not use `backtest.run()` as fake evidence for `llm_bounded` strategies
- Treat `result.total_trades == 0` as an honest no-trade outcome for the
  selected window; do not loosen strategy thresholds just to force trades
- Prefer `generate_chart(result)` over writing ad hoc chart files yourself
- Do not emit `metrics=result.summary` directly for user-visible backtest
  results when the strategy has a configured budget. Convert `net_pnl` to
  strategy-budget return and keep account return under `account_return_pct`.

## Related docs

- [`../../backtest-engine.md`](../../backtest-engine.md)
- [`../../package-schema.md`](../../package-schema.md)
- [`../../sandbox-runtime.md`](../../sandbox-runtime.md)
- [`../runtime/catalog.md`](../runtime/catalog.md)
