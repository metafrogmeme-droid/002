# Backtest Engine

## Contents

- [Basic Usage](#basic-usage)
- [Backtest Eligibility](#backtest-eligibility)
- [Spec Shape](#spec-shape)
- [Execution Model](#execution-model)
- [BacktestResult](#backtestresult)
- [Multi-Instrument Replays](#multi-instrument-replays)
- [Zero-Trade Diagnostics](#zero-trade-diagnostics)
- [Chart Generation](#chart-generation)

## Basic Usage

```python
from getagent import backtest, data, runtime

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
chart_path = backtest.generate_chart(result)
```

## Backtest Eligibility

Not every Playbook can produce a fair historical backtest.

### Use the engine when:

- the core trading decision is deterministic
- the decision can be reconstructed from historical data
- strategy logic can be expressed as a NautilusTrader `Strategy` subclass
- any LLM usage is outside the trade decision path
- the target tradable symbol has enough historical OHLCV coverage, regardless
  of whether the asset is crypto, RWA stock, or RWA metal
- the managed kline probe for every declared symbol returns HTTP 200 with valid
  JSON and non-empty rows for the intended `exchange="bitget"`, interval, and
  replay lookback/window

### Do not use the engine as public evidence when:

- open-ended LLM reasoning decides whether to trade
- the strategy depends on live chat, memory, or search context
- the decision cannot be reconstructed at the original point in time
- any declared symbol returns 204/empty body, 4xx, or no rows from the managed
  replay data path for the intended window

Typical outcome:

- `backtest_support: full` -> use `backtest.run()` and publish historical metrics
- `backtest_support: none` -> use paper or live evidence instead

## Spec Shape

The managed engine expects an explicit Nautilus replay spec from `backtest.yaml`,
usually read through `runtime.backtest_spec`.

`StrategyConfig` fields must not use mutable class defaults such as `=[]`,
`={}`, `=set()`, `=list()`, `=dict()`, or `=set()`. Use tuples, `None`, scalar
defaults, or a supported default-factory pattern instead; Nautilus/Pydantic
rejects mutable collection defaults at import time.

Required sections:

- `venue`
  - `name`
  - `account_type`
  - `oms_type`
  - `starting_balances`
- `instrument` or `instruments`
  - `id`
  - `kind`
  - `raw_symbol` or `symbol`
  - `base_currency`
  - `quote_currency`
  - `price_precision`
  - `size_precision`
  - `price_increment`
  - `size_increment`
  - `bar_type`
  - perpetual instruments also need `settlement_currency`
- `strategy`
  - `module`
  - `class`
  - optional `config_class`
  - optional `config`
- `execution` (optional)
  - optional `start` / `end` — bar filters applied when present; omit them to
    replay every bar you fetched. The window is the author's choice and the
    platform never polices its presence, length, or recency.

## Execution Model

The managed flow is:

1. author code fetches historical bars through `getagent.data`
2. `backtest.run()` normalizes each DataFrame, preserves extra replay columns,
  and derives OHLCV bars for Nautilus
3. the engine builds Nautilus venue + instrument definitions from `backtest.yaml`
4. `BarDataWrangler` converts DataFrames into Nautilus bars
5. the author's `Strategy` subclass is imported from `src/**`
6. Nautilus `BacktestEngine` runs the replay
7. the platform normalizes summary metrics and preserves the deeper reports

For single-instrument strategies the runner auto-injects these config defaults
when they are absent:

- `instrument_id`
- `bar_type`
- `instrument_ids`
- `bar_types`

That means the common author pattern is:

- define `DemoStrategyConfig(StrategyConfig)`
- define `DemoStrategy(Strategy)`
- let `backtest.yaml` carry the wiring

If `backtest.yaml` declares `data_requirements.required_bar_fields`, the engine
keeps those normalized columns on the replay DataFrames and injects the per-
instrument frames into the strategy through `set_feature_frames(...)` or
`strategy.feature_frames` when either hook exists.

## BacktestResult


| Property                  | Type  | Description                  |
| ------------------------- | ----- | ---------------------------- |
| `result.total_return_pct` | float | Account return % using the replay starting balance |
| `result.sharpe_ratio`     | float | Sharpe ratio                 |
| `result.max_drawdown_pct` | float | Max drawdown %               |
| `result.win_rate`         | float | Win rate fraction (0.0-1.0)  |
| `result.total_trades`     | int   | Filled execution count when fills are available |
| `result.fill_count`       | int   | Filled execution count       |
| `result.position_count`   | int   | Nautilus position row count  |
| `result.profit_factor`    | float | Profit factor                |
| `result.summary`          | dict  | Stable normalized account-level summary |
| `result.raw`              | dict  | Full Nautilus-derived output |

`result.summary` carries account-level numbers because the engine denominator
is `backtest.yaml.venue.starting_balances`. **You do not need to convert them
yourself.** The platform rewrites every persisted run / package metrics block
to the per-strategy basis (`net_pnl / manifest.strategy_config.margin_budget`)
before storing or surfacing them on cards / Telegram pushes / run details. The
account-level numbers are preserved alongside as `account_total_return_pct`
and `account_max_drawdown_pct` for analysts.

This is why `manifest.strategy_config.margin_budget` is **required** for
`backtest_support: full` and `execution_mode: follow_trade` Playbooks — it is
the declared denominator. Validation rejects manifests that omit it or set it
to zero. If you opt out of the rewrite by hand-writing strategy-level metrics,
also set `metrics_basis: "strategy"` in your emitted `metrics_output`; the
platform leaves those untouched.

`result.raw` keeps these top-level sections:

- `summary`
- `stats`
- `reports`
- `config`

## Multi-Instrument Replays

Use `instruments:` when the strategy needs multiple instrument definitions.

Provide one OHLCV DataFrame per declared instrument ID or symbol:

```python
result = backtest.run(
    ohlcv_data={
        "BTCUSDT.BINANCE": btc_df,
        "ETHUSDT.BINANCE": eth_df,
    },
    spec=runtime.backtest_spec,
)
```

The engine does not synthesize cross-instrument logic for you. Multi-instrument
behavior belongs in the author's Nautilus strategy code.

## Enriched Replay Columns

Core OHLCV is still the minimum contract for every replay frame. Extra columns
such as `quote_volume`, `trade_count`, or `taker_buy_volume` can ride along in
the same DataFrame.

The standard author pattern is:

1. fetch the base bar series from `getagent.data`
2. fetch any auxiliary datasets from any supported `getagent.data` endpoints
3. aggregate finer-grain feeds yourself when needed (for example raw trades -> hourly features)
4. use `backtest.build_feature_frame(...)` to align those datasets onto the base bars
5. declare the resulting feature column names in `backtest.yaml`

Declare them explicitly in `backtest.yaml`:

```yaml
data_requirements:
  required_bar_fields:
    - quote_volume
    - trade_count
```

Then read them from the injected feature frames in your strategy:

```python
class PriceVolStrategy(Strategy):
    def set_feature_frames(self, feature_frames):
        self.feature_frames = feature_frames

    def on_start(self):
        primary = self.feature_frames["BTCUSDT.BINANCE"]
        latest_quote_volume = primary.iloc[-1]["quote_volume"]
        # ...
```

For example, if author code builds a replay frame with
`taker_buy_volume`, `taker_sell_volume`, and `open_interest`, those exact
normalized names should appear under `required_bar_fields`.

If a field declared in `data_requirements.required_bar_fields` is missing from a
replay DataFrame, or exists but is entirely null inside the effective execution
window, `backtest.run()` fails before Nautilus starts.

## Zero-Trade Diagnostics

If `result.total_trades == 0`, common causes are:

1. bars were filtered out by `execution.start` / `execution.end`
2. the strategy never subscribed to the declared `bar_type`
3. instrument IDs in strategy config do not match the spec
4. order sizing is invalid for the declared increment / lot size

Inspect:

- `result.raw["config"]`
- `result.raw["reports"]["orders"]`
- `result.raw["reports"]["fills"]`
- `result.raw["reports"]["positions"]`

## Backtest Output Contract

When `main_backtest.py` writes output files, the platform Runner collects them
and merges them into the run record. Getting this wrong causes publish failures
("missing publishable real equity curve") or incorrect metrics display.

### Required Output Files

| File | Purpose | Size |
| ---- | ------- | ---- |
| `output/backtest_report.json` | Nautilus raw result (summary, stats, reports, config) | Keep small — omit equity curve from JSON |
| `output/equity_curve.csv` | Lightweight curve the Runner always reads reliably | ~100 bytes/point |

The Runner reads **both** files. If `backtest_report.json` is too large (common
with 3+ month runs), `proxy.read_file()` may silently fail. The CSV is a
guaranteed fallback.

### Equity Curve Metadata

The platform records actual curve metadata such as point count and the first /
last curve timestamp. It does not require a fixed density.

```python
expected_points = ceil((execution.end - execution.start).total_seconds() / interval_seconds)
```

That value may still appear as diagnostic metadata in older runs, but it is not
a publish gate. Do not fabricate forward-filled points just to make the curve
look dense.

### Metrics Merge Priority (Critical)

The Runner builds `metrics_output` with this merge order:

```python
merged_metrics = dict(backtest_report)           # report is BASE
for key, value in signal_metrics.items():
    merged_metrics.setdefault(key, value)         # fill report gaps from signal metrics
```

**`setdefault` does not override existing keys** — even if they are `null`.

`result.raw` from the engine has `result.update(summary)` applied, which
flattens `net_pnl`, `total_return_pct`, `starting_balance` etc. to the top
level. These engine-level values may be `null` or denominated by
`venue.starting_balances` (account basis) rather than `margin_budget` (strategy
basis).

**You must override these top-level keys before writing the JSON:**

```python
# Compute correct absolute USDT values
net_pnl = ending_total - initial_capital
strategy_return_pct = net_pnl / initial_capital * 100.0

# Override engine values so backend merge picks up correct numbers
raw["net_pnl"] = round(net_pnl, 4)
raw["total_return_pct"] = round(strategy_return_pct, 4)
raw["starting_balance"] = initial_capital

# Write files
(out_dir / "backtest_report.json").write_text(json.dumps(raw, default=str))
```

Without this, the platform's `_apply_strategy_basis_metrics` will compute
`total_return_pct = net_pnl / margin_budget * 100` using the engine's
potentially wrong `net_pnl`, producing incorrect display values.

### Equity Curve CSV Format

```csv
timestamp,value,nav
2026-03-01T00:00:00,1000.0,1.0
2026-03-01T01:00:00,1002.5,1.0025
...
```

Do **not** embed the equity curve in `backtest_report.json` (`reports.equity_curve`).
The Runner reads `equity_curve.csv` independently and attaches it to the report
via `_attach_equity_curve_to_report`. Keeping the curve out of the JSON reduces
file size and prevents read failures for long backtest windows.

### Correct Execution Order

```
1. Run backtest.run()
2. Build an equity curve from real replay/account values — never fabricate
   or forward-fill points
3. Compute net_pnl from account report
4. Override raw top-level metrics
5. Write backtest_report.json (without equity curve)
6. Write equity_curve.csv
7. runtime.emit_signal() with correct metrics
```

### `csv` Module Is Blocked

The sandbox blocks the `csv` stdlib module. Write CSV manually:

```python
csv_lines = ["timestamp,value,nav"]
for point in equity_curve:
    csv_lines.append(f"{point.get('timestamp','')},{point.get('value','')},{point.get('nav','')}")
(out_dir / "equity_curve.csv").write_text("\n".join(csv_lines) + "\n", encoding="utf-8")
```

## Chart Generation

```python
chart_path = backtest.generate_chart(result)
```

The managed chart renderer writes a PNG summary to `/workspace/output/`.

Current chart includes:

- equity curve when available
- normalized metrics when no curve is available
- key summary values
