# Derivatives Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`derivatives.futures.curve`](#derivativesfuturescurve)
- [`derivatives.futures.historical`](#derivativesfutureshistorical)
- [`derivatives.futures.info`](#derivativesfuturesinfo)
- [`derivatives.futures.instruments`](#derivativesfuturesinstruments)
- [`derivatives.options.chains`](#derivativesoptionschains)
- [`derivatives.options.snapshots`](#derivativesoptionssnapshots)
- [`derivatives.options.surface`](#derivativesoptionssurface)
- [`derivatives.options.unusual`](#derivativesoptionsunusual)

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
