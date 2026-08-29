# Economy Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`economy.available_indicators`](#economyavailable-indicators)
- [`economy.balance_of_payments`](#economybalance-of-payments)
- [`economy.calendar`](#economycalendar)
- [`economy.central_bank_holdings`](#economycentral-bank-holdings)
- [`economy.composite_leading_indicator`](#economycomposite-leading-indicator)
- [`economy.country_profile`](#economycountry-profile)
- [`economy.cpi`](#economycpi)
- [`economy.direction_of_trade`](#economydirection-of-trade)
- [`economy.export_destinations`](#economyexport-destinations)
- [`economy.fomc_documents`](#economyfomc-documents)
- [`economy.fred_regional`](#economyfred-regional)
- [`economy.fred_release_table`](#economyfred-release-table)
- [`economy.fred_search`](#economyfred-search)
- [`economy.fred_series`](#economyfred-series)
- [`economy.gdp.forecast`](#economygdpforecast)
- [`economy.gdp.nominal`](#economygdpnominal)
- [`economy.gdp.real`](#economygdpreal)
- [`economy.house_price_index`](#economyhouse-price-index)
- [`economy.indicators`](#economyindicators)
- [`economy.interest_rates`](#economyinterest-rates)
- [`economy.money_measures`](#economymoney-measures)
- [`economy.pce`](#economypce)
- [`economy.primary_dealer_fails`](#economyprimary-dealer-fails)
- [`economy.primary_dealer_positioning`](#economyprimary-dealer-positioning)
- [`economy.retail_prices`](#economyretail-prices)
- [`economy.risk_premium`](#economyrisk-premium)
- [`economy.share_price_index`](#economyshare-price-index)
- [`economy.shipping.chokepoint_info`](#economyshippingchokepoint-info)
- [`economy.shipping.chokepoint_volume`](#economyshippingchokepoint-volume)
- [`economy.shipping.port_info`](#economyshippingport-info)
- [`economy.shipping.port_volume`](#economyshippingport-volume)
- [`economy.survey.bls_search`](#economysurveybls-search)
- [`economy.survey.bls_series`](#economysurveybls-series)
- [`economy.survey.economic_conditions_chicago`](#economysurveyeconomic-conditions-chicago)
- [`economy.survey.inflation_expectations`](#economysurveyinflation-expectations)
- [`economy.survey.manufacturing_outlook_ny`](#economysurveymanufacturing-outlook-ny)
- [`economy.survey.manufacturing_outlook_texas`](#economysurveymanufacturing-outlook-texas)
- [`economy.survey.nonfarm_payrolls`](#economysurveynonfarm-payrolls)
- [`economy.survey.sloos`](#economysurveysloos)
- [`economy.survey.university_of_michigan`](#economysurveyuniversity-of-michigan)
- [`economy.total_factor_productivity`](#economytotal-factor-productivity)
- [`economy.unemployment`](#economyunemployment)

## Endpoint reference

### `economy.available_indicators`

```python
data.economy.available_indicators(use_cache=True, query=None, dataflows=None, keywords=None, symbol=None)
```

Summary: Available Indicators

| Field | Value |
|---|---|
| Endpoint ID | `economy.available_indicators` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/available_indicators` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `use_cache` | `no` | `boolean` | `true` | Whether to use cache or not, by default is True The cache of indicator symbols will persist for one week. |
| `query` | `no` | `string | null` | `-` | The search query string. Multiple search phrases can be separated by semicolons. Each phrase can use AND (+) and OR (| ) operators, as well as quoted phrases. Semicolon separation allows commas to be used within search phrases. Multiple comma separated items allowed. |
| `dataflows` | `no` | `string | array | null` | `-` | accepts array values List of IMF dataflow IDs to filter the indicators. Use semicolons to separate multiple dataflow IDs. Multiple comma separated items allowed. |
| `keywords` | `no` | `string | array | null` | `-` | accepts array values List of keywords to filter results. Each keyword is a single word that must appear in the indicator's label or description. Keywords prefixed with 'not' will exclude indicators containing that word (e.g., 'not USD' excludes indicators with 'USD' in them). Multiple comma separated items allowed. |
| `symbol` | `no` | `string | null` | `-` | Dummy field to allow grouping by symbol. Multiple comma separated items allowed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol_root` | `string` | The root symbol representing the indicator. |
| `symbol` | `string` | Symbol representing the entity requested in the data. The root symbol with additional codes. |
| `country` | `string` | The name of the country, region, or entity represented by the symbol. |
| `iso` | `string` | The ISO code of the country, region, or entity represented by the symbol. |
| `description` | `string` | The description of the indicator. |
| `frequency` | `string` | The frequency of the indicator data. |
| `currency` | `string` | The currency, or unit, the data is based in. |
| `scale` | `string` | The scale of the data. |
| `multiplier` | `integer` | The multiplier of the data to arrive at whole units. |
| `transformation` | `string` | Transformation type. |
| `source` | `string` | The original source of the data. |
| `first_date` | `string` | The first date of the data. |
| `last_date` | `string` | The last date of the data. |
| `last_insert_timestamp` | `string` | The time of the last update. Data is typically reported with a lag. |
| `agency_id` | `string` | The agency ID responsible for the indicator. |
| `dataflow_id` | `string` | The IMF dataflow ID associated with the indicator. |
| `dataflow_name` | `string` | The name of the IMF dataflow (symbol root). |
| `structure_id` | `string` | The data structure ID associated with the indicator. |
| `dimension_id` | `string` | The dimension ID of the indicator in the data structure. |
| `long_description` | `string` | Detailed description of the indicator. |
| `member_of` | `array` | List of table symbols (dataflow_id::table_id) this indicator belongs to. |

---

### `economy.balance_of_payments`

```python
data.economy.balance_of_payments(start_time=None, end_time=None, report_type='main', frequency='monthly', country=None)
```

Summary: Balance Of Payments

| Field | Value |
|---|---|
| Endpoint ID | `economy.balance_of_payments` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/balance_of_payments` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `report_type` | `no` | `string` | `main` | enum: main, summary, services, investment_income, direct_investment, portfolio_investment, other_investment The report type, the level of detail in the data. |
| `frequency` | `no` | `string` | `monthly` | enum: monthly, quarterly The frequency of the data. Monthly is valid only for ['main', 'summary']. |
| `country` | `no` | `string` | `-` | The country/region of the data. This parameter will override the 'report_type' parameter.; The country to get data. Enter as a 3-letter ISO country code, default is USA. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `period` | `string` | The date representing the beginning of the reporting period. |
| `balance_percent_of_gdp` | `number` | Current Account Balance as Percent of GDP |
| `balance_total` | `number` | Current Account Total Balance (USD) |
| `balance_total_services` | `number` | Current Account Total Services Balance (USD) |
| `balance_total_secondary_income` | `number` | Current Account Total Secondary Income Balance (USD) |
| `balance_total_goods` | `number` | Current Account Total Goods Balance (USD) |
| `balance_total_primary_income` | `number` | Current Account Total Primary Income Balance (USD) |
| `credits_services_percent_of_goods_and_services` | `number` | Current Account Credits Services as Percent of Goods and Services |
| `credits_services_percent_of_current_account` | `number` | Current Account Credits Services as Percent of Current Account |
| `credits_total_services` | `number` | Current Account Credits Total Services (USD) |
| `credits_total_goods` | `number` | Current Account Credits Total Goods (USD) |
| `credits_total_primary_income` | `number` | Current Account Credits Total Primary Income (USD) |
| `credits_total_secondary_income` | `number` | Current Account Credits Total Secondary Income (USD) |
| `credits_total` | `number` | Current Account Credits Total (USD) |
| `debits_services_percent_of_goods_and_services` | `number` | Current Account Debits Services as Percent of Goods and Services |
| `debits_services_percent_of_current_account` | `number` | Current Account Debits Services as Percent of Current Account |
| `debits_total_services` | `number` | Current Account Debits Total Services (USD) |
| `debits_total_goods` | `number` | Current Account Debits Total Goods (USD) |
| `debits_total_primary_income` | `number` | Current Account Debits Total Primary Income (USD) |
| `debits_total` | `number` | Current Account Debits Total (USD) |
| `debits_total_secondary_income` | `number` | Current Account Debits Total Secondary Income (USD) |
| `current_account_balance` | `number` | Current Account Balance (Billions of EUR) |
| `current_account_credit` | `number` | Current Account Credit (Billions of EUR) |
| `current_account_debit` | `number` | Current Account Debit (Billions of EUR) |
| `goods_balance` | `number` | Goods Balance (Billions of EUR) |
| `goods_credit` | `number` | Goods Credit (Billions of EUR) |
| `goods_debit` | `number` | Goods Debit (Billions of EUR) |
| `services_balance` | `number` | Services Balance (Billions of EUR) |
| `services_credit` | `number` | Services Credit (Billions of EUR) |
| `services_debit` | `number` | Services Debit (Billions of EUR) |
| `primary_income_balance` | `number` | Primary Income Balance (Billions of EUR) |
| `primary_income_credit` | `number` | Primary Income Credit (Billions of EUR) |
| `primary_income_debit` | `number` | Primary Income Debit (Billions of EUR) |
| `investment_income_balance` | `number` | Investment Income Balance (Billions of EUR) |
| `investment_income_credit` | `number` | Investment Income Credits (Billions of EUR) |
| `investment_income_debit` | `number` | Investment Income Debits (Billions of EUR) |
| `secondary_income_balance` | `number` | Secondary Income Balance (Billions of EUR) |
| `secondary_income_credit` | `number` | Secondary Income Credit (Billions of EUR) |
| `secondary_income_debit` | `number` | Secondary Income Debit (Billions of EUR) |
| `capital_account_balance` | `number` | Capital Account Balance (Billions of EUR) |
| `capital_account_credit` | `number` | Capital Account Credit (Billions of EUR) |
| `capital_account_debit` | `number` | Capital Account Debit (Billions of EUR) |
| `assets_total` | `number` | Assets Total (Billions of EUR) |
| `assets_currency_and_deposits` | `number` | Assets Currency and Deposits (Billions of EUR) |
| `assets_loans` | `number` | Assets Loans (Billions of EUR) |
| `assets_trade_credit_and_advances` | `number` | Assets Trade Credits and Advances (Billions of EUR) |
| `assets_eurosystem` | `number` | Assets Eurosystem (Billions of EUR) |
| `assets_other_mfi_ex_eurosystem` | `number` | Assets Other MFIs outside Eurosystem (Billions of EUR) |
| `assets_government` | `number` | Assets Government (Billions of EUR) |
| `assets_other_sectors` | `number` | Assets Other Sectors (Billions of EUR) |
| `liabilities_total` | `number` | Liabilities Total (Billions of EUR) |
| `liabilities_currency_and_deposits` | `number` | Liabilities Currency and Deposits (Billions of EUR) |
| `liabilities_loans` | `number` | Liabilities Loans (Billions of EUR) |
| `liabilities_trade_credit_and_advances` | `number` | Liabilities Trade Credits and Advances (Billions of EUR) |
| `liabilities_eurosystem` | `number` | Liabilities Eurosystem (Billions of EUR) |
| `liabilities_other_mfi_ex_eurosystem` | `number` | Liabilities Other MFIs outside Eurosystem (Billions of EUR) |
| `liabilities_government` | `number` | Liabilities Government (Billions of EUR) |
| `liabilities_other_sectors` | `number` | Liabilities Other Sectors (Billions of EUR) |
| `assets_equity_and_fund_shares` | `number` | Assets Equity and Investment Fund Shares (Billions of EUR) |
| `assets_equity_shares` | `number` | Assets Equity Shares (Billions of EUR) |
| `assets_investment_fund_shares` | `number` | Assets Investment Fund Shares (Billions of EUR) |
| `assets_debt_short_term` | `number` | Assets Debt Short Term (Billions of EUR) |
| `assets_debt_long_term` | `number` | Assets Debt Long Term (Billions of EUR) |
| `assets_resident_sector_eurosystem` | `number` | Assets Resident Sector Eurosystem (Billions of EUR) |
| `assets_resident_sector_mfi_ex_eurosystem` | `number` | Assets Resident Sector MFIs outside Eurosystem (Billions of EUR) |
| `assets_resident_sector_government` | `number` | Assets Resident Sector Government (Billions of EUR) |
| `assets_resident_sector_other` | `number` | Assets Resident Sector Other (Billions of EUR) |
| `liabilities_equity_and_fund_shares` | `number` | Liabilities Equity and Investment Fund Shares (Billions of EUR) |
| `liabilities_equity` | `number` | Liabilities Equity (Billions of EUR) |
| `liabilities_investment_fund_shares` | `number` | Liabilities Investment Fund Shares (Billions of EUR) |
| `liabilities_debt_short_term` | `number` | Liabilities Debt Short Term (Billions of EUR) |
| `liabilities_debt_long_term` | `number` | Liabilities Debt Long Term (Billions of EUR) |
| `liabilities_resident_sector_government` | `number` | Liabilities Resident Sector Government (Billions of EUR) |
| `liabilities_resident_sector_other` | `number` | Liabilities Resident Sector Other (Billions of EUR) |
| `assets_equity` | `number` | Assets Equity (Billions of EUR) |
| `assets_debt_instruments` | `number` | Assets Debt Instruments (Billions of EUR) |
| `assets_mfi` | `number` | Assets MFIs (Billions of EUR) |
| `assets_non_mfi` | `number` | Assets Non MFIs (Billions of EUR) |
| `assets_direct_investment_abroad` | `number` | Assets Direct Investment Abroad (Billions of EUR) |
| `liabilities_debt_instruments` | `number` | Liabilities Debt Instruments (Billions of EUR) |
| `liabilities_mfi` | `number` | Liabilities MFIs (Billions of EUR) |
| `liabilities_non_mfi` | `number` | Liabilities Non MFIs (Billions of EUR) |
| `liabilities_direct_investment_euro_area` | `number` | Liabilities Direct Investment in Euro Area (Billions of EUR) |
| `investment_total_credit` | `number` | Investment Total Credit (Billions of EUR) |
| `investment_total_debit` | `number` | Investment Total Debit (Billions of EUR) |
| `equity_credit` | `number` | Equity Credit (Billions of EUR) |
| `equity_reinvested_earnings_credit` | `number` | Equity Reinvested Earnings Credit (Billions of EUR) |
| `equity_debit` | `number` | Equity Debit (Billions of EUR) |
| `equity_reinvested_earnings_debit` | `number` | Equity Reinvested Earnings Debit (Billions of EUR) |
| `debt_instruments_credit` | `number` | Debt Instruments Credit (Billions of EUR) |
| `debt_instruments_debit` | `number` | Debt Instruments Debit (Billions of EUR) |
| `portfolio_investment_equity_credit` | `number` | Portfolio Investment Equity Credit (Billions of EUR) |
| `portfolio_investment_equity_debit` | `number` | Portfolio Investment Equity Debit (Billions of EUR) |
| `portfolio_investment_debt_instruments_credit` | `number` | Portfolio Investment Debt Instruments Credit (Billions of EUR) |
| `portofolio_investment_debt_instruments_debit` | `number` | Portfolio Investment Debt Instruments Debit (Billions of EUR) |
| `other_investment_credit` | `number` | Other Investment Credit (Billions of EUR) |
| `other_investment_debit` | `number` | Other Investment Debit (Billions of EUR) |
| `reserve_assets_credit` | `number` | Reserve Assets Credit (Billions of EUR) |
| `services_total_credit` | `number` | Services Total Credit (Billions of EUR) |
| `services_total_debit` | `number` | Services Total Debit (Billions of EUR) |
| `transport_credit` | `number` | Transport Credit (Billions of EUR) |
| `transport_debit` | `number` | Transport Debit (Billions of EUR) |
| `travel_credit` | `number` | Travel Credit (Billions of EUR) |
| `travel_debit` | `number` | Travel Debit (Billions of EUR) |
| `financial_services_credit` | `number` | Financial Services Credit (Billions of EUR) |
| `financial_services_debit` | `number` | Financial Services Debit (Billions of EUR) |
| `communications_credit` | `number` | Communications Credit (Billions of EUR) |
| `communications_debit` | `number` | Communications Debit (Billions of EUR) |
| `other_business_services_credit` | `number` | Other Business Services Credit (Billions of EUR) |
| `other_business_services_debit` | `number` | Other Business Services Debit (Billions of EUR) |
| `other_services_credit` | `number` | Other Services Credit (Billions of EUR) |
| `other_services_debit` | `number` | Other Services Debit (Billions of EUR) |
| `primary_income_employee_compensation_credit` | `number` | Primary Income Employee Compensation Credit (Billions of EUR) |
| `primary_income_employee_compensation_debit` | `number` | Primary Income Employee Compensation Debit (Billions of EUR) |
| `current_account` | `number` | Current Account Balance (Billions of EUR) |
| `goods` | `number` | Goods Balance (Billions of EUR) |
| `services` | `number` | Services Balance (Billions of EUR) |
| `primary_income` | `number` | Primary Income Balance (Billions of EUR) |
| `secondary_income` | `number` | Secondary Income Balance (Billions of EUR) |
| `capital_account` | `number` | Capital Account Balance (Billions of EUR) |
| `net_lending_to_rest_of_world` | `number` | Balance of net lending to the rest of the world (Billions of EUR) |
| `financial_account` | `number` | Financial Account Balance (Billions of EUR) |
| `direct_investment` | `number` | Direct Investment Balance (Billions of EUR) |
| `portfolio_investment` | `number` | Portfolio Investment Balance (Billions of EUR) |
| `financial_derivatives` | `number` | Financial Derivatives Balance (Billions of EUR) |
| `other_investment` | `number` | Other Investment Balance (Billions of EUR) |
| `reserve_assets` | `number` | Reserve Assets Balance (Billions of EUR) |
| `errors_and_omissions` | `number` | Errors and Omissions (Billions of EUR) |

---

### `economy.calendar`

```python
data.economy.calendar(start_time=None, end_time=None, release_id=None, country=None, importance=None, group=None, calendar_id=None)
```

Summary: Calendar

| Field | Value |
|---|---|
| Endpoint ID | `economy.calendar` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/calendar` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `release_id` | `no` | `integer | null` | `-` | Filter by release ID. |
| `country` | `no` | `string | null` | `-` | Country of the event. Accepts country names, ISO 3166-1 alpha-2/alpha-3 codes. Multiple comma-separated values allowed. Multiple comma separated items allowed.; Country of the event. Multiple comma separated items allowed. |
| `importance` | `no` | `string | null` | `-` | Importance of the event. |
| `group` | `no` | `string | null` | `-` | Grouping of events. |
| `calendar_id` | `no` | `integer | string | null` | `-` | Get events by TradingEconomics Calendar ID. Multiple comma separated items allowed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `country` | `string` | Country of event. |
| `category` | `string` | Category of event. |
| `event` | `string` | Event name. |
| `importance` | `string` | The importance level for the event. |
| `source` | `string` | Source of the data. |
| `currency` | `string` | Currency of the data. |
| `unit` | `string` | Unit of the data. |
| `consensus` | `string` | Average forecast among a representative group of economists. |
| `previous` | `string` | Value for the previous period after the revision (if revision is applicable). |
| `revised` | `string` | Revised previous value, if applicable. |
| `actual` | `string` | Latest released value. |
| `release_id` | `integer` | Release ID associated with the economic event. |
| `description` | `string` | Event description. |
| `change` | `number` | Value change since previous. |
| `change_percent` | `number` | Percentage change since previous. |
| `forecast` | `string` | TradingEconomics projections. |
| `reference` | `string` | Abbreviated period for which released data refers to. |
| `reference_date` | `string` | Date for the reference period. |
| `calendar_id` | `integer` | TradingEconomics Calendar ID. |
| `date_span` | `integer` | Date span of the event. |
| `symbol` | `string` | TradingEconomics Symbol. |
| `ticker` | `string` | TradingEconomics Ticker symbol. |
| `te_url` | `string` | TradingEconomics URL path. |
| `source_url` | `string` | Source URL. |
| `last_updated` | `string` | Last update of the data. |

---

### `economy.central_bank_holdings`

```python
data.economy.central_bank_holdings(date=None, holding_type='all_treasury', summary=False, cusip=None, wam=False, monthly=False)
```

Summary: Central Bank Holdings

| Field | Value |
|---|---|
| Endpoint ID | `economy.central_bank_holdings` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/central_bank_holdings` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `date` | `no` | `string | null` | `-` | A specific date to get data for. |
| `holding_type` | `no` | `string` | `all_treasury` | Type of holdings to return. |
| `summary` | `no` | `boolean` | `false` | If True, returns historical weekly summary by holding type. This parameter takes priority over other parameters. |
| `cusip` | `no` | `string | null` | `-` | Multiple comma separated items allowed. |
| `wam` | `no` | `boolean` | `false` | If True, returns weighted average maturity aggregated by agency or treasury securities. This parameter takes priority over `holding_type`, `cusip`, and `monthly`. |
| `monthly` | `no` | `boolean` | `false` | If True, returns historical data for all Treasury securities at a monthly interval. This parameter takes priority over other parameters, except `wam`. Only valid when `holding_type` is set to: 'all_treasury', 'bills', 'notesbonds', 'frn', 'tips'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `security_type` | `string` | Type of security - i.e. TIPs, FRNs, etc. |
| `description` | `string` | Description of the security. Only returned for Agency securities. |
| `is_aggregated` | `string` | Whether the security is aggregated. Only returned for Agency securities. |
| `cusip` | `string` | cusip |
| `issuer` | `string` | Issuer of the security. |
| `maturity_date` | `string` | Maturity date of the security. |
| `term` | `string` | Term of the security. Only returned for Agency securities. |
| `face_value` | `number` | Current face value of the security (Thousands of $USD). |
| `par_value` | `number` | Par value of the security (Thousands of $USD). |
| `coupon` | `number` | Coupon rate of the security. |
| `spread` | `number` | Spread to the current reference rate, as determined at each security's initial auction. |
| `percent_outstanding` | `number` | Total percent of the outstanding CUSIP issuance. |
| `bills` | `number` | Treasury bills amount (Thousands of $USD). Only returned when 'summary' is True. |
| `frn` | `number` | Floating rate Treasury notes amount (Thousands of $USD). Only returned when 'summary' is True. |
| `notes_and_bonds` | `number` | Treasury Notes and bonds amount (Thousands of $USD). Only returned when 'summary' is True. |
| `tips` | `number` | Treasury inflation-protected securities amount (Thousands of $USD). Only returned when 'summary' is True. |
| `mbs` | `number` | Mortgage-backed securities amount (Thousands of $USD). Only returned when 'summary' is True. |
| `cmbs` | `number` | Commercial mortgage-backed securities amount (Thousands of $USD). Only returned when 'summary' is True. |
| `agencies` | `number` | Agency securities amount (Thousands of $USD). Only returned when 'summary' is True. |
| `total` | `number` | Total SOMA holdings amount (Thousands of $USD). Only returned when 'summary' is True. |
| `inflationCompensation` | `number` | Treasury inflation-protected securities inflation compensation amount (Thousands of $USD). Only returned when 'summary' is True. |
| `change_prior_week` | `number` | Change in SOMA holdings from the prior week (Thousands of $USD). |
| `change_prior_year` | `number` | Change in SOMA holdings from the prior year (Thousands of $USD). |

---

### `economy.composite_leading_indicator`

```python
data.economy.composite_leading_indicator(start_time=None, end_time=None, country='g20', adjustment='amplitude', growth_rate=False)
```

Summary: Composite Leading Indicator

| Field | Value |
|---|---|
| Endpoint ID | `economy.composite_leading_indicator` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/composite_leading_indicator` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `g20` | Country to get the CLI for, default is G20. Multiple comma separated items allowed. |
| `adjustment` | `no` | `string` | `amplitude` | Adjustment of the data, either 'amplitude' or 'normalized'. Default is amplitude. |
| `growth_rate` | `no` | `boolean` | `false` | Return the 1-year growth rate (%) of the CLI, default is False. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `value` | `number` | CLI value |
| `country` | `string` | Country for the CLI value. |

---

### `economy.country_profile`

```python
data.economy.country_profile(country=..., latest=True, use_cache=True)
```

Summary: Country Profile

| Field | Value |
|---|---|
| Endpoint ID | `economy.country_profile` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/country_profile` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `country` | `yes` | `string` | `-` | The country to get data. Multiple comma separated items allowed |
| `latest` | `no` | `boolean` | `true` | If True, return only the latest data. If False, return all available data for each indicator. |
| `use_cache` | `no` | `boolean` | `true` | If True, the request will be cached for one day.Using cache is recommended to avoid needlessly requesting the same data. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `country` | `string` | country |
| `population` | `integer` | Population. |
| `gdp_usd` | `number` | Gross Domestic Product, in billions of USD. |
| `gdp_qoq` | `number` | GDP growth quarter-over-quarter change, as a normalized percent. |
| `gdp_yoy` | `number` | GDP growth year-over-year change, as a normalized percent. |
| `cpi_yoy` | `number` | Consumer Price Index year-over-year change, as a normalized percent. |
| `core_yoy` | `number` | Core Consumer Price Index year-over-year change, as a normalized percent. |
| `retail_sales_yoy` | `number` | Retail Sales year-over-year change, as a normalized percent. |
| `industrial_production_yoy` | `number` | Industrial Production year-over-year change, as a normalized percent. |
| `policy_rate` | `number` | Short term policy rate, as a normalized percent. |
| `yield_10y` | `number` | 10-year government bond yield, as a normalized percent. |
| `govt_debt_gdp` | `number` | Government debt as a percent (normalized) of GDP. |
| `current_account_gdp` | `number` | Current account balance as a percent (normalized) of GDP. |
| `jobless_rate` | `number` | Unemployment rate, as a normalized percent. |

---

### `economy.cpi`

```python
data.economy.cpi(start_time=None, end_time=None, country='united_states', transform='yoy', frequency='monthly', harmonized=False, expenditure='total', limit=None)
```

Summary: Cpi

| Field | Value |
|---|---|
| Endpoint ID | `economy.cpi` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/cpi` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `united_states` | The country to get data. Multiple comma separated items allowed |
| `transform` | `no` | `string` | `yoy` | Transformation of the CPI data. |
| `frequency` | `no` | `string` | `monthly` | enum: annual, quarter, monthly The frequency of the data. |
| `harmonized` | `no` | `boolean` | `false` | If true, returns harmonized data. |
| `expenditure` | `no` | `string` | `total` | Expenditure component of CPI. |
| `limit` | `no` | `integer | null` | `-` | Maximum number of records to retrieve per series and country. If None, retrieves all available records. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `country` | `string` | Country |
| `value` | `number` | CPI index value or period change. |
| `expenditure` | `string` | Expenditure component of CPI. |
| `unit` | `string` | Unit of measurement. |
| `unit_multiplier` | `integer` | Unit multiplier for the observation value. |
| `country_code` | `string` | ISO3 country code. |
| `series_id` | `string` | IMF series identifier. |
| `title` | `string` | Complete reference title for the series. |
| `order` | `integer` | Sort order for expenditure categories and table presentations. |

---

### `economy.direction_of_trade`

```python
data.economy.direction_of_trade(start_time=None, end_time=None, country=None, counterpart=None, direction='balance', frequency='month', limit=None)
```

Summary: Direction Of Trade

| Field | Value |
|---|---|
| Endpoint ID | `economy.direction_of_trade` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/direction_of_trade` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string | null` | `-` | The country to get data. None is an equiavlent to 'all'. If 'all' is used, the counterpart field cannot be 'all'. Multiple comma separated items allowed |
| `counterpart` | `no` | `string | null` | `-` | Counterpart country to the trade. None is an equiavlent to 'all'. If 'all' is used, the country field cannot be 'all'. Multiple comma separated items allowed |
| `direction` | `no` | `string` | `balance` | Trade direction. Use 'all' to get all data for this dimension. |
| `frequency` | `no` | `string` | `month` | The frequency of the data. |
| `limit` | `no` | `integer | null` | `-` | Limit the number of results returned, the most recent data points first. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. Concatenated series identifier. |
| `country` | `string` | The country or region to the trade. |
| `counterpart` | `string` | Counterpart country or region to the trade. |
| `title` | `string` | Title corresponding to the symbol. |
| `value` | `number` | Trade value. |
| `scale` | `string` | Scale of the value. |
| `unit` | `string` | Unit of the value. |
| `country_code` | `string` | IMF country code. |
| `counterpart_code` | `string` | IMF counterpart country code. |
| `unit_multiplier` | `integer` | Unit multiplier of the value. |

---

### `economy.export_destinations`

```python
data.economy.export_destinations(country=...)
```

Summary: Export Destinations

| Field | Value |
|---|---|
| Endpoint ID | `economy.export_destinations` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/export_destinations` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `country` | `yes` | `string` | `-` | The country to get data. Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `origin_country` | `string` | The country of origin. |
| `destination_country` | `string` | The destination country. |
| `value` | `number` | The value of the export. |
| `units` | `string` | The units of measurement for the value. |
| `title` | `string` | The title of the data. |
| `footnote` | `string` | The footnote for the data. |

---

### `economy.fomc_documents`

```python
data.economy.fomc_documents(year=None, document_type=None)
```

Summary: Fomc Documents

| Field | Value |
|---|---|
| Endpoint ID | `economy.fomc_documents` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/fomc_documents` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `year` | `no` | `integer | null` | `-` | The year of FOMC documents to retrieve. If None, all years since 1959 are returned. |
| `document_type` | `no` | `string | null` | `-` | Filter by document type. Default is all. Choose from: all, monetary_policy, minutes, projections, materials, press_release, press_conference, agenda, transcript, speaker_key, beige_book, teal_book, green_book, blue_book, red_book |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the document, formatted as YYYY-MM-DD. |
| `doc_type` | `string` | The type of the FOMC document. |
| `doc_format` | `string` | The format of the document (e.g., pdf, htm). |
| `url` | `string` | The URL of the document. |

---

### `economy.fred_regional`

```python
data.economy.fred_regional(symbol=..., start_time=None, end_time=None, limit=100000, is_series_group=False, region_type=None, season='nsa', units=None, frequency=None, aggregation_method='eop', transform=None)
```

Summary: Fred Regional

| Field | Value |
|---|---|
| Endpoint ID | `economy.fred_regional` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/fred_regional` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for.; For this function, it is the series_group ID or series ID. If the symbol provided is for a series_group, set the `is_series_group` parameter to True. Not all series that are in FRED have geographical data. |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `limit` | `no` | `integer | null` | `100000` | The number of data entries to return. |
| `is_series_group` | `no` | `boolean` | `false` | When True, the symbol provided is for a series_group, else it is for a series ID. |
| `region_type` | `no` | `string | null` | `-` | The type of regional data. Parameter is only valid when `is_series_group` is True. |
| `season` | `no` | `string` | `nsa` | The seasonal adjustments to the data. Parameter is only valid when `is_series_group` is True. |
| `units` | `no` | `string | null` | `-` | The units of the data. This should match the units returned from searching by series ID. An incorrect field will not necessarily return an error. Parameter is only valid when `is_series_group` is True. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert high frequency data to lower frequency. None = No change a = Annual q = Quarterly m = Monthly w = Weekly d = Daily wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `eop` | A key that indicates the aggregation method used for frequency aggregation. This parameter has no affect if the frequency parameter is not set. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `region` | `string` | The name of the region. |
| `code` | `string` | The code of the region. |
| `value` | `integer` | The observation value. The units are defined in the search results by series ID. |
| `series_id` | `string` | The individual series ID for the region. |

---

### `economy.fred_release_table`

```python
data.economy.fred_release_table(release_id=..., element_id=None, date=None)
```

Summary: Fred Release Table

| Field | Value |
|---|---|
| Endpoint ID | `economy.fred_release_table` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/fred_release_table` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `release_id` | `yes` | `string` | `-` | The ID of the release. Use `fred_search` to find releases. |
| `element_id` | `no` | `string | null` | `-` | The element ID of a specific table in the release. |
| `date` | `no` | `string | null` | `-` | A specific date to get data for. Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `level` | `integer` | The indentation level of the element. |
| `element_type` | `string` | The type of the element. |
| `line` | `integer` | The line number of the element. |
| `element_id` | `string` | The element id in the parent/child relationship. |
| `parent_id` | `string` | The parent id in the parent/child relationship. |
| `children` | `string` | The element_id of each child, as a comma-separated string. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | The name of the series. |
| `value` | `number` | The reported value of the series. |

---

### `economy.fred_search`

```python
data.economy.fred_search(query=None, search_type='full_text', release_id=None, limit=None, offset=0, order_by='observation_end', sort_order='desc', filter_variable=None, filter_value=None, tag_names=None, exclude_tag_names=None, series_id=None)
```

Summary: Fred Search

| Field | Value |
|---|---|
| Endpoint ID | `economy.fred_search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/fred_search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string | null` | `-` | The search word(s). |
| `search_type` | `no` | `string` | `full_text` | enum: full_text, series_id, release The type of search to perform. Automatically set to 'release' when a 'release_id' is provided. |
| `release_id` | `no` | `integer | null` | `-` | A specific release ID to target. |
| `limit` | `no` | `integer | null` | `-` | The number of data entries to return. (1-1000) |
| `offset` | `no` | `integer | null` | `0` | Offset the results in conjunction with limit. This parameter is ignored When search_type is 'release'. |
| `order_by` | `no` | `string` | `observation_end` | enum: search_rank, series_id, title, units, frequency, seasonal_adjustment, realtime_start, realtime_end, last_updated, observation_start, observation_end, popularity, group_popularity Order the results by a specific attribute. The default is 'observation_end'. |
| `sort_order` | `no` | `string` | `desc` | Sort the 'order_by' item in ascending or descending order. The default is 'desc'. |
| `filter_variable` | `no` | `string | null` | `-` | Filter by an attribute. |
| `filter_value` | `no` | `string | null` | `-` | String value to filter the variable by. Used in conjunction with filter_variable. This parameter is ignored when search_type is 'release'. |
| `tag_names` | `no` | `string | null` | `-` | A semicolon delimited list of tag names that series match all of. Example: 'japan;imports' This parameter is ignored when search_type is 'release'. Multiple comma separated items allowed. |
| `exclude_tag_names` | `no` | `string | null` | `-` | A semicolon delimited list of tag names that series match none of. Example: 'imports;services'. Requires that variable tag_names also be set to limit the number of matching series. This parameter is ignored when search_type is 'release'. Multiple comma separated items allowed. |
| `series_id` | `no` | `string | null` | `-` | A FRED Series ID to return series group information for. This returns the required information to query for regional data. Not all series that are in FRED have geographical data. Entering a value for series_id will override all other parameters. Multiple series_ids can be separated by commas. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `release_id` | `string` | The release ID for queries. |
| `series_id` | `string` | The series ID for the item in the release. |
| `series_group` | `string` | The series group ID of the series. This value is used to query for regional data. |
| `region_type` | `string` | The region type of the series. |
| `name` | `string` | The name of the release. |
| `title` | `string` | The title of the series. |
| `observation_start` | `string` | The date of the first observation in the series. |
| `observation_end` | `string` | The date of the last observation in the series. |
| `frequency` | `string` | The frequency of the data. |
| `frequency_short` | `string` | Short form of the data frequency. |
| `units` | `string` | The units of the data. |
| `units_short` | `string` | Short form of the data units. |
| `seasonal_adjustment` | `string` | The seasonal adjustment of the data. |
| `seasonal_adjustment_short` | `string` | Short form of the data seasonal adjustment. |
| `last_updated` | `string` | The datetime of the last update to the data. |
| `popularity` | `integer` | Popularity of the series |
| `group_popularity` | `integer` | Group popularity of the release |
| `realtime_start` | `string` | The realtime start date of the series. |
| `realtime_end` | `string` | The realtime end date of the series. |
| `notes` | `string` | Description of the release. |
| `press_release` | `boolean` | If the release is a press release. |
| `url` | `string` | URL to the release. |

---

### `economy.fred_series`

```python
data.economy.fred_series(symbol=..., start_time=None, end_time=None, limit=1000, frequency=None, aggregation_method='eop', transform=None, all_pages=False, sleep=1.0)
```

Summary: Fred Series

| Field | Value |
|---|---|
| Endpoint ID | `economy.fred_series` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/fred_series` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Replacement target for future data.macro.* facade work. Use this for known, documented FRED series IDs only. For generic IG/HY credit-spread strategies, prefer `fixedincome.bond_indices(index_type="oas", ...)`; do not guess CDX or BAML series symbols here. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `limit` | `no` | `integer | null` | `1000` | The number of data entries to return. Max 1000. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert high frequency data to lower frequency. None = No change a = Annual q = Quarterly m = Monthly w = Weekly d = Daily wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `eop` | A key that indicates the aggregation method used for frequency aggregation. This parameter has no affect if the frequency parameter is not set. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |
| `all_pages` | `no` | `boolean | null` | `false` | Returns all pages of data from the API call at once. |
| `sleep` | `no` | `number | null` | `1.0` | Time to sleep between requests to avoid rate limiting. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `value` | `number` | Value of the index. |

---

### `economy.gdp.forecast`

```python
data.economy.gdp.forecast(start_time=None, end_time=None, country='all', frequency='annual', units='volume')
```

Summary: Forecast

| Field | Value |
|---|---|
| Endpoint ID | `economy.gdp.forecast` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/gdp/forecast` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `all` | Country, or countries, to get forward GDP projections for. Default is all. Multiple comma separated items allowed. |
| `frequency` | `no` | `string` | `annual` | Frequency of the data, default is annual. |
| `units` | `no` | `string` | `volume` | Units of the data, default is volume (chain linked volume, 2015). 'current_prices', 'volume', and 'capita' are expressed in USD; 'growth' as a percent; 'deflator' as an index. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `country` | `string` | Country |
| `value` | `integer` | Forecasted GDP value for the country and date. |

---

### `economy.gdp.nominal`

```python
data.economy.gdp.nominal(start_time=None, end_time=None, country='united_states', use_cache=True, frequency='quarter', units='level', price_base='current_prices')
```

Summary: Nominal

| Field | Value |
|---|---|
| Endpoint ID | `economy.gdp.nominal` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/gdp/nominal` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `united_states` | The country to get data.Use 'all' to get data for all available countries. |
| `use_cache` | `no` | `boolean` | `true` | If True, the request will be cached for one day. Using cache is recommended to avoid needlessly requesting the same data. |
| `frequency` | `no` | `string` | `quarter` | enum: quarter, annual Frequency of the data. |
| `units` | `no` | `string` | `level` | enum: level, index, capita The unit of measurement for the data.Both 'level' and 'capita' (per) are measured in USD. |
| `price_base` | `no` | `string` | `current_prices` | enum: current_prices, volume Price base for the data, volume is chain linked volume. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `country` | `string` | The country represented by the GDP value. |
| `value` | `integer` | GDP value for the country and date. |
| `nominal_growth_qoq` | `number` | Nominal GDP growth rate quarter over quarter. |
| `nominal_growth_yoy` | `number` | Nominal GDP growth rate year over year. |

---

### `economy.gdp.real`

```python
data.economy.gdp.real(start_time=None, end_time=None, country='united_states', use_cache=True, frequency='quarter')
```

Summary: Real

| Field | Value |
|---|---|
| Endpoint ID | `economy.gdp.real` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/gdp/real` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `united_states` | The country to get data.Use 'all' to get data for all available countries. |
| `use_cache` | `no` | `boolean` | `true` | If True, the request will be cached for one day. Using cache is recommended to avoid needlessly requesting the same data. |
| `frequency` | `no` | `string` | `quarter` | enum: quarter, annual Frequency of the data. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `country` | `string` | The country represented by the Real GDP value. |
| `value` | `integer` | Real GDP value for the country and date. |
| `real_growth_qoq` | `number` | Real GDP growth rate quarter over quarter. |
| `real_growth_yoy` | `number` | Real GDP growth rate year over year. |

---

### `economy.house_price_index`

```python
data.economy.house_price_index(start_time=None, end_time=None, country='united_states', frequency='quarter', transform='index')
```

Summary: House Price Index

| Field | Value |
|---|---|
| Endpoint ID | `economy.house_price_index` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/house_price_index` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `united_states` | The country to get data. Multiple comma separated items allowed |
| `frequency` | `no` | `string` | `quarter` | The frequency of the data. |
| `transform` | `no` | `string` | `index` | Transformation of the CPI data. Period represents the change since previous. Defaults to change from one year ago (yoy). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `country` | `string` | country |
| `value` | `number` | Share price index value. |

---

### `economy.indicators`

```python
data.economy.indicators(symbol=..., start_time=None, end_time=None, country=None, frequency=None, transform=None, use_cache=True, dimension_values=None, limit=None, pivot=False)
```

Summary: Indicators

| Field | Value |
|---|---|
| Endpoint ID | `economy.indicators` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/indicators` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed; Symbol to get data for. The base symbol for the indicator (e.g. GDP, CPI, etc.). Use `available_indicators()` to get a list of available symbols.; Symbol to get data for. Symbol format: 'dataflow::identifier' where identifier is either: - A table ID (starts with 'H_') for hierarchical table data - An indicator code for individual indicator data Examples: - 'BOP::H_BOP_BOP_AGG_STANDARD_PRESENTATION' - Balance of Payments table - 'BOP_AGG::GS_CD,BOP_AGG::GS_DB' - Multiple BOP_AGG indicators (Goods & Services) - 'IL::RGV_REVS' - Gold reserves in millions of fine troy ounces - 'WEO::NGDP_RPCH' - Real GDP growth (annual only) - 'WEO::POILBRE' - Brent crude oil price (use country='G001' for world) - 'PCPS::PGOLD' - Gold price per troy ounce (monthly/quarterly available) Use `obb.economy.available_indicators()` to discover symbols. Use `obb.economy.imf_utils.list_tables()` to see available tables. |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string | null` | `-` | The country to get data. Multiple comma separated items allowed; The country to get data. ISO country codes or country names.; ISO3 country code(s). Use comma-separated values for multiple countries. Validated against the dataflow's available countries via constraint API. |
| `frequency` | `no` | `string | null` | `-` | The frequency of the data.; The frequency of the data, default is 'quarter'. Only valid when 'symbol' is 'main'.; The frequency of the data. Choices vary by indicator and country. Common options: 'annual', 'quarter', 'month'. Use 'all' or '*' to return all available frequencies. Direct IMF codes (e.g., 'A', 'Q', 'M') are also accepted. |
| `transform` | `no` | `string | null` | `-` | The transformation to apply to the data, default is None. tpop: Change from previous period toya: Change from one year ago tusd: Values as US dollars tpgp: Values as a percent of GDP Only 'tpop' and 'toya' are applicable to all indicators. Applying transformations across multiple indicators/countries may produce unexpected results. This is because not all indicators are compatible with all transformations, and the original units and scale differ between entities. `tusd` should only be used where values are currencies.; Transformation to apply to the data. User-friendly options: 'index' (raw values), 'yoy' (year-over-year %), 'period' (period-over-period %). Use 'all' or '*' to return all available transformations. Direct IMF codes (e.g., 'USD', 'IX') are also accepted. |
| `use_cache` | `no` | `boolean` | `true` | If True, the request will be cached for one day. Using cache is recommended to avoid needlessly requesting the same data. |
| `dimension_values` | `no` | `array | null` | `-` | accepts array values List of additional dimension filters in 'DIM_ID:DIM_VALUE' format. Parameter can be entered multiple times. |
| `limit` | `no` | `integer | null` | `-` | Maximum number of records to retrieve per series. |
| `pivot` | `no` | `boolean` | `false` | If True, pivots the data to presentation view with 'indicator' and 'country' as the index, date as values. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol_root` | `string` | The root symbol for the indicator (e.g. GDP). |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `country` | `string` | The country represented by the data. |
| `value` | `integer` | value |
| `unit` | `string` | The unit of measurement. |
| `unit_multiplier` | `integer` | The multiplier for the unit. |
| `scale` | `string` | The scale/multiplier of the value. |
| `order` | `integer` | Sort order within the table hierarchy. |
| `level` | `integer` | Indentation level in the table hierarchy. |
| `Indicator` | `string` | Human-readable title of the series. |
| `description` | `string` | Description of the indicator. |
| `country_code` | `string` | ISO3 country code. |

---

### `economy.interest_rates`

```python
data.economy.interest_rates(start_time=None, end_time=None, country='united_states', duration='short', frequency='monthly')
```

Summary: Interest Rates

| Field | Value |
|---|---|
| Endpoint ID | `economy.interest_rates` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/interest_rates` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `united_states` | The country to get data. Multiple comma separated items allowed |
| `duration` | `no` | `string` | `short` | enum: immediate, short, long Duration of the interest rate. 'immediate' is the overnight rate, 'short' is the 3-month rate, and 'long' is the 10-year rate. |
| `frequency` | `no` | `string` | `monthly` | enum: monthly, quarter, annual Frequency to get interest rate for for. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `value` | `number` | The interest rate value. |
| `country` | `string` | Country for which the interest rate is given. |

---

### `economy.money_measures`

```python
data.economy.money_measures(start_time=None, end_time=None, adjusted=True)
```

Summary: Money Measures

| Field | Value |
|---|---|
| Endpoint ID | `economy.money_measures` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/money_measures` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `adjusted` | `no` | `boolean | null` | `true` | Whether to return seasonally adjusted data. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `month` | `string` | The date of the data. |
| `m1` | `number` | Value of the M1 money supply in billions. |
| `m2` | `number` | Value of the M2 money supply in billions. |
| `currency` | `number` | Value of currency in circulation in billions. |
| `demand_deposits` | `number` | Value of demand deposits in billions. |
| `retail_money_market_funds` | `number` | Value of retail money market funds in billions. |
| `other_liquid_deposits` | `number` | Value of other liquid deposits in billions. |
| `small_denomination_time_deposits` | `number` | Value of small denomination time deposits in billions. |

---

### `economy.pce`

```python
data.economy.pce(date=None, category='personal_income')
```

Summary: Pce

| Field | Value |
|---|---|
| Endpoint ID | `economy.pce` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/pce` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `date` | `no` | `string | null` | `-` | A specific date to get data for. Default is the latest report. Multiple comma separated items allowed |
| `category` | `no` | `string` | `personal_income` | The category to query. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `value` | `number` | value |
| `name` | `string` | The name of the series. |
| `element_id` | `string` | The element id in the parent/child relationship. |
| `parent_id` | `string` | The parent id in the parent/child relationship. |
| `children` | `string` | The element_id of each child, as a comma-separated string. |
| `level` | `integer` | The indentation level of the element. |
| `line` | `integer` | The line number of the series in the table. |

---

### `economy.primary_dealer_fails`

```python
data.economy.primary_dealer_fails(start_time=None, end_time=None, asset_class='all', unit='value')
```

Summary: Primary Dealer Fails

| Field | Value |
|---|---|
| Endpoint ID | `economy.primary_dealer_fails` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/primary_dealer_fails` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `asset_class` | `no` | `string` | `all` | enum: all, treasuries, tips, agency, mbs, corporate Asset class to return, default is 'all'. |
| `unit` | `no` | `string` | `value` | enum: value, percent Unit of the data returned to the 'value' field. Default is 'value', which represents millions of USD. 'percent' returns data as the percentage of the total fails-to-receive and fails-to-deliver, by asset class. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `title` | `string` | Title of the series' symbol. |
| `value` | `integer` | Value of the data returned, in millions of USD if the `unit` parameter is 'value' else a normalized percent. |

---

### `economy.primary_dealer_positioning`

```python
data.economy.primary_dealer_positioning(start_time=None, end_time=None, category='treasuries')
```

Summary: Primary Dealer Positioning

| Field | Value |
|---|---|
| Endpoint ID | `economy.primary_dealer_positioning` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/primary_dealer_positioning` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `category` | `no` | `string` | `treasuries` | The category of asset to return, defaults to 'treasuries'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `value` | `integer` | The reported value of the net position (long - short), in millions of $USD. |
| `name` | `string` | Short name for the series. |
| `title` | `string` | Title of the series. |

---

### `economy.retail_prices`

```python
data.economy.retail_prices(start_time=None, end_time=None, item=None, country='united_states', region='all_city', frequency='monthly', transform=None)
```

Summary: Retail Prices

| Field | Value |
|---|---|
| Endpoint ID | `economy.retail_prices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/retail_prices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `item` | `no` | `string | null` | `-` | The item or basket of items to query. |
| `country` | `no` | `string` | `united_states` | The country to get data. |
| `region` | `no` | `string` | `all_city` | The region to get average price levels for. |
| `frequency` | `no` | `string` | `monthly` | The frequency of the data. |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `country` | `string` | country |
| `description` | `string` | Description of the item. |
| `value` | `number` | Price, or change in price, per unit. |

---

### `economy.risk_premium`

```python
data.economy.risk_premium()
```

Summary: Risk Premium

| Field | Value |
|---|---|
| Endpoint ID | `economy.risk_premium` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/risk_premium` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `country` | `string` | Market country. |
| `continent` | `string` | Continent of the country. |
| `total_equity_risk_premium` | `number` | Total equity risk premium for the country. |
| `country_risk_premium` | `number` | Country-specific risk premium. |

---

### `economy.share_price_index`

```python
data.economy.share_price_index(start_time=None, end_time=None, country='united_states', frequency='monthly')
```

Summary: Share Price Index

| Field | Value |
|---|---|
| Endpoint ID | `economy.share_price_index` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/share_price_index` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `united_states` | The country to get data. Multiple comma separated items allowed |
| `frequency` | `no` | `string` | `monthly` | The frequency of the data. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `country` | `string` | country |
| `value` | `number` | Share price index value. |

---

### `economy.shipping.chokepoint_info`

```python
data.economy.shipping.chokepoint_info(theme=None)
```

Summary: Chokepoint Info

| Field | Value |
|---|---|
| Endpoint ID | `economy.shipping.chokepoint_info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/shipping/chokepoint_info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `theme` | `no` | `string | null` | `-` | Theme for the map. Only valid if `openbb-charting` is installed and `chart` parameter is set to `true`. Default is the 'chart_style' setting in `user_settings.json`, if available, otherwise 'dark'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `chokepoint_code` | `string` | Unique ID assigned to the chokepoint by the source. |
| `name` | `string` | Port name. |
| `latitude` | `number` | Latitude of the chokepoint location. |
| `longitude` | `number` | Longitude of the chokepoint location. |
| `vessel_count_total` | `integer` | Yearly average number of all ships transiting through the chokepoint. |
| `vessel_count_tanker` | `integer` | Yearly average number of tankers transiting through the chokepoint. |
| `vessel_count_container` | `integer` | Yearly average number of containers transiting through the chokepoint. |
| `vessel_count_general_cargo` | `integer` | Yearly average number of general cargo ships transiting through the chokepoint. |
| `vessel_count_dry_bulk` | `integer` | Yearly average number of dry bulk carriers transiting through the chokepoint. |
| `vessel_count_roro` | `integer` | Yearly average number of Ro-Ro ships transiting through the chokepoint. |
| `industry_top_1` | `string` | First dominant traded industries based on the volume of goods estimated to flow through the chokepoint. |
| `industry_top_2` | `string` | Second dominant traded industries based on the volume of goods estimated to flow through the chokepoint. |
| `industry_top_3` | `string` | Third dominant traded industries based on the volume of goods estimated to flow through the chokepoint. |

---

### `economy.shipping.chokepoint_volume`

```python
data.economy.shipping.chokepoint_volume(start_time=None, end_time=None, chokepoint=None)
```

Summary: Chokepoint Volume

| Field | Value |
|---|---|
| Endpoint ID | `economy.shipping.chokepoint_volume` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/shipping/chokepoint_volume` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `chokepoint` | `no` | `string | null` | `-` | Name of the chokepoint. Use `None` for all chokepoints. Choices are: - suez_canal - panama_canal - bosporus_strait - bab_el_mandeb_strait - malacca_strait - strait_of_hormuz - cape_of_good_hope - gibraltar_strait - dover_strait - oresund_strait - taiwan_strait - korea_strait - tsugaru_strait - luzon_strait - lombok_strait - ombai_strait - bohai_strait - torres_strait - sunda_strait - makassar_strait - magellan_strait - yucatan_channel - windward_passage - mona_passage Multiple comma separated items allowed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `chokepoint` | `string` | Name of the chokepoint. |
| `vessels_total` | `integer` | Number of all ships transiting through the chokepoint on that date. |
| `vessels_cargo` | `integer` | Total number of ships (excluding tankers) transiting through the chokepoint at this date. |
| `vessels_tanker` | `integer` | Number of tankers transiting through the chokepoint on that date. |
| `vessels_container` | `integer` | Number of containers transiting through the chokepoint on that date. |
| `vessels_general_cargo` | `integer` | Number of general cargo ships transiting through the chokepoint on that date. |
| `vessels_dry_bulk` | `integer` | Yearly average number of dry bulk carriers transiting through the chokepoint. |
| `vessels_roro` | `integer` | Yearly average number of Ro-Ro ships transiting through the chokepoint. |
| `capacity_total` | `number` | Total trade volume (in metric tons) of all ships transiting through the chokepoint at this date. |
| `capacity_cargo` | `number` | Total trade volume (in metric tons) of all ships (excluding tankers) transiting through the chokepoint at this date. |
| `capacity_tanker` | `number` | Total trade volume (in metric tons) of tankers transiting through the chokepoint at this date. |
| `capacity_container` | `number` | Total trade volume (in metric tons) of containers transiting through the chokepoint at this date. |
| `capacity_general_cargo` | `number` | Total trade volume (in metric tons) of general cargo Vessels transiting through the chokepoint at this date. |
| `capacity_dry_bulk` | `number` | Total trade volume (in metric tons) of dry bulk carriers transiting through the chokepoint at this date. |
| `capacity_roro` | `number` | Total trade volume (in metric tons) of Ro-Ro ships transiting through the chokepoint at this date. |

---

### `economy.shipping.port_info`

```python
data.economy.shipping.port_info(continent=None, country=None, port_code=None, limit=None)
```

Summary: Port Info

| Field | Value |
|---|---|
| Endpoint ID | `economy.shipping.port_info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/shipping/port_info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `continent` | `no` | `string | null` | `-` | Filter by continent. This parameter is ignored when a `country` is provided. |
| `country` | `no` | `string | null` | `-` | Country to focus on. Enter as a 3-letter ISO country code. This parameter supersedes `continent` if both are provided. |
| `port_code` | `no` | `string | null` | `-` | This is a dummy parameter to allow grouping in OpenBB Workspace widgets. |
| `limit` | `no` | `integer | null` | `-` | Limit the number of results returned. Limit is determined by the annual average number of vessels transiting through the port. If not provided, all ports are returned. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `port_code` | `string` | Unique ID assigned to the port. |
| `continent` | `string` | Continent where the port is located. |
| `country` | `string` | Country where the port is located. |
| `country_code` | `string` | 3-letter ISO code of the country where the port is located. |
| `port_name` | `string` | Port name. |
| `port_full_name` | `string` | Full name of the port. |
| `latitude` | `number` | Latitude of the port. |
| `longitude` | `number` | Longitude of the port. |
| `vessel_count_total` | `integer` | Yearly average number of all ships transiting through the port. |
| `vessel_count_tanker` | `integer` | Yearly average number of tankers transiting through the port. |
| `vessel_count_container` | `integer` | Yearly average number of containers transiting through the port. |
| `vessel_count_general_cargo` | `integer` | Yearly average number of general cargo ships transiting through the port. |
| `vessel_count_dry_bulk` | `integer` | Yearly average number of dry bulk carriers transiting through the port. |
| `vessel_count_roro` | `integer` | Yearly average number of Ro-Ro ships transiting through the port. |
| `industry_top_1` | `string` | First dominant traded industries based on the volume of goods estimated to flow through the port. |
| `industry_top_2` | `string` | Second dominant traded industries based on the volume of goods estimated to flow through the port. |
| `industry_top_3` | `string` | Third dominant traded industries based on the volume of goods estimated to flow through the port. |
| `share_country_maritime_import` | `number` | Share of the total maritime imports of the country that are estimated to flow through the port. |
| `share_country_maritime_export` | `number` | Share of the total maritime exports of the country that are estimated to flow through the port. |

---

### `economy.shipping.port_volume`

```python
data.economy.shipping.port_volume(start_time=None, end_time=None, port_code=None, country=None)
```

Summary: Port Volume

| Field | Value |
|---|---|
| Endpoint ID | `economy.shipping.port_volume` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/shipping/port_volume` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `port_code` | `no` | `string | null` | `-` | Port code to filter results by a specific port. This parameter is ignored if `country` parameter is provided. To get a list of available ports, use `obb.economy.shipping.port_info()`. Multiple comma separated items allowed. |
| `country` | `no` | `string | null` | `-` | Country to focus on. Enter as a 3-letter ISO country code. This parameter is overridden by `port_code` if both are provided. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `port_code` | `string` | Port code. |
| `port_name` | `string` | Port name. |
| `country` | `string` | Country where the port is located. |
| `country_code` | `string` | 3-letter ISO country code of the country where the port is located. |
| `portcalls` | `integer` | Total number of ships entering the port at this date. |
| `portcalls_tanker` | `integer` | Number of tankers transiting through the chokepoint or making a port call. |
| `portcalls_container` | `integer` | Number of containers transiting through the chokepoint or making a port call. |
| `portcalls_general_cargo` | `integer` | Number of general cargo ships transiting through the chokepoint or making a port call. |
| `portcalls_dry_bulk` | `integer` | Number of dry bulk carriers transiting through the chokepoint or making a port call. |
| `portcalls_roro` | `integer` | Number of Ro-Ro ships transiting through the chokepoint or making a port call. |
| `imports` | `number` | Total import volume (in metric tons) of all ships entering the port at this date. |
| `imports_cargo` | `number` | Total import volume (in metric tons) of all ships (excluding tankers) entering the port at this date. |
| `imports_tanker` | `number` | Total import volume (in metric tons) of tankers entering the port at this date. |
| `imports_container` | `number` | Total import volume (in metric tons) of all container ships entering the port at this date. |
| `imports_general_cargo` | `number` | Total import volume (in metric tons) of general cargo ships entering the port at this date. |
| `imports_dry_bulk` | `number` | Total import volume (in metric tons) of dry bulk carriers entering the port at this date. |
| `imports_roro` | `number` | Total import volume (in metric tons) of Ro-Ro ships entering the port at this date. |
| `exports` | `number` | Total export volume (in metric tons) of all ships entering the port at this date. |
| `exports_cargo` | `number` | Total export volume (in metric tons) of all ships (excluding tankers) entering the port at this date. |
| `exports_tanker` | `number` | Total export volume (in metric tons) of tankers entering the port at this date. |
| `exports_container` | `number` | Total export volume (in metric tons) of all container ships entering the port at this date. |
| `exports_general_cargo` | `number` | Total export volume (in metric tons) of general cargo ships entering the port at this date. |
| `exports_dry_bulk` | `number` | Total export volume (in metric tons) of dry bulk carriers entering the port at this date. |
| `exports_roro` | `number` | Total export volume (in metric tons) of Ro-Ro ships entering the port at this date. |
| `export_dwell_time` | `number` | EconDB model estimate for the average number of days from when a container enters the terminal gates until it is loaded on a vessel. |
| `import_dwell_time` | `number` | EconDB model estimate for the average number of days from when a container is discharged from a vessel until it exits the terminal gates. |
| `import_teu` | `integer` | EconDB model estimate for the number of TEUs of containers imported through the port. |
| `export_teu` | `integer` | EconDB model estimate for the number of TEUs of containers exported through the port. |

---

### `economy.survey.bls_search`

```python
data.economy.survey.bls_search(query='', category=None, include_extras=False, include_code_map=False)
```

Summary: Bls Search

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.bls_search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/bls_search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string` | `` | The search word(s). Use semi-colon to separate multiple queries as an & operator. |
| `category` | `no` | `string | null` | `-` | The category of BLS survey to search within. An empty search query will return all series within the category. Options are: cpi - Consumer Price Index pce - Personal Consumption Expenditure ppi - Producer Price Index ip - Industry Productivity jolts - Job Openings and Labor Turnover Survey nfp - Nonfarm Payrolls cps - Current Population Survey lfs - Labor Force Statistics wages - Wages ec - Employer Costs sla - State and Local Area Employment bed - Business Employment Dynamics tu - Time Use |
| `include_extras` | `no` | `boolean` | `false` | Include additional information in the search results. Extra fields returned are metadata and vary by survey. Fields are undefined strings that typically have names ending with '_code'. |
| `include_code_map` | `no` | `boolean` | `false` | When True, includes the complete code map for eaçh survey in the category, returned separately as a nested JSON to the `extras['results_metadata']` property of the response. Example content is the NAICS industry map for PPI surveys. Each code is a value within the 'symbol' of the time series. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `title` | `string` | The title of the series. |
| `survey_name` | `string` | The name of the survey. |

---

### `economy.survey.bls_series`

```python
data.economy.survey.bls_series(symbol=..., start_time=None, end_time=None, calculations=True, annual_average=False, aspects=False)
```

Summary: Bls Series

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.bls_series` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/bls_series` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `calculations` | `no` | `boolean` | `true` | Include calculations in the response, if available. Default is True. |
| `annual_average` | `no` | `boolean` | `false` | Include annual averages in the response, if available. Default is False. |
| `aspects` | `no` | `boolean` | `false` | Include all aspects associated with a data point for a given BLS series ID, if available. Returned with the series metadata, under `extras` of the response object. Default is False. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `title` | `string` | Title of the series. |
| `value` | `number` | Observation value for the symbol and date. |
| `change_1_m` | `number` | One month change in value. |
| `change_3_m` | `number` | Three month change in value. |
| `change_6_m` | `number` | Six month change in value. |
| `change_12_m` | `number` | One year change in value. |
| `change_percent_1_m` | `number` | One month change in percent. |
| `change_percent_3_m` | `number` | Three month change in percent. |
| `change_percent_6_m` | `number` | Six month change in percent. |
| `change_percent_12_m` | `number` | One year change in percent. |
| `latest` | `boolean` | Latest value indicator. |
| `footnotes` | `string` | Footnotes accompanying the value. |

---

### `economy.survey.economic_conditions_chicago`

```python
data.economy.survey.economic_conditions_chicago(start_time=None, end_time=None, frequency=None, aggregation_method=None, transform=None)
```

Summary: Economic Conditions Chicago

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.economic_conditions_chicago` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/economic_conditions_chicago` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert monthly data to lower frequency. None is monthly. |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `activity_index` | `number` | Activity Index. |
| `one_year_outlook` | `number` | One Year Outlook Index. |
| `manufacturing_activity` | `number` | Manufacturing Activity Index. |
| `non_manufacturing_activity` | `number` | Non-Manufacturing Activity Index. |
| `capital_expenditures_expectations` | `number` | Capital Expenditures Expectations Index. |
| `hiring_expectations` | `number` | Hiring Expectations Index. |
| `current_hiring` | `number` | Current Hiring Index. |
| `labor_costs` | `number` | Labor Costs Index. |
| `non_labor_costs` | `number` | Non-Labor Costs Index. |

---

### `economy.survey.inflation_expectations`

```python
data.economy.survey.inflation_expectations(start_date=None, end_date=None)
```

Summary: Inflation Expectations

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.inflation_expectations` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/inflation_expectations` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_date` | `no` | `string | null` | `-` | Start date of the data, in YYYY-MM-DD format. Data begins from 1970-04-01 and is quarterly. |
| `end_date` | `no` | `string | null` | `-` | End date of the data, in YYYY-MM-DD format. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the survey (first day of the survey quarter). |
| `infpgdp1yr` | `number` | One-year-ahead annual-average GDP price index inflation forecast. |
| `infcpi1yr` | `number` | One-year-ahead annual-average CPI inflation forecast. |
| `infcpi10yr` | `number` | Ten-year-ahead annual-average CPI inflation forecast. |

---

### `economy.survey.manufacturing_outlook_ny`

```python
data.economy.survey.manufacturing_outlook_ny(start_time=None, end_time=None, topic='new_orders', seasonally_adjusted=False, frequency=None, aggregation_method=None, transform=None)
```

Summary: Manufacturing Outlook Ny

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.manufacturing_outlook_ny` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/manufacturing_outlook_ny` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `topic` | `no` | `string` | `new_orders` | The topic for the survey response. Multiple comma separated items allowed. |
| `seasonally_adjusted` | `no` | `boolean` | `false` | Whether the data is seasonally adjusted, default is False |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert monthly data to lower frequency. None is monthly. |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `topic` | `string` | Topic of the survey response. |
| `diffusion_index` | `number` | Diffusion Index. |
| `percent_reporting_increase` | `number` | Percent of respondents reporting an increase over the last month. |
| `percent_reporting_decrease` | `number` | Percent of respondents reporting a decrease over the last month. |
| `percent_reporting_no_change` | `number` | Percent of respondents reporting no change over the last month. |

---

### `economy.survey.manufacturing_outlook_texas`

```python
data.economy.survey.manufacturing_outlook_texas(start_time=None, end_time=None, topic='new_orders_growth', frequency=None, aggregation_method=None, transform=None)
```

Summary: Manufacturing Outlook Texas

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.manufacturing_outlook_texas` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/manufacturing_outlook_texas` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `topic` | `no` | `string` | `new_orders_growth` | The topic for the survey response. Multiple comma separated items allowed. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert monthly data to lower frequency. None is monthly. |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `topic` | `string` | Topic of the survey response. |
| `diffusion_index` | `number` | Diffusion Index. |
| `percent_reporting_increase` | `number` | Percent of respondents reporting an increase over the last month. |
| `percent_reporting_decrease` | `number` | Percent of respondents reporting a decrease over the last month. |
| `percent_reporting_no_change` | `number` | Percent of respondents reporting no change over the last month. |

---

### `economy.survey.nonfarm_payrolls`

```python
data.economy.survey.nonfarm_payrolls(date=None, category='employees_nsa')
```

Summary: Nonfarm Payrolls

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.nonfarm_payrolls` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/nonfarm_payrolls` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `date` | `no` | `string | null` | `-` | A specific date to get data for. Default is the latest report. Multiple comma separated items allowed |
| `category` | `no` | `string` | `employees_nsa` | The category to query. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `value` | `number` | value |
| `name` | `string` | The name of the series. |
| `element_id` | `string` | The element id in the parent/child relationship. |
| `parent_id` | `string` | The parent id in the parent/child relationship. |
| `children` | `string` | The element_id of each child, as a comma-separated string. |
| `level` | `integer` | The indentation level of the element. |

---

### `economy.survey.sloos`

```python
data.economy.survey.sloos(start_time=None, end_time=None, category='spreads', transform=None)
```

Summary: Sloos

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.sloos` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/sloos` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `category` | `no` | `string` | `spreads` | Category of survey response. |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `value` | `number` | Survey value. |
| `title` | `string` | Survey title. |

---

### `economy.survey.university_of_michigan`

```python
data.economy.survey.university_of_michigan(start_time=None, end_time=None, frequency=None, aggregation_method=None, transform=None)
```

Summary: University Of Michigan

| Field | Value |
|---|---|
| Endpoint ID | `economy.survey.university_of_michigan` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/survey/university_of_michigan` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert monthly data to lower frequency. None is monthly. |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `consumer_sentiment` | `number` | Index of the results of the University of Michigan's monthly Survey of Consumers (1966:Q1=100). |
| `inflation_expectation` | `number` | Median expected price change next 12 months, Surveys of Consumers. |

---

### `economy.total_factor_productivity`

```python
data.economy.total_factor_productivity(frequency='quarter', start_date=None, end_date=None)
```

Summary: Total Factor Productivity

| Field | Value |
|---|---|
| Endpoint ID | `economy.total_factor_productivity` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/total_factor_productivity` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `frequency` | `no` | `string` | `quarter` | Type of data to return. 'quarter' for quarterly time series, 'annual' for annual time series, 'summary' for summary statistics (period means). |
| `start_date` | `no` | `string | null` | `-` | Start date of the data, in YYYY-MM-DD format. Only applicable for time series data (quarter/annual). |
| `end_date` | `no` | `string | null` | `-` | End date of the data, in YYYY-MM-DD format. Only applicable for time series data (quarter/annual). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `variable` | `string` | The variable name (e.g., 'd_y', 'd_tfp', 'd_tfp_util'). |
| `variable_title` | `string` | Human-readable title for the variable. |
| `full_sample_mean` | `number` | Mean value over the full sample period. |
| `past_4_quarters` | `number` | Mean value over the past 4 quarters. |
| `past_8_quarters` | `number` | Mean value over the past 8 quarters. |
| `since_2019` | `number` | Mean value since 2019:Q4. |
| `period_2004_2019` | `number` | Mean value for the period 2004:Q4 to 2019:Q4. |
| `period_1995_2004` | `number` | Mean value for the period 1995:Q4 to 2004:Q4. |
| `period_1973_1995` | `number` | Mean value for the period 1973:Q1 to 1995:Q4. |
| `period_1947_1973` | `number` | Mean value for the period 1947:Q1 to 1973:Q1. |
| `date` | `string` | The date of the data. |
| `d_y_prod` | `number` | Business output, expenditure (product) side. |
| `d_y_inc` | `number` | Business output, measured from income side. |
| `d_y` | `number` | Output. Average of d_y_prod and d_y_inc. |
| `d_hours` | `number` | Hours worked in the business sector. |
| `d_lp` | `number` | Business-sector labor productivity. |
| `d_k` | `number` | Capital input. |
| `d_lq_bls_interpolated` | `number` | Labor composition/quality from BLS (pre-1979 interpolated). |
| `d_lq_aaronson_sullivan` | `number` | Labor composition/quality following Aaronson-Sullivan (1979 onwards). |
| `d_lq` | `number` | Labor composition/quality actually used. |
| `alpha` | `number` | Capital's share of income (ratio between 0 and 1). |
| `d_tfp` | `number` | Business sector Total Factor Productivity. |
| `d_util` | `number` | Utilization adjustment for capital and labor. |
| `d_tfp_util` | `number` | Utilization-adjusted Total Factor Productivity. |
| `relative_price` | `number` | Relative price growth of 'consumption' to price of 'equipment'. |
| `inv_share` | `number` | Equipment and consumer durables share of business output (ratio between 0 and 1). |
| `d_tfp_i` | `number` | TFP in equipment and consumer durables sector. |
| `d_tfp_c` | `number` | TFP in non-equipment business output ('consumption' goods and services). |
| `d_u_invest` | `number` | Utilization adjustment in producing investment goods. |
| `d_u_consumption` | `number` | Utilization adjustment in producing non-investment business output. |
| `d_tfp_i_util` | `number` | Utilization-adjusted TFP in producing equipment and consumer durables. |
| `d_tfp_c_util` | `number` | Utilization-adjusted TFP in producing non-equipment business output. |

---

### `economy.unemployment`

```python
data.economy.unemployment(start_time=None, end_time=None, country='united_states', frequency='monthly', sex='total', age='total', seasonal_adjustment=False)
```

Summary: Unemployment

| Field | Value |
|---|---|
| Endpoint ID | `economy.unemployment` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/economy/unemployment` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `country` | `no` | `string` | `united_states` | The country to get data. Multiple comma separated items allowed |
| `frequency` | `no` | `string` | `monthly` | The frequency of the data. |
| `sex` | `no` | `string` | `total` | Sex to get unemployment for. |
| `age` | `no` | `string` | `total` | Age group to get unemployment for. Total indicates 15 years or over |
| `seasonal_adjustment` | `no` | `boolean` | `false` | Whether to get seasonally adjusted unemployment. Defaults to False. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `country` | `string` | Country for which unemployment rate is given |
| `value` | `number` | Unemployment rate, as a normalized percent. |
