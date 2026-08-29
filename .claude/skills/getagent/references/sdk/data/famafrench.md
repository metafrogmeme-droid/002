# Famafrench Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`famafrench.breakpoints`](#famafrenchbreakpoints)
- [`famafrench.country_portfolio_returns`](#famafrenchcountry-portfolio-returns)
- [`famafrench.factors`](#famafrenchfactors)
- [`famafrench.international_index_returns`](#famafrenchinternational-index-returns)
- [`famafrench.regional_portfolio_returns`](#famafrenchregional-portfolio-returns)
- [`famafrench.us_portfolio_returns`](#famafrenchus-portfolio-returns)

## Endpoint reference

### `famafrench.breakpoints`

```python
data.famafrench.breakpoints(breakpoint_type='me', start_date=None, end_date=None)
```

Summary: Breakpoints

| Field | Value |
|---|---|
| Endpoint ID | `famafrench.breakpoints` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/famafrench/breakpoints` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `breakpoint_type` | `no` | `string` | `me` | Type of breakpoint to fetch. The breakpoints for month t use all NYSE stocks that have a CRSP share code of 10 or 11 and have good shares and price data. We exclude closed end funds and REITs. Breakpoints are computed either monthly or annually, see the description of each breakpoint type below. Data contains every fifth percentile, from 5% to 100%. ME -- Market Equity. Market equity (size) is price times shares outstanding. Price and shares outstanding are from CRSP. ME breakpoints are computed for each month. It is price times shares outstanding (divided by 1,000,000) at month end. BE/ME ----- BE/ME breakpoints are computed at the end of each June. The BE used in June of year t is the book equity for the last fiscal year end in t-1. ME is price times shares outstanding at the end of December of t-1. The breakpoints for year t use all NYSE stocks for which we have ME for December of t-1 and (positive) BE for the last fiscal year end in t-1. Operating Profitability ----------------------- Operating Profitability breakpoints are computed at the end of each June. OP for June of year t is annual revenues minus - cost of goods sold - interest expense - selling, general, and administrative expenses divided by book equity for the last fiscal year end in t-1. Please be aware that some of the value-weight averages of operating profitability for deciles 1 and 10 are extreme. These are driven by extraordinary values of OP for individual firms. We have spot checked the accounting data that produce the extraordinary values and all the numbers we examined accurately reflect the data in the firm's accounting statements. The breakpoints for year t use all NYSE stocks for which we have (positive) book equity data for t-1, non-missing revenues data for t-1, and non-missing data for at least one of the following: - cost of goods sold - selling, general and administrative expenses - interest expense for t-1. Investment ---------- Investment breakpoints are computed at the end of each June. Inv used in June of year t is the change in total assets from the fiscal year ending in year t-2 to the fiscal year ending in t-1, divided by t-2 total assets. The breakpoints for year t use all NYSE stocks for which we have total assets data for t-2 and t-1. E/P --- E/P (in percent) breakpoints are computed at the end of each June. The E used in June of year t is the earnings for the last fiscal year end in t-1. P (actually ME) is price times shares outstanding at the end of December of t-1. The breakpoints for year t use all NYSE stocks for which we have ME for December of t-1 and (positive) earnings for the last fiscal year end in t-1. CF/P ---- CF/P (in percent) breakpoints is computed at the end of each June. The CF used in June of year t is the cash flow for the last fiscal year end in t-1. P (actually ME) is price times shares outstanding at the end of December of t-1. The breakpoints for year t use all NYSE stocks for which we have ME for December of t-1 and (positive) cash flow for the last fiscal year end in t-1. D/P --- D/P (in percent) breakpoints are computed at the end of each June. The dividend yield in June of year t is the total dividends paid from July of t-1 to June of t per dollar of equity in June of t. The breakpoints for year t use NYSE stocks for which we have at least seven months (to compute the dividend yield) from July of t-1 to June of t. (Only six monthly returns are required in June 1926.) We do not include stocks that pay no dividends from July of t-1 to June of t. Prior 2-12 ---------- Prior return breakpoints are computed for each month. The prior return at the end of month t is the cumulative return from month t-11 to month t-1. The breakpoints for month t use NYSE stocks. To be included, a stock must have a price for the end of month t-12 and a good return for t-1. In addition, any missing returns from t-11 to t-2 must be -99.0, CRSP's code for a missing price. |
| `start_date` | `no` | `string | null` | `-` | Start date for the data. |
| `end_date` | `no` | `string | null` | `-` | End date for the data. |

---

### `famafrench.country_portfolio_returns`

```python
data.famafrench.country_portfolio_returns(country='united_kingdom', measure='usd', frequency='monthly', dividends=None, all_data_items_required=None, start_date=None, end_date=None)
```

Summary: Country Portfolio Returns

| Field | Value |
|---|---|
| Endpoint ID | `famafrench.country_portfolio_returns` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/famafrench/country_portfolio_returns` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `country` | `no` | `string` | `united_kingdom` | enum: austria, australia, belgium, canada, denmark, finland, france, germany, hong_kong, ireland, italy, japan, malaysia, netherlands, new_zealand, norway, singapore, spain, sweden, switzerland, united_kingdom Country to fetch the portfolio returns for. |
| `measure` | `no` | `string` | `usd` | The measure to fetch for the portfolio. Only 'annual' frequency is supported for 'ratios'. |
| `frequency` | `no` | `string` | `monthly` | The frequency of the data to fetch. Ignored when `measure` is set to 'ratios'. |
| `dividends` | `no` | `boolean | null` | `-` | When False, portoflios exclude dividends. |
| `all_data_items_required` | `no` | `boolean | null` | `-` | If True (default), includes firms with data for all four ratios. When False, includes only firms with Book-to-Market (B/M) data. |
| `start_date` | `no` | `string | null` | `-` | The start date for the data. Defaults to the earliest available date. |
| `end_date` | `no` | `string | null` | `-` | The end date for the data. Defaults to the latest available date. |

---

### `famafrench.factors`

```python
data.famafrench.factors(region='america', factor='3_factors', frequency='monthly', start_date=None, end_date=None)
```

Summary: Factors

| Field | Value |
|---|---|
| Endpoint ID | `famafrench.factors` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/famafrench/factors` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `region` | `no` | `string` | `america` | Region of focus. Default is America. |
| `factor` | `no` | `string` | `3_factors` | Factor to fetch. Default is the 3-Factor Model.Short/long-term reversals are available only for America. |
| `frequency` | `no` | `string` | `monthly` | Frequency of the factor data.Not all are available for all regions, and intervals depend on the factor selected. Weekly is only available for the US 3-Factor Model. |
| `start_date` | `no` | `string | null` | `-` | Start date of the data. Defaults to the complete data range. |
| `end_date` | `no` | `string | null` | `-` | End date of the data. Defaults to the complete data range. |

---

### `famafrench.international_index_returns`

```python
data.famafrench.international_index_returns(index='all', measure='usd', frequency='monthly', dividends=None, all_data_items_required=None, start_date=None, end_date=None)
```

Summary: International Index Returns

| Field | Value |
|---|---|
| Endpoint ID | `famafrench.international_index_returns` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/famafrench/international_index_returns` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `index` | `no` | `string` | `all` | International index to fetch the portfolio returns for. Defaults to 'all'. |
| `measure` | `no` | `string` | `usd` | The measure to fetch for the portfolio. Only 'annual' frequency is supported for 'ratios'. |
| `frequency` | `no` | `string` | `monthly` | The frequency of the data to fetch. Ignored when `measure` is set to 'ratios'. |
| `dividends` | `no` | `boolean | null` | `-` | When False, portoflios exclude dividends. |
| `all_data_items_required` | `no` | `boolean | null` | `-` | If True (default), includes firms with data for all four ratios. When False, includes only firms with Book-to-Market (B/M) data. |
| `start_date` | `no` | `string | null` | `-` | The start date for the data. Defaults to the earliest available date. |
| `end_date` | `no` | `string | null` | `-` | The end date for the data. Defaults to the latest available date. |

---

### `famafrench.regional_portfolio_returns`

```python
data.famafrench.regional_portfolio_returns(portfolio='developed_ex_us_6_portfolios_me_op', measure='value', frequency='monthly', start_date=None, end_date=None)
```

Summary: Regional Portfolio Returns

| Field | Value |
|---|---|
| Endpoint ID | `famafrench.regional_portfolio_returns` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/famafrench/regional_portfolio_returns` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `portfolio` | `no` | `string` | `developed_ex_us_6_portfolios_me_op` | enum: asia_pacific_ex_japan_25_portfolios_me_be-me, asia_pacific_ex_japan_25_portfolios_me_be-me_daily, asia_pacific_ex_japan_25_portfolios_me_inv, asia_pacific_ex_japan_25_portfolios_me_inv_daily, asia_pacific_ex_japan_25_portfolios_me_op, asia_pacific_ex_japan_25_portfolios_me_op_daily, asia_pacific_ex_japan_25_portfolios_me_prior_12_2, asia_pacific_ex_japan_25_portfolios_me_prior_250_20_daily, asia_pacific_ex_japan_32_portfolios_me_be-me_inv_2x4x4, asia_pacific_ex_japan_32_portfolios_me_be-me_op_2x4x4, asia_pacific_ex_japan_32_portfolios_me_inv_op_2x4x4, asia_pacific_ex_japan_6_portfolios_me_be-me, asia_pacific_ex_japan_6_portfolios_me_be-me_daily, asia_pacific_ex_japan_6_portfolios_me_inv, asia_pacific_ex_japan_6_portfolios_me_inv_daily, asia_pacific_ex_japan_6_portfolios_me_op, asia_pacific_ex_japan_6_portfolios_me_op_daily, asia_pacific_ex_japan_6_portfolios_me_prior_12_2, asia_pacific_ex_japan_6_portfolios_me_prior_250_20_daily, developed_25_portfolios_me_be-me, developed_25_portfolios_me_be-me_daily, developed_25_portfolios_me_inv, developed_25_portfolios_me_inv_daily, developed_25_portfolios_me_op, developed_25_portfolios_me_op_daily, developed_25_portfolios_me_prior_12_2, developed_25_portfolios_me_prior_250_20_daily, developed_32_portfolios_me_be-me_inv_2x4x4, developed_32_portfolios_me_be-me_op_2x4x4, developed_32_portfolios_me_inv_op_2x4x4, developed_6_portfolios_me_be-me, developed_6_portfolios_me_be-me_daily, developed_6_portfolios_me_inv, developed_6_portfolios_me_inv_daily, developed_6_portfolios_me_op, developed_6_portfolios_me_op_daily, developed_6_portfolios_me_prior_12_2, developed_6_portfolios_me_prior_250_20_daily, developed_ex_us_25_portfolios_me_be-me, developed_ex_us_25_portfolios_me_be-me_daily, developed_ex_us_25_portfolios_me_inv, developed_ex_us_25_portfolios_me_inv_daily, developed_ex_us_25_portfolios_me_op, developed_ex_us_25_portfolios_me_op_daily, developed_ex_us_25_portfolios_me_prior_12_2, developed_ex_us_25_portfolios_me_prior_250_20_daily, developed_ex_us_32_portfolios_me_be-me_inv_2x4x4, developed_ex_us_32_portfolios_me_be-me_op_2x4x4, developed_ex_us_32_portfolios_me_inv_op_2x4x4, developed_ex_us_6_portfolios_me_be-me, developed_ex_us_6_portfolios_me_be-me_daily, developed_ex_us_6_portfolios_me_inv, developed_ex_us_6_portfolios_me_inv_daily, developed_ex_us_6_portfolios_me_op, developed_ex_us_6_portfolios_me_op_daily, developed_ex_us_6_portfolios_me_prior_12_2, developed_ex_us_6_portfolios_me_prior_250_20_daily, emerging_markets_4_portfolios_be-me_inv, emerging_markets_4_portfolios_be-me_op, emerging_markets_4_portfolios_op_inv, emerging_markets_6_portfolios_me_be-me, emerging_markets_6_portfolios_me_inv, emerging_markets_6_portfolios_me_op, emerging_markets_6_portfolios_me_prior_12_2, europe_25_portfolios_me_be-me, europe_25_portfolios_me_be-me_daily, europe_25_portfolios_me_inv, europe_25_portfolios_me_inv_daily, europe_25_portfolios_me_op, europe_25_portfolios_me_op_daily, europe_25_portfolios_me_prior_12_2, europe_25_portfolios_me_prior_250_20_daily, europe_32_portfolios_me_be-me_inv_2x4x4, europe_32_portfolios_me_be-me_op_2x4x4, europe_32_portfolios_me_inv_op_2x4x4, europe_6_portfolios_me_be-me, europe_6_portfolios_me_be-me_daily, europe_6_portfolios_me_inv, europe_6_portfolios_me_inv_daily, europe_6_portfolios_me_op, europe_6_portfolios_me_op_daily, europe_6_portfolios_me_prior_12_2, europe_6_portfolios_me_prior_250_20_daily, japan_25_portfolios_me_be-me, japan_25_portfolios_me_be-me_daily, japan_25_portfolios_me_inv, japan_25_portfolios_me_inv_daily, japan_25_portfolios_me_op, japan_25_portfolios_me_op_daily, japan_25_portfolios_me_prior_12_2, japan_25_portfolios_me_prior_250_20_daily, japan_32_portfolios_me_be-me_inv_2x4x4, japan_32_portfolios_me_be-me_op_2x4x4, japan_32_portfolios_me_inv_op_2x4x4, japan_6_portfolios_me_be-me, japan_6_portfolios_me_be-me_daily, japan_6_portfolios_me_inv, japan_6_portfolios_me_inv_daily, japan_6_portfolios_me_op, japan_6_portfolios_me_op_daily, japan_6_portfolios_me_prior_12_2, japan_6_portfolios_me_prior_250_20_daily, north_america_25_portfolios_me_be-me, north_america_25_portfolios_me_be-me_daily, north_america_25_portfolios_me_inv, north_america_25_portfolios_me_inv_daily, north_america_25_portfolios_me_op, north_america_25_portfolios_me_op_daily, north_america_25_portfolios_me_prior_12_2, north_america_25_portfolios_me_prior_250_20_daily, north_america_32_portfolios_me_be-me_inv_2x4x4, north_america_32_portfolios_me_be-me_op_2x4x4, north_america_32_portfolios_me_inv_op_2x4x4, north_america_6_portfolios_me_be-me, north_america_6_portfolios_me_be-me_daily, north_america_6_portfolios_me_inv, north_america_6_portfolios_me_inv_daily, north_america_6_portfolios_me_op, north_america_6_portfolios_me_op_daily, north_america_6_portfolios_me_prior_12_2, north_america_6_portfolios_me_prior_250_20_daily The specific portfolio file to fetch. |
| `measure` | `no` | `string` | `value` | The measure to fetch for the portfolio. |
| `frequency` | `no` | `string` | `monthly` | The frequency of the data to fetch. Ignored when the portfolio ends with 'daily'. |
| `start_date` | `no` | `string | null` | `-` | The start date for the data. Defaults to the earliest available date. |
| `end_date` | `no` | `string | null` | `-` | The end date for the data. Defaults to the latest available date. |

---

### `famafrench.us_portfolio_returns`

```python
data.famafrench.us_portfolio_returns(portfolio='portfolios_formed_on_me', measure='value', frequency='monthly', start_date=None, end_date=None)
```

Summary: Us Portfolio Returns

| Field | Value |
|---|---|
| Endpoint ID | `famafrench.us_portfolio_returns` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/famafrench/us_portfolio_returns` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `portfolio` | `no` | `string` | `portfolios_formed_on_me` | enum: portfolios_formed_on_me, portfolios_formed_on_me_wout_div, portfolios_formed_on_me_daily, portfolios_formed_on_be-me, portfolios_formed_on_be-me_wout_div, portfolios_formed_on_be-me_daily, portfolios_formed_on_op, portfolios_formed_on_op_wout_div, portfolios_formed_on_op_daily, portfolios_formed_on_inv, portfolios_formed_on_inv_wout_div, portfolios_formed_on_inv_daily, 6_portfolios_2x3, 6_portfolios_2x3_wout_div, 6_portfolios_2x3_weekly, 6_portfolios_2x3_daily, 25_portfolios_5x5, 25_portfolios_5x5_wout_div, 25_portfolios_5x5_daily, 100_portfolios_10x10, 100_portfolios_10x10_wout_div, 100_portfolios_10x10_daily, 6_portfolios_me_op_2x3, 6_portfolios_me_op_2x3_wout_div, 6_portfolios_me_op_2x3_daily, 25_portfolios_me_op_5x5, 25_portfolios_me_op_5x5_wout_div, 25_portfolios_me_op_5x5_daily, 100_portfolios_me_op_10x10, 100_portfolios_10x10_me_op_wout_div, 100_portfolios_me_op_10x10_daily, 6_portfolios_me_inv_2x3, 6_portfolios_me_inv_2x3_wout_div, 6_portfolios_me_inv_2x3_daily, 25_portfolios_me_inv_5x5, 25_portfolios_me_inv_5x5_wout_div, 25_portfolios_me_inv_5x5_daily, 100_portfolios_me_inv_10x10, 100_portfolios_10x10_me_inv_wout_div, 100_portfolios_me_inv_10x10_daily, 25_portfolios_beme_op_5x5, 25_portfolios_beme_op_5x5_wout_div, 25_portfolios_beme_op_5x5_daily, 25_portfolios_beme_inv_5x5, 25_portfolios_beme_inv_5x5_wout_div, 25_portfolios_beme_inv_5x5_daily, 25_portfolios_op_inv_5x5, 25_portfolios_op_inv_5x5_wout_div, 25_portfolios_op_inv_5x5_daily, 32_portfolios_me_beme_op_2x4x4, 32_portfolios_me_beme_op_2x4x4_wout_div, 32_portfolios_me_beme_inv_2x4x4, 32_portfolios_me_beme_inv_2x4x4_wout_div, 32_portfolios_me_op_inv_2x4x4, 32_portfolios_me_op_inv_2x4x4_wout_div, portfolios_formed_on_e-p, portfolios_formed_on_e-p_wout_div, portfolios_formed_on_cf-p, portfolios_formed_on_cf-p_wout_div, portfolios_formed_on_d-p, portfolios_formed_on_d-p_wout_div, 6_portfolios_me_ep_2x3, 6_portfolios_me_ep_2x3_wout_div, 6_portfolios_me_cfp_2x3, 6_portfolios_me_cfp_2x3_wout_div, 6_portfolios_me_dp_2x3, 6_portfolios_me_dp_2x3_wout_div, 6_portfolios_me_prior_12_2, 6_portfolios_me_prior_12_2_daily, 25_portfolios_me_prior_12_2, 25_portfolios_me_prior_12_2_daily, 10_portfolios_prior_12_2, 10_portfolios_prior_12_2_daily, 6_portfolios_me_prior_1_0, 6_portfolios_me_prior_1_0_daily, 25_portfolios_me_prior_1_0, 25_portfolios_me_prior_1_0_daily, 10_portfolios_prior_1_0, 10_portfolios_prior_1_0_daily, 6_portfolios_me_prior_60_13, 6_portfolios_me_prior_60_13_daily, 25_portfolios_me_prior_60_13, 25_portfolios_me_prior_60_13_daily, 10_portfolios_prior_60_13, 10_portfolios_prior_60_13_daily, portfolios_formed_on_ac, 25_portfolios_me_ac_5x5, portfolios_formed_on_beta, 25_portfolios_me_beta_5x5, portfolios_formed_on_ni, 25_portfolios_me_ni_5x5, portfolios_formed_on_var, 25_portfolios_me_var_5x5, portfolios_formed_on_resvar, 25_portfolios_me_resvar_5x5, 5_industry_portfolios, 5_industry_portfolios_wout_div, 5_industry_portfolios_daily, 10_industry_portfolios, 10_industry_portfolios_wout_div, 10_industry_portfolios_daily, 12_industry_portfolios, 12_industry_portfolios_wout_div, 12_industry_portfolios_daily, 17_industry_portfolios, 17_industry_portfolios_wout_div, 17_industry_portfolios_daily, 30_industry_portfolios, 30_industry_portfolios_wout_div, 30_industry_portfolios_daily, 38_industry_portfolios, 38_industry_portfolios_wout_div, 38_industry_portfolios_daily, 48_industry_portfolios, 48_industry_portfolios_wout_div, 48_industry_portfolios_daily, 49_industry_portfolios, 49_industry_portfolios_wout_div, 49_industry_portfolios_daily The specific portfolio file to fetch. |
| `measure` | `no` | `string` | `value` | The measure to fetch for the portfolio. |
| `frequency` | `no` | `string` | `monthly` | The frequency of the data to fetch. Ignored if the portfolio ends with 'daily' or 'weekly'. |
| `start_date` | `no` | `string | null` | `-` | The start date for the data. Defaults to the earliest available date. |
| `end_date` | `no` | `string | null` | `-` | The end date for the data. Defaults to the latest available date. |
