# Equity Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`equity.calendar.dividend`](#equitycalendardividend)
- [`equity.calendar.earnings`](#equitycalendarearnings)
- [`equity.calendar.events`](#equitycalendarevents)
- [`equity.calendar.ipo`](#equitycalendaripo)
- [`equity.calendar.splits`](#equitycalendarsplits)
- [`equity.compare.company_facts`](#equitycomparecompany-facts)
- [`equity.compare.groups`](#equitycomparegroups)
- [`equity.compare.peers`](#equitycomparepeers)
- [`equity.darkpool.otc`](#equitydarkpoolotc)
- [`equity.discovery.active`](#equitydiscoveryactive)
- [`equity.discovery.aggressive_small_caps`](#equitydiscoveryaggressive-small-caps)
- [`equity.discovery.filings`](#equitydiscoveryfilings)
- [`equity.discovery.gainers`](#equitydiscoverygainers)
- [`equity.discovery.growth_tech`](#equitydiscoverygrowth-tech)
- [`equity.discovery.latest_financial_reports`](#equitydiscoverylatest-financial-reports)
- [`equity.discovery.losers`](#equitydiscoverylosers)
- [`equity.discovery.top_retail`](#equitydiscoverytop-retail)
- [`equity.discovery.undervalued_growth`](#equitydiscoveryundervalued-growth)
- [`equity.discovery.undervalued_large_caps`](#equitydiscoveryundervalued-large-caps)
- [`equity.estimates.analyst_search`](#equityestimatesanalyst-search)
- [`equity.estimates.consensus`](#equityestimatesconsensus)
- [`equity.estimates.forward_ebitda`](#equityestimatesforward-ebitda)
- [`equity.estimates.forward_eps`](#equityestimatesforward-eps)
- [`equity.estimates.forward_pe`](#equityestimatesforward-pe)
- [`equity.estimates.forward_sales`](#equityestimatesforward-sales)
- [`equity.estimates.historical`](#equityestimateshistorical)
- [`equity.estimates.price_target`](#equityestimatesprice-target)
- [`equity.fund_flow.etf`](#equityfund-flowetf)
- [`equity.fundamental.balance`](#equityfundamentalbalance)
- [`equity.fundamental.balance_growth`](#equityfundamentalbalance-growth)
- [`equity.fundamental.cash`](#equityfundamentalcash)
- [`equity.fundamental.cash_growth`](#equityfundamentalcash-growth)
- [`equity.fundamental.dividends`](#equityfundamentaldividends)
- [`equity.fundamental.employee_count`](#equityfundamentalemployee-count)
- [`equity.fundamental.esg_score`](#equityfundamentalesg-score)
- [`equity.fundamental.filings`](#equityfundamentalfilings)
- [`equity.fundamental.historical_attributes`](#equityfundamentalhistorical-attributes)
- [`equity.fundamental.historical_eps`](#equityfundamentalhistorical-eps)
- [`equity.fundamental.historical_splits`](#equityfundamentalhistorical-splits)
- [`equity.fundamental.income`](#equityfundamentalincome)
- [`equity.fundamental.income_growth`](#equityfundamentalincome-growth)
- [`equity.fundamental.latest_attributes`](#equityfundamentallatest-attributes)
- [`equity.fundamental.management`](#equityfundamentalmanagement)
- [`equity.fundamental.management_compensation`](#equityfundamentalmanagement-compensation)
- [`equity.fundamental.management_discussion_analysis`](#equityfundamentalmanagement-discussion-analysis)
- [`equity.fundamental.metrics`](#equityfundamentalmetrics)
- [`equity.fundamental.metrics_evaluation`](#equityfundamentalmetrics-evaluation)
- [`equity.fundamental.metrics_per_share`](#equityfundamentalmetrics-per-share)
- [`equity.fundamental.metrics_performance`](#equityfundamentalmetrics-performance)
- [`equity.fundamental.ratios`](#equityfundamentalratios)
- [`equity.fundamental.reported_financials`](#equityfundamentalreported-financials)
- [`equity.fundamental.revenue_per_geography`](#equityfundamentalrevenue-per-geography)
- [`equity.fundamental.revenue_per_segment`](#equityfundamentalrevenue-per-segment)
- [`equity.fundamental.search_attributes`](#equityfundamentalsearch-attributes)
- [`equity.fundamental.trailing_dividend_yield`](#equityfundamentaltrailing-dividend-yield)
- [`equity.fundamental.transcript`](#equityfundamentaltranscript)
- [`equity.historical_market_cap`](#equityhistorical-market-cap)
- [`equity.market_snapshots`](#equitymarket-snapshots)
- [`equity.ownership.form_13f`](#equityownershipform-13f)
- [`equity.ownership.government_trades`](#equityownershipgovernment-trades)
- [`equity.ownership.insider_trading`](#equityownershipinsider-trading)
- [`equity.ownership.institutional`](#equityownershipinstitutional)
- [`equity.ownership.inst_position_detail`](#equityownershipinst-position-detail)
- [`equity.ownership.inst_position_summary`](#equityownershipinst-position-summary)
- [`equity.ownership.major_holders`](#equityownershipmajor-holders)
- [`equity.ownership.share_statistics`](#equityownershipshare-statistics)
- [`equity.price.historical`](#equitypricehistorical)
- [`equity.price.performance`](#equitypriceperformance)
- [`equity.price.quote`](#equitypricequote)
- [`equity.profile`](#equityprofile)
- [`equity.screener`](#equityscreener)
- [`equity.search`](#equitysearch)
- [`equity.shorts.fails_to_deliver`](#equityshortsfails-to-deliver)
- [`equity.shorts.short_interest`](#equityshortsshort-interest)

## `bitget_data` provider (THS US equities)

Use this section, not the default-provider tables below, when calling
Tonghuashun-backed US-equity data. Public Platform paths are
`/inner/v1/agent-data/<endpoint>` with `provider=bitget_data`.

Call contract:

- Always pass `provider="bitget_data"` and a single uppercase US ticker as
  `symbol`. Do not send `sec_code`; the platform maps `symbol` upstream.
- Dates are `YYYY-MM-DD` (`start_date` / `end_date`). Do not use
  `start_time` / `end_time`, `period`, `fiscal_year`, `ttm`, `year`,
  `quarter`, or `date` unless they appear in the `bitget_data` table for
  that endpoint.
- Public `limit` is page size (default `100`, max `500`). `page` is 1-based
  (default `1`, max `500`). The platform sends `limit` upstream as `size`.
- `report_type` values: `年报`, `一季报`, `中报`, `中报(下半年)`, `二季报`,
  `三季报`, `三季报(累计)`, `四季报`, `其他`.
- An empty THS result is a no-result: do not invent rows. The platform may
  raise `EmptyDataError` instead of returning `[]`; treat that as empty.
- Statement endpoints do not expose query-service `latest_symbol`. Upstream
  defaults to latest rows; use `statement_year` / `start_date` / `end_date`
  to select history.
- Response schemas differ from other providers. Read the `bitget_data`
  response tables in this section and in each endpoint's
  **bitget_data provider** subsection. Extra THS columns may still appear.

Example:

```python
data.equity.fundamental.balance(
    symbol="AAPL",
    statement_year=2025,
    report_type="年报",
    provider="bitget_data",
)
```

### `bitget_data` query parameters

| Endpoints | Parameters after `symbol` and `provider` |
|---|---|
| `equity.fundamental.balance`, `equity.fundamental.income`, `equity.fundamental.cash`, `equity.fundamental.metrics_evaluation` | `report_type`, `statement_year`, `start_date`, `end_date`, `page`, `limit` |
| `equity.fundamental.metrics`, `equity.fundamental.metrics_per_share`, `equity.fundamental.metrics_performance` | `report_type`, `report_annual`, `start_date`, `end_date`, `page`, `limit` |
| `equity.fundamental.ratios` | `start_date`, `end_date`, `page`, `limit` |
| `equity.ownership.major_holders`, `equity.ownership.insider_trading`, `equity.ownership.form_13f`, `equity.ownership.inst_position_detail`, `equity.ownership.inst_position_summary` | `start_date`, `end_date`, `page`, `limit` |
| `equity.estimates.price_target` | `start_date`, `end_date`, `rating_org` |
| `equity.estimates.forward_pe`, `equity.estimates.forward_eps`, `equity.estimates.forward_ebitda`, `equity.estimates.forward_sales` | `annual`, `is_actual_value` |
| `equity.estimates.consensus` | `fore_indicator_name` (`symbol` is required for THS) |
| `equity.fund_flow.etf` | `start_date`, `end_date` (latest 30 days if omitted) |

### `bitget_data` response fields

Standard-model aliases that the platform populates, plus the THS fields agents
should read. Additional THS columns may be present.

| Endpoint | Fields to read |
|---|---|
| `equity.profile` | `symbol`, `name`, `legal_name`, `cusip`, `isin`, `stock_exchange`, `short_description`, `long_description`, `ceo`, `inc_country`, `employees`, `entity_legal_form`, `entity_status`, `industry_category`, `standardized_active`, `first_stock_price_date`, `currency_code`, `reg_region`, `org_type`, `industry_name`, `listed_board_name`, `development_history` |
| `equity.fundamental.management` | `title`, `name`, `pay`, `currency_pay`, `gender`, `year_born`, `sec_code`, `sec_short_name_cn`, `name_cn`, `nationality`, `high_edu`, `resume_cn`, `resume_en`, `position_name_cn`, `manage_type`, `publish_age_on_ed`, `latest_salary_year`, `latest_report_period`, `share_held_num`, `total_held_ratio_cacl_value`, `total_voting_right` |
| `equity.fundamental.balance` | `symbol`, `period_ending`, `fiscal_year`, `fiscal_period`, `currency_code`, `cce`, `net_receivables`, `inventory`, `total_current_assets`, `net_property_plant_and_equip`, `goodwill`, `net_intangible_assets`, `total_noncurrent_assets`, `total_assets`, `accounts_payable`, `st_debt`, `lt_debt`, `total_current_liab`, `total_noncurrent_liab`, `total_liab`, `common_stock`, `preferred_stock`, `retained_earning`, `treasury_stock`, `minority_interest`, `total_holders_equity` |
| `equity.fundamental.income` | `symbol`, `period_ending`, `fiscal_year`, `fiscal_period`, `currency_code`, `revenue`, `total_revenue`, `sales_cost`, `gross_profit`, `rad_expenses`, `marketing_selling_etc`, `operating_income`, `income_from_co_before_it`, `income_tax`, `net_income`, `net_income_atcss`, `total_basic_earning_common_ps`, `total_dlt_earnings_common_ps`, `total_compre_income` |
| `equity.fundamental.cash` | `symbol`, `period_ending`, `fiscal_year`, `fiscal_period`, `currency_code`, `net_cash_provided_by_oa`, `net_cash_used_in_ia`, `net_cash_used_in_fa`, `depreciation_and_amortization`, `payment_for_property_and_equip`, `common_stock_issue`, `repur_of_common_stock`, `dividend_paid`, `effect_of_exchange_chg_on_cce`, `increase_in_cce`, `cce_at_boy`, `cce_at_eoy` |
| `equity.fundamental.ratios` | `symbol`, `period_ending`, `pe`, `pe_lyr`, `pe_ttm_ed`, `pb`, `pb_mrq`, `ps`, `ps_ttm_ed`, `pcf`, `pcf_ttm_ed`, `peg_his`, `ev1`, `ev2`, `ent_multi`, `tmv_usd`, `cir_tmv_usd`, `div_yield_12m` |
| `equity.fundamental.metrics` | `symbol`, `period_ending`, `fiscal_year`, `fiscal_period`, `currency`, `net_sales_rate`, `gross_selling_rate`, `current_ratio`, `quick_ratio`, `asset_liab_ratio`, `equity_multiplier`, `ebit_to_interest_fee`, `roe_dlt` |
| `equity.fundamental.metrics_evaluation` | `symbol`, `ed`, `statement_year`, `report_type`, `total_holders_equity`, `net_income_atcss`, `revenue`, `net_cash_provided_by_oa` |
| `equity.fundamental.metrics_per_share` | `symbol`, `ed`, `report_annual`, `report_type`, `currency_code`, `basic_eps`, `eps_dlt`, `nav_ps`, `revenue_ps`, `ncf_from_oa_ps` |
| `equity.fundamental.metrics_performance` | `symbol`, `ed`, `report_annual`, `report_type`, `roe_avg`, `roa`, `operating_cycle`, `inventory_turnover`, `account_receivable_turnover`, `total_capital_turnover`, `total_revenue_growth_yoy`, `yoy_net_profit`, `yoy_basic_eps`, `equity_multiplier_dupont` |
| `equity.ownership.major_holders` | `symbol`, `investor_name`, `date`, `filing_date`, `share_held_num`, `total_held_ratio_dsclsr_value`, `total_voting_right` |
| `equity.ownership.insider_trading` | `symbol`, `owner_name`, `owner_title`, `ownership_type`, `transaction_date`, `transaction_type`, `securities_transacted`, `transaction_price`, `securities_owned`, `filing_date`, `filing_url` |
| `equity.ownership.form_13f` | `symbol`, `period_ending`, `org_name`, `issuer`, `cusip`, `asset_class`, `principal_amount`, `value`, `option_type` |
| `equity.ownership.inst_position_detail` | `symbol`, `ed`, `org_holder`, `held_num`, `held_changed_num`, `chg_ratio`, `announcement_date` |
| `equity.ownership.inst_position_summary` | `symbol`, `chg_date`, `holder_num`, `holding_total_vol`, `holding_total_value`, `net_trade_vol` |
| `equity.estimates.price_target` | `symbol`, `published_date`, `analyst_firm`, `price_target`, `price_target_previous`, `rating_current`, `rating_previous`, `action`, `rating_org`, `rating_date`, `latest_target_price`, `pre_target_price`, `latest_rating_cn`, `pre_rating_cn`, `rating_chg_cn` |
| `equity.estimates.forward_*` | `symbol`, `annual`, `publish_ed`, `is_actual_value`, `revenue`, `ebit`, `ebitda`, `net_profit_atsopc`, `eps`, `basic_eps`, `roe`, `pe`, `pb_ratio`, `ps_ratio`, `peg`, `ev`, `currency_code`; also `fiscal_year`/`mean`/`date`/`last_updated` aliases where populated |
| `equity.estimates.consensus` | `symbol`, `fore_indicator_name`, `fore_org_num`, `fore_mean`, `min_fore_value`, `high_fore_value`, `his_fore_value`, `target_consensus`, `target_low`, `target_high`, `fiscal_year`, `report_period`, `currency_unit`, `unit`, `scraped_date` |
| `equity.fund_flow.etf` | `date`, `stock_code`, `stock_name`, `etf_count`, `etf_inflow_value`, `etf_outflow_value`, `etf_inflow_count`, `etf_outflow_count`, `etf_net_flow_value` |

## Endpoint reference

### `equity.calendar.dividend`

```python
data.equity.calendar.dividend(start_time=None, end_time=None)
```

Summary: Dividend

| Field | Value |
|---|---|
| Endpoint ID | `equity.calendar.dividend` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/calendar/dividend` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `ex_dividend_date` | `string` | The ex-dividend date - the date on which the stock begins trading without rights to the dividend. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `amount` | `number` | The dividend amount per share. |
| `name` | `string` | Name of the entity. |
| `record_date` | `string` | The record date of ownership for eligibility. |
| `payment_date` | `string` | The payment date of the dividend. |
| `declaration_date` | `string` | Declaration date of the dividend. |
| `annualized_amount` | `number` | The indicated annualized dividend amount. |
| `adjusted_amount` | `number` | The adjusted-dividend amount. |
| `dividend_yield` | `number` | Annualized dividend yield. |
| `frequency` | `string` | Frequency of the regular dividend payment. |

---

### `equity.calendar.earnings`

```python
data.equity.calendar.earnings(start_time=None, end_time=None, symbol=None, country='us')
```

Summary: Earnings

| Field | Value |
|---|---|
| Endpoint ID | `equity.calendar.earnings` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/calendar/earnings` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. |
| `country` | `no` | `string` | `us` | enum: us, ca The country to get calendar data for. Accepts 'us'/'ca', ISO codes ('US', 'USA', 'CA', 'CAN'), or names ('United States', 'Canada'). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `report_date` | `string` | The date of the earnings report. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `eps_previous` | `number` | The earnings-per-share from the same previously reported period. |
| `eps_consensus` | `number` | The analyst consensus earnings-per-share estimate. |
| `eps_actual` | `number` | The actual earnings per share announced. |
| `revenue_consensus` | `number` | The revenue forecast consensus. |
| `revenue_actual` | `number` | The actual reported revenue. |
| `last_updated` | `string` | The date the data was updated last. |
| `surprise_percent` | `number` | The earnings surprise as normalized percentage points. |
| `num_estimates` | `integer` | The number of analysts providing estimates for the consensus. |
| `period_ending` | `string` | The fiscal period end date. |
| `previous_report_date` | `string` | The previous report date for the same period last year. |
| `reporting_time` | `string` | The reporting time - e.g. after market close. |
| `market_cap` | `integer` | The market cap (USD) of the reporting entity. |
| `exchange` | `string` | The primary trading exchange. |
| `sector_id` | `integer` | The Seeking Alpha Sector ID. |
| `eps_surprise` | `number` | The EPS surprise in dollars. |

---

### `equity.calendar.events`

```python
data.equity.calendar.events(start_time=None, end_time=None, country=None)
```

Summary: Events

| Field | Value |
|---|---|
| Endpoint ID | `equity.calendar.events` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/calendar/events` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string | null` | `-` | Country code to filter economic events (e.g., 'US', 'JP', 'CN'). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. The date of the event. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `country` | `string` | Country code for the economic event. |
| `event` | `string` | Name of the economic event or data release. |
| `currency` | `string` | Currency associated with the economic data. |
| `previous` | `number` | Previous value of the economic indicator. |
| `estimate` | `number` | Estimated or forecasted value of the economic indicator. |
| `actual` | `number` | Actual released value of the economic indicator. |
| `change` | `number` | Change in value from the previous release. |
| `impact` | `string` | Expected market impact of the economic event. |
| `changePercentage` | `number` | Percentage change from the previous value. |
| `unit` | `string` | Unit of measurement for the economic indicator. |

---

### `equity.calendar.ipo`

```python
data.equity.calendar.ipo(start_time=None, end_time=None, symbol=None, limit=100, status=None, min_value=None, max_value=None, is_spo=False)
```

Summary: Ipo

| Field | Value |
|---|---|
| Endpoint ID | `equity.calendar.ipo` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/calendar/ipo` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `100` | The number of data entries to return. Max 1000. |
| `status` | `no` | `string | null` | `-` | Status of the IPO. [upcoming, priced, or withdrawn]; The status of the IPO. |
| `min_value` | `no` | `integer | null` | `-` | Return IPOs with an offer dollar amount greater than the given amount. |
| `max_value` | `no` | `integer | null` | `-` | Return IPOs with an offer dollar amount less than the given amount. |
| `is_spo` | `no` | `boolean` | `false` | If True, returns data for secondary public offerings (SPOs). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `ipo_date` | `string` | The date of the IPO, when the stock first trades on a major exchange. |
| `name` | `string` | The name of the company. |
| `offer_amount` | `number` | The dollar value of the shares offered. |
| `share_count` | `integer` | The number of shares offered. |
| `expected_price_date` | `string` | The date the pricing is expected. |
| `filed_date` | `string` | The date the IPO was filed. |
| `withdraw_date` | `string` | The date the IPO was withdrawn. |
| `deal_status` | `string` | The status of the deal. |
| `exchange_date` | `string` | Timezone information for the exchange and date of the IPO. |
| `exchange` | `string` | The exchange where the IPO is listed. |
| `actions` | `string` | Actions related to the IPO, such as, Expected, Priced, Filed, Amended. |
| `shares` | `integer` | The number of shares being offered in the IPO. |
| `price_range` | `string` | The expected price range for the IPO shares. |
| `market_cap` | `integer` | The estimated market capitalization of the company at the time of the IPO. |
| `status` | `string` | The status of the IPO. |
| `share_price` | `number` | The price per share at which the IPO was offered. |
| `share_price_lowest` | `number` | The expected lowest price per share at which the IPO will be offered. |
| `share_price_highest` | `number` | The expected highest price per share at which the IPO will be offered. |
| `share_count_lowest` | `integer` | The expected lowest number of shares that will be offered in the IPO. |
| `share_count_highest` | `integer` | The expected highest number of shares that will be offered in the IPO. |
| `announcement_url` | `string` | The URL to the company's announcement of the IPO. |
| `sec_report_url` | `string` | The URL to the company's S-1, S-1/A, F-1, or F-1/A SEC filing. |
| `open_price` | `number` | The opening price at the beginning of the first trading day. |
| `close_price` | `number` | The closing price at the end of the first trading day. |
| `volume` | `integer` | The volume at the end of the first trading day. |
| `day_change` | `number` | The percentage change between the open price and the close price on the first trading day. |
| `week_change` | `number` | The percentage change between the open price on the first trading day and the close price approximately a week after. |
| `month_change` | `number` | The percentage change between the open price on the first trading day and the close price approximately a month after. |
| `id` | `string` | The Intrinio ID of the IPO. |
| `company` | `object` | The company that is going public via the IPO. |
| `security` | `object` | The primary Security for the Company that is going public via the IPO. |

---

### `equity.calendar.splits`

```python
data.equity.calendar.splits(start_time=None, end_time=None)
```

Summary: Splits

| Field | Value |
|---|---|
| Endpoint ID | `equity.calendar.splits` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/calendar/splits` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `numerator` | `number` | Numerator of the stock split. |
| `denominator` | `number` | Denominator of the stock split. |

---

### `equity.compare.company_facts`

```python
data.equity.compare.company_facts(symbol=None, fact='', year=None, fiscal_period=None, instantaneous=False, use_cache=True)
```

Summary: Company Facts

| Field | Value |
|---|---|
| Endpoint ID | `equity.compare.company_facts` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/compare/company_facts` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `fact` | `no` | `string` | `` | The fact to lookup, typically a GAAP-reporting measure. Choices vary by provider.; Fact or concept from the SEC taxonomy, in UpperCamelCase. Defaults to, 'Revenues'. AAPL, MSFT, GOOG, BRK-A currently report revenue as, 'RevenueFromContractWithCustomerExcludingAssessedTax'. In previous years, they have reported as 'Revenues'. |
| `year` | `no` | `integer | null` | `-` | The year to retrieve the data for. If not provided, the current year is used. When symbol(s) are provided, excluding the year will return all reported values for the concept. |
| `fiscal_period` | `no` | `string | null` | `-` | The fiscal period to retrieve the data for. If not provided, the most recent quarter is used. This parameter is ignored when a symbol is supplied. |
| `instantaneous` | `no` | `boolean` | `false` | Whether to retrieve instantaneous data. See the notes above for more information. Defaults to False. Some facts are only available as instantaneous data. The function will automatically attempt the inverse of this parameter if the initial fiscal quarter request fails. This parameter is ignored when a symbol is supplied. |
| `use_cache` | `no` | `boolean` | `true` | Whether to use cache for the request. Defaults to True. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `value` | `number` | The reported value of the fact or concept. |
| `reported_date` | `string` | The date when the report was filed. |
| `period_beginning` | `string` | The start date of the reporting period. |
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_year` | `integer` | The fiscal year. |
| `fiscal_period` | `string` | The fiscal period of the fiscal year. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `location` | `string` | Geographic location of the reporting entity. |
| `form` | `string` | The SEC form associated with the fact or concept. |
| `frame` | `string` | The frame ID associated with the fact or concept, if applicable. |
| `accession` | `string` | SEC filing accession number associated with the reported fact or concept. |
| `fact` | `string` | The display name of the fact or concept. |
| `unit` | `string` | The unit of measurement for the fact or concept. |

---

### `equity.compare.groups`

```python
data.equity.compare.groups(group='sector', metric='performance')
```

Summary: Groups

| Field | Value |
|---|---|
| Endpoint ID | `equity.compare.groups` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/compare/groups` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `group` | `no` | `string` | `sector` | enum: sector, industry, country, capitalization, energy, materials, industrials, consumer_cyclical, consumer_defensive, healthcare, financial, technology, communication_services, utilities, real_estate US-listed stocks only. When an individual sector is selected, it is broken down by industry. The default is 'sector'. |
| `metric` | `no` | `string` | `performance` | enum: performance, valuation, overview Statistical metric to return. Select from: ['performance', 'valuation', 'overview'] The default is 'performance'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `name` | `string` | Name or label of the group. |
| `stocks` | `integer` | The number of stocks in the group. |
| `market_cap` | `integer` | The market cap of the group. |
| `performance_1d` | `number` | The performance in the last day, as a normalized percent. |
| `performance_1w` | `number` | The performance in the last week, as a normalized percent. |
| `performance_1m` | `number` | The performance in the last month, as a normalized percent. |
| `performance_3m` | `number` | The performance in the last quarter, as a normalized percent. |
| `performance_6m` | `number` | The performance in the last half year, as a normalized percent. |
| `performance_1y` | `number` | The performance in the last year, as a normalized percent. |
| `performance_ytd` | `number` | The performance in the year to date, as a normalized percent. |
| `dividend_yield` | `number` | The dividend yield of the group, as a normalized percent. |
| `pe` | `number` | The P/E ratio of the group. |
| `forward_pe` | `number` | The forward P/E ratio of the group. |
| `peg` | `number` | The PEG ratio of the group. |
| `eps_growth_past_5y` | `number` | The EPS growth of the group for the past 5 years, as a normalized percent. |
| `eps_growth_next_5y` | `number` | The estimated EPS growth of the group for the next 5 years, as a normalized percent. |
| `sales_growth_past_5y` | `number` | The sales growth of the group for the past 5 years, as a normalized percent. |
| `float_short` | `number` | The percent of the float shorted for the group, as a normalized value. |
| `analyst_recommendation` | `number` | The analyst consensus, on a scale of 1-5 where 1 is a buy and 5 is a sell. |
| `volume` | `integer` | The trading volume. |
| `volume_average` | `integer` | The 3-month average volume of the group. |
| `volume_relative` | `number` | The relative volume compared to the 3-month average volume. |

---

### `equity.compare.peers`

```python
data.equity.compare.peers(symbol=...)
```

Summary: Peers

| Field | Value |
|---|---|
| Endpoint ID | `equity.compare.peers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/compare/peers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | The name of the company. |
| `price` | `number` | The current stock price of the company. |
| `market_cap` | `integer` | The market capitalization of the company. |

---

### `equity.darkpool.otc`

```python
data.equity.darkpool.otc(symbol=None, tier='T1', is_ats=True)
```

Summary: Otc

| Field | Value |
|---|---|
| Endpoint ID | `equity.darkpool.otc` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/darkpool/otc` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. |
| `tier` | `no` | `string` | `T1` | "T1 - Securities included in the S&P 500, Russell 1000 and selected exchange-traded products; T2 - All other NMS stocks; OTC - Over-the-Counter equity securities |
| `is_ats` | `no` | `boolean` | `true` | ATS data if true, NON-ATS otherwise |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `update_date` | `string` | Most recent date on which total trades is updated based on data received from each ATS/OTC. |
| `share_quantity` | `number` | Aggregate weekly total number of shares reported by each ATS for the Symbol. |
| `trade_quantity` | `number` | Aggregate weekly total number of trades reported by each ATS for the Symbol. |

---

### `equity.discovery.active`

```python
data.equity.discovery.active(sort='desc', limit=200)
```

Summary: Active

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.active` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/active` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer | null` | `200` | Limit the number of results. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `price` | `number` | Last price. |
| `change` | `number` | Change in price. |
| `percent_change` | `number` | Percent change. |
| `volume` | `integer` | The trading volume. |
| `open` | `number` | Open price for the day. |
| `high` | `number` | High price for the day. |
| `low` | `number` | Low price for the day. |
| `previous_close` | `number` | Previous close price. |
| `ma_50` | `number` | 50-day moving average. |
| `ma_200` | `number` | 200-day moving average. |
| `year_high` | `number` | 52-week high. |
| `year_low` | `number` | 52-week low. |
| `market_cap` | `number` | Market Cap. |
| `shares_outstanding` | `number` | Shares outstanding. |
| `book_value` | `number` | Book value per share. |
| `price_to_book` | `number` | Price to book ratio. |
| `eps_ttm` | `number` | Earnings per share over the trailing twelve months. |
| `eps_forward` | `number` | Forward earnings per share. |
| `pe_forward` | `number` | Forward price-to-earnings ratio. |
| `dividend_yield` | `number` | Trailing twelve month dividend yield. |
| `exchange` | `string` | Exchange where the stock is listed. |
| `exchange_timezone` | `string` | Timezone of the exchange. |
| `earnings_date` | `string` | Most recent earnings date. |
| `currency` | `string` | Currency of the price data. |

---

### `equity.discovery.aggressive_small_caps`

```python
data.equity.discovery.aggressive_small_caps(sort='desc', limit=None)
```

Summary: Aggressive Small Caps

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.aggressive_small_caps` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/aggressive_small_caps` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer | null` | `-` | Limit the number of results. Default is all. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `price` | `number` | Last price. |
| `change` | `number` | Change in price. |
| `percent_change` | `number` | Percent change. |
| `volume` | `integer` | The trading volume. |
| `open` | `number` | Open price for the day. |
| `high` | `number` | High price for the day. |
| `low` | `number` | Low price for the day. |
| `previous_close` | `number` | Previous close price. |
| `ma_50` | `number` | 50-day moving average. |
| `ma_200` | `number` | 200-day moving average. |
| `year_high` | `number` | 52-week high. |
| `year_low` | `number` | 52-week low. |
| `market_cap` | `number` | Market Cap. |
| `shares_outstanding` | `number` | Shares outstanding. |
| `book_value` | `number` | Book value per share. |
| `price_to_book` | `number` | Price to book ratio. |
| `eps_ttm` | `number` | Earnings per share over the trailing twelve months. |
| `eps_forward` | `number` | Forward earnings per share. |
| `pe_forward` | `number` | Forward price-to-earnings ratio. |
| `dividend_yield` | `number` | Trailing twelve month dividend yield. |
| `exchange` | `string` | Exchange where the stock is listed. |
| `exchange_timezone` | `string` | Timezone of the exchange. |
| `earnings_date` | `string` | Most recent earnings date. |
| `currency` | `string` | Currency of the price data. |

---

### `equity.discovery.filings`

```python
data.equity.discovery.filings(start_time=None, end_time=None, form_type=None, limit=100)
```

Summary: Filings

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.filings` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/filings` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `form_type` | `no` | `string | null` | `-` | Filter by form type. Visit https://www.sec.gov/forms for a list of supported form types. |
| `limit` | `no` | `integer | null` | `100` | The number of data entries to return. Max 1000. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `filing_date` | `string` | The date of the data. |
| `accepted_date` | `string` | accepted_date |
| `form_type` | `string` | The form type of the filing. |
| `link` | `string` | URL to the filing page on the SEC site. |
| `final_link` | `string` | Direct URL to the main document of the filing. |

---

### `equity.discovery.gainers`

```python
data.equity.discovery.gainers(sort='desc', category='price_performer', limit=200)
```

Summary: Gainers

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.gainers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/gainers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `category` | `no` | `string` | `price_performer` | enum: dividend, energy, healthcare, industrials, price_performer, rising_stars, real_estate, tech, utilities, 52w_high, volume The category of list to retrieve. Defaults to `price_performer`. |
| `limit` | `no` | `integer | null` | `200` | Limit the number of results. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `price` | `number` | Last price. |
| `change` | `number` | Change in price. |
| `percent_change` | `number` | Percent change. |
| `volume` | `integer` | The trading volume. |
| `open` | `number` | Open price for the day. |
| `high` | `number` | High price for the day. |
| `low` | `number` | Low price for the day. |
| `previous_close` | `number` | Previous close price. |
| `ma_50` | `number` | 50-day moving average. |
| `ma_200` | `number` | 200-day moving average. |
| `year_high` | `number` | 52-week high. |
| `year_low` | `number` | 52-week low. |
| `market_cap` | `number` | Market Cap. |
| `shares_outstanding` | `number` | Shares outstanding. |
| `book_value` | `number` | Book value per share. |
| `price_to_book` | `number` | Price to book ratio. |
| `eps_ttm` | `number` | Earnings per share over the trailing twelve months. |
| `eps_forward` | `number` | Forward earnings per share. |
| `pe_forward` | `number` | Forward price-to-earnings ratio. |
| `dividend_yield` | `number` | Trailing twelve month dividend yield. |
| `exchange` | `string` | Exchange where the stock is listed. |
| `exchange_timezone` | `string` | Timezone of the exchange. |
| `earnings_date` | `string` | Most recent earnings date. |
| `currency` | `string` | Currency of the price data. |
| `thirty_day_price_change` | `number` | 30 Day Price Change. |
| `ninety_day_price_change` | `number` | 90 Day Price Change. |
| `avg_volume_10d` | `number` | 10 Day Avg. Volume. |
| `rank` | `integer` | The rank of the stock in the list. |

---

### `equity.discovery.growth_tech`

```python
data.equity.discovery.growth_tech(sort='desc', limit=200)
```

Summary: Growth Tech

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.growth_tech` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/growth_tech` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer | null` | `200` | Limit the number of results. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `price` | `number` | Last price. |
| `change` | `number` | Change in price. |
| `percent_change` | `number` | Percent change. |
| `volume` | `integer` | The trading volume. |
| `open` | `number` | Open price for the day. |
| `high` | `number` | High price for the day. |
| `low` | `number` | Low price for the day. |
| `previous_close` | `number` | Previous close price. |
| `ma_50` | `number` | 50-day moving average. |
| `ma_200` | `number` | 200-day moving average. |
| `year_high` | `number` | 52-week high. |
| `year_low` | `number` | 52-week low. |
| `market_cap` | `number` | Market Cap. |
| `shares_outstanding` | `number` | Shares outstanding. |
| `book_value` | `number` | Book value per share. |
| `price_to_book` | `number` | Price to book ratio. |
| `eps_ttm` | `number` | Earnings per share over the trailing twelve months. |
| `eps_forward` | `number` | Forward earnings per share. |
| `pe_forward` | `number` | Forward price-to-earnings ratio. |
| `dividend_yield` | `number` | Trailing twelve month dividend yield. |
| `exchange` | `string` | Exchange where the stock is listed. |
| `exchange_timezone` | `string` | Timezone of the exchange. |
| `earnings_date` | `string` | Most recent earnings date. |
| `currency` | `string` | Currency of the price data. |

---

### `equity.discovery.latest_financial_reports`

```python
data.equity.discovery.latest_financial_reports(date=None, report_type=None)
```

Summary: Latest Financial Reports

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.latest_financial_reports` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/latest_financial_reports` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `date` | `no` | `string | null` | `-` | A specific date to get data for. Defaults to today. |
| `report_type` | `no` | `string | null` | `-` | Return only a specific form type. Default is all quarterly, annual, and current reports. Choices: 1-K, 1-SA, 1-U, 10-D, 10-K, 10-KT, 10-Q, 10-QT, 20-F, 40-F, 6-K, 8-K. Multiple comma separated items allowed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `filing_date` | `string` | The date of the filing. |
| `period_ending` | `string` | Report for the period ending. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the company. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `sic` | `string` | Standard Industrial Classification code. |
| `report_type` | `string` | Type of filing. |
| `description` | `string` | Description of the report. |
| `url` | `string` | URL to the filing page. |
| `items` | `string` | Item codes associated with the filing. |
| `index_headers` | `string` | URL to the index headers file. |
| `complete_submission` | `string` | URL to the complete submission text file. |
| `metadata` | `string` | URL to the MetaLinks.json file, if available. |
| `financial_report` | `string` | URL to the Financial_Report.xlsx file, if available. |

---

### `equity.discovery.losers`

```python
data.equity.discovery.losers(sort='desc', limit=200)
```

Summary: Losers

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.losers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/losers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer | null` | `200` | Limit the number of results. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `price` | `number` | Last price. |
| `change` | `number` | Change in price. |
| `percent_change` | `number` | Percent change. |
| `volume` | `integer` | The trading volume. |
| `exchange` | `string` | Stock exchange where the security is listed. |
| `open` | `number` | Open price for the day. |
| `high` | `number` | High price for the day. |
| `low` | `number` | Low price for the day. |
| `previous_close` | `number` | Previous close price. |
| `ma_50` | `number` | 50-day moving average. |
| `ma_200` | `number` | 200-day moving average. |
| `year_high` | `number` | 52-week high. |
| `year_low` | `number` | 52-week low. |
| `market_cap` | `number` | Market Cap. |
| `shares_outstanding` | `number` | Shares outstanding. |
| `book_value` | `number` | Book value per share. |
| `price_to_book` | `number` | Price to book ratio. |
| `eps_ttm` | `number` | Earnings per share over the trailing twelve months. |
| `eps_forward` | `number` | Forward earnings per share. |
| `pe_forward` | `number` | Forward price-to-earnings ratio. |
| `dividend_yield` | `number` | Trailing twelve month dividend yield. |
| `exchange_timezone` | `string` | Timezone of the exchange. |
| `earnings_date` | `string` | Most recent earnings date. |
| `currency` | `string` | Currency of the price data. |

---

### `equity.discovery.top_retail`

```python
data.equity.discovery.top_retail(limit=5)
```

Summary: Top Retail

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.top_retail` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/top_retail` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `limit` | `no` | `integer` | `5` | The number of data entries to return. Max 1000. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `activity` | `number` | Activity of the symbol. |
| `sentiment` | `number` | Sentiment of the symbol. 1 is bullish, -1 is bearish. |

---

### `equity.discovery.undervalued_growth`

```python
data.equity.discovery.undervalued_growth(sort='desc', limit=200)
```

Summary: Undervalued Growth

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.undervalued_growth` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/undervalued_growth` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer | null` | `200` | Limit the number of results. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `price` | `number` | Last price. |
| `change` | `number` | Change in price. |
| `percent_change` | `number` | Percent change. |
| `volume` | `integer` | The trading volume. |
| `open` | `number` | Open price for the day. |
| `high` | `number` | High price for the day. |
| `low` | `number` | Low price for the day. |
| `previous_close` | `number` | Previous close price. |
| `ma_50` | `number` | 50-day moving average. |
| `ma_200` | `number` | 200-day moving average. |
| `year_high` | `number` | 52-week high. |
| `year_low` | `number` | 52-week low. |
| `market_cap` | `number` | Market Cap. |
| `shares_outstanding` | `number` | Shares outstanding. |
| `book_value` | `number` | Book value per share. |
| `price_to_book` | `number` | Price to book ratio. |
| `eps_ttm` | `number` | Earnings per share over the trailing twelve months. |
| `eps_forward` | `number` | Forward earnings per share. |
| `pe_forward` | `number` | Forward price-to-earnings ratio. |
| `dividend_yield` | `number` | Trailing twelve month dividend yield. |
| `exchange` | `string` | Exchange where the stock is listed. |
| `exchange_timezone` | `string` | Timezone of the exchange. |
| `earnings_date` | `string` | Most recent earnings date. |
| `currency` | `string` | Currency of the price data. |

---

### `equity.discovery.undervalued_large_caps`

```python
data.equity.discovery.undervalued_large_caps(sort='desc', limit=200)
```

Summary: Undervalued Large Caps

| Field | Value |
|---|---|
| Endpoint ID | `equity.discovery.undervalued_large_caps` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/discovery/undervalued_large_caps` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `sort` | `no` | `string` | `desc` | enum: asc, desc Sort order. Possible values: 'asc', 'desc'. Default: 'desc'. |
| `limit` | `no` | `integer | null` | `200` | Limit the number of results. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `price` | `number` | Last price. |
| `change` | `number` | Change in price. |
| `percent_change` | `number` | Percent change. |
| `volume` | `integer` | The trading volume. |
| `open` | `number` | Open price for the day. |
| `high` | `number` | High price for the day. |
| `low` | `number` | Low price for the day. |
| `previous_close` | `number` | Previous close price. |
| `ma_50` | `number` | 50-day moving average. |
| `ma_200` | `number` | 200-day moving average. |
| `year_high` | `number` | 52-week high. |
| `year_low` | `number` | 52-week low. |
| `market_cap` | `number` | Market Cap. |
| `shares_outstanding` | `number` | Shares outstanding. |
| `book_value` | `number` | Book value per share. |
| `price_to_book` | `number` | Price to book ratio. |
| `eps_ttm` | `number` | Earnings per share over the trailing twelve months. |
| `eps_forward` | `number` | Forward earnings per share. |
| `pe_forward` | `number` | Forward price-to-earnings ratio. |
| `dividend_yield` | `number` | Trailing twelve month dividend yield. |
| `exchange` | `string` | Exchange where the stock is listed. |
| `exchange_timezone` | `string` | Timezone of the exchange. |
| `earnings_date` | `string` | Most recent earnings date. |
| `currency` | `string` | Currency of the price data. |

---

### `equity.estimates.analyst_search`

```python
data.equity.estimates.analyst_search(analyst_name=None, firm_name=None, analyst_ids=None, firm_ids=None, limit=100, page=0, fields=None)
```

Summary: Analyst Search

| Field | Value |
|---|---|
| Endpoint ID | `equity.estimates.analyst_search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/estimates/analyst_search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `analyst_name` | `no` | `string | null` | `-` | Analyst names to return. Omitting will return all available analysts. Multiple comma separated items allowed |
| `firm_name` | `no` | `string | null` | `-` | Firm names to return. Omitting will return all available firms. Multiple comma separated items allowed |
| `analyst_ids` | `no` | `string | null` | `-` | List of analyst IDs to return. Multiple comma separated items allowed. |
| `firm_ids` | `no` | `string | null` | `-` | Firm IDs to return. Multiple comma separated items allowed. |
| `limit` | `no` | `integer | null` | `100` | Number of results returned. Limit 1000. |
| `page` | `no` | `integer | null` | `0` | Page offset. For optimization, performance and technical reasons, page offsets are limited from 0 - 100000. Limit the query results by other parameters such as date. |
| `fields` | `no` | `string | null` | `-` | Fields to include in the response. See https://docs.benzinga.io/benzinga-apis/calendar/get-ratings to learn about the available fields. Multiple comma separated items allowed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `last_updated` | `string` | Date of the last update. |
| `firm_name` | `string` | Firm name of the analyst. |
| `name_first` | `string` | Analyst first name. |
| `name_last` | `string` | Analyst last name. |
| `name_full` | `string` | Analyst full name. |
| `analyst_id` | `string` | ID of the analyst. |
| `firm_id` | `string` | ID of the analyst firm. |
| `smart_score` | `number` | A weighted average of the total_ratings_percentile, overall_avg_return_percentile, and overall_success_rate. |
| `overall_success_rate` | `number` | The percentage (normalized) of gain/loss ratings that resulted in a gain overall. |
| `overall_avg_return_percentile` | `number` | The percentile (normalized) of this analyst's overall average return per rating in comparison to other analysts. |
| `total_ratings_percentile` | `number` | The percentile (normalized) of this analyst's total number of ratings in comparison to the total number published by all other analysts. |
| `total_ratings` | `integer` | Number of recommendations made by this analyst. |
| `overall_gain_count` | `integer` | The number of ratings that have gained value since the date of recommendation. |
| `overall_loss_count` | `integer` | The number of ratings that have lost value since the date of recommendation. |
| `overall_average_return` | `number` | The average percent (normalized) price difference per rating since the date of recommendation. |
| `overall_std_dev` | `number` | The standard deviation in percent (normalized) price difference in the analyst's ratings since the date of recommendation. |
| `gain_count_1m` | `integer` | The number of ratings that have gained value over the last month. |
| `loss_count_1m` | `integer` | The number of ratings that have lost value over the last month. |
| `average_return_1m` | `number` | The average percent (normalized) price difference per rating over the last month. |
| `std_dev_1m` | `number` | The standard deviation in percent (normalized) price difference in the analyst's ratings over the last month. |
| `smart_score_1m` | `number` | A weighted average smart score over the last month. |
| `success_rate_1m` | `number` | The percentage (normalized) of gain/loss ratings that resulted in a gain over the last month. |
| `gain_count_3m` | `integer` | The number of ratings that have gained value over the last 3 months. |
| `loss_count_3m` | `integer` | The number of ratings that have lost value over the last 3 months. |
| `average_return_3m` | `number` | The average percent (normalized) price difference per rating over the last 3 months. |
| `std_dev_3m` | `number` | The standard deviation in percent (normalized) price difference in the analyst's ratings over the last 3 months. |
| `smart_score_3m` | `number` | A weighted average smart score over the last 3 months. |
| `success_rate_3m` | `number` | The percentage (normalized) of gain/loss ratings that resulted in a gain over the last 3 months. |
| `gain_count_6m` | `integer` | The number of ratings that have gained value over the last 6 months. |
| `loss_count_6m` | `integer` | The number of ratings that have lost value over the last 6 months. |
| `average_return_6m` | `number` | The average percent (normalized) price difference per rating over the last 6 months. |
| `std_dev_6m` | `number` | The standard deviation in percent (normalized) price difference in the analyst's ratings over the last 6 months. |
| `gain_count_9m` | `integer` | The number of ratings that have gained value over the last 9 months. |
| `loss_count_9m` | `integer` | The number of ratings that have lost value over the last 9 months. |
| `average_return_9m` | `number` | The average percent (normalized) price difference per rating over the last 9 months. |
| `std_dev_9m` | `number` | The standard deviation in percent (normalized) price difference in the analyst's ratings over the last 9 months. |
| `smart_score_9m` | `number` | A weighted average smart score over the last 9 months. |
| `success_rate_9m` | `number` | The percentage (normalized) of gain/loss ratings that resulted in a gain over the last 9 months. |
| `gain_count_1y` | `integer` | The number of ratings that have gained value over the last 1 year. |
| `loss_count_1y` | `integer` | The number of ratings that have lost value over the last 1 year. |
| `average_return_1y` | `number` | The average percent (normalized) price difference per rating over the last 1 year. |
| `std_dev_1y` | `number` | The standard deviation in percent (normalized) price difference in the analyst's ratings over the last 1 year. |
| `smart_score_1y` | `number` | A weighted average smart score over the last 1 year. |
| `success_rate_1y` | `number` | The percentage (normalized) of gain/loss ratings that resulted in a gain over the last 1 year. |
| `gain_count_2y` | `integer` | The number of ratings that have gained value over the last 2 years. |
| `loss_count_2y` | `integer` | The number of ratings that have lost value over the last 2 years. |
| `average_return_2y` | `number` | The average percent (normalized) price difference per rating over the last 2 years. |
| `std_dev_2y` | `number` | The standard deviation in percent (normalized) price difference in the analyst's ratings over the last 2 years. |
| `smart_score_2y` | `number` | A weighted average smart score over the last 2 years. |
| `success_rate_2y` | `number` | The percentage (normalized) of gain/loss ratings that resulted in a gain over the last 2 years. |
| `gain_count_3y` | `integer` | The number of ratings that have gained value over the last 3 years. |
| `loss_count_3y` | `integer` | The number of ratings that have lost value over the last 3 years. |
| `average_return_3y` | `number` | The average percent (normalized) price difference per rating over the last 3 years. |
| `std_dev_3y` | `number` | The standard deviation in percent (normalized) price difference in the analyst's ratings over the last 3 years. |
| `smart_score_3y` | `number` | A weighted average smart score over the last 3 years. |
| `success_rate_3y` | `number` | The percentage (normalized) of gain/loss ratings that resulted in a gain over the last 3 years. |

---

### `equity.estimates.consensus`

```python
data.equity.estimates.consensus(symbol="AAPL", fore_indicator_name=None, provider="bitget_data")
```

Summary: Consensus

| Field | Value |
|---|---|
| Endpoint ID | `equity.estimates.consensus` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/estimates/consensus` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single ticker. Required for THS; do not omit. |
| `fore_indicator_name` | `no` | `string / null` | `-` | Indicator filter. Not `industry_group_number`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | Ticker. |
| `fore_indicator_name` | `string / null` | Indicator. |
| `fore_org_num` | `integer / null` | Number of contributing orgs. |
| `fore_mean` | `number / null` | Mean forecast. |
| `min_fore_value` | `number / null` | Low forecast. |
| `high_fore_value` | `number / null` | High forecast. |
| `his_fore_value` | `number / null` | Historical forecast. |
| `target_consensus` | `number / null` | Alias of `fore_mean`. |
| `target_low` | `number / null` | Alias of `min_fore_value`. |
| `target_high` | `number / null` | Alias of `high_fore_value`. |
| `fiscal_year` | `integer / null` | Fiscal year. |
| `report_period` | `string / null` | Report period. |
| `currency_unit` | `string / null` | Currency. |
| `unit` | `string / null` | Unit. |
| `scraped_date` | `string / null` | Scrape date. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `industry_group_number` | `no` | `integer | null` | `-` | The Zacks industry group number. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | The company name. |
| `target_high` | `number` | High target of the price target consensus. |
| `target_low` | `number` | Low target of the price target consensus. |
| `target_consensus` | `number` | Consensus target of the price target consensus. |
| `target_median` | `number` | Median target of the price target consensus. |
| `recommendation` | `string` | Recommendation - buy, sell, etc. |
| `recommendation_mean` | `number` | Mean recommendation score where 1 is strong buy and 5 is strong sell. |
| `number_of_analysts` | `integer` | Number of analysts providing opinions. |
| `current_price` | `number` | Current price of the stock. |
| `currency` | `string` | Currency the stock is priced in. |
| `target_upside` | `number` | Percent of upside, as a normalized percent. |
| `total_analysts` | `integer` | Total number of analyst. |
| `buy_ratings` | `integer` | Number of buy ratings. |
| `sell_ratings` | `integer` | Number of sell ratings. |
| `hold_ratings` | `integer` | Number of hold ratings. |
| `consensus_action` | `string` | Consensus action. |
| `standard_deviation` | `number` | The standard deviation of target price estimates. |
| `raised` | `integer` | The number of analysts that have raised their target price estimates. |
| `lowered` | `integer` | The number of analysts that have lowered their target price estimates. |
| `most_recent_date` | `string` | The date of the most recent estimate. |
| `industry_group_number` | `integer` | The Zacks industry group number. |

---
### `equity.estimates.forward_ebitda`

```python
data.equity.estimates.forward_ebitda(symbol="AAPL", annual=None, is_actual_value=None, provider="bitget_data")
```

Summary: Forward Ebitda

| Field | Value |
|---|---|
| Endpoint ID | `equity.estimates.forward_ebitda` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/estimates/forward_ebitda` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single ticker. Required for THS. |
| `annual` | `no` | `integer / null` | `-` | Forecast fiscal year. Not `fiscal_year`. |
| `is_actual_value` | `no` | `boolean / null` | `-` | Filter actual vs forecast rows. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | Ticker. |
| `annual` | `integer / null` | Fiscal year. |
| `publish_ed` | `date / null` | Publication date. |
| `is_actual_value` | `boolean / null` | Actual vs forecast. |
| `revenue` | `number / null` | Revenue. |
| `ebit` | `number / null` | EBIT. |
| `ebitda` | `number / null` | EBITDA. |
| `net_profit_atsopc` | `number / null` | Attributable net profit. |
| `eps` | `number / null` | EPS. |
| `basic_eps` | `number / null` | Basic EPS. |
| `roe` | `number / null` | ROE. |
| `pe` | `number / null` | Forward PE when present. |
| `pb_ratio` | `number / null` | PB. |
| `ps_ratio` | `number / null` | PS. |
| `peg` | `number / null` | PEG. |
| `ev` | `number / null` | Enterprise value. |
| `currency_code` | `string / null` | Currency. |
| `fiscal_year` | `integer / null` | Alias of `annual` on some rows. |
| `mean` | `number / null` | Endpoint-specific: EPS, EBITDA, or revenue. |
| `date` / `last_updated` | `date / null` | Alias of `publish_ed` on some rows. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `fiscal_period` | `no` | `string | null` | `annual` | The future fiscal period to retrieve estimates for.; Filter for only full-year or quarterly estimates. |
| `limit` | `no` | `integer | null` | `-` | The number of data entries to return. Number of historical periods. |
| `include_historical` | `no` | `boolean` | `false` | If True, the data will include all past data and the limit will be ignored. |
| `estimate_type` | `no` | `string | null` | `-` | Limit the EBITDA estimates to this type. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `last_updated` | `string` | The date of the last update. |
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_year` | `integer` | Fiscal year for the estimate. |
| `fiscal_period` | `string` | Fiscal quarter for the estimate. |
| `calendar_year` | `integer` | Calendar year for the estimate. |
| `calendar_period` | `integer` | Calendar quarter for the estimate. |
| `low_estimate` | `integer` | The EBITDA estimate low for the period. |
| `high_estimate` | `integer` | The EBITDA estimate high for the period. |
| `mean` | `integer` | The EBITDA estimate mean for the period. |
| `median` | `integer` | The EBITDA estimate median for the period. |
| `standard_deviation` | `integer` | The EBITDA estimate standard deviation for the period. |
| `number_of_analysts` | `integer` | Number of analysts providing estimates for the period. |
| `conensus_type` | `string` | The type of estimate. |

---
### `equity.estimates.forward_eps`

```python
data.equity.estimates.forward_eps(symbol="AAPL", annual=None, is_actual_value=None, provider="bitget_data")
```

Summary: Forward Eps

| Field | Value |
|---|---|
| Endpoint ID | `equity.estimates.forward_eps` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/estimates/forward_eps` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single ticker. Required for THS. |
| `annual` | `no` | `integer / null` | `-` | Forecast fiscal year. Not `fiscal_year`. |
| `is_actual_value` | `no` | `boolean / null` | `-` | Filter actual vs forecast rows. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | Ticker. |
| `annual` | `integer / null` | Fiscal year. |
| `publish_ed` | `date / null` | Publication date. |
| `is_actual_value` | `boolean / null` | Actual vs forecast. |
| `revenue` | `number / null` | Revenue. |
| `ebit` | `number / null` | EBIT. |
| `ebitda` | `number / null` | EBITDA. |
| `net_profit_atsopc` | `number / null` | Attributable net profit. |
| `eps` | `number / null` | EPS. |
| `basic_eps` | `number / null` | Basic EPS. |
| `roe` | `number / null` | ROE. |
| `pe` | `number / null` | Forward PE when present. |
| `pb_ratio` | `number / null` | PB. |
| `ps_ratio` | `number / null` | PS. |
| `peg` | `number / null` | PEG. |
| `ev` | `number / null` | Enterprise value. |
| `currency_code` | `string / null` | Currency. |
| `fiscal_year` | `integer / null` | Alias of `annual` on some rows. |
| `mean` | `number / null` | Endpoint-specific: EPS, EBITDA, or revenue. |
| `date` / `last_updated` | `date / null` | Alias of `publish_ed` on some rows. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `fiscal_period` | `no` | `string | null` | `annual` | The future fiscal period to retrieve estimates for. |
| `limit` | `no` | `integer | null` | `-` | The number of data entries to return. Number of historical periods. |
| `include_historical` | `no` | `boolean` | `false` | If True, the data will include all past data and the limit will be ignored. |
| `fiscal_year` | `no` | `integer | null` | `-` | The future fiscal year to retrieve estimates for. When no symbol and year is supplied the current calendar year is used. |
| `calendar_year` | `no` | `integer | null` | `-` | The future calendar year to retrieve estimates for. When no symbol and year is supplied the current calendar year is used. |
| `calendar_period` | `no` | `string | null` | `-` | The future calendar period to retrieve estimates for. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `date` | `string` | The date of the data. |
| `fiscal_year` | `integer` | Fiscal year for the estimate. |
| `fiscal_period` | `string` | Fiscal quarter for the estimate. |
| `calendar_year` | `integer` | Calendar year for the estimate. |
| `calendar_period` | `string` | Calendar quarter for the estimate. |
| `low_estimate` | `number` | Estimated EPS low for the period. |
| `high_estimate` | `number` | Estimated EPS high for the period. |
| `mean` | `number` | Estimated EPS mean for the period. |
| `median` | `number` | Estimated EPS median for the period. |
| `standard_deviation` | `number` | Estimated EPS standard deviation for the period. |
| `number_of_analysts` | `integer` | Number of analysts providing estimates for the period. |
| `revisions_change_percent` | `number` | The earnings per share (EPS) percent change in estimate for the period. |
| `mean_1w` | `number` | The mean estimate for the period one week ago. |
| `mean_1m` | `number` | The mean estimate for the period one month ago. |
| `mean_2m` | `number` | The mean estimate for the period two months ago. |
| `mean_3m` | `number` | The mean estimate for the period three months ago. |

---
### `equity.estimates.forward_pe`

```python
data.equity.estimates.forward_pe(symbol="AAPL", annual=None, is_actual_value=None, provider="bitget_data")
```

Summary: Forward Pe

| Field | Value |
|---|---|
| Endpoint ID | `equity.estimates.forward_pe` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/estimates/forward_pe` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single ticker. Required for THS. |
| `annual` | `no` | `integer / null` | `-` | Forecast fiscal year. Not `fiscal_year`. |
| `is_actual_value` | `no` | `boolean / null` | `-` | Filter actual vs forecast rows. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | Ticker. |
| `annual` | `integer / null` | Fiscal year. |
| `publish_ed` | `date / null` | Publication date. |
| `is_actual_value` | `boolean / null` | Actual vs forecast. |
| `revenue` | `number / null` | Revenue. |
| `ebit` | `number / null` | EBIT. |
| `ebitda` | `number / null` | EBITDA. |
| `net_profit_atsopc` | `number / null` | Attributable net profit. |
| `eps` | `number / null` | EPS. |
| `basic_eps` | `number / null` | Basic EPS. |
| `roe` | `number / null` | ROE. |
| `pe` | `number / null` | Forward PE when present. |
| `pb_ratio` | `number / null` | PB. |
| `ps_ratio` | `number / null` | PS. |
| `peg` | `number / null` | PEG. |
| `ev` | `number / null` | Enterprise value. |
| `currency_code` | `string / null` | Currency. |
| `fiscal_year` | `integer / null` | Alias of `annual` on some rows. |
| `mean` | `number / null` | Endpoint-specific: EPS, EBITDA, or revenue. |
| `date` / `last_updated` | `date / null` | Alias of `publish_ed` on some rows. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `year_1` | `number` | Estimated PE ratio for the next fiscal year. |
| `year_2` | `number` | Estimated PE ratio two fiscal years from now. |
| `year_3` | `number` | Estimated PE ratio three fiscal years from now. |
| `year_4` | `number` | Estimated PE ratio four fiscal years from now. |
| `year_5` | `number` | Estimated PE ratio five fiscal years from now. |
| `peg_ratio_year_1` | `number` | Estimated Forward PEG ratio for the next fiscal year. |
| `eps_ttm` | `number` | The latest trailing twelve months earnings per share. |
| `last_updated` | `string` | The date the data was last updated. |

---
### `equity.estimates.forward_sales`

```python
data.equity.estimates.forward_sales(symbol="AAPL", annual=None, is_actual_value=None, provider="bitget_data")
```

Summary: Forward Sales

| Field | Value |
|---|---|
| Endpoint ID | `equity.estimates.forward_sales` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/estimates/forward_sales` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single ticker. Required for THS. |
| `annual` | `no` | `integer / null` | `-` | Forecast fiscal year. Not `fiscal_year`. |
| `is_actual_value` | `no` | `boolean / null` | `-` | Filter actual vs forecast rows. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | Ticker. |
| `annual` | `integer / null` | Fiscal year. |
| `publish_ed` | `date / null` | Publication date. |
| `is_actual_value` | `boolean / null` | Actual vs forecast. |
| `revenue` | `number / null` | Revenue. |
| `ebit` | `number / null` | EBIT. |
| `ebitda` | `number / null` | EBITDA. |
| `net_profit_atsopc` | `number / null` | Attributable net profit. |
| `eps` | `number / null` | EPS. |
| `basic_eps` | `number / null` | Basic EPS. |
| `roe` | `number / null` | ROE. |
| `pe` | `number / null` | Forward PE when present. |
| `pb_ratio` | `number / null` | PB. |
| `ps_ratio` | `number / null` | PS. |
| `peg` | `number / null` | PEG. |
| `ev` | `number / null` | Enterprise value. |
| `currency_code` | `string / null` | Currency. |
| `fiscal_year` | `integer / null` | Alias of `annual` on some rows. |
| `mean` | `number / null` | Endpoint-specific: EPS, EBITDA, or revenue. |
| `date` / `last_updated` | `date / null` | Alias of `publish_ed` on some rows. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `fiscal_year` | `no` | `integer | null` | `-` | The future fiscal year to retrieve estimates for. When no symbol and year is supplied the current calendar year is used. |
| `fiscal_period` | `no` | `string | null` | `-` | The future fiscal period to retrieve estimates for. |
| `calendar_year` | `no` | `integer | null` | `-` | The future calendar year to retrieve estimates for. When no symbol and year is supplied the current calendar year is used. |
| `calendar_period` | `no` | `string | null` | `-` | The future calendar period to retrieve estimates for. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the entity. |
| `date` | `string` | The date of the data. |
| `fiscal_year` | `integer` | Fiscal year for the estimate. |
| `fiscal_period` | `string` | Fiscal quarter for the estimate. |
| `calendar_year` | `integer` | Calendar year for the estimate. |
| `calendar_period` | `string` | Calendar quarter for the estimate. |
| `low_estimate` | `integer` | The sales estimate low for the period. |
| `high_estimate` | `integer` | The sales estimate high for the period. |
| `mean` | `integer` | The sales estimate mean for the period. |
| `median` | `integer` | The sales estimate median for the period. |
| `standard_deviation` | `integer` | The sales estimate standard deviation for the period. |
| `number_of_analysts` | `integer` | Number of analysts providing estimates for the period. |
| `revisions_1w_up` | `integer` | Number of revisions up in the last week. |
| `revisions_1w_down` | `integer` | Number of revisions down in the last week. |
| `revisions_1w_change_percent` | `number` | The analyst revisions percent change in estimate for the period of 1 week. |
| `revisions_1m_up` | `integer` | Number of revisions up in the last month. |
| `revisions_1m_down` | `integer` | Number of revisions down in the last month. |
| `revisions_1m_change_percent` | `number` | The analyst revisions percent change in estimate for the period of 1 month. |
| `revisions_3m_up` | `integer` | Number of revisions up in the last 3 months. |
| `revisions_3m_down` | `integer` | Number of revisions down in the last 3 months. |
| `revisions_3m_change_percent` | `number` | The analyst revisions percent change in estimate for the period of 3 months. |

---
### `equity.estimates.historical`

```python
data.equity.estimates.historical(symbol=..., freq='quarterly', period='annual', limit=None, page=None)
```

Summary: Historical

| Field | Value |
|---|---|
| Endpoint ID | `equity.estimates.historical` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/estimates/historical` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `freq` | `no` | `string` | `quarterly` | enum: annual, quarterly The frequency of the data. Can be 'annual' or 'quarterly'. |
| `period` | `no` | `string` | `annual` | enum: quarter, annual Time period of the data to return. |
| `limit` | `no` | `integer | null` | `-` | The number of data entries to return. |
| `page` | `no` | `integer | null` | `-` | Page number for paginated results. Used with limit. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `date` | `string` | The date of the data. |
| `estimated_revenue_low` | `integer` | Estimated revenue low. |
| `estimated_revenue_high` | `integer` | Estimated revenue high. |
| `estimated_revenue_avg` | `integer` | Estimated revenue average. |
| `estimated_sga_expense_low` | `integer` | Estimated SGA expense low. |
| `estimated_sga_expense_high` | `integer` | Estimated SGA expense high. |
| `estimated_sga_expense_avg` | `integer` | Estimated SGA expense average. |
| `estimated_ebitda_low` | `integer` | Estimated EBITDA low. |
| `estimated_ebitda_high` | `integer` | Estimated EBITDA high. |
| `estimated_ebitda_avg` | `integer` | Estimated EBITDA average. |
| `estimated_ebit_low` | `integer` | Estimated EBIT low. |
| `estimated_ebit_high` | `integer` | Estimated EBIT high. |
| `estimated_ebit_avg` | `integer` | Estimated EBIT average. |
| `estimated_net_income_low` | `integer` | Estimated net income low. |
| `estimated_net_income_high` | `integer` | Estimated net income high. |
| `estimated_net_income_avg` | `integer` | Estimated net income average. |
| `estimated_eps_avg` | `number` | Estimated EPS average. |
| `estimated_eps_high` | `number` | Estimated EPS high. |
| `estimated_eps_low` | `number` | Estimated EPS low. |
| `number_analyst_estimated_revenue` | `integer` | Number of analysts who estimated revenue. |
| `number_analysts_estimated_eps` | `integer` | Number of analysts who estimated EPS. |

---

### `equity.estimates.price_target`

```python
data.equity.estimates.price_target(symbol="AAPL", start_date=None, end_date=None, rating_org=None, provider="bitget_data")
```

Summary: Price Target

| Field | Value |
|---|---|
| Endpoint ID | `equity.estimates.price_target` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/estimates/price_target` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single ticker. Required for THS. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Not `start_time`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Not `end_time`. |
| `rating_org` | `no` | `string / null` | `-` | Analyst firm filter. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | Ticker. |
| `published_date` | `date / null` | Mapped from `rating_date`. |
| `analyst_firm` | `string / null` | Mapped from `rating_org`. |
| `price_target` | `number / null` | Mapped from `latest_target_price`. |
| `price_target_previous` | `number / null` | Mapped from `pre_target_price`. |
| `rating_current` | `string / null` | Mapped from `latest_rating_cn`. |
| `rating_previous` | `string / null` | Mapped from `pre_rating_cn`. |
| `action` | `string / null` | Mapped from `rating_chg_cn`. |
| `rating_org` | `string / null` | Analyst firm. |
| `rating_date` | `date / null` | Rating date. |
| `latest_target_price` | `number / null` | Current target. |
| `pre_target_price` | `number / null` | Previous target. |
| `latest_rating_cn` | `string / null` | Current rating. |
| `pre_rating_cn` | `string / null` | Previous rating. |
| `rating_chg_cn` | `string / null` | Rating action. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `page` | `no` | `integer | null` | `0` | Page offset. For optimization, performance and technical reasons, page offsets are limited from 0 - 100000. Limit the query results by other parameters such as date. Used in conjunction with the limit and date parameters. |
| `date` | `no` | `string | null` | `-` | Date for calendar data, shorthand for date_from and date_to. |
| `updated` | `no` | `string | integer | null` | `-` | Records last Updated Unix timestamp (UTC). This will force the sort order to be Greater Than or Equal to the timestamp indicated. The date can be a date string or a Unix timestamp. The date string must be in the format of YYYY-MM-DD. |
| `importance` | `no` | `integer | null` | `-` | Importance level to filter by. Uses Greater Than or Equal To the importance indicated |
| `action` | `no` | `string | null` | `-` | Filter by a specific action_company. |
| `analyst_ids` | `no` | `array | string | null` | `-` | accepts array values Comma-separated list of analyst (person) IDs. Omitting will bring back all available analysts. Multiple comma separated items allowed. |
| `firm_ids` | `no` | `array | string | null` | `-` | accepts array values Comma-separated list of firm IDs. Multiple comma separated items allowed. |
| `fields` | `no` | `array | string | null` | `-` | accepts array values Comma-separated list of fields to include in the response. See https://docs.benzinga.io/benzinga-apis/calendar/get-ratings to learn about the available fields. Multiple comma separated items allowed. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `published_date` | `string` | Published date of the price target. |
| `published_time` | `string` | Time of the original rating, UTC. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `exchange` | `string` | Exchange where the company is traded. |
| `company_name` | `string` | Name of company that is the subject of rating. |
| `analyst_name` | `string` | Analyst name. |
| `analyst_firm` | `string` | Name of the analyst firm that published the price target. |
| `currency` | `string` | Currency the data is denominated in. |
| `price_target` | `number` | The current price target. |
| `adj_price_target` | `number` | Adjusted price target for splits and stock dividends. |
| `price_target_previous` | `number` | Previous price target. |
| `previous_adj_price_target` | `number` | Previous adjusted price target. |
| `price_when_posted` | `number` | Price when posted. |
| `rating_current` | `string` | The analyst's rating for the company. |
| `rating_previous` | `string` | Previous analyst rating for the company. |
| `action` | `string` | Description of the change in rating from firm's last rating. |
| `status` | `string` | The action taken by the firm. |
| `rating_change` | `string` | The rating given by the analyst. |
| `news_title` | `string` | News title of the price target. |
| `news_url` | `string` | News URL of the price target. |
| `action_change` | `string` | Description of the change in price target from firm's last price target. |
| `importance` | `integer` | Subjective Basis of How Important Event is to Market. 5 = High. |
| `notes` | `string` | Notes of the price target. |
| `analyst_id` | `string` | Id of the analyst. |
| `url_news` | `string` | URL for analyst ratings news articles for this ticker on Benzinga.com. |
| `url_analyst` | `string` | URL for analyst ratings page for this ticker on Benzinga.com. |
| `id` | `string` | Unique ID of this entry. |
| `last_updated` | `string` | Last updated timestamp, UTC. |

---
### `equity.fundamental.balance`

```python
data.equity.fundamental.balance(symbol="AAPL", report_type=None, statement_year=None, provider="bitget_data")
```

Summary: Balance

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.balance` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/balance` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. |
| `report_type` | `no` | `string / null` | `-` | THS report type. |
| `statement_year` | `no` | `integer / null` | `-` | Fiscal year. Not `fiscal_year`. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `page` | `no` | `integer` | `1` | 1-based; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. Maps to query-service `size`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | From `sec_code`. |
| `period_ending` | `date / null` | From `ed`. |
| `fiscal_year` | `integer / null` | From `statement_year`. |
| `fiscal_period` | `string / null` | From `report_type`. |
| `currency_code` | `string / null` | Reporting currency. |
| `cce` | `number / null` | Cash and cash equivalents. |
| `net_receivables` | `number / null` | Net receivables. |
| `inventory` | `number / null` | Inventory. |
| `total_current_assets` | `number / null` | Current assets. |
| `net_property_plant_and_equip` | `number / null` | Net PP&E. |
| `goodwill` | `number / null` | Goodwill. |
| `total_noncurrent_assets` | `number / null` | Non-current assets. |
| `total_assets` | `number / null` | Total assets. |
| `accounts_payable` | `number / null` | Accounts payable. |
| `st_debt` | `number / null` | Short-term debt. |
| `lt_debt` | `number / null` | Long-term debt. |
| `total_current_liab` | `number / null` | Current liabilities. |
| `total_noncurrent_liab` | `number / null` | Non-current liabilities. |
| `total_liab` | `number / null` | Total liabilities. |
| `common_stock` | `number / null` | Common stock. |
| `retained_earning` | `number / null` | Retained earnings. |
| `total_holders_equity` | `number / null` | Shareholders' equity. |

Do not expect FMP field names such as `cash_and_cash_equivalents`.

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |
| `fiscal_year` | `no` | `integer | null` | `-` | The specific fiscal year. Reports do not go beyond 2008. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the report. |
| `fiscal_year` | `integer` | The fiscal year of the fiscal period. |
| `filing_date` | `string` | The date when the filing was made. |
| `accepted_date` | `string` | The date and time when the filing was accepted. |
| `cik` | `string` | The Central Index Key (CIK) assigned by the SEC, if applicable. |
| `symbol` | `string` | The stock ticker symbol. |
| `reported_currency` | `string` | The currency in which the balance sheet was reported. |
| `cash_and_cash_equivalents` | `integer` | Cash and cash equivalents. |
| `short_term_investments` | `integer` | Short term investments. |
| `cash_and_short_term_investments` | `integer` | Cash and short term investments. |
| `accounts_receivables` | `integer` | Accounts receivables. |
| `other_receivables` | `integer` | Other receivables. |
| `net_receivables` | `integer` | Net receivables. |
| `inventory` | `integer` | Inventory. |
| `other_current_assets` | `integer` | Other current assets. |
| `total_current_assets` | `integer` | Total current assets. |
| `plant_property_equipment_net` | `integer` | Plant property equipment net. |
| `goodwill` | `integer` | Goodwill. |
| `intangible_assets` | `integer` | Intangible assets. |
| `goodwill_and_intangible_assets` | `integer` | Goodwill and intangible assets. |
| `long_term_investments` | `integer` | Long term investments. |
| `tax_assets` | `integer` | Tax assets. |
| `other_non_current_assets` | `integer` | Other non current assets. |
| `non_current_assets` | `integer` | Total non current assets. |
| `other_assets` | `integer` | Other assets. |
| `total_assets` | `integer` | Total assets. |
| `accounts_payable` | `integer` | Accounts payable. |
| `prepaid_expenses` | `integer` | Prepaid expenses. |
| `accrued_expenses` | `integer` | Accrued expenses. |
| `short_term_debt` | `integer` | Short term debt. |
| `tax_payables` | `integer` | Tax payables. |
| `current_deferred_revenue` | `integer` | Current deferred revenue. |
| `other_current_liabilities` | `integer` | Other current liabilities. |
| `other_payables` | `integer` | Other payables. |
| `total_current_liabilities` | `integer` | Total current liabilities. |
| `total_payables` | `integer` | Total payables. |
| `long_term_debt` | `integer` | Long term debt. |
| `deferred_revenue_non_current` | `integer` | Non current deferred revenue. |
| `deferred_tax_liabilities_non_current` | `integer` | Deferred tax liabilities non current. |
| `other_non_current_liabilities` | `integer` | Other non current liabilities. |
| `total_non_current_liabilities` | `integer` | Total non current liabilities. |
| `capital_lease_obligations` | `integer` | Capital lease obligations. |
| `other_liabilities` | `integer` | Other liabilities. |
| `total_liabilities` | `integer` | Total liabilities. |
| `preferred_stock` | `integer` | Preferred stock. |
| `common_stock` | `integer` | Common stock. |
| `retained_earnings` | `integer` | Retained earnings. |
| `additional_paid_in_capital` | `integer` | Additional paid in capital. |
| `accumulated_other_comprehensive_income` | `integer` | Accumulated other comprehensive income (loss). |
| `total_common_equity` | `integer` | Total common equity. |
| `total_liabilities_and_shareholders_equity` | `integer` | Total liabilities and shareholders equity. |
| `minority_interest` | `integer` | Minority interest. |
| `total_liabilities_and_total_equity` | `integer` | Total liabilities and total equity. |
| `total_investments` | `integer` | Total investments. |
| `total_debt` | `integer` | Total debt. |
| `net_debt` | `integer` | Net debt. |

---
### `equity.fundamental.balance_growth`

```python
data.equity.fundamental.balance_growth(symbol=..., limit=50, period='annual')
```

Summary: Balance Growth

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.balance_growth` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/balance_growth` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the report. |
| `fiscal_year` | `integer` | The fiscal year of the fiscal period. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `reported_currency` | `string` | The currency in which the financial data is reported. |
| `growth_cash_and_cash_equivalents` | `number` | Growth rate of cash and cash equivalents. |
| `growth_short_term_investments` | `number` | Growth rate of short-term investments. |
| `growth_cash_and_short_term_investments` | `number` | Growth rate of cash and short-term investments. |
| `growth_accounts_receivables` | `number` | Growth rate of accounts receivable. |
| `growth_net_receivables` | `number` | Growth rate of net receivables. |
| `growth_inventory` | `number` | Growth rate of inventory. |
| `growth_total_current_assets` | `number` | Growth rate of total current assets. |
| `growth_property_plant_equipment_net` | `number` | Growth rate of net property, plant, and equipment. |
| `growth_goodwill` | `number` | Growth rate of goodwill. |
| `growth_intangible_assets` | `number` | Growth rate of intangible assets. |
| `growth_total_assets` | `number` | Growth rate of total assets. |
| `growth_total_liabilities` | `number` | Growth rate of total liabilities. |
| `growth_total_shareholders_equity` | `number` | Growth rate of total stockholders' equity. |
| `growth_total_debt` | `number` | Growth rate of total debt. |
| `growth_net_debt` | `number` | Growth rate of net debt. |

---

### `equity.fundamental.cash`

```python
data.equity.fundamental.cash(symbol="AAPL", report_type=None, statement_year=None, provider="bitget_data")
```

Summary: Cash

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.cash` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/cash` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. |
| `report_type` | `no` | `string / null` | `-` | THS report type. |
| `statement_year` | `no` | `integer / null` | `-` | Fiscal year. Not `fiscal_year`. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `page` | `no` | `integer` | `1` | 1-based; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. Maps to query-service `size`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | From `sec_code`. |
| `period_ending` | `date / null` | From `ed`. |
| `fiscal_year` | `integer / null` | From `statement_year`. |
| `fiscal_period` | `string / null` | From `report_type`. |
| `currency_code` | `string / null` | Reporting currency. |
| `net_cash_provided_by_oa` | `number / null` | Operating cash flow. |
| `net_cash_used_in_ia` | `number / null` | Investing cash flow. |
| `net_cash_used_in_fa` | `number / null` | Financing cash flow. |
| `depreciation_and_amortization` | `number / null` | D&A. |
| `payment_for_property_and_equip` | `number / null` | Capex. |
| `common_stock_issue` | `number / null` | Stock issuance. |
| `repur_of_common_stock` | `number / null` | Buyback. |
| `dividend_paid` | `number / null` | Dividends. |
| `effect_of_exchange_chg_on_cce` | `number / null` | FX effect. |
| `increase_in_cce` | `number / null` | Net change in cash. |
| `cce_at_boy` | `number / null` | Opening cash. |
| `cce_at_eoy` | `number / null` | Closing cash. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |
| `fiscal_year` | `no` | `integer | null` | `-` | The specific fiscal year. Reports do not go beyond 2008. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the report. |
| `fiscal_year` | `integer` | The fiscal year of the fiscal period. |
| `filing_date` | `string` | The date of the filing. |
| `accepted_date` | `string` | The date the filing was accepted. |
| `cik` | `string` | The Central Index Key (CIK) assigned by the SEC, if applicable. |
| `symbol` | `string` | The stock ticker symbol. |
| `reported_currency` | `string` | The currency in which the cash flow statement was reported. |
| `net_income` | `integer` | Net income. |
| `depreciation_and_amortization` | `integer` | Depreciation and amortization. |
| `stock_based_compensation` | `integer` | Stock-based compensation. |
| `change_in_working_capital` | `integer` | Change in working capital. |
| `net_cash_from_operating_activities` | `integer` | Net cash from operating activities. |
| `purchase_of_property_plant_and_equipment` | `integer` | Purchase of property, plant and equipment. |
| `acquisitions` | `integer` | Acquisitions. |
| `net_cash_from_investing_activities` | `integer` | Net cash from investing activities. |
| `repayment_of_debt` | `integer` | Repayment of debt. |
| `common_dividends_paid` | `integer` | Payment of common dividends. |
| `net_cash_from_financing_activities` | `integer` | Net cash from financing activities. |
| `net_change_in_cash_and_equivalents` | `integer` | Net change in cash and equivalents. |
| `cash_at_beginning_of_period` | `integer` | Cash at beginning of period. |
| `cash_at_end_of_period` | `integer` | Cash at end of period. |
| `operating_cash_flow` | `integer` | Operating cash flow. |
| `capital_expenditure` | `integer` | Capital expenditure. |
| `free_cash_flow` | `integer` | Free Cash Flow. |

---
### `equity.fundamental.cash_growth`

```python
data.equity.fundamental.cash_growth(symbol=..., limit=50, period='annual')
```

Summary: Cash Growth

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.cash_growth` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/cash_growth` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the report. |
| `fiscal_year` | `integer` | The fiscal year of the fiscal period. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `reported_currency` | `string` | The currency in which the financial data is reported. |
| `growth_net_income` | `number` | Growth rate of net income. |
| `growth_depreciation_and_amortization` | `number` | Growth rate of depreciation and amortization. |
| `growth_stock_based_compensation` | `number` | Growth rate of stock-based compensation. |
| `growth_change_in_working_capital` | `number` | Growth rate of change in working capital. |
| `growth_net_cash_from_operating_activities` | `number` | Growth rate of net cash provided by operating activities. |
| `growth_purchase_of_property_plant_and_equipment` | `number` | Growth rate of investments in property, plant, and equipment. |
| `growth_acquisitions` | `number` | Growth rate of net acquisitions. |
| `growth_net_cash_from_investing_activities` | `number` | Growth rate of net cash used for investing activities. |
| `growth_net_debt_issuance` | `number` | Growth rate of net debt issuance. |
| `growth_repayment_of_debt` | `number` | Growth rate of debt repayment. |
| `growth_net_cash_from_financing_activities` | `number` | Growth rate of net cash used/provided by financing activities. |
| `growth_net_change_in_cash_and_equivalents` | `number` | Growth rate of net change in cash. |
| `growth_operating_cash_flow` | `number` | Growth rate of operating cash flow. |
| `growth_capital_expenditure` | `number` | Growth rate of capital expenditure. |
| `growth_free_cash_flow` | `number` | Growth rate of free cash flow. |

---

### `equity.fundamental.dividends`

```python
data.equity.fundamental.dividends(symbol=..., start_time=None, end_time=None, limit=None)
```

Summary: Dividends

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.dividends` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/dividends` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `limit` | `no` | `integer | null` | `-` | Return N most recent payments.; The number of data entries to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `ex_dividend_date` | `string` | The ex-dividend date - the date on which the stock begins trading without rights to the dividend. |
| `amount` | `number` | The dividend amount per share. |
| `factor` | `number` | Factor by which to multiply stock prices before this date, in order to calculate historically-adjusted stock prices. |
| `currency` | `string` | The currency in which the dividend is paid. |
| `split_ratio` | `number` | The ratio of the stock split, if a stock split occurred. |
| `dividend_type` | `string` | The type of dividend - i.e., cash, stock. |
| `record_date` | `string` | The record date of ownership for eligibility. |
| `payment_date` | `string` | The payment date of the dividend. |
| `declaration_date` | `string` | Declaration date of the dividend. |
| `adjusted_amount` | `number` | Split-adjusted dividend amount. |
| `dividend_yield` | `number` | Dividend yield represented by the payment. |
| `frequency` | `string` | Frequency of the payment. |

---

### `equity.fundamental.employee_count`

```python
data.equity.fundamental.employee_count(symbol=..., start_time=None, end_time=None, limit=None)
```

Summary: Employee Count

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.employee_count` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/employee_count` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `limit` | `no` | `integer | null` | `-` | Number of records to return. Default is all. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `employees` | `integer` | Reported number of employees. |
| `company_name` | `string` | Company name associated with the data. |
| `source` | `string` | Source reference for the data. |
| `url` | `string` | URL link to the source of the data. |

---

### `equity.fundamental.esg_score`

```python
data.equity.fundamental.esg_score(symbol=...)
```

Summary: Esg Score

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.esg_score` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/esg_score` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | Period ending date of the report. |
| `disclosure_date` | `string` | Date when the report was submitted. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `company_name` | `string` | Company name of the company. |
| `form_type` | `string` | Form type where the disclosure was made. |
| `environmental_score` | `number` | Environmental score of the company. |
| `social_score` | `number` | Social score of the company. |
| `governance_score` | `number` | Governance score of the company. |
| `esg_score` | `number` | ESG score of the company. |
| `url` | `string` | URL to the report or filing. |

---

### `equity.fundamental.filings`

```python
data.equity.fundamental.filings(symbol=None, start_time=None, end_time=None, cik=None, limit=1000, page=0, form_type=None, thea_enabled=None, year=None, form_group='8k', use_cache=True)
```

Summary: Filings

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.filings` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/filings` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `cik` | `no` | `string | integer | null` | `-` | CIK number to look up. Overrides symbol.; Lookup filings by Central Index Key (CIK) instead of by symbol. |
| `limit` | `no` | `integer | null` | `1000` | Number of results to return. Max results is 1000.; The number of data entries to return. |
| `page` | `no` | `integer` | `0` | Page number for paginated results. Max page is 100. |
| `form_type` | `no` | `string | null` | `-` | SEC form type to filter by. |
| `thea_enabled` | `no` | `boolean | null` | `-` | Return filings that have been read by Intrinio's Thea NLP. |
| `year` | `no` | `integer | null` | `-` | Calendar year of the data, default is current year. The earliest year available is 1994, for all companies and form types. |
| `form_group` | `no` | `string` | `8k` | enum: annual, quarterly, proxy, insider, 8k, registration, comment The form group to fetch, default is 8k. |
| `use_cache` | `no` | `boolean` | `true` | Whether or not to use cache. If True, cache will store for one day. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `filing_date` | `string` | The date of the filing. |
| `report_type` | `string` | Type of filing. |
| `report_url` | `string` | URL to the actual report. |
| `period_ending` | `string` | The ending date for the reporting period, if available. |
| `name` | `string` | The name of the company, if available. |
| `reporting_owner` | `string` | The name of the reporting owner, if applicable. |
| `report_date` | `string` | The date of the filing. |
| `act` | `string` | The SEC Act number. |
| `items` | `string` | The SEC Item numbers. |
| `primary_doc_description` | `string` | The description of the primary document. |
| `primary_doc` | `string` | The filename of the primary document. |
| `accession_number` | `string` | The accession number. |
| `file_number` | `string` | The file number. |
| `is_inline_xbrl` | `string` | Whether the filing is an inline XBRL filing. |
| `is_xbrl` | `string` | Whether the filing is an XBRL filing. |
| `size` | `string` | The size of the filing. |
| `complete_submission_url` | `string` | The URL to the complete filing submission. |
| `filing_detail_url` | `string` | The URL to the filing details. |
| `filing_url` | `string` | URL to the filing page. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `accepted_date` | `string` | Accepted date of the filing. |
| `description` | `string` | The description of the filing. |
| `id` | `string` | Intrinio ID of the filing. |
| `period_end_date` | `string` | Ending date of the fiscal period for the filing. |
| `word_count` | `integer` | Number of words in the filing, if available. |

---

### `equity.fundamental.historical_attributes`

```python
data.equity.fundamental.historical_attributes(symbol=..., tag=..., start_time=None, end_time=None, frequency='yearly', limit=1000, tag_type=None, sort='desc')
```

Summary: Historical Attributes

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.historical_attributes` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/historical_attributes` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `tag` | `yes` | `string` | `-` | Intrinio data tag ID or code. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `frequency` | `no` | `string | null` | `yearly` | The frequency of the data. |
| `limit` | `no` | `integer | null` | `1000` | The number of data entries to return. Max 1000. |
| `tag_type` | `no` | `string | null` | `-` | Filter by type, when applicable. |
| `sort` | `no` | `string | null` | `desc` | Sort order. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `tag` | `string` | Tag name for the fetched data. |
| `value` | `number` | The value of the data. |

---

### `equity.fundamental.historical_eps`

```python
data.equity.fundamental.historical_eps(symbol=..., period='quarter', limit=None)
```

Summary: Historical Eps

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.historical_eps` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/historical_eps` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `period` | `no` | `string` | `quarter` | enum: annual, quarter Time period of the data to return. |
| `limit` | `no` | `integer | null` | `-` | The number of data entries to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `date` | `string` | The date of the data. |
| `eps_actual` | `integer` | Actual EPS from the earnings date. |
| `eps_estimated` | `integer` | Estimated EPS for the earnings date. |
| `surprise` | `number` | Surprise in EPS (Actual - Estimated). |
| `surprise_percent` | `number` | EPS surprise as a normalized percent. |
| `reported_date` | `string` | Date of the earnings report. |
| `report_time` | `string` | Time of day when the earnings report was released. |
| `revenue_estimated` | `integer` | Estimated consensus revenue for the reporting period. |
| `revenue_actual` | `integer` | The actual reported revenue. |
| `updated` | `string` | The date when the data was last updated. |

---

### `equity.fundamental.historical_splits`

```python
data.equity.fundamental.historical_splits(symbol=...)
```

Summary: Historical Splits

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.historical_splits` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/historical_splits` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `numerator` | `number` | Numerator of the split. |
| `denominator` | `number` | Denominator of the split. |
| `split_ratio` | `string` | Split ratio. |

---

### `equity.fundamental.income`

```python
data.equity.fundamental.income(symbol="AAPL", report_type=None, statement_year=None, provider="bitget_data")
```

Summary: Income

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.income` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/income` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. |
| `report_type` | `no` | `string / null` | `-` | THS report type. |
| `statement_year` | `no` | `integer / null` | `-` | Fiscal year. Not `fiscal_year`. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `page` | `no` | `integer` | `1` | 1-based; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. Maps to query-service `size`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | From `sec_code`. |
| `period_ending` | `date / null` | From `ed`. |
| `fiscal_year` | `integer / null` | From `statement_year`. |
| `fiscal_period` | `string / null` | From `report_type`. |
| `currency_code` | `string / null` | Reporting currency. |
| `revenue` | `number / null` | Operating revenue. |
| `total_revenue` | `number / null` | Total revenue. |
| `sales_cost` | `number / null` | Cost of sales. |
| `gross_profit` | `number / null` | Gross profit. |
| `rad_expenses` | `number / null` | R&D. |
| `marketing_selling_etc` | `number / null` | Selling expense. |
| `operating_income` | `number / null` | Operating income. |
| `income_from_co_before_it` | `number / null` | Pre-tax income. |
| `income_tax` | `number / null` | Income tax. |
| `net_income` | `number / null` | Net income. |
| `net_income_atcss` | `number / null` | Attributable net income. |
| `total_basic_earning_common_ps` | `number / null` | Basic EPS. |
| `total_dlt_earnings_common_ps` | `number / null` | Diluted EPS. |
| `total_compre_income` | `number / null` | Comprehensive income. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |
| `fiscal_year` | `no` | `integer | null` | `-` | The specific fiscal year. Reports do not go beyond 2008. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the report. |
| `fiscal_year` | `integer` | The fiscal year of the fiscal period. |
| `reported_currency` | `string` | The currency in which the balance sheet is reported. |
| `revenue` | `number` | Total revenue. |
| `cost_of_revenue` | `number` | Total cost of revenue. |
| `gross_profit` | `number` | Total gross profit. |
| `research_and_development_expense` | `number` | Research and development expense. |
| `selling_general_and_admin_expense` | `number` | Selling, general, and admin expense. |
| `total_operating_expenses` | `number` | Total operating expenses. |
| `total_operating_income` | `number` | Total operating income. |
| `ebitda` | `number` | Earnings Before Interest, Taxes, Depreciation and Amortization. |
| `ebit` | `number` | Earnings Before Interest and Taxes. |
| `income_tax_expense` | `number` | Income tax expense. |
| `net_income_attributable_to_common_shareholders` | `number` | Net income attributable to common shareholders. |
| `basic_earnings_per_share` | `number` | Basic earnings per share. |
| `diluted_earnings_per_share` | `number` | Diluted earnings per share. |
| `filing_date` | `string` | The date when the filing was made. |
| `accepted_date` | `string` | The date and time when the filing was accepted. |
| `cik` | `string` | The Central Index Key (CIK) assigned by the SEC, if applicable. |
| `symbol` | `string` | The stock ticker symbol. |

---
### `equity.fundamental.income_growth`

```python
data.equity.fundamental.income_growth(symbol=..., limit=50, period='annual')
```

Summary: Income Growth

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.income_growth` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/income_growth` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the report. |
| `fiscal_year` | `integer` | The fiscal year of the fiscal period. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `reported_currency` | `string` | The currency in which the financial data is reported. |
| `growth_revenue` | `number` | Growth rate of total revenue. |
| `growth_cost_of_revenue` | `number` | Growth rate of cost of goods sold. |
| `growth_gross_profit` | `number` | Growth rate of gross profit. |
| `growth_research_and_development_expense` | `number` | Growth rate of expenses on research and development. |
| `growth_selling_and_marketing_expense` | `number` | Growth rate of expenses on selling and marketing activities. |
| `growth_operating_expenses` | `number` | Growth rate of total operating expenses. |
| `growth_ebit` | `number` | Growth rate of Earnings Before Interest and Taxes (EBIT). |
| `growth_ebitda` | `number` | Growth rate of Earnings Before Interest, Taxes, Depreciation, and Amortization. |
| `growth_operating_income` | `number` | Growth rate of operating income. |
| `growth_income_before_tax` | `number` | Growth rate of income before taxes. |
| `growth_income_tax_expense` | `number` | Growth rate of income tax expenses. |
| `growth_net_income_from_continuing_operations` | `number` | Growth rate of net income from continuing operations. |
| `growth_consolidated_net_income` | `number` | Growth rate of net income. |
| `growth_basic_earings_per_share` | `number` | Growth rate of Earnings Per Share (EPS). |
| `growth_diluted_earnings_per_share` | `number` | Growth rate of diluted Earnings Per Share (EPS). |

---

### `equity.fundamental.latest_attributes`

```python
data.equity.fundamental.latest_attributes(symbol=..., tag=...)
```

Summary: Latest Attributes

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.latest_attributes` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/latest_attributes` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `tag` | `yes` | `string` | `-` | Intrinio data tag ID or code. Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `tag` | `string` | Tag name for the fetched data. |
| `value` | `string` | The value of the data. |

---

### `equity.fundamental.management`

```python
data.equity.fundamental.management(symbol="AAPL", provider="bitget_data")
```

Summary: Management

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.management` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/management` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. Required for THS. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `title` | `string / null` | Mapped from `position_name_en` (falls back to `position_name_cn`). |
| `name` | `string / null` | Mapped from `name_en` (falls back to `name_cn`). Rows missing both `name` and `title` are dropped. |
| `pay` | `number / null` | From `latest_salary`. |
| `currency_pay` | `string / null` | From `salary_currency_code`. |
| `gender` | `string / null` | Gender. |
| `year_born` | `integer / null` | From `year_of_birth`. |
| `sec_code` | `string / null` | Ticker as reported by THS. |
| `sec_short_name_cn` | `string / null` | Chinese short name of the company. |
| `name_cn` | `string / null` | Executive's Chinese name. |
| `nationality` | `string / null` | Nationality. |
| `high_edu` | `string / null` | Highest education level. |
| `resume_cn` | `string / null` | Chinese-language resume. |
| `resume_en` | `string / null` | English-language resume. |
| `position_name_cn` | `string / null` | Chinese position title. |
| `manage_type` | `string / null` | Management role type. |
| `publish_age_on_ed` | `integer / null` | Age as of the report date. |
| `latest_salary_year` | `integer / null` | Fiscal year of `pay`. |
| `latest_report_period` | `string / null` | Latest reporting period. |
| `share_held_num` | `number / null` | Shares held. |
| `total_held_ratio_cacl_value` | `number / null` | Calculated ownership ratio (%). |
| `total_voting_right` | `number / null` | Voting rights. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `title` | `string` | Designation of the key executive. |
| `name` | `string` | Name of the key executive. |
| `pay` | `integer` | Pay of the key executive. |
| `currency_pay` | `string` | Currency of the pay. |
| `gender` | `string` | Gender of the key executive. |
| `year_born` | `integer` | Birth year of the key executive. |
| `exercised_value` | `integer` | Value of shares exercised. |
| `unexercised_value` | `integer` | Value of shares not exercised. |
| `fiscal_year` | `integer` | Fiscal year of the pay. |

---

### `equity.fundamental.management_compensation`

```python
data.equity.fundamental.management_compensation(symbol=..., year=-1)
```

Summary: Management Compensation

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.management_compensation` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/management_compensation` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `year` | `no` | `integer` | `-1` | Filters results by year, enter 0 for all data available. Default is the most recent year in the dataset, -1. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `report_date` | `string` | Date of reported compensation. |
| `company_name` | `string` | The name of the company. |
| `executive` | `string` | Name and position. |
| `year` | `integer` | Year of the compensation. |
| `salary` | `integer` | Base salary. |
| `bonus` | `integer` | Bonus payments. |
| `stock_award` | `integer` | Stock awards. |
| `option_award` | `integer` | Option awards. |
| `incentive_plan_compensation` | `integer` | Incentive plan compensation. |
| `all_other_compensation` | `integer` | All other compensation. |
| `total` | `integer` | Total compensation. |
| `accepted_date` | `string` | Date the filing was accepted. |
| `url` | `string` | URL to the filing data. |

---

### `equity.fundamental.management_discussion_analysis`

```python
data.equity.fundamental.management_discussion_analysis(symbol=..., calendar_year=None, calendar_period=None, include_tables=True, use_cache=True, raw_html=False)
```

Summary: Management Discussion Analysis

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.management_discussion_analysis` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/management_discussion_analysis` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `calendar_year` | `no` | `integer | null` | `-` | Calendar year of the report. By default, is the current year. If the calendar period is not provided, but the calendar year is, it will return the annual report. |
| `calendar_period` | `no` | `string | null` | `-` | Calendar period of the report. By default, is the most recent report available for the symbol. If no calendar year and no calendar period are provided, it will return the most recent report. |
| `include_tables` | `no` | `boolean` | `true` | Return tables formatted as markdown in the text. Default is True. |
| `use_cache` | `no` | `boolean` | `true` | When True, the file will be cached for use later. Default is True. |
| `raw_html` | `no` | `boolean` | `false` | When True, the raw HTML content of the entire filing will be returned. Default is False. Use this option to parse the document manually. |

---

### `equity.fundamental.metrics`

```python
data.equity.fundamental.metrics(symbol="AAPL", report_type=None, report_annual=None, provider="bitget_data")
```

Summary: Metrics

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.metrics` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/metrics` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. |
| `report_type` | `no` | `string / null` | `-` | THS report type. |
| `report_annual` | `no` | `integer / null` | `-` | Report year. Not `fiscal_year` or `period`. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. |
| `page` | `no` | `integer` | `1` | 1-based; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. Maps to query-service `size`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | From `sec_code`. |
| `period_ending` | `date / null` | From `ed`. |
| `fiscal_year` | `integer / null` | From `report_annual`. |
| `fiscal_period` | `string / null` | From `report_type`. |
| `currency` | `string / null` | From `currency_code`. |
| `net_sales_rate` | `number / null` | Net margin (%). |
| `gross_selling_rate` | `number / null` | Gross margin (%). |
| `current_ratio` | `number / null` | Current ratio. |
| `quick_ratio` | `number / null` | Quick ratio. |
| `asset_liab_ratio` | `number / null` | Debt-to-assets (%). |
| `equity_multiplier` | `number / null` | Equity multiplier. |
| `ebit_to_interest_fee` | `number / null` | Interest coverage. |
| `roe_dlt` | `number / null` | Diluted ROE (%). |

Do not expect Intrinio fields such as `market_cap` or `altman_z_score`.

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `ttm` | `no` | `string` | `only` | enum: include, exclude, only Specify whether to include, exclude, or only show TTM (Trailing Twelve Months) data. The default is 'only'. |
| `period` | `no` | `string` | `annual` | enum: q1, q2, q3, q4, fy, annual, quarter Specify the fiscal period for the data. Ignored when TTM is set to 'only'. |
| `limit` | `no` | `integer | null` | `-` | Only applicable when TTM is not set to 'only'. Defines the number of most recent reporting periods to return. The default is 5. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `period_ending` | `string` | End date of the reporting period. |
| `fiscal_year` | `integer` | Fiscal year for the fiscal period, if available. |
| `fiscal_period` | `string` | Fiscal period for the data, if available. |
| `currency` | `string` | Currency in which the data is reported. |
| `market_cap` | `integer` | Market capitalization. |
| `enterprise_value` | `integer` | Enterprise Value. |
| `ev_to_sales` | `number` | Enterprise Value to Sales ratio. |
| `current_ratio` | `number` | Current Ratio. |
| `return_on_assets` | `number` | Return on Assets. |
| `return_on_equity` | `number` | Return on Equity. |
| `return_on_invested_capital` | `number` | Return on Invested Capital. |
| `pe_ratio` | `number` | Price-to-earnings ratio (TTM). |
| `price_to_book` | `number` | Price to book ratio. |
| `price_to_revenue` | `number` | Price to revenue ratio. |
| `quick_ratio` | `number` | Quick ratio. |
| `gross_margin` | `number` | Gross margin, as a normalized percent. |
| `profit_margin` | `number` | Profit margin, as a normalized percent. |
| `eps` | `number` | Basic earnings per share. |
| `ebitda` | `integer` | Earnings before interest, taxes, depreciation, and amortization. |
| `ebit` | `integer` | Earnings before interest and taxes. |
| `total_debt` | `integer` | Total debt. |
| `altman_z_score` | `number` | Altman Z-score. |
| `beta` | `number` | Beta relative to the broad market (rolling three-year). |
| `dividend_yield` | `number` | Dividend yield, as a normalized percent. |
| `last_price` | `number` | Last price of the stock. |
| `year_high` | `number` | 52 week high. |
| `year_low` | `number` | 52 week low. |
| `forward_pe` | `number` | Forward price-to-earnings ratio. |
| `peg_ratio` | `number` | PEG ratio (5-year expected). |

---
### `equity.fundamental.ratios`

```python
data.equity.fundamental.ratios(symbol="AAPL", start_date=None, end_date=None, provider="bitget_data")
```

Summary: Ratios

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.ratios` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/ratios` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Do not use `start_time`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Do not use `end_time`. |
| `page` | `no` | `integer` | `1` | 1-based; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | From `sec_code`. |
| `period_ending` | `date / null` | From `ts`. |
| `pe` | `number / null` | PE. |
| `pe_lyr` | `number / null` | PE LYR. |
| `pe_ttm_ed` | `number / null` | PE TTM. |
| `pb` | `number / null` | PB. |
| `pb_mrq` | `number / null` | PB MRQ. |
| `ps` | `number / null` | PS. |
| `ps_ttm_ed` | `number / null` | PS TTM. |
| `pcf` | `number / null` | PCF. |
| `peg_his` | `number / null` | Historical PEG. |
| `ev1` | `number / null` | Enterprise value. |
| `ent_multi` | `number / null` | EV multiple. |
| `tmv_usd` | `number / null` | Market cap USD. |
| `cir_tmv_usd` | `number / null` | Circulating market cap USD. |
| `div_yield_12m` | `number / null` | 12-month dividend yield. |

Daily series, not TTM statement ratios. Do not expect `grossProfitMarginTTM`.

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `limit` | `no` | `integer | null` | `50` | Only applicable when TTM is not set to 'only'. Number of most recent reporting periods to return. Max 1000. |
| `ttm` | `no` | `string` | `only` | enum: include, exclude, only Specify whether to include, exclude, or only show TTM (Trailing Twelve Months) data. The default is 'only'. |
| `period` | `no` | `string` | `annual` | Specify the fiscal period for the data.; Time period of the data to return. |
| `fiscal_year` | `no` | `integer | null` | `-` | The specific fiscal year. Reports do not go beyond 2008. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `period_ending` | `string` | The date of the data. |
| `fiscal_period` | `string` | Period of the financial ratios. |
| `fiscal_year` | `integer` | Fiscal year. |
| `currency` | `string` | Currency in which the company reports financials. |
| `grossProfitMarginTTM` | `number` | Gross profit margin. |
| `ebitMarginTTM` | `number` | Earnings before interest and taxes (EBIT) margin. |
| `ebitdaMarginTTM` | `number` | Earnings before interest, taxes, depreciation, and amortization (EBITDA) margin. |
| `operatingProfitMarginTTM` | `number` | Operating profit margin. |
| `netProfitMarginTTM` | `number` | Net profit margin. |
| `priceToEarningsRatioTTM` | `number` | Price to earnings (P/E) ratio. |
| `priceToBookRatioTTM` | `number` | Price to book (P/B) ratio. |
| `priceToSalesRatioTTM` | `number` | Price to sales (P/S) ratio. |
| `debtToEquityRatioTTM` | `number` | Debt to equity ratio. |
| `currentRatioTTM` | `number` | Current ratio. |
| `dividendYieldTTM` | `number` | Dividend yield. |
| `dividendPerShareTTM` | `number` | Dividend per share. |
| `revenuePerShareTTM` | `number` | Revenue per share. |
| `bookValuePerShareTTM` | `number` | Book value per share. |
| `freeCashFlowPerShareTTM` | `number` | Free cash flow per share. |

---
### `equity.fundamental.reported_financials`

```python
data.equity.fundamental.reported_financials(symbol=..., period='annual', statement_type='balance', limit=100, fiscal_year=None)
```

Summary: Reported Financials

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.reported_financials` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/reported_financials` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |
| `statement_type` | `no` | `string` | `balance` | The type of financial statement - i.e, balance, income, cash.; Cash flow statements are reported as YTD, Q4 is the same as FY. |
| `limit` | `no` | `integer | null` | `100` | The number of data entries to return. Max 1000. |
| `fiscal_year` | `no` | `integer | null` | `-` | The specific fiscal year. Reports do not go beyond 2008. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The ending date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the report (e.g. FY, Q1, etc.). |
| `fiscal_year` | `integer` | The fiscal year of the fiscal period. |

---

### `equity.fundamental.revenue_per_geography`

```python
data.equity.fundamental.revenue_per_geography(symbol=..., period='annual')
```

Summary: Revenue Per Geography

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.revenue_per_geography` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/revenue_per_geography` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the reporting period. |
| `fiscal_year` | `integer` | The fiscal year of the reporting period. |
| `filing_date` | `string` | The filing date of the report. |
| `region` | `string` | The region represented by the revenue data. |
| `revenue` | `integer` | The total revenue attributed to the region. |

---

### `equity.fundamental.revenue_per_segment`

```python
data.equity.fundamental.revenue_per_segment(symbol=..., period='annual')
```

Summary: Revenue Per Segment

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.revenue_per_segment` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/revenue_per_segment` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `period` | `no` | `string` | `annual` | Time period of the data to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end date of the reporting period. |
| `fiscal_period` | `string` | The fiscal period of the reporting period. |
| `fiscal_year` | `integer` | The fiscal year of the reporting period. |
| `filing_date` | `string` | The filing date of the report. |
| `business_line` | `string` | The business line represented by the revenue data. |
| `revenue` | `integer` | The total revenue attributed to the business line. |

---

### `equity.fundamental.search_attributes`

```python
data.equity.fundamental.search_attributes(query=..., limit=1000)
```

Summary: Search Attributes

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.search_attributes` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/search_attributes` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `yes` | `string` | `-` | Query to search for. |
| `limit` | `no` | `integer | null` | `1000` | The number of data entries to return. Max 1000. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | ID of the financial attribute. |
| `name` | `string` | Name of the financial attribute. |
| `tag` | `string` | Tag of the financial attribute. |
| `statement_code` | `string` | Code of the financial statement. |
| `statement_type` | `string` | Type of the financial statement. |
| `parent_name` | `string` | Parent's name of the financial attribute. |
| `sequence` | `integer` | Sequence of the financial statement. |
| `factor` | `string` | Unit of the financial attribute. |
| `transaction` | `string` | Transaction type (credit/debit) of the financial attribute. |
| `type` | `string` | Type of the financial attribute. |
| `unit` | `string` | Unit of the financial attribute. |

---

### `equity.fundamental.trailing_dividend_yield`

```python
data.equity.fundamental.trailing_dividend_yield(symbol=..., limit=252)
```

Summary: Trailing Dividend Yield

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.trailing_dividend_yield` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/trailing_dividend_yield` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `252` | The number of data entries to return. Default is 252 (trading days in a year). Max 1000. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `trailing_dividend_yield` | `number` | Trailing dividend yield. |

---

### `equity.fundamental.transcript`

```python
data.equity.fundamental.transcript(symbol=..., year=None, quarter=None)
```

Summary: Transcript

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.transcript` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/transcript` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `year` | `no` | `integer | null` | `-` | Year of the earnings call transcript. |
| `quarter` | `no` | `integer | null` | `-` | Quarterly period of the earnings call transcript. |

---

### `equity.historical_market_cap`

```python
data.equity.historical_market_cap(symbol=..., start_time=None, end_time=None, interval='day')
```

Summary: Historical Market Cap

| Field | Value |
|---|---|
| Endpoint ID | `equity.historical_market_cap` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/historical_market_cap` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `interval` | `no` | `string` | `day` | enum: day, week, month, quarter, year None |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `market_cap` | `integer` | Market capitalization of the security. |

---

### `equity.market_snapshots`

```python
data.equity.market_snapshots(market='nasdaq', date=None)
```

Summary: Market Snapshots

| Field | Value |
|---|---|
| Endpoint ID | `equity.market_snapshots` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/market_snapshots` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `market` | `no` | `string` | `nasdaq` | enum: amex, ams, ase, asx, ath, bme, bru, bud, bue, cai, cnq, commodity, cph, crypto, dfm, doh, dus, etf, euronext, forex, hel, hkse, ice, iob, index, ist, jkt, jnb, jpx, kls, koe, ksc, kuw, lse, mex, mil, mutual_fund, nasdaq, neo, nse, nyse, nze, osl, otc, pnk, pra, ris, sao, sau, ses, set, sgo, shh, shz, six, sto, tai, tlv, tsx, two, vie, wse, xetra The market to fetch data for. |
| `date` | `no` | `string | null` | `-` | The date of the data. Can be a datetime or an ISO datetime string. Historical data appears to go back to mid-June 2022. Example: '2024-03-08T12:15:00+0400' |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `exchange` | `string` | Exchange the security is listed on. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the company, fund, or security. |
| `open` | `number` | The open price. |
| `high` | `number` | The high price. |
| `low` | `number` | The low price. |
| `close` | `number` | The close price. |
| `volume` | `integer` | The trading volume. |
| `prev_close` | `number` | The previous close price. |
| `change` | `number` | The change in price from the previous close. |
| `change_percent` | `number` | The change in price from the previous close, as a normalized percent. |
| `last_price` | `number` | The last trade price. |
| `last_size` | `integer` | The last trade size. |
| `last_volume` | `integer` | The last trade volume. |
| `last_trade_timestamp` | `string` | The timestamp of the last trade. |
| `bid_size` | `integer` | The size of the last bid price. |
| `bid_price` | `number` | The last bid price. |
| `ask_price` | `number` | The last ask price. |
| `ask_size` | `integer` | The size of the last ask price. |
| `ma_50` | `number` | The 50-day moving average. |
| `ma_200` | `number` | The 200-day moving average. |
| `year_high` | `number` | The 52-week high. |
| `year_low` | `number` | The 52-week low. |
| `market_cap` | `integer` | Market cap of the stock. |
| `last_price_timestamp` | `string` | The timestamp of the last price. |

---

### `equity.ownership.form_13f`

```python
data.equity.ownership.form_13f(symbol="AAPL", start_date=None, end_date=None, provider="bitget_data")
```

Summary: Form 13F

| Field | Value |
|---|---|
| Endpoint ID | `equity.ownership.form_13f` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/ownership/form_13f` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. Pass a US ticker, not a CIK. Do not use `date`. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Do not use `start_time`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Do not use `end_time`. |
| `page` | `no` | `integer` | `1` | 1-based; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | US ticker requested. |
| `period_ending` | `date / null` | From `ts`. |
| `org_name` | `string / null` | Institution. |
| `issuer` | `string / null` | From `issuer_name`. |
| `cusip` | `string / null` | CUSIP. |
| `asset_class` | `string / null` | From `position_type`. |
| `principal_amount` | `integer / null` | From `position_shares`. |
| `value` | `integer / null` | From `position_market_value`. |
| `option_type` | `string / null` | From `option_direction` when call/put. |

`symbol` is a US ticker, not a CIK. `date` is not a THS filter.

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. A CIK can be used. |
| `date` | `no` | `string | null` | `-` | A specific date to get data for. The date represents the end of the reporting period. All form 13F-HR filings are based on the calendar year and are reported quarterly. If a date is not supplied, the most recent filing is returned. Submissions beginning 2013-06-30 are supported. |
| `limit` | `no` | `integer | null` | `1` | Number of previous filings to return. The date parameter takes priority over this parameter. Max 100. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `period_ending` | `string` | The end-of-quarter date of the filing. |
| `issuer` | `string` | The name of the issuer. |
| `cusip` | `string` | The CUSIP of the security. |
| `asset_class` | `string` | The title of the asset class for the security. |
| `security_type` | `string` | Whether the principal amount represents the number of shares or the principal amount of such class. |
| `option_type` | `string` | Defined when the holdings being reported are put or call options. |
| `investment_discretion` | `string` | The investment discretion held by the Manager. |
| `voting_authority_sole` | `integer` | The number of shares for which the Manager exercises sole voting authority. |
| `voting_authority_shared` | `integer` | The number of shares for which the Manager exercises a defined shared voting authority. |
| `voting_authority_none` | `integer` | The number of shares for which the Manager exercises no voting authority. |
| `principal_amount` | `integer` | The total number of shares of the class of security or the principal amount of such class. |
| `value` | `integer` | The fair market value of the holding of the particular class of security. |
| `weight` | `number` | The weight of the security relative to the market value of all securities in the filing, as a normalized percent. |

---
### `equity.ownership.government_trades`

```python
data.equity.ownership.government_trades(symbol=None, chamber='all', limit=50)
```

Summary: Government Trades

| Field | Value |
|---|---|
| Endpoint ID | `equity.ownership.government_trades` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/ownership/government_trades` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `chamber` | `no` | `string` | `all` | Government Chamber. |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `date` | `string` | The date of the data. |
| `transaction_date` | `string` | Date of Transaction. |
| `representative` | `string` | Name of Representative. |
| `chamber` | `string` | Government Chamber - House or Senate. |
| `owner` | `string` | Ownership status (e.g., Spouse, Joint). |
| `asset_type` | `string` | Type of asset involved in the transaction. |
| `asset_description` | `string` | Description of the asset. |
| `transaction_type` | `string` | Type of transaction (e.g., Sale, Purchase). |
| `amount` | `string` | Transaction amount range. |
| `comment` | `string` | Additional comments on the transaction. |
| `url` | `string` | Link to the transaction document. |

---

### `equity.ownership.insider_trading`

```python
data.equity.ownership.insider_trading(symbol="AAPL", start_date=None, end_date=None, provider="bitget_data")
```

Summary: Insider Trading

| Field | Value |
|---|---|
| Endpoint ID | `equity.ownership.insider_trading` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/ownership/insider_trading` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. Use `start_date`/`end_date`, not `start_time`/`end_time`. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Do not use `start_time`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Do not use `end_time`. |
| `page` | `no` | `integer` | `1` | 1-based; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | From `sec_code`. |
| `owner_name` | `string / null` | From `reporter_name`. |
| `owner_title` | `string / null` | From `specific_position`. |
| `ownership_type` | `string / null` | From `inner_type`. |
| `transaction_date` | `date / null` | From `td_date`. |
| `transaction_type` | `string / null` | From `inner_trans_type`. |
| `securities_transacted` | `number / null` | From `td_vol`. |
| `transaction_price` | `number / null` | From `td_price`. |
| `securities_owned` | `number / null` | From `held_num_after_trading`. |
| `filing_date` | `date / null` | From `announcement_date`. |
| `filing_url` | `string / null` | From `announ_source_link`. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `transaction_type` | `no` | `string | null` | `-` | Type of the transaction. |
| `statistics` | `no` | `boolean` | `false` | Flag to return summary statistics for the given symbol. Setting as True will ignore other parameters except symbol. |
| `ownership_type` | `no` | `string | null` | `-` | Type of ownership. |
| `sort_by` | `no` | `string | null` | `updated_on` | Field to sort by. |
| `use_cache` | `no` | `boolean` | `true` | Persist the data locally for future use. Default is True. Each form submission is an individual download and the SEC limits the number of concurrent downloads. This prevents the same file from being downloaded multiple times. |
| `summary` | `no` | `boolean` | `false` | Return a summary of the insider activity instead of the individuals. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `company_cik` | `string` | CIK number of the company. |
| `filing_date` | `string` | Filing date of the trade. |
| `transaction_date` | `string` | Date of the transaction. |
| `owner_cik` | `integer` | Reporting individual's CIK. |
| `owner_name` | `string` | Name of the reporting individual. |
| `owner_title` | `string` | The title held by the reporting individual. |
| `ownership_type` | `string` | Type of ownership, direct or indirect. |
| `transaction_type` | `string` | Type of transaction being reported. |
| `acquisition_or_disposition` | `string` | Acquisition or disposition of the shares. |
| `security_type` | `string` | The type of security transacted. |
| `securities_owned` | `number` | Number of securities owned by the reporting individual. |
| `securities_transacted` | `number` | Number of securities transacted by the reporting individual. |
| `transaction_price` | `number` | The price of the transaction. |
| `filing_url` | `string` | Link to the filing. |
| `company_name` | `string` | Name of the company. |
| `form` | `string` | Form type. |
| `transaction_value` | `number` | Total value of the transaction. |

---
### `equity.ownership.institutional`

```python
data.equity.ownership.institutional(symbol=..., year=None, quarter=None)
```

Summary: Institutional

| Field | Value |
|---|---|
| Endpoint ID | `equity.ownership.institutional` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/ownership/institutional` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `year` | `no` | `integer | null` | `-` | Calendar year for the data. If not provided, the latest year is used. |
| `quarter` | `no` | `integer | null` | `-` | Calendar quarter for the data. Valid values are 1, 2, 3, or 4. If not provided, the quarter previous to the current quarter is used. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `date` | `string` | The date of the data. |
| `investors_holding` | `integer` | Number of investors holding the stock. |
| `last_investors_holding` | `integer` | Number of investors holding the stock in the last quarter. |
| `investors_holding_change` | `integer` | Change in the number of investors holding the stock. |
| `number_of_13f_shares` | `integer` | Number of 13F shares. |
| `total_invested` | `number` | Total amount invested. |
| `ownership_percent` | `number` | Ownership percent. |
| `new_positions` | `integer` | Number of new positions. |
| `increased_positions` | `integer` | Number of increased positions. |
| `closed_positions` | `integer` | Number of closed positions. |
| `reduced_positions` | `integer` | Number of reduced positions. |
| `put_call_ratio` | `number` | Put-call ratio. |

---

### `equity.ownership.major_holders`

```python
data.equity.ownership.major_holders(symbol="AAPL", start_date=None, end_date=None, provider="bitget_data")
```

Summary: Major Holders

| Field | Value |
|---|---|
| Endpoint ID | `equity.ownership.major_holders` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/ownership/major_holders` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. Do not use `year`/`quarter`. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Do not use `start_time`. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Do not use `end_time`. |
| `page` | `no` | `integer` | `1` | 1-based; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | From `sec_code`. |
| `investor_name` | `string / null` | From `reporter_name`. |
| `date` | `date / null` | From `ed`. |
| `filing_date` | `date / null` | From `announcement_date`. |
| `share_held_num` | `number / null` | Shares held. |
| `total_held_ratio_dsclsr_value` | `number / null` | Disclosed ownership (%). |
| `total_voting_right` | `number / null` | Voting rights. |

Do not use `year`/`quarter`. `page` is 1-based, default `1`.

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `year` | `no` | `integer | null` | `-` | Calendar year for the data. If not provided, the latest year is used. |
| `quarter` | `no` | `integer | null` | `-` | Calendar quarter for the data. Valid values are 1, 2, 3, or 4. If not provided, the quarter previous to the current quarter is used. |
| `page` | `no` | `integer | null` | `-` | Page number, used in conjunction with the limit. The default is 0. |
| `limit` | `no` | `integer | null` | `-` | Number of items to return per page. The default is 100, which is the maximum. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `investor_name` | `string` | Investing entity's name. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `date` | `string` | The date of the data. For the period ending. |
| `filing_date` | `string` | Date when reported. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `security_name` | `string` | Security name. |
| `security_type` | `string` | Type or class of security. |
| `security_cusip` | `string` | CUSIP of the security. |
| `weight` | `number` | Weight relative to the total reported portfolio. |
| `market_value` | `integer` | Market value of the stock ownership. |
| `shares_number` | `integer` | Number of controlled shares. |
| `shares_change` | `number` | Change in shares number from the previous quarter. |
| `is_new` | `boolean` | If the security was newly added this quarter. |
| `is_sold_out` | `boolean` | If the security was sold out this quarter. |
| `ownership` | `number` | Ownership stake in the security, as a percent. |
| `avg_price_paid` | `number` | Average price paid for the shares. |
| `holding_period` | `integer` | Holding period of the security. |
| `first_added` | `string` | When the security was first reported as held. |
| `performance` | `number` | Performance value of the security holding. |

---
### `equity.ownership.share_statistics`

```python
data.equity.ownership.share_statistics(symbol=...)
```

Summary: Share Statistics

| Field | Value |
|---|---|
| Endpoint ID | `equity.ownership.share_statistics` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/ownership/share_statistics` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `date` | `string` | The date of the data. |
| `free_float` | `number` | Percentage of unrestricted shares of a publicly-traded company. |
| `float_shares` | `integer` | Number of shares available for trading by the general public. |
| `outstanding_shares` | `integer` | Total number of shares of a publicly-traded company. |
| `adjusted_outstanding_shares` | `number` | Total number of shares of a publicly-traded company, adjusted for splits. |
| `public_float` | `number` | Aggregate market value of the shares of a publicly-traded company. |
| `url` | `string` | URL to the source document, if available. |
| `implied_shares_outstanding` | `integer` | Implied Shares Outstanding of common equity. |
| `short_interest` | `integer` | Number of shares that are reported short. |
| `short_percent_of_float` | `number` | Percentage of shares that are reported short, as a normalized percent. |
| `days_to_cover` | `number` | Number of days to repurchase the shares as a ratio of average daily volume. |
| `insider_ownership` | `number` | Percentage of shares held by insiders, as a normalized percent. |
| `institution_ownership` | `number` | Percentage of shares held by institutions, as a normalized percent. |
| `institutions_count` | `integer` | Number of institutions holding shares. |

---

### `equity.price.historical`

```python
data.equity.price.historical(symbol="AAPL", start_date=None, end_date=None, provider="bitget_data")
```

Summary: Historical

| Field | Value |
|---|---|
| Endpoint ID | `equity.price.historical` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/price/historical` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Provider massive returns one page of aggregate bars per request. Paginate by passing `cursor` and `next_time` from the prior response when `has_more` is true. Also supports `provider="bitget_data"` — this is a separate Bitget-exchange equity-perpetual kline feed, **not** the THS contract described at the top of this file; use only the **bitget_data provider** query/response tables below and ignore the THS notes and other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single ticker only (no multi-symbol). Sent upstream unchanged as `<SYMBOL>/USDT` against Bitget's equity-perpetual market — no RWA (`R`) prefix. |
| `start_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Defaults to `end_date` minus 90 days. |
| `end_date` | `no` | `date / null` | `-` | Inclusive `YYYY-MM-DD`. Defaults to today. |
| `start_time` | `no` | `integer / null` | `-` | Unix ms timestamp. Takes priority over `start_date` when both are provided. |
| `end_time` | `no` | `integer / null` | `-` | Unix ms timestamp. Takes priority over `end_date` when both are provided. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |

Fixed upstream values (not configurable): exchange `bitget`, market type `spot`, interval `1d`, limit `1000` bars/request. The effective start/end window is clamped to a maximum of 90 days.

**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Bar timestamp (UTC), from the kline `ts`. |
| `open` | `number / null` | Open price. |
| `high` | `number / null` | High price. |
| `low` | `number / null` | Low price. |
| `close` | `number / null` | Close price. |
| `volume` | `number / null` | Trading volume. |
| `vwap` | `null` | Not returned by this provider; always `null`. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed; A Security identifier (Ticker, FIGI, ISIN, CUSIP, Intrinio ID). |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `interval` | `no` | `string | integer` | `daily` | Data granularity: daily, weekly, or monthly.; Time interval of the data to return.; Time interval of the data to return. The most recent trading day is not including in daily historical data. Intraday data is only available for the most recent trading day at 1 minute intervals.; Time interval of the data to return. Or, any integer (entered as a string) representing the number of minutes. Default is daily data. There is no extended hours data, and intraday data is limited to after April 12 2022.; enum: 1m, 5m, 15m, 1h, 1d (provider: massive) |
| `market` | `no` | `string` | `a_share` | enum: a_share, hk Market selection. 'a_share' for mainland China A-shares, 'hk' for Hong Kong stocks. |
| `adjust` | `no` | `string` | `qfq` | enum: , qfq, hfq Price adjustment method. '' for unadjusted, 'qfq' for forward-adjusted, 'hfq' for backward-adjusted. |
| `adjustment` | `no` | `string` | `splits_only` | The adjustment factor to apply. 'splits_only' is not supported for intraday data.; Type of adjustment for historical prices. Only applies to daily data.; The adjustment factor to apply. Only valid for daily data.; The adjustment factor to apply. Default is splits only. |
| `extended_hours` | `no` | `boolean` | `false` | Include Pre and Post market data. |
| `use_cache` | `no` | `boolean` | `true` | When True, the company directories will be cached for 24 hours and are used to validate symbols. The results of the function are not cached. Set as False to bypass. |
| `start_clock_time` | `no` | `string | null` | `-` | Return intervals starting at the specified time on the `start_date` formatted as 'HH:MM:SS'. |
| `end_clock_time` | `no` | `string | null` | `-` | Return intervals stopping at the specified time on the `end_date` formatted as 'HH:MM:SS'. |
| `timezone` | `no` | `string | null` | `America/New_York` | Timezone of the data, in the IANA format (Continent/City). |
| `source` | `no` | `string` | `realtime` | enum: realtime, delayed, nasdaq_basic The source of the data. |
| `include_actions` | `no` | `boolean` | `true` | Include dividends and stock splits in results. |
| `limit` | `no` | `integer | null` | `1000` | Maximum aggregate bars per request (1–1000). (provider: massive) |
| `cursor` | `no` | `string | null` | `-` | Pagination cursor from `next_cursor` on the previous response. Must be used with `next_time`. (provider: massive) |
| `next_time` | `no` | `integer | null` | `-` | Millisecond timestamp from `next_time` on the previous response. Required when `cursor` is set. (provider: massive) |
| `sort` | `no` | `string` | `asc` | enum: asc, desc Sort bars by timestamp ascending or descending. (provider: massive) |
| `adjusted` | `no` | `boolean` | `true` | Whether aggregate bars are split-adjusted. (provider: massive) |

#### Response fields (other providers)

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
| `change` | `number` | Change in the price from the previous close. |
| `change_percent` | `number` | Change in the price from the previous close, as a normalized percent. |
| `next_cursor` | `string` | Cursor for the next page. Pass with `next_time` on the next request. (provider: massive) |
| `next_time` | `integer` | Millisecond timestamp for the next page window. (provider: massive) |
| `has_more` | `boolean` | Whether more bars are available beyond this page. (provider: massive) |

---

### `equity.price.performance`

```python
data.equity.price.performance(symbol=...)
```

Summary: Performance

| Field | Value |
|---|---|
| Endpoint ID | `equity.price.performance` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/price/performance` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | The ticker symbol. |
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
| `five_year` | `number` | Five-year return. |
| `ten_year` | `number` | Ten-year return. |
| `max` | `number` | Return from the beginning of the time series. |
| `volatility_week` | `number` | One-week realized volatility, as a normalized percent. |
| `volatility_month` | `number` | One-month realized volatility, as a normalized percent. |
| `price` | `number` | Last Price. |
| `volume` | `number` | Current volume. |
| `average_volume` | `number` | Average daily volume. |
| `analyst_recommendation` | `number` | The analyst consensus, on a scale of 1-5 where 1 is a buy and 5 is a sell. |

---

### `equity.price.quote`

```python
data.equity.price.quote(symbol="AAPL", provider="bitget_data")
```

Summary: Quote

| Field | Value |
|---|---|
| Endpoint ID | `equity.price.quote` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/price/quote` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` — this is a separate Bitget-exchange RWA-tokenized equity-spot feed, **not** the THS contract described at the top of this file; use only the **bitget_data provider** query/response tables below and ignore the THS notes and other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single ticker only (no multi-symbol). Internally converted to Bitget's RWA-tokenized spot pair `R<SYMBOL>/USDT` (e.g. `AAPL` -> `RAAPL/USDT`). |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |

Fixed upstream values (not configurable): exchange `bitget`, market type `spot`, quote currency `USDT`, interval `1d`.

**bitget_data** response:

| Field | Type | Notes                                                                                                    |
|---|---|----------------------------------------------------------------------------------------------------------|
| `symbol` | `string` | Ticker, as requested (bare, no `R` prefix).                                                              |
| `last_price` | `number / null` | Latest daily-kline close.                                                                                |
| `open` | `number / null` | Latest session's open price.                                                                             |
| `high` | `number / null` | Latest session's high price.                                                                             |
| `low` | `number / null` | Latest session's low price.                                                                              |
| `close` | `number / null` | Same value as `last_price`.                                                                              |
| `volume` | `number / null` | Latest session's trading volume（RWA）.                                                                  |
| `prev_close` | `number / null` | Previous session's close. `null` if no previous bar is available.                                        |
| `change` | `number / null` | `last_price - prev_close`.                                                                               |
| `change_percent` | `number / null` | `change / prev_close`, normalized.                                                                       |
| `total_shares` | `number / null` | Total shares outstanding, from the low-frequency stock screener index.                                   |
| `float_shares` | `number / null` | Float (freely tradable) shares outstanding, from the stock screener index.                               |
| `total_market_cap` | `number / null` | `total_shares * last_price`, computed in real time.                                                      |
| `float_market_cap` | `number / null` | `float_shares * last_price`, computed in real time.                                                      |
| `pb` | `number / null` | `total_market_cap / total_holders_equity` (latest reported shareholders' equity), computed in real time. |
| `turnover_rate` | `number / null` | `volume / float_shares * 100`, computed in real time.                                                    |
| `amplitude` | `number / null` | `(high - low) / prev_close * 100`, computed in real time.                                                |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed; A Security identifier (Ticker, FIGI, ISIN, CUSIP, Intrinio ID). |
| `market` | `no` | `string` | `a_share` | enum: a_share, hk Market selection. 'a_share' for mainland China A-shares, 'hk' for Hong Kong stocks. |
| `use_cache` | `no` | `boolean` | `true` | When True, the company directories will be cached for 24 hours and are used to validate symbols. The results of the function are not cached. Set as False to bypass. |
| `source` | `no` | `string` | `iex` | enum: iex, bats, bats_delayed, utp_delayed, cta_a_delayed, cta_b_delayed, intrinio_mx, intrinio_mx_plus, delayed_sip Source of the data. |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `asset_type` | `string` | Type of asset - i.e, stock, ETF, etc. |
| `name` | `string` | Name of the company or asset. |
| `exchange` | `string` | The name or symbol of the venue where the data is from. |
| `bid` | `number` | Price of the top bid order. |
| `bid_size` | `integer` | This represents the number of round lot orders at the given price. |
| `ask` | `number` | Price of the top ask order. |
| `ask_size` | `integer` | This represents the number of round lot orders at the given price. |
| `last_price` | `number` | Price of the last trade. |
| `last_size` | `integer` | Size of the last trade. |
| `last_timestamp` | `string` | Date and Time when the last price was recorded. |
| `open` | `number` | The open price. |
| `high` | `number` | The high price. |
| `low` | `number` | The low price. |
| `close` | `number` | The close price. |
| `volume` | `integer` | The trading volume. |
| `prev_close` | `number` | The previous close price. |
| `change` | `number` | Change in price from previous close. |
| `change_percent` | `number` | Change in price as a normalized percentage. |
| `year_high` | `number` | The one year high (52W High). |
| `year_low` | `number` | The one year low (52W Low). |
| `updated_on` | `string` | Date and Time when the data was last updated. |

---

### `equity.profile`

```python
data.equity.profile(symbol="AAPL", provider="bitget_data")
```

Summary: Profile

| Field | Value |
|---|---|
| Endpoint ID | `equity.profile` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/profile` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Supports `provider="bitget_data"` (THS). Use only the **bitget_data provider** query/response tables; ignore other-provider params/fields. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker. Required for THS. |
| `provider` | `yes` | `string` | `-` | Must be `bitget_data`. |


**bitget_data** response:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | From `sec_code`. |
| `name` | `string / null` | From `org_short_name_en` (falls back to `org_name_en`). |
| `legal_name` | `string / null` | From `org_name_en`. |
| `cusip` | `string / null` | CUSIP. |
| `isin` | `string / null` | ISIN. |
| `stock_exchange` | `string / null` | From `td_mkt`. |
| `short_description` | `string / null` | From `main_operation_business`. |
| `long_description` | `string / null` | From `org_cn_introduction`. |
| `ceo` | `string / null` | From `general_manager`. |
| `inc_country` | `string / null` | From `reg_region`. |
| `employees` | `number / null` | From `staff_num`. |
| `entity_legal_form` | `string / null` | From `corp_nature`. |
| `entity_status` | `string / null` | From `listed_status`. |
| `industry_category` | `string / null` | From `industry_name`. |
| `standardized_active` | `boolean / null` | From `is_listing`. |
| `first_stock_price_date` | `string / null` | From `listed_date`. |
| `currency_code` | `string / null` | Currency. |
| `reg_region` | `string / null` | Registered region, raw THS field. |
| `org_type` | `string / null` | Organization type. |
| `industry_name` | `string / null` | Industry name, raw THS field. |
| `listed_board_name` | `string / null` | Listing board name. |
| `development_history` | `string / null` | Company development history. |

---


#### Query parameters (other providers)

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |

#### Response fields (other providers)

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Common name of the company. |
| `cik` | `string` | Central Index Key (CIK) for the requested entity. |
| `isin` | `string` | International Securities Identification Number. |
| `lei` | `string` | Legal Entity Identifier assigned to the company. |
| `stock_exchange` | `string` | Stock exchange where the company is traded. |
| `sic` | `integer` | Standard Industrial Classification code for the company. |
| `short_description` | `string` | Short description of the company. |
| `long_description` | `string` | Long description of the company. |
| `ceo` | `string` | Chief Executive Officer of the company. |
| `company_url` | `string` | URL of the company's website. |
| `hq_address_city` | `string` | City of the company's headquarters. |
| `hq_country` | `string` | Country of the company's headquarters. |
| `employees` | `integer` | Number of employees working for the company. |
| `sector` | `string` | Sector in which the company operates. |
| `industry_category` | `string` | Category of industry in which the company operates. |
| `industry_group` | `string` | Group of industry in which the company operates. |
| `is_etf` | `boolean` | If the symbol is an ETF. |
| `is_actively_trading` | `boolean` | If the company is actively trading. |
| `currency` | `string` | Currency in which the stock is traded. |
| `market_cap` | `integer` | Market capitalization of the company. |
| `last_price` | `number` | The last traded price. |
| `year_high` | `number` | The one-year high of the price. |
| `year_low` | `number` | The one-year low of the price. |
| `volume_avg` | `integer` | Average daily trading volume. |
| `annualized_dividend_amount` | `number` | The annualized dividend payment based on the most recent regular dividend payment. |
| `beta` | `number` | Beta of the stock relative to the market. |
| `shares_outstanding` | `integer` | The number of listed shares outstanding. |

---

### `equity.screener`

```python
data.equity.screener(metric='overview', exchange='all', index='all', sector='all', industry='all', mktcap='all', recommendation='all', signal=None, preset=None, limit=None, mktcap_min=None, mktcap_max=None, price_min=None, price_max=None, beta_min=None, beta_max=None, volume_min=None, volume_max=None, dividend_min=None, dividend_max=None, country=None, is_etf=None, is_active=None, is_fund=None, all_share_classes=None, exsubcategory='all', region='all', body=...)
```

Summary: Screener

| Field | Value |
|---|---|
| Endpoint ID | `equity.screener` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/screener` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `metric` | `no` | `string` | `overview` | enum: overview, valuation, financial, ownership, performance, technical The data group to return, default is 'overview'. |
| `exchange` | `no` | `string | null` | `all` | Filter by exchange. |
| `index` | `no` | `string` | `all` | enum: all, dow, nasdaq, sp500, russell Filter by index. |
| `sector` | `no` | `string | null` | `all` | Filter by sector. |
| `industry` | `no` | `string | null` | `all` | Filter by industry. |
| `mktcap` | `no` | `string` | `all` | Filter by market cap. Mega - > 200B Large - 10B - 200B Mid - 2B - 10B Small - 300M - 2B Micro - 50M - 300M Nano - < 50M |
| `recommendation` | `no` | `string` | `all` | Filter by analyst recommendation.; Filter by consensus analyst action. Multiple comma separated items allowed. |
| `signal` | `no` | `string | null` | `-` | The Finviz screener signal to use. When no parameters are provided, the screener defaults to 'top_gainers'. Available signals are: channel: both support and resistance trendlines are horizontal channel_down: both support and resistance trendlines slope downward channel_up: both support and resistance trendlines slope upward double_bottom: stock with 'W' shape that indicates a bullish reversal in trend double_top: stock with 'M' shape that indicates a bearish reversal in trend downgrades: stocks downgraded by analysts today earnings_after: companies reporting earnings today, after market close earnings_before: companies reporting earnings today, before market open head_shoulders: chart formation that predicts a bullish-to-bearish trend reversal head_shoulders_inverse: chart formation that predicts a bearish-to-bullish trend reversal horizontal_sr: horizontal channel of price range between support and resistance trendlines major_news: stocks with the highest news coverage today most_active: stocks with the highest trading volume today most_volatile: stocks with the highest widest high/low trading range today multiple_bottom: same as double_bottom hitting more lows multiple_top: same as double_top hitting more highs new_high: stocks making 52-week high today new_low: stocks making 52-week low today overbought: stock is becoming overvalued and may experience a pullback. oversold: oversold stocks may represent a buying opportunity for investors recent_insider_buying: stocks with recent insider buying activity recent_insider_selling: stocks with recent insider selling activity tl_resistance: once a rising trendline is broken tl_support: once a falling trendline is broken top_gainers: stocks with the highest price gain percent today top_losers: stocks with the highest price percent loss today triangle_ascending: upward trendline support and horizontal trendline resistance triangle_descending: horizontal trendline support and downward trendline resistance unusual_volume: stocks with unusually high volume today - the highest relative volume ratio upgrades: stocks upgraded by analysts today wedge: upward trendline support, downward trendline resistance (continuation) wedge_down: downward trendline support and downward trendline resistance (reversal) wedge_up: upward trendline support and upward trendline resistance (reversal) |
| `preset` | `no` | `string | null` | `-` | A configured preset file to use for the query. This overrides all other query parameters except 'metric', and 'limit'. Presets (.ini text files) can be created and modified in the '~/OpenBBUserData/finviz/presets' directory. If the path does not exist, it will be created and populated with the default presets on the first run. Refer to the file, 'screener_template.ini', for the format and options. Note: Syntax of parameters in preset files must follow the template file exactly - i.e, Analyst Recom. = Strong Buy (1) |
| `limit` | `no` | `integer | null` | `-` | The number of data entries to return.; Limit the number of results to return.; Limit the number of results returned. Default is, 200. Set to, 0, for all results. |
| `mktcap_min` | `no` | `integer | null` | `-` | Filter by market cap greater than this value. |
| `mktcap_max` | `no` | `integer | null` | `-` | Filter by market cap less than this value. |
| `price_min` | `no` | `number | null` | `-` | Filter by price greater than this value. |
| `price_max` | `no` | `number | null` | `-` | Filter by price less than this value. |
| `beta_min` | `no` | `number | null` | `-` | Filter by a beta greater than this value. |
| `beta_max` | `no` | `number | null` | `-` | Filter by a beta less than this value. |
| `volume_min` | `no` | `integer | null` | `-` | Filter by volume greater than this value. |
| `volume_max` | `no` | `integer | null` | `-` | Filter by volume less than this value. |
| `dividend_min` | `no` | `number | null` | `-` | Filter by dividend amount greater than this value. |
| `dividend_max` | `no` | `number | null` | `-` | Filter by dividend amount less than this value. |
| `country` | `no` | `string | null` | `-` | Filter by country. Accepts ISO 3166-1 alpha-2 codes (e.g., 'US', 'DE'), alpha-3 codes (e.g., 'USA'), or country names (e.g., 'United States', 'united_states'). |
| `is_etf` | `no` | `boolean | null` | `-` | If true, includes ETFs. |
| `is_active` | `no` | `boolean | null` | `-` | If false, returns only inactive tickers. |
| `is_fund` | `no` | `boolean | null` | `-` | If true, includes funds. |
| `all_share_classes` | `no` | `boolean | null` | `-` | If true, includes all share classes of a equity. |
| `exsubcategory` | `no` | `string` | `all` | Filter by exchange subcategory. - NGS - Nasdaq Global Select Market - NGM - Nasdaq Global Market - NCM - Nasdaq Capital Market - ADR - American Depository Receipt Multiple comma separated items allowed. |
| `region` | `no` | `string` | `all` | Filter by region. Multiple comma separated items allowed. |
| `body` | `no` | `object | string | null` | `-` | A formatted dictionary, or serialized JSON string, of additional filters to apply to the query. This parameter can be used as an alternative to preset files, and is ignored when a preset is supplied. Invalid entries will raise an error. Syntax should follow the 'screener_template.ini' file. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the company. |
| `last_price` | `number` | Last sale price. |
| `change` | `number` | 1-day change in price. |
| `change_percent` | `number` | 1-day percent change in price. |
| `market_cap` | `integer` | Market cap. |
| `earnings_date` | `string` | Earnings date. |
| `country` | `string` | Country of the company. |
| `sector` | `string` | Sector of the company. |
| `industry` | `string` | Industry of the company. |
| `beta` | `number` | Beta of the stock. |
| `analyst_recommendation` | `number` | Analyst's mean recommendation. (1=Buy 5=Sell). |
| `volume` | `integer` | The trading volume. |
| `volume_avg` | `integer` | 3-month average daily volume. |
| `price_change_1w` | `number` | One-week price return. |
| `price_change_1m` | `number` | One-month price return. |
| `price_change_1y` | `number` | One-year price return. |
| `dividend_yield` | `number` | Annualized dividend yield. |
| `return_on_assets` | `number` | Return on assets. |
| `return_on_equity` | `number` | Return on equity. |
| `gross_margin` | `number` | Gross margin. |
| `operating_margin` | `number` | Operating margin. |
| `profit_margin` | `number` | Profit margin. |
| `price_to_earnings` | `number` | Price to earnings ratio. |
| `price_to_book` | `number` | Price to book ratio. |
| `exchange` | `string` | The exchange code the asset trades on. |
| `is_etf` | `boolean` | Whether the ticker is an ETF. |

---

### `equity.search`

```python
data.equity.search(query='', is_symbol=False, use_cache=True, active=True, limit=1000, is_etf=False, is_fund=False)
```

Summary: Search

| Field | Value |
|---|---|
| Endpoint ID | `equity.search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string` | `` | Search query. |
| `is_symbol` | `no` | `boolean` | `false` | Whether to search by ticker symbol.; Whether the query is a symbol. Defaults to False. |
| `use_cache` | `no` | `boolean` | `true` | Whether to use the cache or not.; Whether to use a cached request. The list of companies is cached for two days. |
| `active` | `no` | `boolean` | `true` | When true, return companies that are actively traded (having stock prices within the past 14 days). When false, return companies that are not actively traded or never have been traded. |
| `limit` | `no` | `integer | null` | `1000` | The number of data entries to return. Max 1000. |
| `is_etf` | `no` | `boolean` | `false` | If True, returns only ETFs. |
| `is_fund` | `no` | `boolean` | `false` | Whether to direct the search to the list of mutual funds and ETFs. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the company. |
| `dpm_name` | `string` | Name of the primary market maker. |
| `post_station` | `string` | Post and station location on the CBOE trading floor. |
| `nasdaq_traded` | `string` | Is Nasdaq traded? |
| `exchange` | `string` | Primary Exchange. |
| `market_category` | `string` | Market Category. |
| `etf` | `string` | Is ETF? |
| `round_lot_size` | `number` | Round Lot Size. |
| `financial_status` | `string` | Financial Status. |
| `cik` | `string` | Central Index Key. |
| `lei` | `string` | The Legal Entity Identifier (LEI) of the company. |
| `intrinio_id` | `string` | The Intrinio ID of the company. |
| `security_type` | `string` | Type of security. |

---

### `equity.shorts.fails_to_deliver`

```python
data.equity.shorts.fails_to_deliver(symbol=..., limit=24, skip_reports=0, use_cache=True)
```

Summary: Fails To Deliver

| Field | Value |
|---|---|
| Endpoint ID | `equity.shorts.fails_to_deliver` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/shorts/fails_to_deliver` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer | null` | `24` | Limit the number of reports to parse, from most recent. Approximately 24 reports per year, going back to 2009. Max 240. |
| `skip_reports` | `no` | `integer | null` | `0` | Skip N number of reports from current. A value of 1 will skip the most recent report. |
| `use_cache` | `no` | `boolean | null` | `true` | Whether or not to use cache for the request, default is True. Each reporting period is a separate URL, new reports will be added to the cache. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `settlement_date` | `string` | The settlement date of the fail. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `cusip` | `string` | CUSIP of the Security. |
| `quantity` | `integer` | The number of fails on that settlement date. |
| `price` | `number` | The price at the previous closing price from the settlement date. |
| `description` | `string` | The description of the Security. |

---

### `equity.shorts.short_interest`

```python
data.equity.shorts.short_interest(symbol=...)
```

Summary: Short Interest

| Field | Value |
|---|---|
| Endpoint ID | `equity.shorts.short_interest` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/shorts/short_interest` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `settlement_date` | `string` | The settlement date of the short interest report. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `issue_name` | `string` | Unique identifier of the issue. |
| `market_class` | `string` | Primary listing market. |
| `current_short_position` | `number` | The total number of shares in the issue reported as short as of the current cycle's designated settlement date. |
| `previous_short_position` | `number` | The total number of shares in the issue reported as short as of the previous cycle's designated settlement date. |
| `avg_daily_volume` | `number` | Average daily volume. |
| `days_to_cover` | `number` | The number of days of average share volume it would require to buy all of the shares that were sold short. |
| `change` | `number` | Change in Shares Short from Previous Cycle. |
| `change_pct` | `number` | Change in Shares Short from Previous Cycle as a percent. |

## Additional `bitget_data` endpoint reference

These six endpoints exist only on `provider="bitget_data"`. They are listed
in the Contents above; the sections live here because they have no
other-provider table.

### `equity.fundamental.metrics_evaluation`

```python
data.equity.fundamental.metrics_evaluation(symbol=..., provider="bitget_data")
```

Summary: THS financial-statement values used as equity valuation inputs.

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.metrics_evaluation` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/metrics_evaluation` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | US symbols only. Extra THS columns are preserved. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker; normalized to uppercase. |
| `report_type` | `no` | `string / null` | `-` | THS report type listed in the provider section above. |
| `statement_year` | `no` | `integer / null` | `-` | Fiscal year, for example `2024`. |
| `start_date` | `no` | `date / null` | `-` | Inclusive start date. |
| `end_date` | `no` | `date / null` | `-` | Inclusive end date. |
| `page` | `no` | `integer` | `1` | 1-based page number; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `no` | `string` | `bitget_data` | THS-backed provider. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | US ticker. |
| `ed` | `date / null` | Report period end date. |
| `statement_year` | `integer / null` | Fiscal year. |
| `report_type` | `string / null` | Report type. |
| `total_holders_equity` | `number / null` | Equity attributable to shareholders. |
| `net_income_atcss` | `number / null` | Net income attributable to common shareholders. |
| `revenue` | `number / null` | Revenue. |
| `net_cash_provided_by_oa` | `number / null` | Operating cash flow. |

---

### `equity.fundamental.metrics_per_share`

```python
data.equity.fundamental.metrics_per_share(symbol=..., provider="bitget_data")
```

Summary: THS per-share financial metrics.

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.metrics_per_share` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/metrics_per_share` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | US symbols only. Extra THS columns are preserved. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker; normalized to uppercase. |
| `report_type` | `no` | `string / null` | `-` | THS report type listed in the provider section above. |
| `report_annual` | `no` | `integer / null` | `-` | Report year, for example `2024`. |
| `start_date` | `no` | `date / null` | `-` | Inclusive start date. |
| `end_date` | `no` | `date / null` | `-` | Inclusive end date. |
| `page` | `no` | `integer` | `1` | 1-based page number; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `no` | `string` | `bitget_data` | THS-backed provider. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | US ticker. |
| `ed` | `date / null` | Report period end date. |
| `report_annual` | `integer / null` | Report year. |
| `report_type` | `string / null` | Report type. |
| `currency_code` | `string / null` | Reporting currency. |
| `basic_eps` | `number / null` | Basic EPS. |
| `eps_dlt` | `number / null` | Diluted EPS. |
| `nav_ps` | `number / null` | Book value per share. |
| `revenue_ps` | `number / null` | Revenue per share. |
| `ncf_from_oa_ps` | `number / null` | Operating cash flow per share. |

---

### `equity.fundamental.metrics_performance`

```python
data.equity.fundamental.metrics_performance(symbol=..., provider="bitget_data")
```

Summary: THS profitability, operating-efficiency, and growth metrics.

| Field | Value |
|---|---|
| Endpoint ID | `equity.fundamental.metrics_performance` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fundamental/metrics_performance` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | US symbols only. Extra THS columns are preserved. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker; normalized to uppercase. |
| `report_type` | `no` | `string / null` | `-` | THS report type listed in the provider section above. |
| `report_annual` | `no` | `integer / null` | `-` | Report year, for example `2024`. |
| `start_date` | `no` | `date / null` | `-` | Inclusive start date. |
| `end_date` | `no` | `date / null` | `-` | Inclusive end date. |
| `page` | `no` | `integer` | `1` | 1-based page number; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `no` | `string` | `bitget_data` | THS-backed provider. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | US ticker. |
| `ed` | `date / null` | Report period end date. |
| `report_annual` | `integer / null` | Report year. |
| `report_type` | `string / null` | Report type. |
| `roe_avg` | `number / null` | Average ROE (%). |
| `roa` | `number / null` | ROA (%). |
| `operating_cycle` | `number / null` | Operating cycle. |
| `inventory_turnover` | `number / null` | Inventory turnover. |
| `account_receivable_turnover` | `number / null` | Accounts-receivable turnover. |
| `total_capital_turnover` | `number / null` | Total-asset turnover. |
| `total_revenue_growth_yoy` | `number / null` | Total revenue growth YoY (%). |
| `yoy_net_profit` | `number / null` | Net-income growth YoY (%). |
| `yoy_basic_eps` | `number / null` | Basic-EPS growth YoY (%). |
| `equity_multiplier_dupont` | `number / null` | DuPont equity multiplier. |

---

### `equity.ownership.inst_position_detail`

```python
data.equity.ownership.inst_position_detail(symbol=..., provider="bitget_data")
```

Summary: THS per-institution holdings and period changes for a US stock.

| Field | Value |
|---|---|
| Endpoint ID | `equity.ownership.inst_position_detail` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/ownership/inst_position_detail` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | US symbols only. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker; normalized to uppercase. |
| `start_date` | `no` | `date / null` | `-` | Inclusive start date. |
| `end_date` | `no` | `date / null` | `-` | Inclusive end date. |
| `page` | `no` | `integer` | `1` | 1-based page number; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `no` | `string` | `bitget_data` | THS-backed provider. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | US ticker. |
| `ed` | `date / null` | Position as-of date. |
| `org_holder` | `string / null` | Institution name. |
| `held_num` | `number / null` | Shares held. |
| `held_changed_num` | `number / null` | Change in shares held. |
| `chg_ratio` | `number / null` | Change ratio. |
| `announcement_date` | `date / string / null` | Announcement date. |

---

### `equity.ownership.inst_position_summary`

```python
data.equity.ownership.inst_position_summary(symbol=..., provider="bitget_data")
```

Summary: THS aggregate institutional-position summary for a US stock.

| Field | Value |
|---|---|
| Endpoint ID | `equity.ownership.inst_position_summary` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/ownership/inst_position_summary` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | US symbols only. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker; normalized to uppercase. |
| `start_date` | `no` | `date / null` | `-` | Inclusive start date. |
| `end_date` | `no` | `date / null` | `-` | Inclusive end date. |
| `page` | `no` | `integer` | `1` | 1-based page number; max `500`. |
| `limit` | `no` | `integer` | `100` | Page size; max `500`. |
| `provider` | `no` | `string` | `bitget_data` | THS-backed provider. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string / null` | US ticker. |
| `chg_date` | `date / null` | Position-summary date. |
| `holder_num` | `number / null` | Number of institutional holders. |
| `holding_total_vol` | `number / null` | Total shares held. |
| `holding_total_value` | `number / null` | Total holding value. |
| `net_trade_vol` | `number / null` | Net traded shares. |

---

### `equity.fund_flow.etf`

```python
data.equity.fund_flow.etf(symbol=..., provider="bitget_data")
```

Summary: A US stock's aggregate inflow and outflow across ETF holdings.

| Field | Value |
|---|---|
| Endpoint ID | `equity.fund_flow.etf` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/equity/fund_flow/etf` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Returns the latest 30 days when no date range is supplied. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Single US ticker; normalized to uppercase. |
| `start_date` | `no` | `date / null` | `-` | Inclusive start date. |
| `end_date` | `no` | `date / null` | `-` | Inclusive end date. |
| `provider` | `no` | `string` | `bitget_data` | THS-backed provider. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `date` | Flow date. |
| `stock_code` | `string` | Stock symbol held by ETFs. |
| `stock_name` | `string / null` | Stock name. |
| `etf_count` | `integer / null` | Number of ETFs holding the stock. |
| `etf_inflow_value` | `number / null` | Value of ETF position increases. |
| `etf_outflow_value` | `number / null` | Value of ETF position decreases. |
| `etf_inflow_count` | `number / null` | Shares added by ETFs. |
| `etf_outflow_count` | `number / null` | Shares removed by ETFs. |
| `etf_net_flow_value` | `number / null` | Net ETF flow value. |
