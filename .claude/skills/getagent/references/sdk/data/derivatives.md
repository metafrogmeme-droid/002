# Derivatives Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

US listed-options research uses two providers. Do not mix them, and do
not treat OCC option symbols as Bitget tradable pairs.

OpenAPI `operationId` values are flattened snake_case (for example
`derivatives_options_volatility_summaries`). That string is **not** an
HTTP path and is **not** the DataSDK name. Use the dotted Endpoint ID
and the nested Path below, matching the current 3-level classification:

- HTTP: `/inner/v1/agent-data/derivatives/options/volatility/summaries`
- SDK: `data.derivatives.options.volatility.summaries(...)`
- Same pattern for `marketdata/*` (`derivatives_options_marketdata_cbbo`
  → `/derivatives/options/marketdata/cbbo`).

There is no route `/derivatives/derivatives_options_volatility_summaries`.

Selector rules (do not mix `orats` and `databento` on the same call):

| Endpoints | Provider | What to pass |
|---|---|---|
| `options.volatility.*`, `options.chains` | `orats` | Exactly one of `symbol` or `symbols` (max 10). No OCC contract. |
| `options.marketdata.definitions`, `statistics`, `status` | `databento` | Exactly one of `symbol`, `symbols` (max 10), or `contract_symbols`. Underlying-only is valid. |
| `options.marketdata.cbbo`, `trades`, `tcbbo`, `ohlcv` | `databento` | **Both** `symbol` and `contract_symbols` (max 10, same underlying). Do not pass `symbols`. |

For L1 (`cbbo` / `trades` / `tcbbo` / `ohlcv`): copy `contract_symbol` from a `definitions` row. Do not hand-build OSI strings (root padding and strike width are easy to get wrong). If the user already pasted a raw OCC symbol, pass it unchanged. Explicit `start`/`end` must not exceed 1 hour; L1 history must stay within the last 12 months.

`derivatives.options.surface` is a chain-derived chart helper (POST body),
not the ORATS `iv_surface` feed.

## Contents
- [`derivatives.futures.curve`](#derivativesfuturescurve)
- [`derivatives.futures.historical`](#derivativesfutureshistorical)
- [`derivatives.futures.info`](#derivativesfuturesinfo)
- [`derivatives.futures.instruments`](#derivativesfuturesinstruments)
- [`derivatives.options.chains`](#derivativesoptionschains)
- [`derivatives.options.snapshots`](#derivativesoptionssnapshots)
- [`derivatives.options.surface`](#derivativesoptionssurface)
- [`derivatives.options.unusual`](#derivativesoptionsunusual)
- [`derivatives.options.volatility.iv_surface`](#derivativesoptionsvolatilityiv-surface)
- [`derivatives.options.volatility.summaries`](#derivativesoptionsvolatilitysummaries)
- [`derivatives.options.volatility.cores`](#derivativesoptionsvolatilitycores)
- [`derivatives.options.volatility.historical_volatility`](#derivativesoptionsvolatilityhistorical-volatility)
- [`derivatives.options.volatility.iv_rank`](#derivativesoptionsvolatilityiv-rank)
- [`derivatives.options.marketdata.definitions`](#derivativesoptionsmarketdatadefinitions)
- [`derivatives.options.marketdata.cbbo`](#derivativesoptionsmarketdatacbbo)
- [`derivatives.options.marketdata.statistics`](#derivativesoptionsmarketdatastatistics)
- [`derivatives.options.marketdata.trades`](#derivativesoptionsmarketdatatrades)
- [`derivatives.options.marketdata.tcbbo`](#derivativesoptionsmarketdatatcbbo)
- [`derivatives.options.marketdata.ohlcv`](#derivativesoptionsmarketdataohlcv)
- [`derivatives.options.marketdata.status`](#derivativesoptionsmarketdatastatus)

## Endpoint reference

### `derivatives.futures.curve`

```python
data.derivatives.futures.curve(symbol=..., date=None, hours_ago=None)
```

Summary: Curve

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.futures.curve` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/futures/curve` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for.; Symbol to get data for.Default is 'VX_EOD'. Entered dates return the data nearest to the entered date. 'VX_AM' = Mid-Morning TWAP Levels 'VX_EOD' = 4PM Eastern Time Levels; Symbol to get data for. Default is 'btc' Supported symbols are: ['btc', 'eth', 'paxg'] |
| `date` | `no` | `string | null` | `-` | A specific date to get data for. Multiple comma separated items allowed |
| `hours_ago` | `no` | `integer | array | string | null` | `-` | accepts array values Compare the current curve with the specified number of hours ago. Default is None. Multiple comma separated items allowed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `expiration` | `string` | Futures expiration month. |
| `price` | `number` | The price of the futures contract. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `hours_ago` | `integer` | The number of hours ago represented by the price. Only available when hours_ago is set in the query. |

---

### `derivatives.futures.historical`

```python
data.derivatives.futures.historical(symbol=..., start_time=None, end_time=None, expiration=None, interval='1d')
```

Summary: Historical

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.futures.historical` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/futures/historical` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `expiration` | `no` | `string | null` | `-` | Future expiry date with format YYYY-MM |
| `interval` | `no` | `string` | `1d` | Time interval of the data to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `open` | `number` | The open price. |
| `high` | `number` | The high price. |
| `low` | `number` | The low price. |
| `close` | `number` | The close price. |
| `volume` | `number` | The trading volume. |
| `volume_notional` | `number` | Trading volume in quote currency. |

---

### `derivatives.futures.info`

```python
data.derivatives.futures.info(symbol=None)
```

Summary: Info

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.futures.info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/futures/info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Perpetual contracts can be referenced by their currency pair - i.e, SOLUSDC - or by their official Deribit symbol - i.e, SOL_USDC-PERPETUAL For a list of currently available instruments, use `derivatives.futures.instruments()` Multiple comma separated items allowed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `state` | `string` | The state of the order book. Possible values are open and closed. |
| `open_interest` | `number` | The total amount of outstanding contracts in the corresponding amount units. |
| `index_price` | `number` | Current index (reference) price. |
| `best_ask_amount` | `number` | Requested order size of all best asks. |
| `best_ask_price` | `number` | The current best ask price, null if there aren't any asks. |
| `best_bid_price` | `number` | The current best bid price, null if there aren't any bids. |
| `best_bid_amount` | `number` | Requested order size of all best bids. |
| `last_price` | `number` | The price for the last trade. |
| `high` | `number` | Highest price during 24h. |
| `low` | `number` | Lowest price during 24h. |
| `change_percent` | `number` | 24-hour price change expressed as a percentage. |
| `volume` | `number` | Volume during last 24h in base currency. |
| `volume_usd` | `number` | Volume in USD. |
| `mark_price` | `number` | The mark price for the instrument. |
| `settlement_price` | `number` | The settlement price for the instrument. Only when state = open. |
| `delivery_price` | `number` | The settlement price for the instrument. Only when state = closed. |
| `estimated_delivery_price` | `number` | Estimated delivery price for the market. |
| `current_funding` | `number` | Current funding (perpetual only). |
| `funding_8h` | `number` | Funding 8h (perpetual only). |
| `interest_value` | `number` | Value used to calculate realized_funding in positions (perpetual only). |
| `max_price` | `number` | The maximum price for the future. |
| `min_price` | `number` | The minimum price for the future. |
| `timestamp` | `string` | The timestamp of the data. |

---

### `derivatives.futures.instruments`

```python
data.derivatives.futures.instruments()
```

Summary: Instruments

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.futures.instruments` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/futures/instruments` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `instrument_id` | `integer` | Deribit Instrument ID. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `base_currency` | `string` | The underlying currency being traded. |
| `counter_currency` | `string` | Counter currency for the instrument. |
| `quote_currency` | `string` | The currency in which the instrument prices are quoted. |
| `settlement_currency` | `string` | Settlement currency for the instrument. |
| `future_type` | `string` | Type of the instrument. linear or reversed. |
| `settlement_period` | `string` | The settlement period. |
| `price_index` | `string` | Name of price index that is used for this instrument. |
| `contract_size` | `number` | Contract size for instrument. |
| `is_active` | `boolean` | Indicates if the instrument can currently be traded. |
| `creation_timestamp` | `string` | The time when the instrument was first created (milliseconds since the UNIX epoch). |
| `expiration_timestamp` | `string` | The time when the instrument will expire (milliseconds since the UNIX epoch). |
| `tick_size` | `number` | Specifies minimal price change and the number of decimal places for instrument prices. |
| `min_trade_amount` | `number` | Minimum amount for trading, in USD units. |
| `max_leverage` | `integer` | Maximal leverage for instrument. |
| `max_liquidation_commission` | `number` | Maximal liquidation trade commission for instrument. |
| `block_trade_commission` | `number` | Block Trade commission for instrument. |
| `block_trade_min_trade_amount` | `number` | Minimum amount for block trading. |
| `block_trade_tick_size` | `number` | Specifies minimal price change for block trading. |
| `maker_commission` | `number` | Maker commission for instrument. |
| `taker_commission` | `number` | Taker commission for instrument. |

---

### `derivatives.options.chains`

```python
data.derivatives.options.chains(symbol=..., use_cache=True, delay='eod', date=None, option_type=None, moneyness='all', strike_gt=None, strike_lt=None, volume_gt=None, volume_lt=None, oi_gt=None, oi_lt=None, model='black_scholes', show_extended_price=True, include_related_symbols=False)
```

Summary: Chains

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.chains` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/chains` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `use_cache` | `no` | `boolean` | `true` | When True, the company directories will be cached for24 hours and are used to validate symbols. The results of the function are not cached. Set as False to bypass.; Caching is used to validate the supplied ticker symbol, or if a historical EOD chain is requested. To bypass, set to False. |
| `delay` | `no` | `string` | `eod` | enum: eod, realtime, delayed Whether to return delayed, realtime, or eod data. |
| `date` | `no` | `string | null` | `-` | The end-of-day date for options chains data.; A specific date to get data for. |
| `option_type` | `no` | `string | null` | `-` | The option type, call or put, 'None' is both (default). |
| `moneyness` | `no` | `string` | `all` | enum: otm, itm, all Return only contracts that are in or out of the money, default is 'all'. Parameter is ignored when a date is supplied. |
| `strike_gt` | `no` | `integer | null` | `-` | Return options with a strike price greater than the given value. Parameter is ignored when a date is supplied. |
| `strike_lt` | `no` | `integer | null` | `-` | Return options with a strike price less than the given value. Parameter is ignored when a date is supplied. |
| `volume_gt` | `no` | `integer | null` | `-` | Return options with a volume greater than the given value. Parameter is ignored when a date is supplied. |
| `volume_lt` | `no` | `integer | null` | `-` | Return options with a volume less than the given value. Parameter is ignored when a date is supplied. |
| `oi_gt` | `no` | `integer | null` | `-` | Return options with an open interest greater than the given value. Parameter is ignored when a date is supplied. |
| `oi_lt` | `no` | `integer | null` | `-` | Return options with an open interest less than the given value. Parameter is ignored when a date is supplied. |
| `model` | `no` | `string` | `black_scholes` | enum: black_scholes, bjerk The pricing model to use for options chains data, default is 'black_scholes'. Parameter is ignored when a date is supplied. |
| `show_extended_price` | `no` | `boolean` | `true` | Whether to include OHLC type fields, default is True. Parameter is ignored when a date is supplied. |
| `include_related_symbols` | `no` | `boolean` | `false` | Include related symbols that end in a 1 or 2 because of a corporate action, default is False. |

---

### `derivatives.options.snapshots`

```python
data.derivatives.options.snapshots(date=None, only_traded=True)
```

Summary: Snapshots

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.snapshots` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/snapshots` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `date` | `no` | `string | null` | `-` | The date of the data. Can be a datetime or an ISO datetime string. Data appears to go back to around 2022-06-01 Example: '2024-03-08T12:15:00+0400' |
| `only_traded` | `no` | `boolean` | `true` | Only include options that have been traded during the session, default is True. Setting to false will dramatically increase the size of the response - use with caution. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `underlying_symbol` | `array` | Ticker symbol of the underlying asset. |
| `contract_symbol` | `array` | Symbol of the options contract. |
| `expiration` | `array` | Expiration date of the options contract. |
| `dte` | `array` | Number of days to expiration of the options contract. |
| `strike` | `array` | Strike price of the options contract. |
| `option_type` | `array` | The type of option. |
| `volume` | `array` | The trading volume. |
| `open_interest` | `array` | Open interest at the time. |
| `last_price` | `array` | Last trade price at the time. |
| `last_size` | `array` | Lot size of the last trade. |
| `last_timestamp` | `array` | Timestamp of the last price. |
| `open` | `array` | The open price. |
| `high` | `array` | The high price. |
| `low` | `array` | The low price. |
| `close` | `array` | The close price. |
| `bid` | `array` | The last bid price at the time. |
| `bid_size` | `array` | The size of the last bid price. |
| `bid_timestamp` | `array` | The timestamp of the last bid price. |
| `ask` | `array` | The last ask price at the time. |
| `ask_size` | `array` | The size of the last ask price. |
| `ask_timestamp` | `array` | The timestamp of the last ask price. |
| `total_bid_volume` | `array` | Total volume of bids. |
| `bid_high` | `array` | The highest bid price. |
| `bid_low` | `array` | The lowest bid price. |
| `total_ask_volume` | `array` | Total volume of asks. |
| `ask_high` | `array` | The highest ask price. |
| `ask_low` | `array` | The lowest ask price. |

---

### `derivatives.options.surface`

```python
data.derivatives.options.surface(target='implied_volatility', underlying_price=None, option_type='otm', dte_min=None, dte_max=None, moneyness=None, strike_min=None, strike_max=None, oi=False, volume=False, theme='dark', body=...)
```

Summary: Surface

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.surface` |
| HTTP | `POST` |
| Path | `/inner/v1/agent-data/derivatives/options/surface` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `target` | `no` | `string` | `implied_volatility` | - |
| `underlying_price` | `no` | `number | null` | `-` | - |
| `option_type` | `no` | `string | null` | `otm` | - |
| `dte_min` | `no` | `integer | null` | `-` | - |
| `dte_max` | `no` | `integer | null` | `-` | - |
| `moneyness` | `no` | `number | null` | `-` | - |
| `strike_min` | `no` | `number | null` | `-` | - |
| `strike_max` | `no` | `number | null` | `-` | - |
| `oi` | `no` | `boolean` | `false` | - |
| `volume` | `no` | `boolean` | `false` | - |
| `theme` | `no` | `string` | `dark` | enum: dark, light |
| `body` | `yes` | `object` | `-` | JSON request body. |

---

### `derivatives.options.unusual`

```python
data.derivatives.options.unusual(symbol=None, start_time=None, end_time=None, trade_type=None, sentiment=None, min_value=None, max_value=None, limit=100000, source='delayed')
```

Summary: Unusual

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.unusual` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/unusual` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. (the underlying symbol) |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `trade_type` | `no` | `string | null` | `-` | The type of unusual activity to query for. |
| `sentiment` | `no` | `string | null` | `-` | The sentiment type to query for. |
| `min_value` | `no` | `integer | number | null` | `-` | The inclusive minimum total value for the unusual activity. |
| `max_value` | `no` | `integer | number | null` | `-` | The inclusive maximum total value for the unusual activity. |
| `limit` | `no` | `integer` | `100000` | The number of data entries to return. A typical day for all symbols will yield 50-80K records. The API will paginate at 1000 records. The high default limit (100K) is to be able to reliably capture the most days. The high absolute limit (1.25M) is to allow for outlier days. Queries at the absolute limit will take a long time, and might be unreliable. Apply filters to improve performance. |
| `source` | `no` | `string` | `delayed` | The source of the data. Either realtime or delayed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `underlying_symbol` | `string` | Symbol representing the entity requested in the data (the underlying symbol). |
| `contract_symbol` | `string` | Contract symbol for the option. |
| `trade_timestamp` | `string` | The datetime of order placement. |
| `trade_type` | `string` | The type of unusual trade. |
| `sentiment` | `string` | Bullish, Bearish, or Neutral Sentiment estimated based on whether the trade was executed at the bid, ask, or mark price. |
| `bid_at_execution` | `number` | Bid price at execution. |
| `ask_at_execution` | `number` | Ask price at execution. |
| `average_price` | `number` | The average premium paid per option contract. |
| `underlying_price_at_execution` | `number` | Price of the underlying security at execution of trade. |
| `total_size` | `integer` | The total number of contracts involved in a single transaction. |
| `total_value` | `integer` | The aggregated value of all option contract premiums included in the trade. |

---

### `derivatives.options.volatility.iv_surface`

```python
data.derivatives.options.volatility.iv_surface(symbol="AAPL", date=None, interval="1d", provider="orats")
```

Summary: Implied-volatility surface

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.volatility.iv_surface` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/volatility/iv_surface` |
| SDK | `supported` |
| Host | `supported` |
| Notes | ORATS only (`provider="orats"`). Not the POST `derivatives.options.surface` chart helper. `interval=1d` is EOD; `interval=1m` is a one-minute snapshot (date-only values default to 09:31 ET). |

**orats** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Single underlying ticker. Provide exactly one of `symbol` or `symbols`. |
| `symbols` | `no` | `string / null` | `-` | Comma-delimited underlyings, max 10. |
| `date` | `no` | `date / datetime / null` | `-` | Trade date or timestamp. |
| `interval` | `no` | `string` | `1d` | enum: `1d`, `1m`. |
| `fields` | `no` | `string / null` | `-` | Comma-delimited ORATS fields. |
| `provider` | `yes` | `string` | `-` | Must be `orats`. |

**orats** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Underlying ticker. |
| `date` | `date` | Trade date. |
| `expiration` | `date` | Option expiration. |
| `stock_price` | `number / null` | Underlying price. |
| `spot_price` | `number / null` | Index spot, when returned. |
| `risk_free_rate` | `number / null` | Risk-free rate. |
| `yield_rate` | `number / null` | Dividend yield. |
| `confidence` | `number / null` | Surface fit confidence. |
| `atm_iv` | `number / null` | At-the-money IV. |
| `slope` | `number / null` | Skew slope. |
| `derivative` | `number / null` | Skew derivative. |
| `fit` | `number / null` | Surface fit error. |
| `calendar_volatility` | `number / null` | Smoothed calendar vol. |
| `unadjusted_volatility` | `number / null` | Vol before earnings adjustment. |
| `earnings_effect` | `number / null` | Implied earnings effect. |
| `dte` | `integer / null` | Days to expiration. |
| `vol_0` … `vol_100` | `number / null` | IV nodes every 5 delta points. |
| `snapshot_at` | `datetime / null` | One-minute snapshot timestamp. |
| `snapshot_est_time` | `integer / null` | Eastern snapshot time as HHMM. |

---

### `derivatives.options.volatility.summaries`

```python
data.derivatives.options.volatility.summaries(symbol="AAPL", date=None, interval="1d", provider="orats")
```

Summary: Underlying-level volatility summaries

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.volatility.summaries` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/volatility/summaries` |
| SDK | `supported` |
| Host | `supported` |
| Notes | ORATS only. Same `symbol`/`symbols` and `interval=1d|1m` contract as `iv_surface`. |

**orats** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Single underlying. Exactly one of `symbol` or `symbols`. |
| `symbols` | `no` | `string / null` | `-` | Comma-delimited underlyings, max 10. |
| `date` | `no` | `date / datetime / null` | `-` | Trade date or timestamp. |
| `interval` | `no` | `string` | `1d` | enum: `1d`, `1m`. |
| `fields` | `no` | `string / null` | `-` | Comma-delimited ORATS fields. |
| `provider` | `yes` | `string` | `-` | Must be `orats`. |

**orats** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Underlying ticker. |
| `date` | `date` | Trade date. |
| `stock_price` | `number / null` | Underlying price. |
| `confidence` | `number / null` | Fit confidence. |
| `implied_earnings_move` | `number / null` | Move implied by the earnings effect. |
| `implied_move` | `number / null` | Implied move. |
| `earnings_effect` | `number / null` | Earnings effect. |
| `iv_10d` / `iv_20d` / `iv_30d` / `iv_60d` / `iv_90d` / `iv_6m` / `iv_1y` | `number / null` | Term IVs. |
| `ex_earnings_iv_*` | `number / null` | Same tenors excluding earnings. |
| `skew` | `number / null` | Skew. |
| `contango` | `number / null` | Contango. |
| `snapshot_at` | `datetime / null` | One-minute snapshot timestamp. |
| `snapshot_est_time` | `integer / null` | Eastern snapshot time as HHMM. |

---

### `derivatives.options.volatility.cores`

```python
data.derivatives.options.volatility.cores(symbol="AAPL", date=None, provider="orats")
```

Summary: Daily underlying-level core option metrics

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.volatility.cores` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/volatility/cores` |
| SDK | `supported` |
| Host | `supported` |
| Notes | ORATS only. Daily `hist/cores`. Extra ORATS columns may still appear. |

**orats** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Single underlying. Exactly one of `symbol` or `symbols`. |
| `symbols` | `no` | `string / null` | `-` | Comma-delimited underlyings, max 10. |
| `date` | `no` | `date / null` | `-` | Single trade date. |
| `fields` | `no` | `string / null` | `-` | Comma-delimited ORATS fields. |
| `provider` | `yes` | `string` | `-` | Must be `orats`. |

**orats** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Underlying ticker. |
| `date` | `date` | Trade date. |
| `prior_close` | `number / null` | Prior close. |
| `stock_price` | `number / null` | ATM / stock price. |
| `market_cap` | `number / null` | Market cap. |
| `call_volume` / `put_volume` | `integer / null` | Call / put volume. |
| `call_open_interest` / `put_open_interest` / `options_open_interest` | `integer / null` | Open interest. |
| `forecast_volatility_20d` | `number / null` | 20d forecast vol. |
| `forecast_iv_20d` | `number / null` | 20d forecast IV. |
| `ex_earnings_iv_20d` | `number / null` | 20d IV excluding earnings. |
| `historical_volatility_20d` | `number / null` | 20d HV. |
| `implied_volatility_30d` | `number / null` | 30d IV. |
| `slope` / `contango` / `volatility_of_volatility` | `number / null` | Skew / term / vol-of-vol. |
| `implied_move` | `number / null` | Implied straddle-style earnings move (decimal). |
| `implied_earnings_move` | `number / null` | Implied earnings move. |
| `sector_name` | `string / null` | Sector. |

---

### `derivatives.options.volatility.historical_volatility`

```python
data.derivatives.options.volatility.historical_volatility(symbol="AAPL", date=None, provider="orats")
```

Summary: Historical volatility across lookback windows

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.volatility.historical_volatility` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/volatility/historical_volatility` |
| SDK | `supported` |
| Host | `supported` |
| Notes | ORATS only. Same `symbol`/`symbols`/`date` contract as `cores`. |

**orats** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Single underlying. Exactly one of `symbol` or `symbols`. |
| `symbols` | `no` | `string / null` | `-` | Comma-delimited underlyings, max 10. |
| `date` | `no` | `date / null` | `-` | Single trade date. |
| `provider` | `yes` | `string` | `-` | Must be `orats`. |

**orats** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Underlying ticker. |
| `date` | `date` | Trade date. |
| `or_hv_{1,5,10,20,30,60,90,100,120,252,500,1000}d` | `number / null` | ORATS historical vol windows. |
| `close_hv_{5..1000}d` | `number / null` | Close-to-close HV windows. |
| `or_hv_ex_earnings_*` / `close_hv_ex_earnings_*` | `number / null` | Same windows excluding earnings. |

---

### `derivatives.options.volatility.iv_rank`

```python
data.derivatives.options.volatility.iv_rank(symbol="AAPL", date=None, provider="orats")
```

Summary: Implied-volatility rank and percentile

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.volatility.iv_rank` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/volatility/iv_rank` |
| SDK | `supported` |
| Host | `supported` |
| Notes | ORATS only. |

**orats** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Single underlying. Exactly one of `symbol` or `symbols`. |
| `symbols` | `no` | `string / null` | `-` | Comma-delimited underlyings, max 10. |
| `date` | `no` | `date / null` | `-` | Single trade date. |
| `provider` | `yes` | `string` | `-` | Must be `orats`. |

**orats** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Underlying ticker. |
| `date` | `date` | Trade date. |
| `implied_volatility` | `number / null` | Current IV. |
| `iv_rank_1m` / `iv_percentile_1m` | `number / null` | 1-month rank / percentile. |
| `iv_rank_1y` / `iv_percentile_1y` | `number / null` | 1-year rank / percentile. |

---

### `derivatives.options.marketdata.definitions`

```python
data.derivatives.options.marketdata.definitions(symbol="AAPL", provider="databento")
```

Summary: Point-in-time instrument definitions

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.marketdata.definitions` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/marketdata/definitions` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Databento OPRA only (`provider="databento"`). Provide exactly one of `symbol`, `symbols`, or `contract_symbols`. |

**databento** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Single underlying ticker. |
| `symbols` | `no` | `string / null` | `-` | Comma-delimited underlyings, max 10. |
| `contract_symbols` | `no` | `string / null` | `-` | Comma-delimited raw OCC contract symbols. |
| `start` | `no` | `date / datetime / null` | `-` | Inclusive start. |
| `end` | `no` | `date / datetime / null` | `-` | Exclusive end. Must be after `start`. |
| `limit` | `no` | `integer / null` | `-` | Maximum records. |
| `provider` | `yes` | `string` | `-` | Must be `databento`. |

**databento** response:

| Field | Type | Notes |
|---|---|---|
| `received_at` | `datetime` | Definition receive timestamp. |
| `event_at` | `datetime / null` | Definition event timestamp. |
| `instrument_id` | `integer` | Databento numeric instrument ID. |
| `contract_symbol` | `string` | Raw OCC option symbol. |
| `underlying_symbol` | `string / null` | Underlying ticker. |
| `option_type` | `string / null` | Call / put. |
| `expiration` | `datetime / null` | Expiration. |
| `activation` | `datetime / null` | Activation. |
| `strike` | `number / null` | Strike. |
| `contract_multiplier` | `integer / null` | Multiplier. |
| `min_price_increment` | `number / null` | Tick size. |
| `currency` | `string / null` | Currency. |
| `exchange` | `string / null` | Exchange. |
| `security_type` | `string / null` | Security type. |
| `update_action` | `string / null` | Update action. |

---

### `derivatives.options.marketdata.cbbo`

```python
data.derivatives.options.marketdata.cbbo(symbol="AAPL", contract_symbols="AAPL  250919C00200000", interval="1s", provider="databento")
```

Summary: Consolidated best bid and offer

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.marketdata.cbbo` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/marketdata/cbbo` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Databento OPRA L1. Requires `symbol` + `contract_symbols` (max 10, same underlying). Do not pass `symbols`. Explicit `start`/`end` must be within 1 hour and the last 12 months. |

**databento** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single underlying. |
| `contract_symbols` | `yes` | `string` | `-` | Comma-delimited OCC contracts, max 10. |
| `interval` | `no` | `string` | `1s` | enum: `1s`, `1m` (`cbbo-1s` / `cbbo-1m`). |
| `start` | `no` | `date / datetime / null` | `-` | Inclusive start. Required when `end` is set. |
| `end` | `no` | `date / datetime / null` | `-` | Exclusive end. |
| `limit` | `no` | `integer / null` | `10000` | Max records. |
| `provider` | `yes` | `string` | `-` | Must be `databento`. |

**databento** response:

| Field | Type | Notes |
|---|---|---|
| `received_at` | `datetime` | End of the sample interval. |
| `event_at` | `datetime / null` | Last-trade timestamp. |
| `instrument_id` | `integer` | Databento instrument ID. |
| `contract_symbol` | `string` | OCC symbol. |
| `underlying_symbol` | `string / null` | Underlying. |
| `last_price` / `last_size` / `trade_side` | `number / integer / string / null` | Last sale. |
| `bid` / `ask` / `bid_size` / `ask_size` | `number / integer / null` | NBBO. |
| `interval` | `string` | Sample interval. |

---

### `derivatives.options.marketdata.statistics`

```python
data.derivatives.options.marketdata.statistics(symbol="AAPL", provider="databento")
```

Summary: Official venue statistics

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.marketdata.statistics` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/marketdata/statistics` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Databento OPRA. Same selector contract as `definitions` (exactly one of `symbol` / `symbols` / `contract_symbols`). Open interest and session prices. |

**databento** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Single underlying. |
| `symbols` | `no` | `string / null` | `-` | Comma-delimited underlyings, max 10. |
| `contract_symbols` | `no` | `string / null` | `-` | Comma-delimited OCC contracts. |
| `start` | `no` | `date / datetime / null` | `-` | Inclusive start. |
| `end` | `no` | `date / datetime / null` | `-` | Exclusive end. |
| `limit` | `no` | `integer / null` | `-` | Maximum records. |
| `provider` | `yes` | `string` | `-` | Must be `databento`. |

**databento** response:

| Field | Type | Notes |
|---|---|---|
| `received_at` | `datetime` | Statistic receive timestamp. |
| `event_at` | `datetime / null` | Event timestamp. |
| `instrument_id` | `integer` | Databento instrument ID. |
| `contract_symbol` | `string / null` | OCC symbol. |
| `underlying_symbol` | `string / null` | Underlying. |
| `statistic_type` | `integer / null` | Databento `stat_type` code. |
| `statistic_name` | `string / null` | Human-readable statistic type. |
| `price` | `number / null` | Statistic price. |
| `quantity` | `integer / null` | Statistic quantity (e.g. open interest). |
| `reference_at` | `datetime / null` | Reference timestamp. |

---

### `derivatives.options.marketdata.trades`

```python
data.derivatives.options.marketdata.trades(symbol="AAPL", contract_symbols="AAPL  250919C00200000", provider="databento")
```

Summary: Last-sale trades

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.marketdata.trades` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/marketdata/trades` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Databento OPRA L1. Same `symbol` + `contract_symbols` and 1-hour / 12-month window as `cbbo`. |

**databento** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single underlying. |
| `contract_symbols` | `yes` | `string` | `-` | Comma-delimited OCC contracts, max 10. |
| `start` | `no` | `date / datetime / null` | `-` | Inclusive start. Required when `end` is set. |
| `end` | `no` | `date / datetime / null` | `-` | Exclusive end. |
| `limit` | `no` | `integer / null` | `10000` | Max records. |
| `provider` | `yes` | `string` | `-` | Must be `databento`. |

**databento** response:

| Field | Type | Notes |
|---|---|---|
| `received_at` | `datetime` | Capture-server receive timestamp. |
| `event_at` | `datetime / null` | Matching-engine timestamp. |
| `instrument_id` | `integer` | Databento instrument ID. |
| `contract_symbol` | `string / null` | OCC symbol. |
| `underlying_symbol` | `string / null` | Underlying. |
| `price` | `number / null` | Trade price. |
| `size` | `integer / null` | Trade size. |
| `side` | `string / null` | Aggressor side. |
| `action` | `string / null` | Trade action. |

---

### `derivatives.options.marketdata.tcbbo`

```python
data.derivatives.options.marketdata.tcbbo(symbol="AAPL", contract_symbols="AAPL  250919C00200000", provider="databento")
```

Summary: Trades with NBBO immediately before each trade

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.marketdata.tcbbo` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/marketdata/tcbbo` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Databento OPRA L1. Same selector and window contract as `trades`. |

**databento** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single underlying. |
| `contract_symbols` | `yes` | `string` | `-` | Comma-delimited OCC contracts, max 10. |
| `start` | `no` | `date / datetime / null` | `-` | Inclusive start. Required when `end` is set. |
| `end` | `no` | `date / datetime / null` | `-` | Exclusive end. |
| `limit` | `no` | `integer / null` | `10000` | Max records. |
| `provider` | `yes` | `string` | `-` | Must be `databento`. |

**databento** response:

| Field | Type | Notes |
|---|---|---|
| `received_at` | `datetime` | Capture-server receive timestamp. |
| `event_at` | `datetime / null` | Event timestamp. |
| `instrument_id` | `integer` | Databento instrument ID. |
| `contract_symbol` | `string / null` | OCC symbol. |
| `price` / `size` / `side` / `action` | mixed | Trade print. |
| `bid` / `ask` / `bid_size` / `ask_size` | `number / integer / null` | NBBO immediately before the trade. |

---

### `derivatives.options.marketdata.ohlcv`

```python
data.derivatives.options.marketdata.ohlcv(symbol="AAPL", contract_symbols="AAPL  250919C00200000", interval="1s", provider="databento")
```

Summary: One-second OHLCV bars

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.marketdata.ohlcv` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/marketdata/ohlcv` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Databento OPRA. Requires `symbol` + `contract_symbols`. Only `interval=1s` is collected. Explicit `start`/`end` must not exceed 1 hour. |

**databento** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single underlying. |
| `contract_symbols` | `yes` | `string` | `-` | Comma-delimited OCC contracts, max 10. |
| `interval` | `no` | `string` | `1s` | Only `1s`. |
| `start` | `no` | `date / datetime / null` | `-` | Inclusive start. Required when `end` is set. |
| `end` | `no` | `date / datetime / null` | `-` | Exclusive end. |
| `limit` | `no` | `integer / null` | `10000` | Max records. |
| `provider` | `yes` | `string` | `-` | Must be `databento`. |

**databento** response:

| Field | Type | Notes |
|---|---|---|
| `event_at` | `datetime / null` | Inclusive start of the bar. |
| `instrument_id` | `integer` | Databento instrument ID. |
| `contract_symbol` | `string / null` | OCC symbol. |
| `underlying_symbol` | `string / null` | Underlying. |
| `open` / `high` / `low` / `close` | `number / null` | Bar OHLC. |
| `volume` | `integer / null` | Bar volume. |
| `interval` | `string` | Always `1s`. |

---

### `derivatives.options.marketdata.status`

```python
data.derivatives.options.marketdata.status(symbol="AAPL", dte_min=0, dte_max=21, provider="databento")
```

Summary: Trading-status events

| Field | Value |
|---|---|
| Endpoint ID | `derivatives.options.marketdata.status` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/derivatives/options/marketdata/status` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Databento OPRA. Same selector contract as `definitions`. `dte_min` must be `<= dte_max`. |

**databento** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Single underlying. |
| `symbols` | `no` | `string / null` | `-` | Comma-delimited underlyings, max 10. |
| `contract_symbols` | `no` | `string / null` | `-` | Comma-delimited OCC contracts. |
| `start` | `no` | `date / datetime / null` | `-` | Inclusive start. |
| `end` | `no` | `date / datetime / null` | `-` | Exclusive end. |
| `limit` | `no` | `integer / null` | `10000` | Max records. |
| `dte_min` | `no` | `integer / null` | `0` | Minimum days to expiration. |
| `dte_max` | `no` | `integer / null` | `21` | Maximum days to expiration. |
| `provider` | `yes` | `string` | `-` | Must be `databento`. |

**databento** response:

| Field | Type | Notes |
|---|---|---|
| `received_at` | `datetime` | Capture-server receive timestamp. |
| `event_at` | `datetime / null` | Event timestamp. |
| `instrument_id` | `integer` | Databento instrument ID. |
| `contract_symbol` | `string / null` | OCC symbol. |
| `underlying_symbol` | `string / null` | Underlying. |
| `action` / `action_name` | `integer / string / null` | Status action. |
| `reason` | `integer / null` | Status reason code. |
| `trading_event` | `integer / null` | Trading event code. |
| `is_trading` / `is_quoting` / `is_short_sell_restricted` | `string / null` | Status flags. |
