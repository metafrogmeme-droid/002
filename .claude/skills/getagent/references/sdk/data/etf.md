# Etf Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`etf.countries`](#etfcountries)
- [`etf.discovery.active`](#etfdiscoveryactive)
- [`etf.discovery.gainers`](#etfdiscoverygainers)
- [`etf.discovery.losers`](#etfdiscoverylosers)
- [`etf.equity_exposure`](#etfequity-exposure)
- [`etf.historical`](#etfhistorical)
- [`etf.holdings`](#etfholdings)
- [`etf.info`](#etfinfo)
- [`etf.nport_disclosure`](#etfnport-disclosure)
- [`etf.price_performance`](#etfprice-performance)
- [`etf.search`](#etfsearch)
- [`etf.sectors`](#etfsectors)

## `bitget_data` provider (THS US ETFs)

Use this section, not the default-provider tables below, when calling
Tonghuashun-backed US ETF data. Always pass `provider="bitget_data"` and a
single uppercase US ETF `symbol`. Dates are `YYYY-MM-DD`.

Do not send `date`, `use_cache`, `return_type`, or `adjustment` for THS.
Those belong to other providers and are ignored or rejected.

| Endpoint | Query after `symbol` + `provider` | Response fields |
|---|---|---|
| `etf.info` | none | `symbol`, `name` (from `underlying_cn`), `issuer` (from `publisher`), `publisher`, `etf_admin`, `underlying_cn`, `leverage_ratio`, `td_direction`, `expense_ratio`, `dividend_frequency`, `etf_type`, `assets_type`, `assets_style`, `the_industry`, `thedistrict`, `bond_type` |
| `etf.holdings` | `ed` (holding date). Omit to get the latest dated snapshot | `name` (from `constituent_name`), `ed`, `constituent_name`, `constituent_code`, `constituent_num`, `constituent_market_value`, `fund_net_assets_rate` |
| `etf.price_performance` | `start_date`, `end_date`. Omit `start_date` for latest 30 days | `date` (from `dt`), `dt`, `fund_nav`, `fund_total_assets`, `return_this_year`, `premium_rate`, `dividend_rate`, `expense_ratio` |

Stock-level ETF inflow/outflow is `equity.fund_flow.etf`, not an `etf.*`
endpoint.

## Endpoint reference

### `etf.countries`

```python
data.etf.countries(symbol=..., use_cache=True)
```

Summary: Countries

| Field | Value |
|---|---|
| Endpoint ID | `etf.countries` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/countries` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `use_cache` | `no` | `boolean` | `true` | Whether to use a cached request. All ETF data comes from a single JSON file that is updated daily. To bypass, set to False. If True, the data will be cached for 4 hours. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `country` | `string` | The country of the exposure. Corresponding values are normalized percentage points. |
| `weight` | `number` | The net exposure of the ETF to the country as a percentage of the total ETF assets. |

---

### `etf.discovery.active`

```python
data.etf.discovery.active(sort='desc', limit=10)
```

Summary: Active

| Field | Value |
|---|---|
| Endpoint ID | `etf.discovery.active` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/discovery/active` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer` | `10` | The number of data entries to return. Max 100. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `last_price` | `number` | Last price. |
| `percent_change` | `number` | Percent change. |
| `net_change` | `number` | Net change. |
| `volume` | `number` | The trading volume. |
| `date` | `string` | The date of the data. |
| `country` | `string` | Country of the entity. |
| `mantissa` | `integer` | Mantissa. |
| `type` | `string` | Type of the entity. |
| `formatted_price` | `string` | Formatted price. |
| `formatted_volume` | `string` | Formatted volume. |
| `formatted_price_change` | `string` | Formatted price change. |
| `formatted_percent_change` | `string` | Formatted percent change. |
| `url` | `string` | The source url. |

---

### `etf.discovery.gainers`

```python
data.etf.discovery.gainers(sort='desc', limit=10)
```

Summary: Gainers

| Field | Value |
|---|---|
| Endpoint ID | `etf.discovery.gainers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/discovery/gainers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer` | `10` | The number of data entries to return. Max 100. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `last_price` | `number` | Last price. |
| `percent_change` | `number` | Percent change. |
| `net_change` | `number` | Net change. |
| `volume` | `number` | The trading volume. |
| `date` | `string` | The date of the data. |
| `bluegrass_channel` | `string` | Bluegrass channel. |
| `country` | `string` | Country of the entity. |
| `mantissa` | `integer` | Mantissa. |
| `type` | `string` | Type of the entity. |
| `formatted_price` | `string` | Formatted price. |
| `formatted_volume` | `string` | Formatted volume. |
| `formatted_price_change` | `string` | Formatted price change. |
| `formatted_percent_change` | `string` | Formatted percent change. |
| `url` | `string` | The source url. |

---

### `etf.discovery.losers`

```python
data.etf.discovery.losers(sort='desc', limit=10)
```

Summary: Losers

| Field | Value |
|---|---|
| Endpoint ID | `etf.discovery.losers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/discovery/losers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer` | `10` | The number of data entries to return. Max 100. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `last_price` | `number` | Last price. |
| `percent_change` | `number` | Percent change. |
| `net_change` | `number` | Net change. |
| `volume` | `number` | The trading volume. |
| `date` | `string` | The date of the data. |
| `bluegrass_channel` | `string` | Bluegrass channel. |
| `country` | `string` | Country of the entity. |
| `mantissa` | `integer` | Mantissa. |
| `type` | `string` | Type of the entity. |
| `formatted_price` | `string` | Formatted price. |
| `formatted_volume` | `string` | Formatted volume. |
| `formatted_price_change` | `string` | Formatted price change. |
| `formatted_percent_change` | `string` | Formatted percent change. |
| `url` | `string` | The source url. |

---

### `etf.equity_exposure`

```python
data.etf.equity_exposure(symbol=...)
```

Summary: Equity Exposure

| Field | Value |
|---|---|
| Endpoint ID | `etf.equity_exposure` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/equity_exposure` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. (underlying equity) Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `equity_symbol` | `string` | The symbol of the equity requested. |
| `etf_symbol` | `string` | The symbol of the ETF with exposure to the requested equity. |
| `weight` | `number` | The weight of the equity in the ETF, as a normalized percent. |
| `market_value` | `integer` | The market value of the equity position in the ETF. |
| `shares` | `integer` | Number of reported shares controlled by the ETF. |

---

### `etf.historical`

```python
data.etf.historical(symbol=..., start_time=None, end_time=None, interval='1d', adjustment='splits_only', extended_hours=False, use_cache=True, start_clock_time=None, end_clock_time=None, timezone='America/New_York', source='realtime', include_actions=True)
```

Summary: Historical

| Field | Value |
|---|---|
| Endpoint ID | `etf.historical` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/historical` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed; A Security identifier (Ticker, FIGI, ISIN, CUSIP, Intrinio ID). |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `interval` | `no` | `string | integer` | `1d` | Time interval of the data to return. |
| `adjustment` | `no` | `string` | `splits_only` | The adjustment factor to apply. 'splits_only' is not supported for intraday data.; Type of adjustment for historical prices. Only applies to daily data.; The adjustment factor to apply. Only valid for daily data.; The adjustment factor to apply. Default is splits only. |
| `extended_hours` | `no` | `boolean` | `false` | Include Pre and Post market data. |
| `use_cache` | `no` | `boolean` | `true` | When True, the company directories will be cached for 24 hours and are used to validate symbols. The results of the function are not cached. Set as False to bypass. |
| `start_clock_time` | `no` | `string | null` | `-` | Return intervals starting at the specified time on the `start_date` formatted as 'HH:MM:SS'. |
| `end_clock_time` | `no` | `string | null` | `-` | Return intervals stopping at the specified time on the `end_date` formatted as 'HH:MM:SS'. |
| `timezone` | `no` | `string | null` | `America/New_York` | Timezone of the data, in the IANA format (Continent/City). |
| `source` | `no` | `string` | `realtime` | enum: realtime, delayed, nasdaq_basic The source of the data. |
| `include_actions` | `no` | `boolean` | `true` | Include dividends and stock splits in results. |

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
| `adj_open` | `number` | The adjusted open price. |
| `adj_high` | `number` | The adjusted high price. |
| `adj_low` | `number` | The adjusted low price. |
| `adj_close` | `number` | The adjusted close price. |
| `adj_volume` | `number` | The adjusted volume. |
| `split_ratio` | `number` | Ratio of the equity split, if a split occurred. |
| `dividend` | `number` | Dividend amount, if a dividend was paid. |
| `calls_volume` | `integer` | Number of calls traded during the most recent trading period. Only valid if interval is 1m. |
| `puts_volume` | `integer` | Number of puts traded during the most recent trading period. Only valid if interval is 1m. |
| `total_options_volume` | `integer` | Total number of options traded during the most recent trading period. Only valid if interval is 1m. |
| `change` | `number` | Change in the price from the previous close. |
| `change_percent` | `number` | Change in the price from the previous close, as a normalized percent. |
| `average` | `number` | Average trade price of an individual equity during the interval. |
| `fifty_two_week_high` | `number` | 52 week high price for the symbol. |
| `fifty_two_week_low` | `number` | 52 week low price for the symbol. |
| `factor` | `number` | Factor by which to multiply equity prices before this date, in order to calculate historically-adjusted equity prices. |
| `close_time` | `string` | The timestamp that represents the end of the interval span. |
| `interval` | `string` | The data time frequency. |
| `intra_period` | `boolean` | If true, the equity price represents an unfinished period. |
| `transactions` | `integer` | Total number of transactions recorded. |
| `transactions_value` | `number` | Nominal value of recorded transactions. |
| `last_price` | `number` | The last price of the equity. |

---

### `etf.holdings`

```python
data.etf.holdings(symbol="SPY", ed=None, provider="bitget_data")
```

Summary: Holdings

| Field | Value |
|---|---|
| Endpoint ID | `etf.holdings` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/holdings` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** tables; ignore other-provider params/fields. Use `ed`, not `date`. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ETF ticker. |
| `ed` | `no` | `date / null` | `-` | Holding date `YYYY-MM-DD`. Not `date`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |

**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `name` | `string / null` | Mapped from `constituent_name`. |
| `ed` | `date / null` | Holding date. |
| `constituent_name` | `string / null` | Constituent name. |
| `constituent_code` | `string / null` | Constituent ticker/code. |
| `constituent_num` | `number / null` | Shares held. |
| `constituent_market_value` | `number / null` | Market value. |
| `fund_net_assets_rate` | `number / null` | Weight of fund NAV. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. (ETF) |
| `date` | `no` | `string | null` | `-` | A specific date to get data for. |
| `use_cache` | `no` | `boolean` | `true` | Whether to use a cached request. All ETF data comes from a single JSON file that is updated daily. To bypass, set to False. If True, the data will be cached for 4 hours. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | The ticker symbol of the asset. |
| `name` | `string` | The name of the asset. |
| `weight` | `number` | The weight of the asset in the portfolio, as a normalized percentage. |
| `shares` | `integer` | The value of the assets under management. |
| `market_value` | `number` | The market value of the holding. |
| `currency` | `string` | The currency of the holding. |
| `share_percentage` | `number` | The share percentage of the holding, as a normalized percentage. |
| `share_change` | `number` | The change in shares of the holding. |
| `country` | `string` | The country of the holding. |
| `exchange` | `string` | The exchange code of the holding. |
| `type_id` | `string` | The holding type ID of the asset. |
| `fund_id` | `string` | The fund ID of the asset. |
| `cusip` | `string` | The CUSIP of the holding. |
| `isin` | `string` | The ISIN of the holding. |
| `value` | `number` | The market value of the holding. |
| `updated` | `string` | The date the data was updated. |
| `security_type` | `string` | The type of instrument for this holding. |
| `ric` | `string` | The Reuters Instrument Code. |
| `sedol` | `string` | The Stock Exchange Daily Official List. |
| `share_class_figi` | `string` | The OpenFIGI symbol for the holding. |
| `maturity_date` | `string` | The maturity date for the debt security, if available. |
| `contract_expiry_date` | `string` | Expiry date for the futures contract held, if available. |
| `coupon` | `number` | The coupon rate of the debt security, if available. |
| `balance` | `integer` | The number of units of the security held, if available. |
| `unit` | `string` | The units of the 'balance' field. |
| `units_per_share` | `number` | Number of units of the security held per share outstanding of the ETF, if available. |
| `face_value` | `number` | The face value of the debt security, if available. |
| `derivatives_value` | `number` | The notional value of derivatives contracts held. |

---
### `etf.info`

```python
data.etf.info(symbol="SPY", provider="bitget_data")
```

Summary: Info

| Field | Value |
|---|---|
| Endpoint ID | `etf.info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ETF ticker. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |

**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | ETF ticker. |
| `name` | `string / null` | Mapped from `underlying_cn`. |
| `issuer` | `string / null` | Mapped from `publisher`. |
| `publisher` | `string / null` | Publisher. |
| `etf_admin` | `string / null` | Administrator. |
| `underlying_cn` | `string / null` | Underlying. |
| `leverage_ratio` | `number / null` | Leverage. |
| `td_direction` | `string / null` | Long/short direction. |
| `expense_ratio` | `number / null` | Expense ratio. |
| `dividend_frequency` | `string / null` | Dividend frequency. |
| `etf_type` | `string / null` | ETF type. |
| `assets_type` | `string / null` | Asset type. |
| `assets_style` | `string / null` | Style. |
| `the_industry` | `string / null` | Industry. |
| `thedistrict` | `string / null` | Region. |
| `bond_type` | `string / null` | Bond type. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. (ETF) Multiple comma separated items allowed |
| `use_cache` | `no` | `boolean` | `true` | Whether to use a cached request. All ETF data comes from a single JSON file that is updated daily. To bypass, set to False. If True, the data will be cached for 4 hours. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. (ETF) |
| `name` | `string` | Name of the ETF. |
| `issuer` | `string` | Issuer of the ETF. |
| `domicile` | `string` | Domicile of the ETF. |
| `website` | `string` | Website of the ETF. |
| `description` | `string` | Description of the fund. |
| `inception_date` | `string` | Inception date of the ETF. |
| `cusip` | `string` | CUSIP of the ETF. |
| `isin` | `string` | ISIN of the ETF. |
| `asset_class` | `string` | Asset class of the ETF. |
| `currency` | `string` | Currency of the ETF's net asset value. |
| `holdings_count` | `integer` | Number of holdings. |
| `aum` | `number` | Assets under management. |
| `expense_ratio` | `number` | The expense ratio, as a normalized percent. |
| `nav` | `number` | Net asset value of the ETF. |
| `volume_avg` | `integer` | Average daily trading volume. |
| `updated` | `string` | As of date for the latest data point. |
| `fund_listing_date` | `string` | The date on which the ETP or share class is listed on a specific exchange. |
| `data_change_date` | `string` | The last date on which there was a change in a classifications data field for this ETF. |
| `etn_maturity_date` | `string` | If the product is an ETN, this field identifies the maturity date. |
| `is_listed` | `boolean` | If true, the ETF is still listed on an exchange. |
| `close_date` | `string` | The date on which the ETF was de-listed if it is no longer listed. |
| `exchange` | `string` | The exchange Market Identifier Code (MIC). |
| `ric` | `string` | Reuters Instrument Code (RIC). |
| `sedol` | `string` | Stock Exchange Daily Official List (SEDOL). |
| `figi_symbol` | `string` | Financial Instrument Global Identifier (FIGI) symbol. |
| `share_class_figi` | `string` | Financial Instrument Global Identifier (FIGI). |
| `firstbridge_id` | `string` | The FirstBridge unique identifier for the ETF. |
| `firstbridge_parent_id` | `string` | The FirstBridge unique identifier for the parent ETF, if applicable. |
| `intrinio_id` | `string` | Intrinio unique identifier for the security. |
| `intraday_nav_symbol` | `string` | Intraday Net Asset Value (NAV) symbol. |
| `primary_symbol` | `string` | The primary ticker field for ETPs that have multiple listings and share classes. |
| `etp_structure_type` | `string` | Classifies ETPs into broad categories based on legal structure. |
| `legal_structure` | `string` | Legal structure of the fund. |
| `etn_issuing_bank` | `string` | If the product is an ETN, identifies the issuing bank. |
| `fund_family` | `string` | The fund family to which the ETF belongs. |
| `investment_style` | `string` | Investment style of the ETF. |
| `derivatives_based` | `string` | Populated if the ETF holds listed or over-the-counter derivatives. |
| `income_category` | `string` | Identifies if an ETF is designed to provide high yield or income. |
| `other_asset_types` | `string` | If 'asset_class' is 'Other Asset Types', captures the specific category. |
| `single_category_designation` | `string` | Categorization forcing every ETF into a single bucket. |
| `beta_type` | `string` | Identifies whether an ETF provides 'Traditional' or 'Smart' beta exposure. |
| `beta_details` | `string` | Further detail within the traditional and smart beta categories. |
| `market_cap_range` | `string` | Equity ETFs classified by market cap description. |
| `market_cap_weighting_type` | `string` | For market cap weighted ETFs, provides detail on the weighting type. |
| `index_weighting_scheme` | `string` | For ETFs tracking an index, provides detail on the index weighting type. |
| `index_linked` | `string` | Identifies whether an ETF is index linked or active. |
| `index_name` | `string` | Name of the underlying index tracked by the ETF. |
| `index_symbol` | `string` | OpenFIGI ticker for the Index underlying the ETF. |
| `parent_index` | `string` | Name of the parent index. |
| `index_family` | `string` | Index family to which the underlying index belongs. |
| `broader_index_family` | `string` | Broader index family to which the underlying index belongs. |
| `index_provider` | `string` | Index provider for the index underlying the ETF. |
| `index_provider_code` | `string` | First Bridge code for each Index provider. |
| `replication_structure` | `string` | The replication structure of the ETP. |
| `growth_value_tilt` | `string` | Classifies equity ETFs as 'Growth', 'Value', or 'Core / Blend'. |
| `growth_type` | `string` | Further identifies growth ETFs selected and weighted by growth scores. |
| `value_type` | `string` | Further identifies value ETFs selected and weighted by value scores. |
| `sector` | `string` | For equity ETFs with targeted sector exposure, identifies the sector. |
| `industry` | `string` | For equity ETFs with targeted industry exposure, identifies the industry. |
| `industry_group` | `string` | For equity ETFs with targeted sub-industry exposure, identifies the sub-industry. |
| `cross_sector_theme` | `string` | For equity ETFs with cross-sector theme exposure, identifies the theme. |
| `natural_resources_type` | `string` | For ETFs classified as 'Natural Resources', provides further detail. |
| `us_or_excludes_us` | `string` | Takes the value 'Domestic', 'International', or 'Global'. |
| `developed_emerging` | `string` | Identifies the stage of development of markets the ETF provides exposure to. |
| `specialized_region` | `string` | Populated if the ETF provides targeted exposure to a specific geography grouping. |
| `continent` | `string` | Populated if the ETF provides targeted exposure to a specific continent. |
| `latin_america_sub_group` | `string` | Further detail for Latin America classified ETFs. |
| `europe_sub_group` | `string` | Further detail for Europe classified ETFs. |
| `asia_sub_group` | `string` | Further detail for Asia classified ETFs. |
| `specific_country` | `string` | Populated if the ETF provides targeted exposure to a specific country. |
| `china_listing_location` | `string` | For China ETFs, provides further detail on the type of exposure. |
| `us_state` | `string` | Takes the value of a US state if the ETF provides targeted exposure. |
| `real_estate` | `string` | For real estate ETFs, identifies the specific segment of the real estate market. |
| `fundamental_weighting_type` | `string` | For fundamental weighted ETFs, provides detail on the methodology. |
| `dividend_weighting_type` | `string` | For dividend weighted ETFs, provides detail on the methodology. |
| `bond_type` | `string` | For bond ETFs, provides detail on the type of bonds held. |
| `government_bond_types` | `string` | For government bond ETFs, provides detail on the exposure. |
| `municipal_bond_region` | `string` | For municipal bond ETFs, provides additional detail on geographic exposure. |
| `municipal_vrdo` | `boolean` | For municipal bond ETFs, identifies those holding Variable Rate Demand Obligations. |
| `mortgage_bond_types` | `string` | For mortgage bond ETFs, provides additional detail on underlying securities. |
| `bond_tax_status` | `string` | For US bond ETFs, provides additional detail on tax treatment. |
| `credit_quality` | `string` | For bond ETFs, identifies targeted credit quality range. |
| `average_maturity` | `string` | For bond ETFs, identifies targeted maturity range. |
| `specific_maturity_year` | `integer` | For bond ETFs with 'Specific Maturity Year', specifies the calendar year. |
| `commodity_types` | `string` | For commodity ETFs, provides detail on the type of commodities held. |
| `energy_type` | `string` | For energy commodity ETFs, provides detail on the type of energy exposure. |
| `agricultural_type` | `string` | For agricultural commodity ETFs, provides detail on the type of exposure. |
| `livestock_type` | `string` | For livestock commodity ETFs, provides detail on the type of exposure. |
| `metal_type` | `string` | For gold and metals ETFs, provides detail on the type of exposure. |
| `inverse_leveraged` | `string` | Populated if the ETF provides inverse or leveraged exposure. |
| `target_date_multi_asset_type` | `string` | For target date/multi-asset ETFs, provides detail on the type. |
| `currency_pair` | `string` | Populated if the ETF's strategy involves currency exposure or hedging. |
| `social_environmental_type` | `string` | Populated if the ETF's strategy involves social or environmental theme exposure. |
| `clean_energy_type` | `string` | Populated if the ETF has a value of 'Clean Energy' in social_environmental_type. |
| `dividend_type` | `string` | Populated if the ETF has an objective of holding dividend-oriented stocks. |
| `regular_dividend_payor_type` | `string` | Populated for ETFs with 'Dividend - Regular Payors' in dividend_type. |
| `quant_strategies_type` | `string` | Populated if the ETF has an index-linked or active quantitative strategy. |
| `other_quant_models` | `string` | For 'Other Quant Model' ETFs, provides the name of the proprietary quant model. |
| `hedge_fund_type` | `string` | For hedge fund replication ETFs, provides detail on the strategy type. |
| `excludes_financials` | `boolean` | If true, the ETF will not hold financials stocks. |
| `excludes_technology` | `boolean` | If true, the ETF will not hold technology stocks. |
| `holds_only_nyse_stocks` | `boolean` | If true, the ETF holds only stocks listed on NYSE. |
| `holds_only_nasdaq_stocks` | `boolean` | If true, the ETF holds only stocks listed on Nasdaq. |
| `holds_mlp` | `boolean` | If true, the ETF's investment objective includes MLPs. |
| `holds_preferred_stock` | `boolean` | If true, the ETF's investment objective includes preferred stock. |
| `holds_closed_end_funds` | `boolean` | If true, the ETF's investment objective includes closed end funds. |
| `holds_adr` | `boolean` | If true, the ETF's investment objective includes ADRs. |
| `laddered` | `boolean` | For bond ETFs, identifies those holding bonds in a laddered structure. |
| `zero_coupon` | `boolean` | For bond ETFs, identifies those holding zero coupon Treasury Bills. |
| `floating_rate` | `boolean` | For bond ETFs, identifies those holding floating rate bonds. |
| `build_america_bonds` | `boolean` | For municipal bond ETFs, identifies those holding Build America Bonds. |
| `dynamic_futures_roll` | `boolean` | For futures ETFs, identifies those with a dynamic roll strategy. |
| `currency_hedged` | `boolean` | Populated if the ETF's strategy involves hedging currency exposure. |
| `includes_short_exposure` | `boolean` | Populated if the ETF has short exposure in any of its holdings. |
| `ucits` | `boolean` | If true, the ETP is UCITS compliant. |
| `registered_countries` | `string` | List of countries where the ETF is legally registered for sale. |
| `issuer_country` | `string` | 2 letter ISO country code for the country where the issuer is located. |
| `listing_country_code` | `string` | 2 letter ISO country code for the country of the primary listing. |
| `listing_region` | `string` | Geographic region in which the country of the primary listing falls. |
| `bond_currency_denomination` | `string` | For bond ETFs, additional detail on the currency denomination. |
| `base_currency` | `string` | Base currency in which NAV is reported. |
| `listing_currency` | `string` | Listing currency of the ETP. |
| `number_of_holdings` | `integer` | The number of holdings in the ETF. |
| `month_end_assets` | `number` | Net assets in millions of dollars as of the most recent month end. |
| `net_expense_ratio` | `number` | Gross expense net of Fee Waivers, as a percentage of net assets. |
| `etf_portfolio_turnover` | `number` | The percentage of positions turned over in the last 12 months. |
| `fund_type` | `string` | The legal type of fund. |
| `category` | `string` | The fund category. |
| `exchange_timezone` | `string` | The timezone of the exchange. |
| `nav_price` | `number` | The net asset value per unit of the fund. |
| `total_assets` | `integer` | The total value of assets held by the fund. |
| `trailing_pe` | `number` | The trailing twelve month P/E ratio of the fund's assets. |
| `dividend_yield` | `number` | The dividend yield of the fund, as a normalized percent. |
| `dividend_rate_ttm` | `number` | The trailing twelve month annual dividend rate of the fund, in currency units. |
| `dividend_yield_ttm` | `number` | The trailing twelve month annual dividend yield of the fund, as a normalized percent. |
| `year_high` | `number` | The fifty-two week high price. |
| `year_low` | `number` | The fifty-two week low price. |
| `ma_50d` | `number` | 50-day moving average price. |
| `ma_200d` | `number` | 200-day moving average price. |
| `return_ytd` | `number` | The year-to-date return of the fund, as a normalized percent. |
| `return_3y_avg` | `number` | The three year average return of the fund, as a normalized percent. |
| `return_5y_avg` | `number` | The five year average return of the fund, as a normalized percent. |
| `beta_3y_avg` | `number` | The three year average beta of the fund. |
| `volume_avg_10d` | `number` | The average daily trading volume of the fund over the past ten days. |
| `bid` | `number` | The current bid price. |
| `bid_size` | `number` | The current bid size. |
| `ask` | `number` | The current ask price. |
| `ask_size` | `number` | The current ask size. |
| `open` | `number` | The open price of the most recent trading session. |
| `high` | `number` | The highest price of the most recent trading session. |
| `low` | `number` | The lowest price of the most recent trading session. |
| `volume` | `integer` | The trading volume of the most recent trading session. |
| `prev_close` | `number` | The previous closing price. |
| `esg` | `boolean` | Whether the ETF qualifies as an ESG fund. |
| `unit_price` | `number` | The unit price of the ETF. |
| `close` | `number` | The closing price of the ETF. |
| `return_1m` | `number` | The one-month return of the ETF, as a normalized percent. |
| `return_3m` | `number` | The three-month return of the ETF, as a normalized percent. |
| `return_6m` | `number` | The six-month return of the ETF, as a normalized percent. |
| `return_1y` | `number` | The one-year return of the ETF, as a normalized percent. |
| `return_3y` | `number` | The three-year return of the ETF, as a normalized percent. |
| `return_5y` | `number` | The five-year return of the ETF, as a normalized percent. |
| `return_10y` | `number` | The ten-year return of the ETF, as a normalized percent. |
| `return_from_inception` | `number` | The return from inception of the ETF, as a normalized percent. |
| `avg_volume` | `integer` | The average daily volume of the ETF. |
| `avg_volume_30d` | `integer` | The 30-day average volume of the ETF. |
| `pe_ratio` | `number` | The price-to-earnings ratio of the ETF. |
| `pb_ratio` | `number` | The price-to-book ratio of the ETF. |
| `management_fee` | `number` | The management fee of the ETF, as a normalized percent. |
| `mer` | `number` | The management expense ratio of the ETF, as a normalized percent. |
| `distribution_yield` | `number` | The distribution yield of the ETF, as a normalized percent. |
| `dividend_frequency` | `string` | The dividend payment frequency of the ETF. |

---
### `etf.nport_disclosure`

```python
data.etf.nport_disclosure(symbol=..., year=None, quarter=None, use_cache=True)
```

Summary: Nport Disclosure

| Field | Value |
|---|---|
| Endpoint ID | `etf.nport_disclosure` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/nport_disclosure` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. (Fund ticker or CIK) |
| `year` | `no` | `integer | null` | `-` | Reporting year of the filing. Default is the year for the most recent, reported, quarter. |
| `quarter` | `no` | `integer | null` | `-` | Reporting quarter of the filing. Default is the most recent, reported, quarter. |
| `use_cache` | `no` | `boolean` | `true` | Whether or not to use cache for the request. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the asset. |
| `title` | `string` | Title of the asset. |
| `cusip` | `string` | CUSIP of the holding. |
| `lei` | `string` | The LEI of the holding. |
| `isin` | `string` | The ISIN of the holding. |
| `other_id` | `string` | Internal identifier for the holding. |
| `is_restricted` | `string` | Whether the holding is restricted. |
| `fair_value_level` | `integer` | The fair value level of the holding. |
| `is_cash_collateral` | `string` | Whether the holding is cash collateral. |
| `is_non_cash_collateral` | `string` | Whether the holding is non-cash collateral. |
| `is_loan_by_fund` | `string` | Whether the holding is loan by fund. |
| `loan_value` | `number` | The loan value of the holding. |
| `issuer_conditional` | `string` | The issuer conditions of the holding. |
| `asset_conditional` | `string` | The asset conditions of the holding. |
| `payoff_profile` | `string` | The payoff profile of the holding. |
| `asset_category` | `string` | The asset category of the holding. |
| `issuer_category` | `string` | The issuer category of the holding. |
| `country` | `string` | The country of the holding. |
| `balance` | `integer` | The balance of the holding, in shares or units. |
| `units` | `integer` | The type of units. |
| `currency` | `string` | The currency of the holding. |
| `value` | `integer` | The value of the holding, in dollars. |
| `weight` | `number` | The weight of the holding, as a normalized percent. |
| `maturity_date` | `string` | The maturity date of the debt security. |
| `coupon_kind` | `string` | The type of coupon for the debt security. |
| `rate_type` | `string` | The type of rate for the debt security, floating or fixed. |
| `annualized_return` | `number` | The annualized return on the debt security. |
| `is_default` | `string` | If the debt security is defaulted. |
| `in_arrears` | `string` | If the debt security is in arrears. |
| `is_paid_kind` | `string` | If the debt security payments are paid in kind. |
| `derivative_category` | `string` | The derivative category of the holding. |
| `counterparty` | `string` | The counterparty of the derivative. |
| `underlying_name` | `string` | The name of the underlying asset associated with the derivative. |
| `option_type` | `string` | The type of option. |
| `derivative_payoff` | `string` | The payoff profile of the derivative. |
| `expiry_date` | `string` | The expiry or termination date of the derivative. |
| `exercise_price` | `number` | The exercise price of the option. |
| `exercise_currency` | `string` | The currency of the option exercise price. |
| `shares_per_contract` | `number` | The number of shares per contract. |
| `delta` | `string` | The delta of the option. |
| `rate_type_rec` | `string` | The type of rate for receivable portion of the swap. |
| `receive_currency` | `string` | The receive currency of the swap. |
| `upfront_receive` | `number` | The upfront amount received of the swap. |
| `floating_rate_index_rec` | `string` | The floating rate index for receivable portion of the swap. |
| `floating_rate_spread_rec` | `number` | The floating rate spread for receivable portion of the swap. |
| `rate_tenor_rec` | `string` | The rate tenor for receivable portion of the swap. |
| `rate_tenor_unit_rec` | `string` | The rate tenor unit for receivable portion of the swap. |
| `reset_date_rec` | `string` | The reset date for receivable portion of the swap. |
| `reset_date_unit_rec` | `string` | The reset date unit for receivable portion of the swap. |
| `rate_type_pmnt` | `string` | The type of rate for payment portion of the swap. |
| `payment_currency` | `string` | The payment currency of the swap. |
| `upfront_payment` | `number` | The upfront amount received of the swap. |
| `floating_rate_index_pmnt` | `string` | The floating rate index for payment portion of the swap. |
| `floating_rate_spread_pmnt` | `number` | The floating rate spread for payment portion of the swap. |
| `rate_tenor_pmnt` | `string` | The rate tenor for payment portion of the swap. |
| `rate_tenor_unit_pmnt` | `string` | The rate tenor unit for payment portion of the swap. |
| `reset_date_pmnt` | `string` | The reset date for payment portion of the swap. |
| `reset_date_unit_pmnt` | `string` | The reset date unit for payment portion of the swap. |
| `repo_type` | `string` | The type of repo. |
| `is_cleared` | `string` | If the repo is cleared. |
| `is_tri_party` | `string` | If the repo is tri party. |
| `principal_amount` | `number` | The principal amount of the repo. |
| `principal_currency` | `string` | The currency of the principal amount. |
| `collateral_type` | `string` | The collateral type of the repo. |
| `collateral_amount` | `number` | The collateral amount of the repo. |
| `collateral_currency` | `string` | The currency of the collateral amount. |
| `exchange_currency` | `string` | The currency of the exchange rate. |
| `exchange_rate` | `number` | The exchange rate. |
| `currency_sold` | `string` | The currency sold in a Forward Derivative. |
| `currency_amount_sold` | `number` | The amount of currency sold in a Forward Derivative. |
| `currency_bought` | `string` | The currency bought in a Forward Derivative. |
| `currency_amount_bought` | `number` | The amount of currency bought in a Forward Derivative. |
| `notional_amount` | `number` | The notional amount of the derivative. |
| `notional_currency` | `string` | The currency of the derivative's notional amount. |
| `unrealized_gain` | `number` | The unrealized gain or loss on the derivative. |
| `as_of` | `string` | The acceptance datetime of the filing. |

---

### `etf.price_performance`

```python
data.etf.price_performance(symbol="SPY", start_date=None, end_date=None, provider="bitget_data")
```

Summary: Price Performance

| Field | Value |
|---|---|
| Endpoint ID | `etf.price_performance` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/price_performance` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** tables; ignore other-provider params/fields. Use `start_date`/`end_date`, not `return_type`/`adjustment`. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ETF ticker. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Defaults to latest 30 days. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |

**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `date` | `date / null` | Mapped from `dt`. |
| `dt` | `date / null` | NAV date. |
| `fund_nav` | `number / null` | NAV. |
| `fund_total_assets` | `number / null` | Total assets. |
| `return_this_year` | `number / null` | YTD return. |
| `premium_rate` | `number / null` | Premium/discount. |
| `dividend_rate` | `number / null` | Dividend yield. |
| `expense_ratio` | `number / null` | Expense ratio. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `return_type` | `no` | `string` | `trailing` | enum: trailing, calendar The type of returns to return, a trailing or calendar window. |
| `adjustment` | `no` | `string` | `splits_and_dividends` | enum: splits_only, splits_and_dividends The adjustment factor, 'splits_only' will return pure price performance. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `one_day` | `number` | One-day return. |
| `wtd` | `number` | Week to date return. |
| `one_week` | `number` | One-week return. |
| `mtd` | `number` | Month to date return. |
| `one_month` | `number` | One-month return. |
| `qtd` | `number` | Quarter to date return. |
| `three_month` | `number` | Three-month return. |
| `six_month` | `number` | Six-month return. |
| `ytd` | `number` | Year to date return. |
| `one_year` | `number` | One-year return. |
| `two_year` | `number` | Two-year return. |
| `three_year` | `number` | Three-year return. |
| `four_year` | `number` | Four-year return. |
| `five_year` | `number` | Five-year return. |
| `ten_year` | `number` | Ten-year return. |
| `max` | `number` | Return from the beginning of the time series. |
| `max_annualized` | `number` | Annualized rate of return from inception. |
| `volatility_one_year` | `number` | Trailing one-year annualized volatility. |
| `volatility_three_year` | `number` | Trailing three-year annualized volatility. |
| `volatility_five_year` | `number` | Trailing five-year annualized volatility. |
| `volume` | `integer` | The trading volume. |
| `volume_avg_30` | `number` | The one-month average daily volume. |
| `volume_avg_90` | `number` | The three-month average daily volume. |
| `volume_avg_180` | `number` | The six-month average daily volume. |
| `beta` | `number` | Beta compared to the S&P 500. |
| `nav` | `number` | Net asset value per share. |
| `year_high` | `number` | The 52-week high price. |
| `year_low` | `number` | The 52-week low price. |
| `market_cap` | `number` | The market capitalization. |
| `shares_outstanding` | `integer` | The number of shares outstanding. |
| `updated` | `string` | The date of the data. |
| `volatility_week` | `number` | One-week realized volatility, as a normalized percent. |
| `volatility_month` | `number` | One-month realized volatility, as a normalized percent. |
| `price` | `number` | Last Price. |
| `average_volume` | `number` | Average daily volume. |
| `relative_volume` | `number` | Relative volume as a ratio of current volume to average volume. |
| `analyst_recommendation` | `number` | The analyst consensus, on a scale of 1-5 where 1 is a buy and 5 is a sell. |

---
### `etf.search`

```python
data.etf.search(query='', exchange=None, country=None, div_freq=None, sort_by=None, use_cache=True)
```

Summary: Search

| Field | Value |
|---|---|
| Endpoint ID | `etf.search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string | null` | `` | Search query. |
| `exchange` | `no` | `string | null` | `-` | Exchange where the ETF is listed. If not provided, all exchanges are searched.; Target a specific exchange by providing the MIC code. |
| `country` | `no` | `string | null` | `-` | Filter by country. Accepts ISO 3166-1 alpha-2 codes (e.g., 'US', 'DE'), alpha-3 codes (e.g., 'USA'), or country names (e.g., 'United States', 'united_states'). |
| `div_freq` | `no` | `string | null` | `-` | The dividend payment frequency. |
| `sort_by` | `no` | `string | null` | `-` | The column to sort by. |
| `use_cache` | `no` | `boolean` | `true` | Whether to use a cached request. All ETF data comes from a single JSON file that is updated daily. To bypass, set to False. If True, the data will be cached for 4 hours. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. (ETF) |
| `name` | `string` | Name of the ETF. |
| `short_name` | `string` | The short name of the ETF. |
| `inception_date` | `string` | The inception date of the ETF. |
| `issuer` | `string` | The issuer of the ETF. |
| `investment_style` | `string` | The investment style of the ETF. |
| `esg` | `boolean` | Whether the ETF qualifies as an ESG fund. |
| `currency` | `string` | The currency of the ETF. |
| `unit_price` | `number` | The unit price of the ETF. |
| `close` | `number` | The closing price of the ETF. |
| `prev_close` | `number` | The previous closing price of the ETF. |
| `return_1m` | `number` | The one-month return of the ETF, as a normalized percent. |
| `return_3m` | `number` | The three-month return of the ETF, as a normalized percent. |
| `return_6m` | `number` | The six-month return of the ETF, as a normalized percent. |
| `return_ytd` | `number` | The year-to-date return of the ETF, as a normalized percent. |
| `return_1y` | `number` | The one-year return of the ETF, as a normalized percent. |
| `beta_1y` | `number` | The one-year beta of the ETF, as a normalized percent. |
| `return_3y` | `number` | The three-year return of the ETF, as a normalized percent. |
| `beta_3y` | `number` | The three-year beta of the ETF, as a normalized percent. |
| `return_5y` | `number` | The five-year return of the ETF, as a normalized percent. |
| `beta_5y` | `number` | The five-year beta of the ETF, as a normalized percent. |
| `return_10y` | `number` | The ten-year return of the ETF, as a normalized percent. |
| `beta_10y` | `number` | The ten-year beta of the ETF. |
| `beta_15y` | `number` | The fifteen-year beta of the ETF. |
| `return_from_inception` | `number` | The return from inception of the ETF, as a normalized percent. |
| `avg_volume` | `integer` | The average daily volume of the ETF. |
| `avg_volume_30d` | `integer` | The 30-day average volume of the ETF. |
| `aum` | `number` | The AUM of the ETF. |
| `pe_ratio` | `number` | The price-to-earnings ratio of the ETF. |
| `pb_ratio` | `number` | The price-to-book ratio of the ETF. |
| `management_fee` | `number` | The management fee of the ETF, as a normalized percent. |
| `mer` | `number` | The management expense ratio of the ETF, as a normalized percent. |
| `distribution_yield` | `number` | The distribution yield of the ETF, as a normalized percent. |
| `dividend_frequency` | `string` | The dividend payment frequency of the ETF. |
| `exchange` | `string` | The exchange MIC code. |
| `figi_ticker` | `string` | The OpenFIGI ticker. |
| `ric` | `string` | The Reuters Instrument Code. |
| `isin` | `string` | The International Securities Identification Number. |
| `sedol` | `string` | The Stock Exchange Daily Official List. |
| `intrinio_id` | `string` | The unique Intrinio ID for the security. |
| `country` | `string` | Country where the ETF is domiciled. |
| `exchange_name` | `string` | The full name of the exchange. |
| `market_cap` | `integer` | Market capitalization of the ETF. |
| `beta` | `number` | Beta of the ETF. |
| `price` | `number` | Current price of the ETF. |
| `last_annual_dividend` | `number` | Last annual dividend paid. |
| `volume` | `integer` | Current trading volume of the ETF. |

---

### `etf.sectors`

```python
data.etf.sectors(symbol=..., use_cache=True)
```

Summary: Sectors

| Field | Value |
|---|---|
| Endpoint ID | `etf.sectors` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/etf/sectors` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. (ETF) Multiple comma separated items allowed |
| `use_cache` | `no` | `boolean` | `true` | Whether to use a cached request. All ETF data comes from a single JSON file that is updated daily. To bypass, set to False. If True, the data will be cached for 4 hours. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `sector` | `string` | Sector of exposure. |
| `weight` | `number` | Sector exposure for the ETF as a percent of total assets. |
