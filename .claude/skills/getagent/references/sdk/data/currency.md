# Currency Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`currency.price.historical`](#currencypricehistorical)
- [`currency.reference_rates`](#currencyreference-rates)
- [`currency.search`](#currencysearch)
- [`currency.snapshots`](#currencysnapshots)

## Endpoint reference

### `currency.price.historical`

```python
data.currency.price.historical(symbol=..., start_time=None, end_time=None, interval='1d')
```

Summary: Historical

| Field | Value |
|---|---|
| Endpoint ID | `currency.price.historical` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/currency/price/historical` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Can use CURR1-CURR2 or CURR1CURR2 format. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
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
| `vwap` | `number` | Volume Weighted Average Price over the period. |
| `change` | `number` | Change in the price from the previous close. |
| `change_percent` | `number` | Percent change in the price from the previous close. |

---

### `currency.reference_rates`

```python
data.currency.reference_rates()
```

Summary: Reference Rates

| Field | Value |
|---|---|
| Endpoint ID | `currency.reference_rates` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/currency/reference_rates` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

---

### `currency.search`

```python
data.currency.search(query=None)
```

Summary: Search

| Field | Value |
|---|---|
| Endpoint ID | `currency.search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/currency/search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string | null` | `-` | Query to search for currency pairs. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the currency pair. |
| `base_currency` | `string` | ISO 4217 currency code of the base currency. |
| `quote_currency` | `string` | ISO 4217 currency code of the quote currency. |
| `from_currency` | `string` | Base currency of the currency pair. |
| `to_currency` | `string` | Quote currency of the currency pair. |
| `from_name` | `string` | Name of the base currency. |
| `to_name` | `string` | Name of the quote currency. |

---

### `currency.snapshots`

```python
data.currency.snapshots(base='usd', quote_type='indirect', counter_currencies=None)
```

Summary: Snapshots

| Field | Value |
|---|---|
| Endpoint ID | `currency.snapshots` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/currency/snapshots` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `base` | `no` | `string` | `usd` | The base currency symbol. Multiple comma separated items allowed |
| `quote_type` | `no` | `string` | `indirect` | enum: direct, indirect Whether the quote is direct or indirect. Selecting 'direct' will return the exchange rate as the amount of domestic currency required to buy one unit of the foreign currency. Selecting 'indirect' (default) will return the exchange rate as the amount of foreign currency required to buy one unit of the domestic currency. |
| `counter_currencies` | `no` | `string | array | null` | `-` | accepts array values An optional list of counter currency symbols to filter for. None returns all. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `base_currency` | `string` | The base, or domestic, currency. |
| `counter_currency` | `string` | The counter, or foreign, currency. |
| `last_rate` | `number` | The exchange rate, relative to the base currency. |
| `open` | `number` | The open price. |
| `high` | `number` | The high price. |
| `low` | `number` | The low price. |
| `close` | `number` | The close price. |
| `volume` | `integer` | The trading volume. |
| `prev_close` | `number` | The previous close price. |
| `last_rate_timestamp` | `string` | UTC timestamp of when the exchange rate was last updated. |
| `change` | `number` | The change in the price from the previous close. |
| `change_percent` | `number` | The change in the price from the previous close, as a normalized percent. |
| `ma_50` | `number` | The 50-day moving average. |
| `ma_200` | `number` | The 200-day moving average. |
| `year_high` | `number` | The 52-week high. |
| `year_low` | `number` | The 52-week low. |
