# Playbook Package Schema

## Contents

- [Directory Layout](#directory-layout)
- [manifest.yaml](#manifestyaml)
- [backtest.yaml](#backtestyaml)
- [src/main.py](#srcmainpy)

## Directory Layout

Implemented upload layout:

```text
<package-name>/
├── README.md
├── manifest.yaml
├── src/
│   ├── main.py
│   ├── strategy.py
│   ├── indicators.py
│   ├── risk.py
│   ├── execution.py
│   ├── prompts.py        # optional
│   ├── llm_policy.py     # optional
│   └── agent_tools.py    # optional
└── backtest.yaml         # optional; only for backtest_support: full
```

Design rules:

- **Required:** `README.md`, `manifest.yaml`, `src/main.py`
- **Optional in upload:** extra modules under `src/`, `backtest.yaml`
- **Local-only (must not upload):** `tests/`, `notebooks/`, `research/`, `data/`,
`backtest_results/`, `logs/`, `output/`, virtualenv and cache directories
- **Do not infer strategy class from file layout.** Public behavior belongs in
`manifest.yaml`.

## README.md

Human-readable strategy explanation. This file is required because subscribers
need to understand the Playbook before trusting its signals.

Write in plain language, not implementation notes. Avoid code blocks unless they
make the explanation easier to understand. Cover at least:

- What market behavior this strategy tries to capture
- When it opens a long or short position
- When it closes, takes profit, or stops loss
- What each user-tunable parameter means and what happens when it is raised or
  lowered
- How to read the backtest metrics, especially strategy return vs account return
- Main risks and market conditions where the strategy can perform poorly

`README.md` must be UTF-8 text, at least 200 characters, and include enough
plain-language content for the upload validator to detect sections covering
`策略`, `开仓`, `平仓`, and `风险`. Use bilingual headings such as
`策略 / Strategy`, `开仓 / Entry`, `平仓 / Exit`, and `风险 / Risk` so both users
and validators read the same package contract.

## manifest.yaml

Package identity, public behavior, and runtime contract.


| Field                    | Type         | Required | Description                                                                                                                                   |
| ------------------------ | ------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                   | string       | yes      | URL-safe identifier. Lowercase, alphanumeric, hyphens only. 1-63 chars.                                                                       |
| `display_name`           | string       | yes      | Human-readable name.                                                                                                                          |
| `display_name_i18n`      | mapping      | yes for newly authored packages | Localized display names keyed by `en`, `zh`, `zh-tw`, `es`, `ja`, and `vi`. The platform returns the selected value as `display_name`. |
| `version`                | string       | no       | Server-assigned on publish. Do not write this for drafts; `upload` returns a `draft_id`, and `publish` returns the formal semver.              |
| `description`            | string       | yes      | One-line description.                                                                                                                         |
| `description_i18n`       | mapping      | yes for newly authored packages | Localized one-line descriptions keyed by `en`, `zh`, `zh-tw`, `es`, `ja`, and `vi`. The platform returns the selected value as `description`. |
| `long_description`       | string       | yes      | 300–400 English words. Plain-language strategy summary that subscribers read in the marketplace UI. Must cover what the strategy captures, when it enters/exits, what each tunable parameter does, and where it underperforms — without revealing numeric parameters, indicator periods, thresholds, or formulas. See [`long_description` Writing Rules](#long_description-writing-rules). |
| `market_type`            | string       | yes      | `"spot"` or `"contract"`.                                                                                                                     |
| `trading_symbols`        | list[string] | yes      | Exchange-native tradable pairs, e.g. `["BTCUSDT"]`, `["RAAPLUSDT"]`, or `["AAPLUSDT"]`. No slash or colon. An empty list `[]` means the user (or the Playbook itself) selects symbols at runtime; use this for grid and agentic strategies that auto-select candidates. |
| `output_kind`            | string       | no       | `trade_strategy` (default), `selection_basket`, or `grid`. Set explicitly for callout / basket Playbooks and grid Playbooks.                                              |
| `decision_mode`          | string       | yes      | `deterministic`, `llm_assisted`, or `agentic`.                                                                                                |
| `backtest_support`       | string       | yes      | `full` or `none`.                                                                                                                             |
| `runtime_profile`        | string       | yes      | `deterministic`, `llm_bounded`, or `agentic`. Historical backtest uses `deterministic`; live-only bounded model execution uses `llm_bounded`. |
| `execution_mode`         | string       | yes for `trade_strategy` and `grid`; omitted for `selection_basket` | `follow_trade` or `grid`. `grid` routes execution through the managed Grid engine. |
| `follow_trade_supported` | bool         | yes      | Whether the Playbook can follow trades using a subscriber's bound subaccount. Must be `false` for `grid`.                                      |
| `strategy_config`        | mapping      | no       | User-tunable strategy parameters read by both live and backtest code paths.                                                                    |
| `user_config_schema`     | mapping      | no       | Authoritative declaration of which `strategy_config` fields users may override when subscribing.                                               |
| `tags`                   | list[string] | no       | Searchable tags.                                                                                                                              |
| `template_source`        | string       | no       | Stable source identifier for a package derived from a bundled template; keep the template's existing value and omit it for original packages. |
| `schedule.cron`          | string       | no       | Suggested publish-time schedule, e.g. `"0 */4 * * *"`. Required for `output_kind: grid` (default every 4 hours).                                                                                        |
| `schedule.tz`            | string       | required with `schedule.cron` | Default IANA timezone for subscription instances, e.g. `"Asia/Shanghai"`. Users may override it when creating their own instance. |
| `official_evidence_kind` | string       | no       | For live-only strategies, optional declared evidence type: `paper` or `live`.                                                                 |


**Name rules:** must match `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`.

### Contract rules

- Use `backtest_support: full` only when the core trading logic is fairly replayable on historical data.
- Do not manually bump `version` in `manifest.yaml`. Versions belong to published
  artifacts and are assigned by the server from the strategy's latest published
  version.
- New authoring should include `display_name_i18n` and `description_i18n` for
  product locales `en`, `zh`, `zh-tw`, `es`, `ja`, and `vi`. Keep
  `display_name` and `description` as the English fallback/source fields.
- Keep `template_source` unchanged when starting from a bundled example so
  template usage can be measured; omit it when authoring an original package.
- Use `backtest_support: none` when open-ended LLM reasoning or unreplayable external context determines the trade.
- Asset class does not determine the output contract. Crypto, Bitget RWA stock
  tokens, and RWA metals can all use `output_kind: trade_strategy` when the
  target market is tradable and the strategy satisfies the same replay/follow
  rules as any other strategy.
- Use `output_kind: selection_basket` only for callout/watchlist Playbooks that
  emit `meta.basket`, not merely because the assets are non-crypto; read
  [`selection-basket.md`](selection-basket.md) before authoring one.
- `output_kind: trade_strategy` requires `execution_mode: follow_trade` and
  `follow_trade_supported: true`.
- `output_kind: selection_basket` requires `backtest_support: none`, must omit
  `execution_mode`, and requires `follow_trade_supported: false`.
- Use `output_kind: grid` for Grid Strategy Bot Orchestration Playbooks. Read
  [`strategy-bot-orchestration.md`](strategy-bot-orchestration.md) before
  authoring lifecycle code and [`grid-playbook.md`](grid-playbook.md) for
  Grid-specific parameters and method mappings. Grid Playbooks do not support
  backtests and run on a recurring schedule.
- `output_kind: grid` requires `execution_mode: grid`,
  `backtest_support: none`, `follow_trade_supported: false`, and a valid
  `schedule.cron` entry (suggested default: `0 */4 * * *`). `decision_mode`
  and `runtime_profile` are not restricted by grid contract rules; use
  whatever combination fits the strategy. Grid Playbooks must not include a
  `backtest.yaml`.
  Grid Playbooks may use documented `trade.*` read APIs for decision input.
  Every `trade.grid` mutation must be the single mutation in the `execute=`
  callback of `runtime.execute_strategy_bot_action(...)`. Grid mode forbids
  `trade.contract`, `trade.spot`, and `trade.account` mutations. Direct
  `emit_decision(create/modify/shutdown)` does not execute a bot action.
- `execution_mode: grid` requires `output_kind: grid` and
  `follow_trade_supported: false`.
- `decision_mode: agentic` requires `runtime_profile: agentic`.
- `runtime_profile: llm_bounded` requires `backtest_support: none`.
- `runtime_profile: llm_bounded` with `output_kind: trade_strategy` may use
  `execution_mode: follow_trade` and `follow_trade_supported: true`; publish with
  paper/live evidence instead of historical backtest claims.
- `execution_mode: follow_trade` requires `follow_trade_supported: true`.
- Live-only playbooks with `runtime_profile` other than `llm_bounded` must not
  default to `execution_mode: follow_trade`.
- Live-only playbooks must not declare `official_evidence_kind: backtest`.
- Backtest-capable playbooks should not predeclare paper/live official evidence.
- `schedule.cron` must not run more often than every 15 minutes. This limits
  live execution frequency only; Playbooks may still use 5m or other finer-grain
  bars for historical replay and signal features.
- `schedule.tz` is required whenever `schedule.cron` is present. Use a valid
  IANA timezone such as `Asia/Shanghai`. This is the default for new
  subscription instances, not a strategy parameter, so do not put timezone in
  `strategy_config` or `user_config_schema`.
- Live contract order prices must align with exchange tick size. Do not pass
  fixed decimal rounding such as `str(round(tp_price, 2))` to
  `tp_trigger_price` / `sl_trigger_price`; use
  `trade.helpers.resolve_contract_tpsl(...)` or quantize with
  `trade.helpers.contract_rules(symbol).price_step`. The helper is
  keyword-only and does not accept percentage override kwargs such as
  `tp_pct_override` or `sl_pct_override`; convert percentage TP/SL tunables to
  concrete trigger prices before calling it.
- Live code should use `runtime.emit_signal_or_follow(...)` to emit the signal
  and let the runtime decide whether to call the provided trade callback. The
  callback runs only for actionable signals in an authorized live execution.
- Do not add `run_mode`. Historical vs live execution is selected by
  `runtime.evaluation_mode`, injected by the platform at run time.
- Every user-editable strategy parameter must appear in both `strategy_config`
  (default runtime value) and `user_config_schema` (type/range/options for UI
  and API validation). Do not declare fake editable fields that strategy code
  does not read.
- Grid Playbooks must declare and consume the shared product configuration
  fields below. Additional internal strategy settings belong in
  `strategy_config` but must not be exposed through `user_config_schema` unless
  the product UI supports editing them:
  - `trade_type`: `string`, options `spot` / `contract`
  - `style`: `string`, options `balanced` / `aggressive`
  - `leverage`: `integer`, range `1..100`
  - `capital_pct`: `number`, range `1..100`
  - `max_bots`: `integer`, range `1..8`
  - `trading_symbols`: array of exchange-native symbols
  - `auto_follow_new_coins`: `boolean`
  Values in `strategy_config` must satisfy these types, enums, and ranges.
  Whenever a corresponding `user_config_schema` entry declares `default`, it
  must equal the `strategy_config` value.
  `capital_pct` limits the aggregate occupied funds of all running and
  current-cycle planned bots for each symbol. Its basis is current Funding
  equity (`available + frozen + locked`), and actual creation must not exceed
  current Funding `available`; it is not a per-bot allowance.
  Grid code must restore running bots with
  `runtime.list_strategy_bots(status="running")` and fail if occupied funds
  cannot be resolved from snapshot params or bot detail.
  Launch callers may omit `trade_type`; the platform materializes the package's
  configured trade type into the instance. Grid Playbooks read Funding balances
  at runtime through `trade.account.funding_assets(coin="USDT")`.
- Playbook code must read editable values from
  `runtime.manifest["strategy_config"]`; never hardcode user-editable values in
  Python constants.
- For configurable trading pairs, keep top-level `trading_symbols` and
  `strategy_config.trading_symbols` aligned. The platform syncs the top-level
  field when a user override changes `strategy_config.trading_symbols`.
- **`strategy_config.margin_budget` is required** when `backtest_support: full`
  or `execution_mode: follow_trade`. It is the per-strategy denominator the
  platform uses to compute user-facing return % (`net_pnl / margin_budget`).
  Validation rejects manifests that omit it or set it to a non-positive value.
  Subscribers may override it via `config_overrides.margin_budget`; otherwise
  the manifest default applies. Non-trading selection baskets that never
  surface a return % may omit the field.

Example:

```yaml
name: btc-ema-crossover
display_name: "BTC EMA Crossover"
description: "Trend following strategy based on EMA 12/26 crossover on 4h chart"
long_description: |
  This Playbook is a trend-following strategy on BTC perpetual futures. It is
  built on the assumption that once the broader market enters a sustained
  directional move, price tends to travel along that direction in a relatively
  clean trend rather than chopping back and forth. The goal is to capture the
  middle portion of those trends and stay out of grinding sideways markets where
  most signals are noise.

  Entry decisions are driven by alignment between a shorter-term and a
  longer-term directional read. When both reads point clearly upward, the
  strategy opens a long; when both point clearly downward, it opens a short. It
  deliberately waits until momentum has formed and is still in motion, rather
  than trying to fade extremes or call tops and bottoms.

  Exits work by inversion. When the shorter-term direction flips before the
  longer-term direction does, the strategy treats that as a fade in conviction,
  retracts the trade signal, and closes the position. The intent is to lock in
  whatever was captured rather than insist on every trade winning. Many small
  losing trades are accepted as the cost of catching the occasional larger
  trend run.

  Two parameters are exposed to subscribers: leverage and margin budget. Higher
  leverage amplifies both upside and drawdowns equally; the strategy does not
  become more selective when leverage rises. Margin budget is the per-strategy
  cap that the platform sizes orders against and uses as the denominator for
  return percentage; treat it as the maximum amount of capital you are willing
  to put at risk on this Playbook.

  The strategy underperforms in choppy, range-bound markets where short-term
  direction flips repeatedly without committing to a real trend. Gap-driven
  moves around major events, illiquid pairs, and persistent funding-rate
  dislocation can also produce a string of stops or trapped positions. Strong
  historical backtest metrics are not a guarantee of live profitability — match
  this Playbook against your own risk tolerance before subscribing.
market_type: contract
trading_symbols: ["BTCUSDT"]
tags: ["trend", "ema", "btc", "contract"]
schedule:
  cron: "0 */4 * * *"
  tz: "Asia/Shanghai"
decision_mode: deterministic
backtest_support: full
runtime_profile: deterministic
execution_mode: follow_trade
follow_trade_supported: true

strategy_config:
  trading_symbols: ["BTCUSDT"]
  fast_period: 12
  slow_period: 26
  leverage: 5
  margin_budget: "50"

user_config_schema:
  trading_symbols:
    type: array
    item_type: string
    default: ["BTCUSDT"]
    options: ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    aliases:
      btc: BTCUSDT
      bitcoin: BTCUSDT
      eth: ETHUSDT
      ethereum: ETHUSDT
    min_items: 1
    max_items: 1
    label: "Trading symbol"
  leverage:
    type: integer
    default: 5
    min: 1
    max: 20
    aliases:
      10x: 10
    label: "Leverage"
  margin_budget:
    type: string
    default: "50"
    pattern: "^[0-9]+(\\.[0-9]+)?$"
    label: "Margin budget USDT"
```

Supported `user_config_schema.*.type` values are `string`, `integer`,
`number`, `boolean`, and `array`. `array` may declare `item_type`, `min_items`,
and `max_items`. `options` restricts scalar values or each array item.
`aliases` maps common user phrases to canonical values. The platform also
normalizes common raw user intent before validation: `eth` -> `ETHUSDT`,
`10x` -> `10`, and `200U` / `200 USDT` -> `200` for budget fields.
`key_aliases` or `synonyms` may be used when a field needs custom input names
beyond built-ins such as `symbol` -> `trading_symbols`.

### long_description Writing Rules

`manifest.long_description` is the strategy summary that subscribers see in the
marketplace UI when deciding whether to subscribe. Unlike `description` (one
line) or `README.md` (full reference), it is a single short essay. Two goals
have to coexist:

1. **Make a non-technical user understand the strategy** — what market behavior
   it bets on, when it enters and exits, what they can tune, and where it can
   lose them money.
2. **Protect the strategy** — never reveal the exact recipe a competitor or
   reader could use to clone or front-run it.

#### Length

- Target **300–400 English words**.
- Hard floor: **250 words**. Hard ceiling: **500 words**. Outside this range,
  `validate.py` fails the upload.
- Write in English only. Do not mix Chinese into the same field.

#### Required 5-section skeleton

The text must read as continuous prose (no bullet headers, no numbered lists),
but must cover all five logical sections in order. Aim for 60–90 words per
section.

1. **What it does and what behavior it captures.** The strategy thesis. Which
   market(s), which side (long/short/both), which kind of price behavior it
   bets on.
2. **How it decides to enter.** Direction-of-decision language only ("enters
   long when momentum aligns with trend"). No periods, no thresholds, no
   formulas.
3. **How it decides to exit, take profit, or stop loss.** Same direction-of-
   decision phrasing.
4. **What subscribers can tune and what each tunable does.** Describe the
   *effect* of raising or lowering each user-editable parameter declared in
   `user_config_schema`. Do not show default values inside the prose.
5. **Risks and unsuitable market conditions.** Be honest about where the
   strategy underperforms or actively loses money. Past backtest performance
   disclaimer should appear here.

The validator confirms each section is present by detecting required keyword
clusters (`captures`/`thesis`/`aim` for §1, `enter`/`open`/`long`/`short` for
§2, `exit`/`close`/`stop`/`take profit` for §3, `parameter`/`tunable`/
`leverage`/`margin`/`adjust` for §4, `risk`/`drawdown`/`underperform`/
`unsuitable`/`lose` for §5). Missing any cluster fails validation.

#### What you may write (allowed)

- The strategy *category* in plain English: `trend-following`, `mean
  reversion`, `momentum`, `breakout`, `range`, `arbitrage`, `grid`,
  `event-driven`, `risk parity`, `pairs`.
- The general *kind* of feature input, e.g. "price action", "volatility
  regime", "open-interest behavior", "funding-rate behavior", "liquidation
  pressure", "order-book imbalance".
- The general *direction* of decisions ("waits for momentum to align with the
  trend before entering", "fades extreme moves after volatility contracts").
- The *effect* of each tunable parameter ("higher leverage amplifies both
  upside and drawdowns equally", "raising the symbol universe spreads risk
  across more pairs but increases data load").
- The *qualitative* market regimes where it works/fails ("performs well in
  sustained trends; underperforms in choppy ranges or around major news
  gaps").

#### What you must not write (forbidden — validator hard-fails)

- **Numeric indicator periods.** `EMA 12`, `RSI 14`, `MA 200`, `ATR 1.5`,
  `Bollinger 20`, `MACD 9`, `ADX 14`, `Stochastic 5`, `VWAP 30`, `MFI 14`,
  `CCI 20`, `OBV 50`. Pattern: any indicator name immediately followed by a
  number.
- **Numeric lookback windows.** `14 bars`, `20 candles`, `5-period`, `30-day`,
  `4-hour`, `15-minute`, `90 days`, `1 week`. Pattern: any number followed by
  a time/candle/period unit.
- **Explicit numeric thresholds.** `> 30`, `<= 0.7`, `>= 3%`, `drops below 5%`,
  `volatility above 25%`. Any explicit comparison operator with a number, or
  any standalone percentage with a number, is forbidden.
- **Multipliers and ratios.** `1.5x ATR`, `2x volatility`, `3:1 reward/risk`.
  Any `<number>x` or numeric ratio is forbidden.
- **Formulas or pseudocode.** No `=`, no arithmetic expressions, no `if/then`
  blocks, no parameter names from the source code.
- **Default values for tunable parameters.** Do not mention specific defaults
  even though they are public in `manifest.strategy_config`. Describe the
  *effect* of changing the parameter, not its default.
- **Specific provider/endpoint names.** No `data.crypto.futures.kline`, no
  `Coinglass`, no `Binance funding_weighted`. Stay one level above the SDK.

#### Example

See the `btc-ema-crossover` manifest example above for a full 300–400 word
`long_description` block that satisfies all rules.

#### Common authoring mistakes

- Repeating `description` verbatim or padding it to length. The validator
  catches near-duplicate strings.
- Writing in numbered list / bullet form ("**1.** Goal: …"). Keep it as
  flowing prose.
- Naming the indicators by acronym alone with no number (`uses EMA`, `uses
  RSI`). The validator allows this — a clue is fine, an exact period is not —
  but treat naked indicator-name name-dropping as a code smell. Prefer
  category-level language ("uses moving-average crossovers", "uses momentum
  oscillator").
- Mentioning *backtest* configuration parameters (`max_backtest_symbols`,
  `backtest_batch_size`). These are operational, not strategy semantics, and
  do not belong in this field.
- Any text that translates to "buy when X drops more than N percent". Rewrite
  as "buys after a sharp washout move" without a number.

## backtest.yaml

Optional Nautilus replay specification. This file is only valid when
`manifest.yaml` sets `backtest_support: full`.

The runner exposes this file to Playbook code via `runtime.backtest_spec`.

Sections:


| Field                         | Type                     | Description                                                         |
| ----------------------------- | ------------------------ | ------------------------------------------------------------------- |
| `venue`                       | mapping                  | Venue name, account type, OMS type, and starting balances           |
| `instrument` or `instruments` | mapping or list[mapping] | Explicit instrument definitions and `bar_type` declarations         |
| `strategy`                    | mapping                  | Author strategy module/class entry plus config payload              |
| `execution`                   | mapping                  | Optional replay window filters `start` and `end`                    |
| `data_requirements`           | mapping                  | Optional replay data contract such as required enriched bar columns |


`execution.start` and `execution.end` are optional bar filters: when present
the engine drops bars outside the window before replay; when omitted the
replay covers every bar the strategy fetched. The window is entirely the
author's choice — the platform never polices window presence, length, or
recency. Pick whatever range the strategy needs; if a single fetch cannot
cover it, batch history requests. The only hard rule is honesty: the replay
must run on real bars, and metrics/curves must come from the actual run.

Symbols are part of the package contract. `manifest.trading_symbols`,
`strategy_config.trading_symbols`, `backtest.yaml` instrument symbols, data
calls, trade calls, and emitted signal symbols must all use the same
exchange-native tradable pair format: no slash, no colon. Use `BTCUSDT` for BTC,
`RAAPLUSDT` for Bitget RWA spot Apple, `AAPLUSDT` for Bitget RWA Apple
perpetual, and `XAUUSDT` for Bitget RWA gold perpetual. Do not put CCXT unified
symbols such as `AAPL/USDT:USDT` in the package contract.

Before writing a strategy package, resolve every user-requested tradable asset
with Bitget's official public config APIs during authoring. This determines
whether the asset is tradable and what exact exchange-native symbol must appear
in the package contract:

```bash
curl "https://api.bitget.com/api/v2/spot/public/symbols?symbol=RAAPLUSDT"
curl "https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES&symbol=AAPLUSDT"
```

Spot rows with `status: online` and contract rows with `symbolStatus: normal`
are exchange-supported markets. This lookup belongs to the authoring workflow;
do not add direct HTTP clients to Playbook `src/**`.

Tradability is not the same as replayability. Before declaring
`backtest_support: full`, also probe the managed replay data path for every
declared symbol, using the same market, `exchange="bitget"`, interval, and
intended lookback/window that `backtest.yaml` will use. The probe must return
HTTP 200 with a valid JSON body and non-empty rows. A 204/empty body or a 4xx
means that symbol is not currently eligible for official historical backtest,
even if it is tradable on Bitget.

Keep the symbol text in `display_name`, `description`, and README aligned with
those package symbols. If a user submits a typo such as `TCUSDT` and you correct
it to `BTCUSDT`, the package must be renamed and the README/final summary must
explicitly say the submitted symbol was corrected to the supported symbol. Never
publish a package whose title claims one symbol while its backtest uses another.

Do not put `provider` anywhere in `backtest.yaml`. The managed runtime chooses
the DataSDK provider for the deployment; package authors declare symbols,
venues, intervals, instruments, and feature requirements only.

Optional `data_requirements.required_bar_fields` lets a deterministic strategy
declare extra normalized bar columns it expects in addition to core OHLCV.
These names should use lower snake case to match the replay engine's normalized
DataFrame columns, for example `quote_volume`, `trade_count`, or
`taker_buy_volume`. Every field listed here must also appear in `src/**` code
and be created by `getagent.backtest.build_feature_frame(...)` or equivalent
before calling `backtest.run(...)`; otherwise validation rejects the package as a
custom bar fields mismatch.

Every backtest instrument must declare explicit `maker_fee` and `taker_fee`.
Do not rely on zero-fee defaults. High-frequency Playbooks can look profitable
or only slightly negative without fees, while real execution would pay a fee on
every entry and exit. Use conservative exchange rates for the target venue, for
example `maker_fee: "0.0002"` and `taker_fee: "0.0005"` for a simple Binance
contract assumption.

Data coverage is part of the package contract. If a strategy requires enriched
columns such as `quote_volume`, `taker_buy_ratio`, open interest, funding, or
liquidation data, author code must prove that the selected DataSDK endpoint,
symbol, and interval returns enough rows for the claimed replay window and the
exact fields used by the strategy. Do not pass `provider=...` to `getagent.data`
calls. Do not silently fill a missing decision feature with constants such as
`0`, `0.5`, or `False` and still claim a valid backtest. If a feature is
degraded, expose that in metrics/meta or fail the run with a clear error.

Large multi-symbol backtests must batch data fetches instead of issuing one
tight loop over every symbol and endpoint. If a Playbook scans many symbols
across several historical datasets, expose controls such as
`max_backtest_symbols`, `backtest_batch_size`, and
`backtest_batch_sleep_seconds` in both `strategy_config` and
`user_config_schema`. Default to a modest slice, for example 30 symbols in
batches of 5 with a short sleep between batches, and report
`symbols_requested`, `symbols_loaded`, batch settings, and skipped symbols in
metrics/meta.

When `backtest.yaml` declares more instruments than the data fetch actually
loads, author code must filter the effective runtime spec to the loaded
instrument ids before calling `backtest.run(...)`. The engine expects OHLCV data
for every declared instrument and will fail if the spec still includes missing
symbols. For full-universe evidence, split the symbol universe across multiple
runs or a controlled workflow rather than making one default run fetch every
symbol.

Sizing is also part of the public contract. Backtest and live signal output
should expose `notional_usdt`, `min_open_notional_usdt`, and `sizing_ok` when
orders are sized from margin budgets. If the configured margin and leverage are
too small for exchange lot size, tell the user to raise margin or leverage.

When the strategy class defines `set_feature_frames(...)` or exposes a
`feature_frames` attribute, the replay engine injects one full DataFrame per
instrument ID with those extra columns preserved. Nautilus bar construction
still consumes OHLCV, but the strategy can read richer columns from the
injected feature frames.

Use `getagent.backtest.prepare_frame()` / `getagent.backtest.build_feature_frame()`
in author code to assemble those extra columns from multiple `getagent.data`
datasets before calling `backtest.run(...)`.

Minimal example:

```yaml
venue:
  name: BINANCE
  account_type: CASH
  oms_type: NETTING
  starting_balances:
    - amount: 100000
      currency: USDT

strategy:
  module: strategy
  class: DemoStrategy
  config_class: DemoStrategyConfig
  config:
    order_id_tag: "001"
    trade_size: "0.01"

instrument:
  id: BTCUSDT.BINANCE
  kind: spot
  raw_symbol: BTCUSDT
  base_currency: BTC
  quote_currency: USDT
  price_precision: 2
  size_precision: 6
  price_increment: "0.01"
  size_increment: "0.000001"
  lot_size: "0.000001"
  maker_fee: "0.0002"
  taker_fee: "0.0005"
  bar_type: BTCUSDT.BINANCE-1-HOUR-LAST-EXTERNAL
```

Feature-aware example:

```yaml
venue:
  name: BINANCE
  account_type: CASH
  oms_type: NETTING
  starting_balances:
    - amount: 100000
      currency: USDT

strategy:
  module: strategy
  class: PriceVolStrategy
  config_class: PriceVolStrategyConfig

instrument:
  id: BTCUSDT.BINANCE
  kind: spot
  raw_symbol: BTCUSDT
  base_currency: BTC
  quote_currency: USDT
  price_precision: 2
  size_precision: 6
  price_increment: "0.01"
  size_increment: "0.000001"
  lot_size: "0.000001"
  maker_fee: "0.0002"
  taker_fee: "0.0005"
  bar_type: BTCUSDT.BINANCE-1-HOUR-LAST-EXTERNAL

data_requirements:
  required_bar_fields:
    - quote_volume
    - trade_count
    - taker_buy_volume
```

## src/main.py

Sandbox entry point. The runner executes the package as `python -m src.main`.
`src/main.py` remains the required handoff into the runtime, but additional
modules under `src/**` are first-class and encouraged.

For packages with both live and backtest behavior, keep `manifest.yaml`
immutable and route in code:

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

Put shared data fetch and feature engineering in a neutral module such as
`features.py`. `main_backtest.py` must not import live trading code, because
historical runs should not require a configured trading identity.

When defining Nautilus `StrategyConfig` classes, never use mutable collection
class defaults such as `=[]`, `={}`, `=set()`, `=list()`, or `=dict()`. Use
tuples, `None`, scalar defaults, or a supported default-factory pattern. Mutable
defaults can pass syntax checks but fail when the strategy module is imported by
the backtest runtime.

**Allowed imports:** `getagent`, `nautilus_trader`, `pandas`, `numpy`, `json`,
`math`, `datetime`, `pathlib`, `asyncio`, `typing`, `dataclasses`,
`collections`, `functools`, `re`, `decimal`, `statistics`, `itertools`, plus
local modules under `src/`**.

**Blocked imports:** `requests`, `httpx`, `trade_sdk`, `ccxt`, `os`, `subprocess`,
`importlib`, `socket`, and other network/system/database libraries.

**Output convention:** signals via `runtime.emit_signal()`, reports/artifacts via
`/workspace/output/`, and public backtest charts via `backtest.generate_chart()`.

**Progress / Strategy Bot actions (Grid Playbooks only):** Grid Playbooks may
report scheduling steps through `runtime.emit_progress(blocks)`. Lifecycle
actions use `runtime.execute_strategy_bot_action(...)`, with `action` in
`create` / `modify` / `shutdown` / `watch`. Mutation actions require one
matching `trade.grid` call in `execute=`; `watch` requires a valid `sub_action`
and forbids a callback. See
[`strategy-bot-orchestration.md`](./strategy-bot-orchestration.md),
[`grid-playbook.md`](./grid-playbook.md), and
[`sdk/runtime/catalog.md`](./sdk/runtime/catalog.md).

## Nautilus strategy lifecycle

The Playbook runner uses a NautilusTrader version where strategy lifecycle
cleanup APIs are instrument-scoped. Do not call these methods without an
instrument id:

```python
def on_stop(self) -> None:
    if self.config.instrument_id is not None:
        self.cancel_all_orders(self.config.instrument_id)
        self.close_all_positions(self.config.instrument_id)
```

For multi-instrument strategies, iterate `instrument_ids`:

```python
def on_stop(self) -> None:
    for instrument_id in self.config.instrument_ids:
        self.cancel_all_orders(instrument_id)
        self.close_all_positions(instrument_id)
```

Invalid patterns such as `self.cancel_all_orders()` or
`self.close_all_positions()` are rejected by `scripts/validate.py` and
the server-side upload validator because they fail at replay shutdown.
