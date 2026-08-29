# Regulators Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`regulators.cftc.cot`](#regulatorscftccot)
- [`regulators.cftc.cot_search`](#regulatorscftccot-search)
- [`regulators.sec.cik_map`](#regulatorsseccik-map)
- [`regulators.sec.filing_headers`](#regulatorssecfiling-headers)
- [`regulators.sec.htm_file`](#regulatorssechtm-file)
- [`regulators.sec.institutions_search`](#regulatorssecinstitutions-search)
- [`regulators.sec.rss_litigation`](#regulatorssecrss-litigation)
- [`regulators.sec.schema_files`](#regulatorssecschema-files)
- [`regulators.sec.sic_search`](#regulatorssecsic-search)
- [`regulators.sec.symbol_map`](#regulatorssecsymbol-map)
- [`uscongress.bill_info`](#uscongressbill-info)
- [`uscongress.bill_text_urls`](#uscongressbill-text-urls)
- [`uscongress.bills`](#uscongressbills)

## Endpoint reference

### `regulators.cftc.cot`

```python
data.regulators.cftc.cot(start_time=None, end_time=None, id='045601', report_type='legacy', futures_only=False)
```

Summary: Cot

| Field | Value |
|---|---|
| Endpoint ID | `regulators.cftc.cot` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/cftc/cot` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `id` | `no` | `string` | `045601` | A string with the CFTC market code or other identifying string, such as the contract market name, commodity name, or commodity group - i.e, 'gold' or 'japanese yen'.Default report is Fed Funds Futures. Use the 'cftc_market_code' for an exact match. |
| `report_type` | `no` | `string` | `legacy` | enum: legacy, disaggregated, financial, supplemental The type of report to retrieve. Set `id` as 'all' to return all items in the report type (default date range returns the latest report). The Legacy report is broken down by exchange with reported open interest further broken down into three trader classifications: commercial, non-commercial and non-reportable. The Disaggregated reports are broken down by Agriculture and Natural Resource contracts. The Disaggregated reports break down reportable open interest positions into four classifications: Producer/Merchant, Swap Dealers, Managed Money and Other Reportables. The Traders in Financial Futures (TFF) report includes financial contracts. The TFF report breaks down the reported open interest into five classifications: Dealer, Asset Manager, Leveraged Money, Other Reportables and Non-Reportables. |
| `futures_only` | `no` | `boolean` | `false` | Returns the futures-only report. Default is False, for the combined report. |

---

### `regulators.cftc.cot_search`

```python
data.regulators.cftc.cot_search(query='')
```

Summary: Cot Search

| Field | Value |
|---|---|
| Endpoint ID | `regulators.cftc.cot_search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/cftc/cot_search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string` | `` | Search query. |

---

### `regulators.sec.cik_map`

```python
data.regulators.sec.cik_map(symbol=..., use_cache=True)
```

Summary: Cik Map

| Field | Value |
|---|---|
| Endpoint ID | `regulators.sec.cik_map` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/sec/cik_map` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `use_cache` | `no` | `boolean | null` | `true` | Whether or not to use cache for the request, default is True. |

---

### `regulators.sec.filing_headers`

```python
data.regulators.sec.filing_headers(url='', use_cache=True)
```

Summary: Filing Headers

| Field | Value |
|---|---|
| Endpoint ID | `regulators.sec.filing_headers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/sec/filing_headers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `url` | `no` | `string` | `` | URL for the SEC filing. The specific URL is not directly used or downloaded, but is used to generate the base URL for the filing. e.g. https://www.sec.gov/Archives/edgar/data/317540/000031754024000045/coke-20240731.htm and https://www.sec.gov/Archives/edgar/data/317540/000031754024000045/ are both valid URLs for the same filing. |
| `use_cache` | `no` | `boolean` | `true` | Use cache for the index headers and cover page. Default is True. |

---

### `regulators.sec.htm_file`

```python
data.regulators.sec.htm_file(url='', use_cache=True)
```

Summary: Htm File

| Field | Value |
|---|---|
| Endpoint ID | `regulators.sec.htm_file` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/sec/htm_file` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `url` | `no` | `string` | `` | URL for the SEC filing. |
| `use_cache` | `no` | `boolean` | `true` | Cache the file for use later. Default is True. |

---

### `regulators.sec.institutions_search`

```python
data.regulators.sec.institutions_search(query='', use_cache=True)
```

Summary: Institutions Search

| Field | Value |
|---|---|
| Endpoint ID | `regulators.sec.institutions_search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/sec/institutions_search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string` | `` | Search query. |
| `use_cache` | `no` | `boolean | null` | `true` | Whether or not to use cache. |

---

### `regulators.sec.rss_litigation`

```python
data.regulators.sec.rss_litigation()
```

Summary: Rss Litigation

| Field | Value |
|---|---|
| Endpoint ID | `regulators.sec.rss_litigation` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/sec/rss_litigation` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

---

### `regulators.sec.schema_files`

```python
data.regulators.sec.schema_files(taxonomy=None, year=None, component=None, category=None)
```

Summary: Schema Files

| Field | Value |
|---|---|
| Endpoint ID | `regulators.sec.schema_files` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/sec/schema_files` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `taxonomy` | `no` | `string | null` | `-` | Taxonomy family to explore. Omit to list all available taxonomies and their descriptions. |
| `year` | `no` | `integer | null` | `-` | Taxonomy year (e.g. 2011+ for us-gaap, varies by taxonomy). Defaults to the most recent year when omitted. |
| `component` | `no` | `string | null` | `-` | Presentation component to retrieve. Values are taxonomy-specific. Omit to return all components for the taxonomy. |
| `category` | `no` | `string | null` | `-` | Filter taxonomies by SEC filer category. |

---

### `regulators.sec.sic_search`

```python
data.regulators.sec.sic_search(query='', use_cache=True)
```

Summary: Sic Search

| Field | Value |
|---|---|
| Endpoint ID | `regulators.sec.sic_search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/sec/sic_search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string` | `` | Search query. |
| `use_cache` | `no` | `boolean | null` | `true` | Whether or not to use cache. |

---

### `regulators.sec.symbol_map`

```python
data.regulators.sec.symbol_map(query=..., use_cache=True)
```

Summary: Symbol Map

| Field | Value |
|---|---|
| Endpoint ID | `regulators.sec.symbol_map` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/sec/symbol_map` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `yes` | `string` | `-` | Search query. |
| `use_cache` | `no` | `boolean | null` | `true` | Whether or not to use cache. If True, cache will store for seven days. |

---

### `uscongress.bill_info`

```python
data.uscongress.bill_info(bill_url=None)
```

Summary: Bill Info

| Field | Value |
|---|---|
| Endpoint ID | `uscongress.bill_info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/uscongress/bill_info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `bill_url` | `no` | `string | null` | `-` | Enter a base URL of a bill (e.g., 'https://api.congress.gov/v3/bill/119/s/1947?format=json'). Alternatively, you can enter a bill number (e.g., '119/s/1947'). |

---

### `uscongress.bill_text_urls`

```python
data.uscongress.bill_text_urls(bill_url=..., is_workspace=False)
```

Summary: Bill Text Urls

| Field | Value |
|---|---|
| Endpoint ID | `uscongress.bill_text_urls` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/uscongress/bill_text_urls` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `bill_url` | `yes` | `string` | `-` | Base URL or bill number of the bill to retrieve document choices for. |
| `is_workspace` | `no` | `boolean` | `false` | - |

---

### `uscongress.bills`

```python
data.uscongress.bills(congress=None, bill_type=None, start_time=None, end_time=None, limit=100, offset=0, sort_by='desc')
```

Summary: Bills

| Field | Value |
|---|---|
| Endpoint ID | `uscongress.bills` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/regulators/uscongress/bills` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `congress` | `no` | `integer | null` | `-` | Congress number (e.g., 118 for the 118th Congress). The 103rd Congress started in 1993. Each Congress spans two years, starting in odd-numbered years. |
| `bill_type` | `no` | `string | null` | `-` | Bill type. Must be one of: hr, s, hjres, sjres, hconres, sconres, hres, sres. |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Filters bills by last updated date. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Filters bills by last updated date. |
| `limit` | `no` | `integer | null` | `100` | The number of data entries to return. Default 100, max 250. Set to 0 for no limit (must be used with 'bill_type' and 'congress'). |
| `offset` | `no` | `integer | null` | `0` | The starting record returned. 0 is the first record. |
| `sort_by` | `no` | `string` | `desc` | Sort by update date. Default is latest first. enum: asc, desc |
