# Crypto/Stock Screener — Cross-Sectional Scan

Read this file whenever the task is **coin/stock screening, selection, or
scanning** — "选币", "选股", "screener", "screen for symbols that...",
"which coins/stocks satisfy...", cross-sectional factor filtering, or
building a `selection_basket` Playbook that ranks/filters a universe by
technical, funding, on-chain, or fundamental conditions. This file is the
single source of truth for `crypto.market.screener.scan`; it supersedes any
older/shorter description of this endpoint. Do not use `crypto.md` for this
endpoint — that file only keeps a short pointer back here.

`crypto.market.screener.scan` answers "which symbols satisfy a condition
right now" with **one row per matching symbol** (cross-sectional). It is
backed by an Elasticsearch index (one physical index per underlying market
type: spot/swap/stock/etf/metal) and is not limited to technical
indicators — funding/derivatives, on-chain, US-stock fundamentals
(`financials.*`, stock-only), and composite tag labels are all queryable. Contrast with `crypto.indicators.technical_indicators`
(`references/sdk/data/crypto.md`), which is coin-centric and returns a time
series for symbols you already picked.

## Endpoint

```python
data.crypto.market.screener.scan(
    asset_class=...,
    columns=...,
    filter=None,
    sort=None,
    interval=None,
    page=None,
    size=None,
    provider="bitget_data",
)
```

| Field | Value |
|---|---|
| Endpoint ID | `crypto.market.screener.scan` |
| HTTP | `POST` |
| Path | `/inner/v1/agent-data/crypto/market/screener/scan` |
| Default provider | `bitget_data` (currently the only supported provider) |
| SDK | `supported` |
| Host | `supported` |
| Notes | Cross-sectional scan over an ES index; returns matching rows with caller-specified columns. `asset_class` is **required**. |

## Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `asset_class` | `yes` | `string` | `-` | Top-level asset-class scope. Only `"crypto"` or `"stock"` are supported. This is a coarser scope than the ES index's own `market_type` field (`spot`/`swap`/`stock`/`etf`/`metal`, one per physical index). |
| `columns` | `yes` | `list[string]` | `-` | Fields to return for each matching symbol. Must include at least `"symbol"`. Every entry must follow the **field-naming convention** below — see that section before writing this list. |
| `filter` | `no` | `list[object]` | `-` | Filter conditions; multiple entries are combined with **AND**. Each entry is `{"left": "<field>", "operation": "<op>", "right": <value>}`. See **Filter operations** below. |
| `sort` | `no` | `object` | `-` | `{"sortBy": "<field>", "sortOrder": "asc" \| "desc"}`. `sortBy` follows the same naming rule as `filter.left`. |
| `interval` | `no` | `string` | `"1d"` | Default/context K-line interval. One of `5m`, `15m`, `1h`, `4h`, `1d`. **Does not implicitly scope `columns`/`filter.left`/`sort.sortBy`** — every T0 technical field reference must carry its own `technical_{interval}.` prefix regardless of this value, so a single request can mix conditions from multiple intervals. `ichimoku_*` and `clenow_slope` are `null` for `5m`/`15m`. |
| `page` | `no` | `integer` | `1` | Page number (1-based). |
| `size` | `no` | `integer` | `100` | Rows per page. Maximum `500`. |

Unlike some other endpoints in this SDK, this is a **POST** call with a
native JSON body — `filter` and `sort` are structured objects, not
URL-encoded JSON strings. `asset_class` (and `provider`) are the only
parameters carried in the URL query string.

## Field-naming convention (read before building `columns`/`filter`/`sort`)

The ES document has three kinds of fields. Getting this wrong is the most
common screener mistake — a misqualified field name simply returns no match,
it does not raise an error.

1. **Top-level flat fields** — identity (`symbol`, `exchange`, ...), market
   cap, sentiment, and *all* funding/derivatives and Crypto-metrics fields
   (e.g. `funding_rate_d`, `oi_usd_d`, `market_cap`, `top100_holder_pct_d`).
   These are **period-agnostic** (not sliced by K-line interval). Reference
   them by their **bare name**, already including its type suffix
   (`_d` double / `_i` long / `_k` keyword) where one exists. **Do not**
   add a `technical_{interval}.` prefix to these — see §Funding/derivatives
   and §Crypto metrics below for the complete field lists.
2. **T0 technical indicators** — every field computed off K-line bars
   (price/SMA/EMA/RSI/MACD/Bollinger/pivots/... and the 4 tag arrays) lives
   inside one of 5 separate per-interval containers: `technical_5m` /
   `technical_15m` / `technical_1h` / `technical_4h` / `technical_1d`.
   Every reference in `columns`, `filter.left`, or `sort.sortBy` **must be
   fully qualified** as `technical_{interval}.{field_name}_{suffix}`, e.g.
   `technical_1h.rsi_14_d`, `technical_1d.tech_rating_d`. A bare `rsi_14`
   (no prefix, no suffix) will **not** resolve. Different conditions in the
   same request may reference different intervals (e.g. filter on a 5m
   signal while returning 1d columns) — see §T0 technical factors below for
   the complete field list.
3. **Composite tag arrays** — 4 special T0 fields (still interval-prefixed)
   store a *keyword array* instead of a scalar and only support **exact-value
   membership** checks (`operation: "equal"`), e.g.
   `{"left": "technical_1h.pattern_tags_k", "operation": "equal", "right": "boll_expand"}`.
   See §Composite tag arrays below for the complete candidate lists.
4. **US-stock fundamentals** (`asset_class="stock"` only) — two sub-kinds,
   both **top-level** (no `technical_{interval}.` prefix):
   - **Identity / corporate-action flat fields** — bare names such as
     `listed_board_name_k`, `top10_holder_ratio_d`, `float_share_ratio_d`.
   - **Financial statement & valuation fields** — prefixed with `financials.`
     (e.g. `financials.pe_d`, `financials.roe_avg_d`, `financials.revenue_yoy_d`).
     These hold the latest reported period's values (generally **not TTM** for
     flow items like revenue/net income/EPS). See §E below for the full
     catalogue. **Do not use any §E field when `asset_class="crypto"`** — they
     will not resolve.

## Filter operations

| # | `operation` value | Meaning | `right` type | Example |
|---|---|---|---|---|
| 1 | `equal` | Equals (array-field semantics: contains) | number / string / boolean | `{"left":"exchange","operation":"equal","right":"bitget"}` |
| 2 | `not_equal` | Not equal | number / string / boolean | `{"left":"exchange","operation":"not_equal","right":"bitget"}` |
| 3 | `greater` | Greater than | number | `{"left":"technical_1h.rsi_14_d","operation":"greater","right":70}` |
| 4 | `greater_equal` | Greater than or equal | number | `{"left":"oi_change_pct_d","operation":"greater_equal","right":10}` |
| 5 | `less` | Less than | number | `{"left":"technical_1h.rsi_14_d","operation":"less","right":30}` |
| 6 | `less_equal` | Less than or equal | number | `{"left":"funding_rate_d","operation":"less_equal","right":-0.005}` |
| 7 | `in_range` | Value inside the closed interval `[min, max]` | `[min, max]` array | `{"left":"technical_1d.rsi_14_d","operation":"in_range","right":[30,50]}` |
| 8 | `not_in_range` | Value outside `[min, max]` | `[min, max]` array | `{"left":"technical_1d.bb_pct_d","operation":"not_in_range","right":[0.2,0.8]}` |
| 9 | `in` | Value in the given list (OR semantics, like MySQL `IN`) | array | `{"left":"exchange","operation":"in","right":["binance","okx"]}` |
| 10 | `not_in` | Value not in the given list | array | `{"left":"exchange","operation":"not_in","right":["binance","okx"]}` |
| 11 | `is_null` | Field absent / empty | none (omit `right`) | `{"left":"next_unlock_date_i","operation":"is_null"}` |
| 12 | `is_not_null` | Field present / non-empty | none (omit `right`) | `{"left":"next_unlock_date_i","operation":"is_not_null"}` |
| 13 | `crosses_above` | Greater than; supports field-vs-field comparison | number or field name | `{"left":"technical_1h.price_d","operation":"crosses_above","right":"technical_1h.ema_20_d"}` |
| 14 | `crosses_below` | Less than; supports field-vs-field comparison | number or field name | `{"left":"technical_1h.ema_20_d","operation":"crosses_below","right":"technical_1h.ema_50_d"}` |

Notes:

- Multiple entries in `filter` are combined with **AND**. There is no
  documented OR-across-conditions operator; express OR-over-values with
  `in` on a single field instead.
- For the 4 tag-array fields (`pattern_tags_k` / `signal_tags_k` /
  `stage_tags_k` / `label_tags_k`) only `equal` (single exact tag) is
  meaningful; to require several tags simultaneously, add one `equal`
  condition per tag (they AND together).
- `crosses_above` / `crosses_below` compare the current row's value against
  either a numeric constant or another (fully-qualified) field on the same
  row — they are not a true "crossed during this bar" time-series event,
  they simply compare the two most-recent aligned values.
- For `left="symbol"`, `right` is auto-normalised from concat format
  (`BTCUSDT`) to pair format (`BTC/USDT`) before the downstream call.

## Response shape

```json
{
  "totalCount": 137,
  "data": [
    {"s": "BTCUSDT", "d": [68000.1, 42.3, "strong_trend"]},
    {"s": "ETHUSDT", "d": [3200.5, 55.1, null]}
  ]
}
```

- `s` — trading pair in concat format (e.g. `BTCUSDT`), converted from the
  downstream's pair format.
- `d` — values array aligned **positionally** to the requested `columns`
  order (including `symbol` if you included it, though the SDK typically
  keys the flattened row on `s` for `symbol`). Zip `d` with `columns` to
  build a flat `{column_name: value}` dict per row; a `null` entry means
  that field had no value for that symbol.

## Verified usage examples

```python
# 1) RSI oversold + Bollinger lower-band pressure, 1d, size 50.
rows = data.crypto.market.screener.scan(
    asset_class="crypto",
    columns=["symbol", "technical_1d.price_d", "technical_1d.rsi_14_d",
             "technical_1d.bb_lower_d", "technical_1d.bb_pct_d", "technical_1d.tech_rating_d"],
    filter=[
        {"left": "technical_1d.rsi_14_d", "operation": "less", "right": 35},
        {"left": "technical_1d.bb_pct_d", "operation": "less", "right": 0.2},
    ],
    interval="1d",
    size=50,
)

# 2) Strong trend + accumulation tag (4h). label_tags_k is a keyword array —
#    match each candidate tag with its own "equal" condition. funding_rate_d
#    is period-agnostic and never takes a technical_ prefix.
rows = data.crypto.market.screener.scan(
    asset_class="crypto",
    columns=["symbol", "technical_4h.adx_14_d", "funding_rate_d"],
    filter=[
        {"left": "technical_4h.label_tags_k", "operation": "equal", "right": "strong_trend"},
        {"left": "technical_4h.label_tags_k", "operation": "equal", "right": "accumulation"},
    ],
    interval="4h",
    size=20,
)

# 3) OI surge + negative funding: funding/derivatives fields are always
#    top-level (no K-line interval prefix), regardless of `interval`.
rows = data.crypto.market.screener.scan(
    asset_class="crypto",
    columns=["symbol", "oi_usd_d", "oi_change_pct_d", "funding_rate_d", "long_short_ratio_top_d"],
    filter=[
        {"left": "oi_change_pct_d", "operation": "greater", "right": 10},
        {"left": "funding_rate_d", "operation": "less", "right": -0.005},
    ],
    size=20,
)

# 4) Price crosses above EMA20 (1h). The right side of crosses_above must
#    also be fully qualified with the technical_1h. prefix.
rows = data.crypto.market.screener.scan(
    asset_class="crypto",
    columns=["symbol", "technical_1h.price_d", "technical_1h.ema_20_d", "technical_1h.volume_ratio_20d_d"],
    filter=[
        {"left": "technical_1h.price_d", "operation": "crosses_above", "right": "technical_1h.ema_20_d"},
        {"left": "technical_1h.volume_ratio_20d_d", "operation": "greater", "right": 1.5},
    ],
    interval="1h",
    size=30,
)

# 5) Stock scope: asset_class="stock", paginated (technical only).
rows = data.crypto.market.screener.scan(
    asset_class="stock",
    columns=["symbol", "technical_1h.price_d", "technical_1h.rsi_14_d", "technical_1h.tech_rating_d"],
    filter=[
        {"left": "technical_1h.rsi_14_d", "operation": "less", "right": 30},
        {"left": "technical_1h.signal_tags_k", "operation": "equal", "right": "boll_expand"},
    ],
    interval="1h",
    page=1,
    size=100,
)

# 6) Industry-classification filter (asset_class="stock" only).
#    industry_name_k is a keyword field; use "equal" for a single industry or
#    "in" for multiple. Combine with any technical or financials.* condition.
rows = data.crypto.market.screener.scan(
    asset_class="stock",
    columns=["symbol", "sec_short_name_cn_k", "industry_name_k",
             "financials.pe_d", "financials.roe_avg_d", "technical_1d.rsi_14_d"],
    filter=[
        {"left": "industry_name_k", "operation": "in",
         "right": ["Software", "Semiconductors"]},
        {"left": "financials.roe_avg_d", "operation": "greater", "right": 15},
    ],
    interval="1d",
    size=50,
)

# 7) US-stock fundamental screen (asset_class="stock" only). financials.* and
#    identity fields (incl. industry_name_k) are unavailable for crypto.
rows = data.crypto.market.screener.scan(
    asset_class="stock",
    columns=[
        "symbol", "sec_short_name_cn_k", "td_mkt_k",
        "financials.pe_d", "financials.pb_d", "financials.roe_avg_d",
        "financials.revenue_yoy_d", "financials.gross_margin_d",
        "financials.div_yield_12m_d", "technical_1d.rsi_14_d",
    ],
    filter=[
        {"left": "financials.pe_d", "operation": "in_range", "right": [5, 25]},
        {"left": "financials.roe_avg_d", "operation": "greater", "right": 15},
        {"left": "financials.revenue_yoy_d", "operation": "greater", "right": 10},
        {"left": "financials.asset_liab_ratio_d", "operation": "less", "right": 60},
        {"left": "td_mkt_k", "operation": "in", "right": ["NASDAQ", "NYSE"]},
    ],
    interval="1d",
    size=50,
)
```

## Verified Playbook usage notes

- `columns` is **required** — there is no default column set.
- `asset_class` is required and is `"crypto"` or `"stock"` only; it is not
  the same thing as the ES index's own `market_type` (spot/swap/stock/etf/metal).
- Passing an unlisted tag value to a tag-array `equal` filter simply matches
  zero rows — it does not error.
- `chg_pct_ytd` and `drawdown_from_ath` were designed but **not shipped** —
  do not use them; they will not resolve.
- The `label_tags_k` candidate values (`accumulation`, `washout`,
  `distribution`, `strong_trend`, `consolidation`, `volume_spike`,
  `breakout`, `whale_active`, `high_control`) depend on external
  derivatives/on-chain/market-cap fields that are not currently wired into
  this pipeline — treat filters on these as **currently always false** until
  confirmed otherwise by an actual non-empty result.
- `pct_5m`/`pct_15m`/`pct_1h`/`pct_4h`/`pct_1d` (single-bar % change) all
  collapse onto one ES field, `technical_{interval}.pct_d` — its value is
  only populated for the interval matching that container; request the
  interval-matching container, not a different one.
- **§E US-stock fundamentals** (`financials.*`, `sec_*`, `listed_*`, `td_*`,
  `top10_holder_ratio_d`, insider flags, share-count fields) require
  `asset_class="stock"`. Using them with `asset_class="crypto"` returns no
  match — not an error.
- Flow-type fundamentals (`financials.revenue_d`, `financials.net_income_d`,
  `financials.eps_d`, `financials.free_cash_flow_d`, …) are the **latest
  reported period** (quarterly or annual), not TTM. Cross-company absolute
  amount comparisons may be affected by differing report currencies.
- Six valuation/dividend metrics from the original wish-list are **not
  shipped**: EV/Sales, PEG Ratio, earnings yield (derive as `1/pe`), dividend
  growth rate, consecutive dividend-increase years, consecutive dividend-pay
  years.

## Factor catalogue

Everything below is either (A) a T0 technical field that **must** be
prefixed with `technical_{interval}.` where `{interval}` is one of `5m` /
`15m` / `1h` / `4h` / `1d`, or (B) a top-level flat field that **must not**
be prefixed. Field names in the tables are given **without** the prefix —
add `technical_{interval}.` yourself for every field in §A.

### A. T0 technical factors — require `technical_{interval}.` prefix

#### A.1 Numeric factors (20 shipped; 2 designed but not shipped)

Group A — momentum/streak factors:

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `chg_pct_1d_d` | 1-day % change |
| `chg_pct_5d_d` | 5-day % change |
| `chg_pct_20d_d` | 20-day % change |
| `chg_pct_60d_d` | 60-day % change |
| `consecutive_up_i` | Consecutive up-bar count |
| `consecutive_down_i` | Consecutive down-bar count |
| `vol_change_pct_d` | Volume change % vs. prior 5-bar average |
| `stage_consolidation_range_pct_d` | 20-bar close range / 20-bar min close, as % (narrow-range consolidation ratio) |

Group B — stage change/amplitude:

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `stage_chg_pct_10d_d` | 10-day stage % change |
| `stage_chg_pct_20d_d` | 20-day stage % change |
| `stage_chg_pct_60d_d` | 60-day stage % change |
| `stage_chg_pct_120d_d` | 120-day stage % change |
| `stage_amplitude_10d_d` | 10-day stage amplitude %, `(high-low)/low*100` over the window |
| `stage_amplitude_20d_d` | 20-day stage amplitude % |
| `stage_amplitude_60d_d` | 60-day stage amplitude % |

Group D' — short MAs / momentum:

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `sma_5_d` | 5-period SMA |
| `sma_10_d` | 10-period SMA |
| `sma_60_d` | 60-period SMA |
| `mtm_d` | Momentum, `close - close.shift(12)` |
| `mtm_ma_d` | Momentum MA, `SMA(mtm, 6)` |

Designed but **not shipped** — do not use:

| Field | Meaning |
|---|---|
| ~~`chg_pct_ytd_d`~~ | ~~Year-to-date % change~~ |
| ~~`drawdown_from_ath_d`~~ | ~~Approx. drawdown from all-time high (200-bar rolling window, not true full-history ATH)~~ |

#### A.2 Numeric factors — existing/backward-compatible set (106)

Group 价 (Price):

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `price_d` | Latest close |
| `pct_d` | Prior-bar % change for the *matching* interval only (`pct_5m`/`pct_15m`/`pct_1h`/`pct_4h`/`pct_1d` all collapse onto this one ES field; only the container matching the actual bar interval is populated) |
| `pct_7d_d` | 7-day % change |
| `pct_30d_d` | 30-day % change |
| `volume_24h_usd_d` | 24h turnover in USD |
| `volume_ratio_20d_d` | Volume ratio: current bar volume / 20-day average volume |
| `high_52w_d` | 52-week high |
| `low_52w_d` | 52-week low |
| `volatility_30d_d` | 30-day realized volatility (annualized %) |

Group 均 (Moving averages / trend):

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `sma_20_d` | 20-period SMA |
| `sma_50_d` | 50-period SMA |
| `sma_200_d` | 200-period SMA |
| `ema_20_d` | 20-period EMA |
| `ema_50_d` | 50-period EMA |
| `ema_200_d` | 200-period EMA |
| `price_vs_ema20_pct_d` | Price deviation from EMA20, % |
| `price_vs_ema50_pct_d` | Price deviation from EMA50, % |
| `price_vs_ema200_pct_d` | Price deviation from EMA200, % |
| `ema_alignment_i` | MA alignment direction: `1` bullish (EMA20>EMA50>EMA200), `-1` bearish, `0` mixed |
| `wma_9_d` | 9-period WMA |
| `hma_9_d` | 9-period Hull MA |
| `vwap_d` | Volume-weighted average price |
| `adx_14_d` | ADX(14), trend strength |
| `aroon_up_14_d` | Aroon Up(14) |
| `aroon_down_14_d` | Aroon Down(14) |
| `ichimoku_conv_d` | Ichimoku conversion line (Tenkan, 9) — 1h+ intervals only |
| `ichimoku_base_d` | Ichimoku base line (Kijun, 26) — 1h+ intervals only |
| `ichimoku_span_a_d` | Ichimoku leading span A — 1h+ intervals only |
| `ichimoku_span_b_d` | Ichimoku leading span B (52) — 1h+ intervals only |
| `clenow_slope_d` | Clenow momentum slope (90-bar regression, annualized × R²) — 1h+ intervals only |
| `sar_d` | Parabolic SAR (af0=0.02, max_af=0.2) |
| `dema_20_d` | 20-period DEMA |
| `tema_20_d` | 20-period TEMA |
| `smma_20_d` | 20-period smoothed MA (RMA) |

Group 动 (Momentum/oscillators):

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `rsi_14_d` | RSI(14) |
| `rsi_slope_5_d` | RSI 5-bar slope |
| `macd_line_d` | MACD line (DIF) |
| `macd_signal_d` | MACD signal line (DEA) |
| `macd_hist_d` | MACD histogram (DIF - DEA) |
| `stoch_k_d` | Stochastic %K (14,3,3) |
| `stoch_d_d` | Stochastic %D |
| `cci_20_d` | CCI(20) |
| `williams_r_14_d` | Williams %R(14) |
| `roc_9_d` | ROC(9) |
| `mfi_14_d` | Money Flow Index(14) |
| `fisher_14_d` | Fisher Transform(14) |
| `cog_14_d` | Center of Gravity(14) |
| `tech_rating_d` | Composite technical rating (-1 to 1), average of RSI/MACD-hist/CCI/MA-alignment signals |
| `stoch_rsi_k_d` | StochRSI %K (14,14,3,3) |
| `stoch_rsi_d_d` | StochRSI %D |
| `uo_d` | Ultimate Oscillator (7,14,28) |
| `bull_power_d` | Bull power, `high - EMA(close,13)` |
| `bear_power_d` | Bear power, `low - EMA(close,13)` |

Group 波 (Volatility/bands):

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `bb_upper_d` | Bollinger upper band (20,2) |
| `bb_mid_d` | Bollinger middle band |
| `bb_lower_d` | Bollinger lower band |
| `bb_width_d` | Bollinger bandwidth |
| `bb_pct_d` | Bollinger %B |
| `atr_14_d` | ATR(14) |
| `keltner_upper_d` | Keltner Channel upper (20,2) |
| `keltner_lower_d` | Keltner Channel lower |
| `donchian_upper_d` | 20-period Donchian upper (max high) |
| `donchian_lower_d` | 20-period Donchian lower (min low) |
| `vol_cone_close_d` | Close-to-close realized volatility cone (annualized) |
| `vol_cone_parkinson_d` | Parkinson volatility cone (annualized) |
| `vol_cone_garman_klass_d` | Garman-Klass volatility cone (annualized) |

Group 量 (Volume):

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `obv_d` | On-Balance Volume |
| `obv_slope_5_d` | OBV 5-bar slope |
| `ad_line_d` | Accumulation/Distribution line |
| `adosc_d` | Accumulation/Distribution Oscillator (3,10) |

Group 轴 (Pivots/support-resistance):

| Field (add `technical_{interval}.` prefix) | Meaning |
|---|---|
| `pivot_classic_pp_d` / `pivot_classic_s1_d` / `pivot_classic_s2_d` / `pivot_classic_s3_d` / `pivot_classic_r1_d` / `pivot_classic_r2_d` / `pivot_classic_r3_d` | Classic pivot points (PP, S1-S3, R1-R3) |
| `pivot_fib_pp_d` / `pivot_fib_s1_d` / `pivot_fib_s2_d` / `pivot_fib_s3_d` / `pivot_fib_r1_d` / `pivot_fib_r2_d` / `pivot_fib_r3_d` | Fibonacci pivot points |
| `pivot_demark_pp_d` / `pivot_demark_s1_d` / `pivot_demark_r1_d` | DeMark pivot points |
| `pivot_cam_s1_d`…`pivot_cam_s4_d` / `pivot_cam_r1_d`…`pivot_cam_r4_d` | Camarilla pivot points (S1-S4, R1-R4) |
| `pivot_woodie_pp_d` / `pivot_woodie_s1_d` / `pivot_woodie_s2_d` / `pivot_woodie_r1_d` / `pivot_woodie_r2_d` | Woodie pivot points |
| `dist_to_support_pct_d` | Distance to nearest support, % |
| `dist_to_resistance_pct_d` | Distance to nearest resistance, % |

### A.3 Composite tag arrays — require `technical_{interval}.` prefix, `equal` only

These 4 fields hold a keyword array per bar; only tags whose condition was
true for that bar appear. Filter with `{"left": "technical_{interval}.<array>", "operation": "equal", "right": "<tag_value>"}`
— one condition per required tag (they AND together).

#### (1) `pattern_tags_k` — K-line / chart patterns (41 patterns)

Classic candlestick patterns (TA-Lib, tri-state: bullish vs. bearish variant):

`hammer_bull`/`hammer_bear` (Hammer), `inverted_hammer_bull`/`inverted_hammer_bear` (Inverted hammer),
`shooting_star_bull`/`shooting_star_bear` (Shooting star), `doji_bull`/`doji_bear` (Doji),
`spinning_top_bull`/`spinning_top_bear` (Spinning top), `engulfing_bull`/`engulfing_bear` (Engulfing),
`harami_bull`/`harami_bear` (Harami), `piercing_line_bull`/`piercing_line_bear` (Piercing line),
`dark_cloud_bull`/`dark_cloud_bear` (Dark cloud cover), `morning_star_bull`/`morning_star_bear` (Morning star),
`evening_star_bull`/`evening_star_bear` (Evening star), `three_white_soldiers_bull`/`three_white_soldiers_bear` (Three white soldiers),
`three_black_crows_bull`/`three_black_crows_bear` (Three black crows)

Short-pattern extensions (boolean): `rising_channel` (Rising channel), `box_breakout` (Box breakout),
`vol_breakout` (Volume breakout), `multi_cannon` (Multiple cannon), `one_yang_three_line` (One yang three line),
`piercing_full` (Full piercing), `long_lower_shadow` (Long lower shadow), `fake_bearish` (Fake bearish candle)

Long-cycle chart patterns (boolean): `header_shoulder_top` (Head and shoulders top), `header_shoulder_bottom` (Head and shoulders bottom),
`double_top` (Double top), `double_bottom` (Double bottom), `ascending_triangle` (Ascending triangle),
`descending_triangle` (Descending triangle), `symmetrical_triangle` (Symmetrical triangle), `triple_top` (Triple top),
`triple_bottom` (Triple bottom), `rising_wedge` (Rising wedge), `falling_wedge` (Falling wedge), `bull_flag` (Bull flag),
`bear_flag` (Bear flag), `bull_pennant` (Bull pennant), `bear_pennant` (Bear pennant), `rectangle` (Rectangle consolidation),
`cup_and_handle` (Cup and handle), `inv_cup_and_handle` (Inverted cup and handle), `rounding_top` (Rounding top),
`rounding_bottom` (Rounding bottom)

#### (2) `signal_tags_k` — event signals (19)

| Tag value | Meaning |
|---|---|
| `ma_bull_arrange` | Bullish MA alignment |
| `ma_bindweed` | MA convergence/entanglement |
| `price_above_ma5` | Price crossed above 5-period MA |
| `ma5_cross_ma10` | 5-period MA golden-crosses 10-period MA |
| `macd_golden_cross` | MACD golden cross |
| `macd_zero_cross` | MACD golden cross at the zero line |
| `macd_bullish_diverge` | MACD bullish divergence |
| `kdj_golden_cross` | KDJ golden cross |
| `kdj_bullish_diverge` | KDJ bullish divergence |
| `rsi_oversold` | RSI oversold |
| `rsi_bullish_diverge` | RSI bullish divergence |
| `boll_break_lower` | Broke below Bollinger lower band |
| `boll_break_mid` | Broke through Bollinger middle band |
| `boll_break_upper` | Broke above Bollinger upper band |
| `boll_expand` | Bollinger bands opening/expanding |
| `cci_oversold` | CCI oversold |
| `cci_bullish_diverge` | CCI bullish divergence |
| `wr_buy` | Williams %R buy signal |
| `mtm_golden_cross` | Momentum (MTM) golden cross |

#### (3) `stage_tags_k` — stage/phase performance (22)

| Tag value | Meaning |
|---|---|
| `new_high` | Stage new high (default 20-day window) |
| `new_low` | Stage new low (default 20-day window) |
| `new_high_20d` | New 20-day high |
| `new_high_60d` | New 60-day high |
| `new_high_120d` | New 120-day high |
| `new_low_20d` | New 20-day low |
| `new_low_60d` | New 60-day low |
| `new_low_120d` | New 120-day low |
| `breakout` | Platform breakout (default 20-day window) |
| `breakout_10d` | Broke out of a 10-day platform |
| `breakout_20d` | Broke out of a 20-day platform |
| `breakout_60d` | Broke out of a 60-day platform |
| `volume_shrink` | Stage volume shrink (default 20-day) |
| `vol_shrink_10d` | 10-day volume shrink |
| `vol_shrink_20d` | 20-day volume shrink |
| `vol_shrink_60d` | 60-day volume shrink |
| `vol_expand_10d` | 10-day volume expansion |
| `vol_expand_20d` | 20-day volume expansion |
| `vol_expand_60d` | 60-day volume expansion |
| `consolidation_10d` | 10-day platform consolidation |
| `consolidation_20d` | 20-day platform consolidation |
| `consolidation_60d` | 60-day platform consolidation |

#### (4) `label_tags_k` — composite labels (9, currently always false)

> These 9 tags depend on external derivatives/on-chain/market-cap fields
> that are not yet wired into this pipeline — in practice they will not
> currently appear in scan results. Listed for completeness; do not build a
> filter that requires a non-empty match on these until this note is updated.

| Tag value | Meaning | Condition (depends on unwired external fields) |
|---|---|---|
| `accumulation` | Accumulation | ADX<25 + OBV slope>0 + volume ratio>1.5 + 7d funding<0.01 + net outflow + price<EMA200 |
| `washout` | Washout | RSI<35 + hammer/engulfing pattern + OI change>-5% + funding<-0.005 + volume ratio>2 |
| `distribution` | Distribution | RSI>65 + volume ratio>1.5 + net inflow + 7d funding>0.02 + OBV slope<0 |
| `strong_trend` | Strong trend | ADX>30 + bullish MA alignment + RSI 50-70 + price>EMA20 |
| `consolidation` | Consolidation | ADX<20 + BB bandwidth near 30-day low |
| `volume_spike` | Volume spike | Volume ratio>3 |
| `breakout` | Breakout | Price breaks 20/50-day high + volume ratio>1.5 + ADX>20 |
| `whale_active` | Whale activity | Top-10 holder share changed >3% over 7 days |
| `high_control` | High control | top10_holder_pct>60% + market cap<500M + listing age>180 days |

### B. Funding / derivatives factors — top-level, NO `technical_{interval}.` prefix (18)

Read-only projections of existing funding/derivatives tables, aggregated on
5-minute (G1, per trading pair), 1-hour (G2, per token), and 1-day (G3, per
token) cadences. Field values are `null`/absent when not computed for that
cadence.

| Field | Meaning | Update cadence |
|---|---|---|
| `funding_rate_d` | Latest funding rate | 5 min |
| `funding_rate_7d_avg_d` | 7-day average funding rate | 5 min |
| `label_funding_extreme_k` | Extreme/crowded funding label (`"0"`/`"1"`); `\|funding_rate\| >= 0.3%` | 5 min |
| `oi_usd_d` | Latest open interest, USD | 5 min |
| `oi_change_pct_d` | Open interest change %, day-over-day | 5 min |
| `long_short_ratio_d` | Long/short ratio (all accounts) | 5 min |
| `long_short_ratio_top_d` | Long/short ratio (top accounts) | 5 min |
| `orderbook_imbalance_d` | Order-book imbalance (OFI) | 5 min |
| `taker_buy_sell_ratio_d` | Taker buy/sell volume ratio (1d) | 1 hour |
| `whale_txn_count_i` | Whale transaction count (taker buy + sell count, 1d) | 1 hour |
| `etf_flow_net_1d_d` | ETF net inflow, approx. (1-day) | 1 day |
| `whale_bias_score_d` | Whale long/short bias score (Whale/TidalWhale/Leviathan average) | 1 day |

Note: the G1 group is keyed per trading pair (adds `exchange`/`symbol`/
`quote_asset` identity fields); G2/G3 are token-dimension only (`base_asset`,
no trading-pair concept). Fields with `null` values are omitted from the
underlying message, but that does not change how you filter/select them.

### C. Crypto metrics factors — top-level, NO `technical_{interval}.` prefix (26)

Produced outside this pipeline by two MaxCompute batch jobs (hourly and
daily); values already carry their ES suffix or are explicit top-level
fields as noted.

Hourly (`ads_crypto_factors_hourly_v2_hf`):

| Field | Meaning |
|---|---|
| `market_cap` (top-level, no suffix) | Circulating market cap (USD) |
| `fully_diluted_market_cap` (top-level, no suffix) | Fully diluted market cap (USD) |
| `rank` (top-level, no suffix) | Market cap rank |
| `volume_24h_d` | 24h turnover (USD) |
| `hold_hhi_d` | Holder concentration (HHI index) |
| `dex_liquidity_d` | On-chain DEX liquidity (USD) |
| `fdv_mc_ratio_d` | FDV / circulating market cap ratio (dilution pressure) |
| `listing_exchange_count_i` | Number of exchanges the token is listed on |
| `holder_count_i` | Number of holder addresses |

Daily (`ads_crypto_factors_daily_v2_df`):

| Field | Meaning |
|---|---|
| `circ_supply_ratio` (top-level, no suffix) | Circulating / total supply ratio |
| `listing_days` (top-level, no suffix) | Days since listing |
| `list_date` (top-level, no suffix) | Listing date |
| `total_supply_d` | Total supply |
| `circulating_supply_d` | Circulating supply |
| `top100_holder_pct_d` | Top-100 address holding % |
| `staking_ratio_d` | Staking ratio |
| `cex_amount_d` | Total CEX holdings amount |
| `dex_pool_amount_d` | DEX pool locked amount |
| `lending_amount_d` | Lending-protocol locked amount |
| `next_unlock_pct_d` | Next unlock as % of circulating supply |
| `unlock_pressure_30d_d` | 30-day unlock pressure, approx. (`next_unlock_tokens / market_cap` — a single-event ratio, not a true 30-day cumulative figure) |
| `exchange_netflow_1d_d` | Exchange-type 1d net inflow (USD) |
| `exchange_netflow_7d_d` | Exchange-type 7d net inflow (USD) |
| `exchange_netflow_30d_d` | Exchange-type 30d net inflow (USD) |
| `next_unlock_date_i` | Next unlock timestamp, ms |
| `label_unlock_pressure_i` | Unlock-pressure warning flag; `unlock_pressure_30d_d > 0.05` → `1` |

Note: `market_cap`, `hold_hhi_d`, and `holder_count_i` moved from the daily
table to the hourly table; treat the hourly table as authoritative for
those three fields going forward.

### D. Other top-level identity fields

`symbol`, `exchange`, plus `base_asset`/`market_type`/`chain`/`token_address`
identity fields and `data_ts_i`/`etl_time` metadata fields exist as
top-level fields (no `technical_{interval}.` prefix) but are not factors in
their own right — use them for identity filters (e.g.
`{"left":"exchange","operation":"equal","right":"bitget"}`) rather than
ranking/scoring conditions.

### E. US-stock fundamentals — `asset_class="stock"` only (60 shipped)

Everything in this section is **stock-only**. Reference fields by their **full
name** (including the `financials.` prefix where shown). Do **not** add a
`technical_{interval}.` prefix. These fields are absent from crypto scans.

#### E.1 Identity / corporate structure (14)

| Field | Meaning |
|---|---|
| `sec_code_k` | Security code |
| `sec_short_name_cn_k` | Chinese short name (replaces deprecated `sec_short_name_en_k`) |
| `listed_board_name_k` | Listed board name (e.g. main board, growth board) |
| `listed_date_k` | Listing / first-trade date (`YYYY-MM-DD`); derive listing age downstream |
| `listed_status_k` | Listing status (pipeline pre-filters to active listings) |
| `td_mkt_k` | Exchange (`NYSE`, `NASDAQ`, …) |
| `td_currency_code_k` | Trading currency code |
| `top10_holder_ratio_d` | Top-10 shareholder holding ratio, company-level (%) |
| `insider_increase_1m_flag_i` | Insider buying in the past 30 calendar days (`0`/`1`) |
| `insider_decrease_1m_flag_i` | Insider selling in the past 30 calendar days (`0`/`1`) |
| `total_shares_d` | Total shares outstanding |
| `float_shares_num_d` | Float shares outstanding |
| `float_share_ratio_d` | Float ratio = `float_shares_num_d / total_shares_d` |
| `industry_name_k` | Industry classification name (keyword); use `equal` or `in` to filter by sector/industry — `asset_class="stock"` only |

#### E.2 Valuation (10)

| Field | Meaning |
|---|---|
| `financials.ent_multi_d` | Enterprise multiple (approx. EV/EBITDA) |
| `financials.ev1_d` | Enterprise value (incl. cash) |
| `financials.ev2_d` | Enterprise value (excl. cash) |
| `financials.pb_d` | Price-to-book (PB) |
| `financials.pb_mrq_d` | Price-to-book, most recent quarter |
| `financials.pcf_d` | Price-to-cash-flow (operating CF) |
| `financials.pe_d` | Price-to-earnings (PE) |
| `financials.ps_d` | Price-to-sales (PS) |
| `financials.tmv_usd_d` | Total market cap (USD) |
| `financials.cir_tmv_usd_d` | Float market cap (USD) |

#### E.3 Financial statement levels (12)

| Field | Meaning |
|---|---|
| `financials.net_income_d` | Net income (latest consolidated period) |
| `financials.net_income_atcss_d` | Net income attributable to common shareholders |
| `financials.nav_ps_d` | Book value per share |
| `financials.eps_d` | Basic EPS (latest period, not TTM) |
| `financials.retained_earning_ps_d` | Retained earnings per share |
| `financials.ncf_from_oa_ps_d` | Operating cash flow per share |
| `financials.capital_reserve_ps_d` | Capital reserve per share |
| `financials.cce_d` | Cash & cash equivalents (cross-industry normalized) |
| `financials.total_holders_equity_d` | Total shareholders' equity |
| `financials.free_cash_flow_d` | Free cash flow (OCF + capex payment) |
| `financials.revenue_d` | Revenue (cross-industry normalized) |
| `financials.total_assets_d` | Total assets |

#### E.4 Dividend (2)

| Field | Meaning |
|---|---|
| `financials.dividend_ps_d` | Latest cash dividend per share |
| `financials.div_yield_12m_d` | Dividend yield, trailing 12 months (%) |

#### E.5 Growth (5)

| Field | Meaning |
|---|---|
| `financials.net_profit_yoy_d` | Net profit YoY growth (%) |
| `financials.eps_yoy_d` | Basic EPS YoY growth (%) |
| `financials.ncf_from_oa_yoy_d` | Operating cash flow YoY growth (%) |
| `financials.revenue_yoy_d` | Revenue YoY growth (%) |
| `financials.capex_yoy_d` | Capital expenditure YoY growth (%) |

#### E.6 Solvency / leverage (8)

| Field | Meaning |
|---|---|
| `financials.net_debt_d` | Net debt = ST debt + LT debt − cash (less meaningful for banks) |
| `financials.ebit_to_interest_fee_d` | Interest coverage (EBIT / interest expense) |
| `financials.total_liab_d` | Total liabilities |
| `financials.current_ratio_d` | Current ratio |
| `financials.equity_ratio_d` | Debt-to-equity ratio (liabilities / equity, %) |
| `financials.asset_liab_ratio_d` | Debt-to-assets ratio (%) |
| `financials.quick_ratio_d` | Quick ratio |
| `financials.lt_debt_to_equity_d` | Long-term debt / equity |

#### E.7 Profitability / efficiency (10)

| Field | Meaning |
|---|---|
| `financials.net_profit_margin_d` | Net profit margin (%) |
| `financials.roe_avg_d` | Return on equity, average (%) |
| `financials.roe_dlt_d` | Return on equity, diluted (%) |
| `financials.inventory_turnover_d` | Inventory turnover (×) |
| `financials.account_receivable_turnover_d` | Accounts-receivable turnover (×) |
| `financials.roa_d` | Return on assets (%) |
| `financials.np_to_total_profit_ratio_d` | Net profit / total profit (%) |
| `financials.operating_margin_d` | Operating margin = EBIT / revenue (%) |
| `financials.total_capital_turnover_d` | Total asset turnover (×) |
| `financials.gross_margin_d` | Gross margin (%) |
