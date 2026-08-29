# Index Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`index.available`](#indexavailable)
- [`index.constituents`](#indexconstituents)
- [`index.price.historical`](#indexpricehistorical)
- [`index.search`](#indexsearch)
- [`index.sectors`](#indexsectors)
- [`index.snapshots`](#indexsnapshots)
- [`index.sp500_multiples`](#indexsp500-multiples)

## Endpoint reference

### `index.available`

```python
data.index.available(use_cache=True)
```

Summary: Available

| Field | Value |
|---|---|
| Endpoint ID | `index.available` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/index/available` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `use_cache` | `no` | `boolean` | `true` | When True, the Cboe Index directory will be cached for 24 hours. Set as False to bypass.; Whether to use a cached request. Index data is from a single JSON file, updated each day after close. It is cached for one day. To bypass, set to False. |

---

### `index.constituents`

```python
data.index.constituents(symbol=..., historical=False, use_cache=True)
```

Summary: Constituents

| Field | Value |
|---|---|
| Endpoint ID | `index.constituents` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/index/constituents` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `historical` | `no` | `boolean` | `false` | Flag to retrieve historical removals and additions. |
| `use_cache` | `no` | `boolean` | `true` | Whether to use a cached request. Index data is from a single JSON file, updated each day after close. It is cached for one day. To bypass, set to False. |

---

### `index.price.historical`

```python
data.index.price.historical(symbol=..., start_time=None, end_time=None, interval='1d', use_cache=True, limit=1000)
```

Summary: Historical

| Field | Value |
|---|---|
| Endpoint ID | `index.price.historical` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/index/price/historical` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `interval` | `no` | `string` | `1d` | Time interval of the data to return. The most recent trading day is not including in daily historical data. Intraday data is only available for the most recent trading day at 1 minute intervals.; Time interval of the data to return. |
| `use_cache` | `no` | `boolean` | `true` | When True, the company directories will be cached for 24 hours and are used to validate symbols. The results of the function are not cached. Set as False to bypass. |
| `limit` | `no` | `integer | null` | `1000` | The number of data entries to return. Max 1000. |

---

### `index.search`

```python
data.index.search(query='', is_symbol=False, use_cache=True)
```

Summary: Search

| Field | Value |
|---|---|
| Endpoint ID | `index.search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/index/search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string` | `` | Search query. |
| `is_symbol` | `no` | `boolean` | `false` | Whether to search by ticker symbol. |
| `use_cache` | `no` | `boolean` | `true` | When True, the Cboe Index directory will be cached for 24 hours. Set as False to bypass. |

---

### `index.sectors`

```python
data.index.sectors(symbol=..., use_cache=True)
```

Summary: Sectors

| Field | Value |
|---|---|
| Endpoint ID | `index.sectors` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/index/sectors` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `use_cache` | `no` | `boolean` | `true` | Whether to use a cached request. All Index data comes from a single JSON file that is updated daily. To bypass, set to False. If True, the data will be cached for 1 day. |

---

### `index.snapshots`

```python
data.index.snapshots(region='us', use_cache=True)
```

Summary: Snapshots

| Field | Value |
|---|---|
| Endpoint ID | `index.snapshots` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/index/snapshots` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `region` | `no` | `string` | `us` | The region of focus for the data - i.e., us, eu. |
| `use_cache` | `no` | `boolean` | `true` | Whether to use a cached request. Index data is from a single JSON file, updated each day after close. It is cached for one day. To bypass, set to False. |

---

### `index.sp500_multiples`

```python
data.index.sp500_multiples(start_time=None, end_time=None, series_name='pe_month')
```

Summary: Sp500 Multiples

| Field | Value |
|---|---|
| Endpoint ID | `index.sp500_multiples` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/index/sp500_multiples` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `series_name` | `no` | `string` | `pe_month` | The name of the series. Defaults to 'pe_month'. Multiple comma separated items allowed |
