# Fixedincome Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`fixedincome.bond_indices`](#fixedincomebond-indices)
- [`fixedincome.corporate.bond_prices`](#fixedincomecorporatebond-prices)
- [`fixedincome.corporate.commercial_paper`](#fixedincomecorporatecommercial-paper)
- [`fixedincome.corporate.hqm`](#fixedincomecorporatehqm)
- [`fixedincome.corporate.spot_rates`](#fixedincomecorporatespot-rates)
- [`fixedincome.government.svensson_yield_curve`](#fixedincomegovernmentsvensson-yield-curve)
- [`fixedincome.government.tips_yields`](#fixedincomegovernmenttips-yields)
- [`fixedincome.government.treasury_auctions`](#fixedincomegovernmenttreasury-auctions)
- [`fixedincome.government.treasury_prices`](#fixedincomegovernmenttreasury-prices)
- [`fixedincome.government.treasury_rates`](#fixedincomegovernmenttreasury-rates)
- [`fixedincome.government.yield_curve`](#fixedincomegovernmentyield-curve)
- [`fixedincome.mortgage_indices`](#fixedincomemortgage-indices)
- [`fixedincome.rate.ameribor`](#fixedincomerateameribor)
- [`fixedincome.rate.dpcredit`](#fixedincomeratedpcredit)
- [`fixedincome.rate.ecb`](#fixedincomerateecb)
- [`fixedincome.rate.effr`](#fixedincomerateeffr)
- [`fixedincome.rate.effr_forecast`](#fixedincomerateeffr-forecast)
- [`fixedincome.rate.estr`](#fixedincomerateestr)
- [`fixedincome.rate.iorb`](#fixedincomerateiorb)
- [`fixedincome.rate.overnight_bank_funding`](#fixedincomerateovernight-bank-funding)
- [`fixedincome.rate.sofr`](#fixedincomeratesofr)
- [`fixedincome.rate.sonia`](#fixedincomeratesonia)
- [`fixedincome.spreads.tcm`](#fixedincomespreadstcm)
- [`fixedincome.spreads.tcm_effr`](#fixedincomespreadstcm-effr)
- [`fixedincome.spreads.treasury_effr`](#fixedincomespreadstreasury-effr)

## Endpoint reference

### `fixedincome.bond_indices`

```python
data.fixedincome.bond_indices(start_time=None, end_time=None, index_type='yield', category='us', index='yield_curve', frequency=None, aggregation_method='avg', transform=None)
```

Summary: Bond Indices

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.bond_indices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/bond_indices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Use `index_type="oas"` for option-adjusted spread series. For credit-spread strategies, use `category="us", index="corporate"` as the Investment Grade OAS proxy and `category="high_yield", index="us"` as the High Yield OAS proxy. This endpoint does not expose exact CDX IG/HY series names; do not label OAS proxy data as exact CDX data. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `index_type` | `no` | `string` | `yield` | The type of series. OAS is the option-adjusted spread. Default is yield. |
| `category` | `no` | `string` | `us` | The type of index category. Used in conjunction with 'index', default is 'us'. |
| `index` | `no` | `string` | `yield_curve` | The specific index to query. Used in conjunction with 'category' and 'index_type', default is 'yield_curve'. Possible values are: corporate seasoned_corporate liquid_corporate yield_curve crossover public_sector private_sector non_financial high_grade high_yield liquid_emea emea liquid_asia asia liquid_latam latam liquid_aaa liquid_bbb aaa aa a bbb bb b ccc Multiple comma separated items allowed. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert daily data to lower frequency. None = No change a = Annual q = Quarterly m = Monthly w = Weekly d = Daily wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string` | `avg` | A key that indicates the aggregation method used for frequency aggregation. This parameter has no affect if the frequency parameter is not set, default is 'avg'. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `value` | `number` | Index values. |
| `maturity` | `string` | The maturity range of the bond index. Only applicable when 'index' is 'yield_curve'. |
| `title` | `string` | The title of the index. |

---

### `fixedincome.corporate.bond_prices`

```python
data.fixedincome.corporate.bond_prices(country=None, issuer_name=None, isin=None, lei=None, currency=None, coupon_min=None, coupon_max=None, issued_amount_min=None, issued_amount_max=None, maturity_date_min=None, maturity_date_max=None, issue_date_min=None, issue_date_max=None, last_traded_min=None, use_cache=True)
```

Summary: Bond Prices

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.corporate.bond_prices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/corporate/bond_prices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `country` | `no` | `string | null` | `-` | The country to get data. Matches partial name. |
| `issuer_name` | `no` | `string | null` | `-` | Name of the issuer. Returns partial matches and is case insensitive. |
| `isin` | `no` | `array | string | null` | `-` | accepts array values International Securities Identification Number(s) of the bond(s). Multiple comma separated items allowed |
| `lei` | `no` | `string | null` | `-` | Legal Entity Identifier of the issuing entity. |
| `currency` | `no` | `array | string | null` | `-` | accepts array values Currency of the bond. Formatted as the 3-letter ISO 4217 code (e.g. GBP, EUR, USD). |
| `coupon_min` | `no` | `number | null` | `-` | Minimum coupon rate of the bond. |
| `coupon_max` | `no` | `number | null` | `-` | Maximum coupon rate of the bond. |
| `issued_amount_min` | `no` | `integer | null` | `-` | Minimum issued amount of the bond. |
| `issued_amount_max` | `no` | `string | null` | `-` | Maximum issued amount of the bond. |
| `maturity_date_min` | `no` | `string | null` | `-` | Minimum maturity date of the bond. |
| `maturity_date_max` | `no` | `string | null` | `-` | Maximum maturity date of the bond. |
| `issue_date_min` | `no` | `string | null` | `-` | Filter by the minimum original issue date. |
| `issue_date_max` | `no` | `string | null` | `-` | Filter by the maximum original issue date. |
| `last_traded_min` | `no` | `string | null` | `-` | Filter by the minimum last trade date. |
| `use_cache` | `no` | `boolean` | `true` | All bond data is sourced from a single JSON file that is updated daily. The file is cached for one day to eliminate downloading more than once. Caching will significantly speed up subsequent queries. To bypass, set to False. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `isin` | `string` | International Securities Identification Number of the bond. |
| `lei` | `string` | Legal Entity Identifier of the issuing entity. |
| `figi` | `string` | FIGI of the bond. |
| `cusip` | `string` | CUSIP of the bond. |
| `coupon_rate` | `number` | Coupon rate of the bond. |
| `ytm` | `number` | Yield to maturity (YTM) is the rate of return anticipated on a bond if it is held until the maturity date. |
| `price` | `number` | The last price for the bond. |
| `highest_price` | `number` | The highest price for the bond on the last traded date. |
| `lowest_price` | `number` | The lowest price for the bond on the last traded date. |
| `total_trades` | `integer` | Total number of trades on the last traded date. |
| `last_traded_date` | `string` | Last traded date of the bond. |
| `maturity_date` | `string` | Maturity date of the bond. |
| `issue_date` | `string` | Issue date of the bond. This is the date when the bond first accrues interest. |
| `issuer_name` | `string` | Name of the issuing entity. |

---

### `fixedincome.corporate.commercial_paper`

```python
data.fixedincome.corporate.commercial_paper(start_time=None, end_time=None, maturity='all', category='all', frequency=None, aggregation_method=None, transform=None)
```

Summary: Commercial Paper

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.corporate.commercial_paper` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/corporate/commercial_paper` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `maturity` | `no` | `string` | `all` | A target maturity. Multiple comma separated items allowed. |
| `category` | `no` | `string` | `all` | The category of asset. Multiple comma separated items allowed. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert daily data to lower frequency. a = Annual q = Quarterly m = Monthly w = Weekly wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `maturity` | `string` | Maturity length of the item. |
| `rate` | `number` | Interest rate. |
| `title` | `string` | Title of the series. |
| `asset_type` | `string` | The category of asset. |

---

### `fixedincome.corporate.hqm`

```python
data.fixedincome.corporate.hqm(date=None, yield_curve='spot')
```

Summary: Hqm

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.corporate.hqm` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/corporate/hqm` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `date` | `no` | `string | null` | `-` | A specific date to get data for. Multiple comma separated items allowed |
| `yield_curve` | `no` | `string` | `spot` | The yield curve type. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | Interest rate. |
| `maturity` | `string` | Maturity. |

---

### `fixedincome.corporate.spot_rates`

```python
data.fixedincome.corporate.spot_rates(start_time=None, end_time=None, maturity=10.0, category='spot_rate')
```

Summary: Spot Rates

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.corporate.spot_rates` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/corporate/spot_rates` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `maturity` | `no` | `number | string` | `10.0` | Maturities in years. Multiple comma separated items allowed |
| `category` | `no` | `string` | `spot_rate` | Rate category. Options: spot_rate, par_yield. Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | Spot Rate. |

---

### `fixedincome.government.svensson_yield_curve`

```python
data.fixedincome.government.svensson_yield_curve(series_type='all', start_date=None, end_date=None)
```

Summary: Svensson Yield Curve

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.government.svensson_yield_curve` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/government/svensson_yield_curve` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `series_type` | `no` | `string` | `all` | Type of yield curve series to return. Accepts a single value or comma-separated list for multiple selections. Group options: - 'all' (default) - 'zero_coupon' (SVENY, continuously compounded) - 'par_yield'(SVENPY, coupon-equivalent) - 'forward_instantaneous' (SVENF, continuously compounded) - 'forward_1y' (SVEN1F, coupon-equivalent) - 'parameters' (BETA0-BETA3, TAU1-TAU2) Individual columns can also be specified (e.g., 'sveny10,sveny20,beta0'). Used to filter columns after fetching. Multiple comma separated items allowed. |
| `start_date` | `no` | `string | null` | `-` | Start date of the data, in YYYY-MM-DD format. Used to filter results after fetching. |
| `end_date` | `no` | `string | null` | `-` | End date of the data, in YYYY-MM-DD format. Used to filter results after fetching. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `beta0` | `number` | Level component of the Nelson-Siegel-Svensson model. Represents the long-term asymptotic yield. |
| `beta1` | `number` | Slope component of the Nelson-Siegel-Svensson model. Represents the short-term component. |
| `beta2` | `number` | First curvature component of the Nelson-Siegel-Svensson model. Represents the medium-term component. |
| `beta3` | `number` | Second curvature component of the Nelson-Siegel-Svensson model. Provides additional flexibility for fitting the yield curve. |
| `tau1` | `number` | First decay factor of the Nelson-Siegel-Svensson model. Controls the rate of decay for beta1 and beta2 components. |
| `tau2` | `number` | Second decay factor of the Nelson-Siegel-Svensson model. Controls the rate of decay for the beta3 component. |
| `sven1f01` | `number` | One-year forward rate starting 1 year ahead, coupon-equivalent. |
| `sven1f04` | `number` | One-year forward rate starting 4 years ahead, coupon-equivalent. |
| `sven1f09` | `number` | One-year forward rate starting 9 years ahead, coupon-equivalent. |
| `svenf01` | `number` | Instantaneous forward rate at 1-year horizon, continuously compounded. |
| `svenf02` | `number` | Instantaneous forward rate at 2-year horizon, continuously compounded. |
| `svenf03` | `number` | Instantaneous forward rate at 3-year horizon, continuously compounded. |
| `svenf04` | `number` | Instantaneous forward rate at 4-year horizon, continuously compounded. |
| `svenf05` | `number` | Instantaneous forward rate at 5-year horizon, continuously compounded. |
| `svenf06` | `number` | Instantaneous forward rate at 6-year horizon, continuously compounded. |
| `svenf07` | `number` | Instantaneous forward rate at 7-year horizon, continuously compounded. |
| `svenf08` | `number` | Instantaneous forward rate at 8-year horizon, continuously compounded. |
| `svenf09` | `number` | Instantaneous forward rate at 9-year horizon, continuously compounded. |
| `svenf10` | `number` | Instantaneous forward rate at 10-year horizon, continuously compounded. |
| `svenf11` | `number` | Instantaneous forward rate at 11-year horizon, continuously compounded. |
| `svenf12` | `number` | Instantaneous forward rate at 12-year horizon, continuously compounded. |
| `svenf13` | `number` | Instantaneous forward rate at 13-year horizon, continuously compounded. |
| `svenf14` | `number` | Instantaneous forward rate at 14-year horizon, continuously compounded. |
| `svenf15` | `number` | Instantaneous forward rate at 15-year horizon, continuously compounded. |
| `svenf16` | `number` | Instantaneous forward rate at 16-year horizon, continuously compounded. |
| `svenf17` | `number` | Instantaneous forward rate at 17-year horizon, continuously compounded. |
| `svenf18` | `number` | Instantaneous forward rate at 18-year horizon, continuously compounded. |
| `svenf19` | `number` | Instantaneous forward rate at 19-year horizon, continuously compounded. |
| `svenf20` | `number` | Instantaneous forward rate at 20-year horizon, continuously compounded. |
| `svenf21` | `number` | Instantaneous forward rate at 21-year horizon, continuously compounded. |
| `svenf22` | `number` | Instantaneous forward rate at 22-year horizon, continuously compounded. |
| `svenf23` | `number` | Instantaneous forward rate at 23-year horizon, continuously compounded. |
| `svenf24` | `number` | Instantaneous forward rate at 24-year horizon, continuously compounded. |
| `svenf25` | `number` | Instantaneous forward rate at 25-year horizon, continuously compounded. |
| `svenf26` | `number` | Instantaneous forward rate at 26-year horizon, continuously compounded. |
| `svenf27` | `number` | Instantaneous forward rate at 27-year horizon, continuously compounded. |
| `svenf28` | `number` | Instantaneous forward rate at 28-year horizon, continuously compounded. |
| `svenf29` | `number` | Instantaneous forward rate at 29-year horizon, continuously compounded. |
| `svenf30` | `number` | Instantaneous forward rate at 30-year horizon, continuously compounded. |
| `svenpy01` | `number` | Par yield at 1-year maturity, coupon-equivalent. |
| `svenpy02` | `number` | Par yield at 2-year maturity, coupon-equivalent. |
| `svenpy03` | `number` | Par yield at 3-year maturity, coupon-equivalent. |
| `svenpy04` | `number` | Par yield at 4-year maturity, coupon-equivalent. |
| `svenpy05` | `number` | Par yield at 5-year maturity, coupon-equivalent. |
| `svenpy06` | `number` | Par yield at 6-year maturity, coupon-equivalent. |
| `svenpy07` | `number` | Par yield at 7-year maturity, coupon-equivalent. |
| `svenpy08` | `number` | Par yield at 8-year maturity, coupon-equivalent. |
| `svenpy09` | `number` | Par yield at 9-year maturity, coupon-equivalent. |
| `svenpy10` | `number` | Par yield at 10-year maturity, coupon-equivalent. |
| `svenpy11` | `number` | Par yield at 11-year maturity, coupon-equivalent. |
| `svenpy12` | `number` | Par yield at 12-year maturity, coupon-equivalent. |
| `svenpy13` | `number` | Par yield at 13-year maturity, coupon-equivalent. |
| `svenpy14` | `number` | Par yield at 14-year maturity, coupon-equivalent. |
| `svenpy15` | `number` | Par yield at 15-year maturity, coupon-equivalent. |
| `svenpy16` | `number` | Par yield at 16-year maturity, coupon-equivalent. |
| `svenpy17` | `number` | Par yield at 17-year maturity, coupon-equivalent. |
| `svenpy18` | `number` | Par yield at 18-year maturity, coupon-equivalent. |
| `svenpy19` | `number` | Par yield at 19-year maturity, coupon-equivalent. |
| `svenpy20` | `number` | Par yield at 20-year maturity, coupon-equivalent. |
| `svenpy21` | `number` | Par yield at 21-year maturity, coupon-equivalent. |
| `svenpy22` | `number` | Par yield at 22-year maturity, coupon-equivalent. |
| `svenpy23` | `number` | Par yield at 23-year maturity, coupon-equivalent. |
| `svenpy24` | `number` | Par yield at 24-year maturity, coupon-equivalent. |
| `svenpy25` | `number` | Par yield at 25-year maturity, coupon-equivalent. |
| `svenpy26` | `number` | Par yield at 26-year maturity, coupon-equivalent. |
| `svenpy27` | `number` | Par yield at 27-year maturity, coupon-equivalent. |
| `svenpy28` | `number` | Par yield at 28-year maturity, coupon-equivalent. |
| `svenpy29` | `number` | Par yield at 29-year maturity, coupon-equivalent. |
| `svenpy30` | `number` | Par yield at 30-year maturity, coupon-equivalent. |
| `sveny01` | `number` | Zero-coupon yield at 1-year maturity, continuously compounded. |
| `sveny02` | `number` | Zero-coupon yield at 2-year maturity, continuously compounded. |
| `sveny03` | `number` | Zero-coupon yield at 3-year maturity, continuously compounded. |
| `sveny04` | `number` | Zero-coupon yield at 4-year maturity, continuously compounded. |
| `sveny05` | `number` | Zero-coupon yield at 5-year maturity, continuously compounded. |
| `sveny06` | `number` | Zero-coupon yield at 6-year maturity, continuously compounded. |
| `sveny07` | `number` | Zero-coupon yield at 7-year maturity, continuously compounded. |
| `sveny08` | `number` | Zero-coupon yield at 8-year maturity, continuously compounded. |
| `sveny09` | `number` | Zero-coupon yield at 9-year maturity, continuously compounded. |
| `sveny10` | `number` | Zero-coupon yield at 10-year maturity, continuously compounded. |
| `sveny11` | `number` | Zero-coupon yield at 11-year maturity, continuously compounded. |
| `sveny12` | `number` | Zero-coupon yield at 12-year maturity, continuously compounded. |
| `sveny13` | `number` | Zero-coupon yield at 13-year maturity, continuously compounded. |
| `sveny14` | `number` | Zero-coupon yield at 14-year maturity, continuously compounded. |
| `sveny15` | `number` | Zero-coupon yield at 15-year maturity, continuously compounded. |
| `sveny16` | `number` | Zero-coupon yield at 16-year maturity, continuously compounded. |
| `sveny17` | `number` | Zero-coupon yield at 17-year maturity, continuously compounded. |
| `sveny18` | `number` | Zero-coupon yield at 18-year maturity, continuously compounded. |
| `sveny19` | `number` | Zero-coupon yield at 19-year maturity, continuously compounded. |
| `sveny20` | `number` | Zero-coupon yield at 20-year maturity, continuously compounded. |
| `sveny21` | `number` | Zero-coupon yield at 21-year maturity, continuously compounded. |
| `sveny22` | `number` | Zero-coupon yield at 22-year maturity, continuously compounded. |
| `sveny23` | `number` | Zero-coupon yield at 23-year maturity, continuously compounded. |
| `sveny24` | `number` | Zero-coupon yield at 24-year maturity, continuously compounded. |
| `sveny25` | `number` | Zero-coupon yield at 25-year maturity, continuously compounded. |
| `sveny26` | `number` | Zero-coupon yield at 26-year maturity, continuously compounded. |
| `sveny27` | `number` | Zero-coupon yield at 27-year maturity, continuously compounded. |
| `sveny28` | `number` | Zero-coupon yield at 28-year maturity, continuously compounded. |
| `sveny29` | `number` | Zero-coupon yield at 29-year maturity, continuously compounded. |
| `sveny30` | `number` | Zero-coupon yield at 30-year maturity, continuously compounded. |

---

### `fixedincome.government.tips_yields`

```python
data.fixedincome.government.tips_yields(start_time=None, end_time=None, maturity=None, frequency=None, aggregation_method=None, transform=None)
```

Summary: Tips Yields

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.government.tips_yields` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/government/tips_yields` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `maturity` | `no` | `string | null` | `-` | The maturity of the security in years - 5, 10, 20, 30 - defaults to all. Note that the maturity is the tenor of the security, not the time to maturity. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert high frequency data to lower frequency. None = No change a = Annual q = Quarterly m = Monthly w = Weekly d = Daily wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `due` | `string` | The due date (maturation date) of the security. |
| `name` | `string` | The name of the security. |
| `value` | `number` | The yield value. |

---

### `fixedincome.government.treasury_auctions`

```python
data.fixedincome.government.treasury_auctions(start_time=None, end_time=None, security_type=None, cusip=None, page_size=100, page_num=None)
```

Summary: Treasury Auctions

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.government.treasury_auctions` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/government/treasury_auctions` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `security_type` | `no` | `string | null` | `-` | Used to only return securities of a particular type. |
| `cusip` | `no` | `string | null` | `-` | Filter securities by CUSIP. |
| `page_size` | `no` | `integer | null` | `100` | Maximum number of results to return; you must also include pagenum when using pagesize. Max 1000. |
| `page_num` | `no` | `integer | null` | `-` | The first page number to display results for; used in combination with page size. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `cusip` | `string` | CUSIP of the Security. |
| `issue_date` | `string` | The issue date of the security. |
| `security_type` | `string` | The type of security. |
| `security_term` | `string` | The term of the security. |
| `maturity_date` | `string` | The maturity date of the security. |
| `interest_rate` | `number` | The interest rate of the security. |
| `cpi_on_issue_date` | `number` | Reference CPI rate on the issue date of the security. |
| `cpi_on_dated_date` | `number` | Reference CPI rate on the dated date of the security. |
| `announcement_date` | `string` | The announcement date of the security. |
| `auction_date` | `string` | The auction date of the security. |
| `auction_date_year` | `integer` | The auction date year of the security. |
| `dated_date` | `string` | The dated date of the security. |
| `first_payment_date` | `string` | The first payment date of the security. |
| `accrued_interest_per_100` | `number` | Accrued interest per $100. |
| `accrued_interest_per_1000` | `number` | Accrued interest per $1000. |
| `adjusted_accrued_interest_per_100` | `number` | Adjusted accrued interest per $100. |
| `adjusted_accrued_interest_per_1000` | `number` | Adjusted accrued interest per $1000. |
| `adjusted_price` | `number` | Adjusted price. |
| `allocation_percentage` | `number` | Allocation percentage, as normalized percentage points. |
| `allocation_percentage_decimals` | `number` | The number of decimals in the Allocation percentage. |
| `announced_cusip` | `string` | The announced CUSIP of the security. |
| `auction_format` | `string` | The auction format of the security. |
| `avg_median_discount_rate` | `number` | The average median discount rate of the security. |
| `avg_median_investment_rate` | `number` | The average median investment rate of the security. |
| `avg_median_price` | `number` | The average median price paid for the security. |
| `avg_median_discount_margin` | `number` | The average median discount margin of the security. |
| `avg_median_yield` | `number` | The average median yield of the security. |
| `back_dated` | `string` | Whether the security is back dated. |
| `back_dated_date` | `string` | The back dated date of the security. |
| `bid_to_cover_ratio` | `number` | The bid to cover ratio of the security. |
| `call_date` | `string` | The call date of the security. |
| `callable` | `string` | Whether the security is callable. |
| `called_date` | `string` | The called date of the security. |
| `cash_management_bill` | `string` | Whether the security is a cash management bill. |
| `closing_time_competitive` | `string` | The closing time for competitive bids on the security. |
| `closing_time_non_competitive` | `string` | The closing time for non-competitive bids on the security. |
| `competitive_accepted` | `integer` | The accepted value for competitive bids on the security. |
| `competitive_accepted_decimals` | `integer` | The number of decimals in the Competitive Accepted. |
| `competitive_tendered` | `integer` | The tendered value for competitive bids on the security. |
| `competitive_tenders_accepted` | `string` | Whether competitive tenders are accepted on the security. |
| `corp_us_cusip` | `string` | The CUSIP of the security. |
| `cpi_base_reference_period` | `string` | The CPI base reference period of the security. |
| `currently_outstanding` | `integer` | The currently outstanding value on the security. |
| `direct_bidder_accepted` | `integer` | The accepted value from direct bidders on the security. |
| `direct_bidder_tendered` | `integer` | The tendered value from direct bidders on the security. |
| `est_amount_of_publicly_held_maturing_security` | `integer` | The estimated amount of publicly held maturing securities on the security. |
| `fima_included` | `string` | Whether the security is included in the FIMA. |
| `fima_non_competitive_accepted` | `integer` | The non-competitive accepted value on the security from FIMAs. |
| `fima_non_competitive_tendered` | `integer` | The non-competitive tendered value on the security from FIMAs. |
| `first_interest_period` | `string` | The first interest period of the security. |
| `first_interest_payment_date` | `string` | The first interest payment date of the security. |
| `floating_rate` | `string` | Whether the security is a floating rate. |
| `frn_index_determination_date` | `string` | The FRN index determination date of the security. |
| `frn_index_determination_rate` | `number` | The FRN index determination rate of the security. |
| `high_discount_rate` | `number` | The high discount rate of the security. |
| `high_investment_rate` | `number` | The high investment rate of the security. |
| `high_price` | `number` | The high price of the security at auction. |
| `high_discount_margin` | `number` | The high discount margin of the security. |
| `high_yield` | `number` | The high yield of the security at auction. |
| `index_ratio_on_issue_date` | `number` | The index ratio on the issue date of the security. |
| `indirect_bidder_accepted` | `integer` | The accepted value from indirect bidders on the security. |
| `indirect_bidder_tendered` | `integer` | The tendered value from indirect bidders on the security. |
| `interest_payment_frequency` | `string` | The interest payment frequency of the security. |
| `low_discount_rate` | `number` | The low discount rate of the security. |
| `low_investment_rate` | `number` | The low investment rate of the security. |
| `low_price` | `number` | The low price of the security at auction. |
| `low_discount_margin` | `number` | The low discount margin of the security. |
| `low_yield` | `number` | The low yield of the security at auction. |
| `maturing_date` | `string` | The maturing date of the security. |
| `max_competitive_award` | `integer` | The maximum competitive award at auction. |
| `max_non_competitive_award` | `integer` | The maximum non-competitive award at auction. |
| `max_single_bid` | `integer` | The maximum single bid at auction. |
| `min_bid_amount` | `integer` | The minimum bid amount at auction. |
| `min_strip_amount` | `integer` | The minimum strip amount at auction. |
| `min_to_issue` | `integer` | The minimum to issue at auction. |
| `multiples_to_bid` | `integer` | The multiples to bid at auction. |
| `multiples_to_issue` | `integer` | The multiples to issue at auction. |
| `nlp_exclusion_amount` | `integer` | The NLP exclusion amount at auction. |
| `nlp_reporting_threshold` | `integer` | The NLP reporting threshold at auction. |
| `non_competitive_accepted` | `integer` | The accepted value from non-competitive bidders on the security. |
| `non_competitive_tenders_accepted` | `string` | Whether or not the auction accepted non-competitive tenders. |
| `offering_amount` | `integer` | The offering amount at auction. |
| `original_cusip` | `string` | The original CUSIP of the security. |
| `original_dated_date` | `string` | The original dated date of the security. |
| `original_issue_date` | `string` | The original issue date of the security. |
| `original_security_term` | `string` | The original term of the security. |
| `pdf_announcement` | `string` | The PDF filename for the announcement of the security. |
| `pdf_competitive_results` | `string` | The PDF filename for the competitive results of the security. |
| `pdf_non_competitive_results` | `string` | The PDF filename for the non-competitive results of the security. |
| `pdf_special_announcement` | `string` | The PDF filename for the special announcements. |
| `price_per_100` | `number` | The price per 100 of the security. |
| `primary_dealer_accepted` | `integer` | The primary dealer accepted value on the security. |
| `primary_dealer_tendered` | `integer` | The primary dealer tendered value on the security. |
| `reopening` | `string` | Whether or not the auction was reopened. |
| `security_term_day_month` | `string` | The security term in days or months. |
| `security_term_week_year` | `string` | The security term in weeks or years. |
| `series` | `string` | The series name of the security. |
| `soma_accepted` | `integer` | The SOMA accepted value on the security. |
| `soma_holdings` | `integer` | The SOMA holdings on the security. |
| `soma_included` | `string` | Whether or not the SOMA was included on the security. |
| `soma_tendered` | `integer` | The SOMA tendered value on the security. |
| `spread` | `number` | The spread on the security. |
| `standard_payment_per_1000` | `number` | The standard payment per 1000 of the security. |
| `strippable` | `string` | Whether or not the security is strippable. |
| `term` | `string` | The term of the security. |
| `tiin_conversion_factor_per_1000` | `number` | The TIIN conversion factor per 1000 of the security. |
| `tips` | `string` | Whether or not the security is TIPS. |
| `total_accepted` | `integer` | The total accepted value at auction. |
| `total_tendered` | `integer` | The total tendered value at auction. |
| `treasury_retail_accepted` | `integer` | The accepted value on the security from retail. |
| `treasury_retail_tenders_accepted` | `string` | Whether or not the tender offers from retail are accepted. |
| `type` | `string` | The type of issuance. This might be different than the security type. |
| `unadjusted_accrued_interest_per_1000` | `number` | The unadjusted accrued interest per 1000 of the security. |
| `unadjusted_price` | `number` | The unadjusted price of the security. |
| `updated_timestamp` | `string` | The updated timestamp of the security. |
| `xml_announcement` | `string` | The XML filename for the announcement of the security. |
| `xml_competitive_results` | `string` | The XML filename for the competitive results of the security. |
| `xml_special_announcement` | `string` | The XML filename for special announcements. |
| `tint_cusip_1` | `string` | Tint CUSIP 1. |
| `tint_cusip_2` | `string` | Tint CUSIP 2. |

---

### `fixedincome.government.treasury_prices`

```python
data.fixedincome.government.treasury_prices(date=None, cusip=None, security_type=None, govt_type='federal', issue_date_min=None, issue_date_max=None, last_traded_min=None, maturity_date_min=None, maturity_date_max=None, use_cache=True)
```

Summary: Treasury Prices

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.government.treasury_prices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/government/treasury_prices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `date` | `no` | `string | null` | `-` | A specific date to get data for. Defaults to the last business day. |
| `cusip` | `no` | `string | null` | `-` | Filter by CUSIP. |
| `security_type` | `no` | `string | null` | `-` | Filter by security type. |
| `govt_type` | `no` | `string` | `federal` | enum: federal, provincial, municipal The level of government issuer. |
| `issue_date_min` | `no` | `string | null` | `-` | Filter by the minimum original issue date. |
| `issue_date_max` | `no` | `string | null` | `-` | Filter by the maximum original issue date. |
| `last_traded_min` | `no` | `string | null` | `-` | Filter by the minimum last trade date. |
| `maturity_date_min` | `no` | `string | null` | `-` | Filter by the minimum maturity date. |
| `maturity_date_max` | `no` | `string | null` | `-` | Filter by the maximum maturity date. |
| `use_cache` | `no` | `boolean` | `true` | All bond data is sourced from a single JSON file that is updated daily. The file is cached for one day to eliminate downloading more than once. Caching will significantly speed up subsequent queries. To bypass, set to False. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `issuer_name` | `string` | Name of the issuing entity. |
| `cusip` | `string` | CUSIP of the security. |
| `isin` | `string` | ISIN of the security. |
| `security_type` | `string` | The type of Treasury security - i.e., Bill, Note, Bond, TIPS, FRN. |
| `issue_date` | `string` | The original issue date of the security. |
| `maturity_date` | `string` | The maturity date of the security. |
| `call_date` | `string` | The call date of the security. |
| `bid` | `number` | The bid price of the security. |
| `offer` | `number` | The offer price of the security. |
| `eod_price` | `number` | The end-of-day price of the security. |
| `last_traded_date` | `string` | The last trade date of the security. |
| `total_trades` | `integer` | Total number of trades on the last traded date. |
| `last_price` | `number` | The last price of the security. |
| `highest_price` | `number` | The highest price for the bond on the last traded date. |
| `lowest_price` | `number` | The lowest price for the bond on the last traded date. |
| `rate` | `number` | The annualized interest rate or coupon of the security. |
| `ytm` | `number` | Yield to maturity (YTM) is the rate of return anticipated on a bond if it is held until the maturity date. |

---

### `fixedincome.government.treasury_rates`

```python
data.fixedincome.government.treasury_rates(start_time=None, end_time=None)
```

Summary: Treasury Rates

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.government.treasury_rates` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/government/treasury_rates` |
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
| `week_4` | `number` | 4 week Treasury bills rate (secondary market). |
| `month_1` | `number` | 1 month Treasury rate. |
| `month_2` | `number` | 2 month Treasury rate. |
| `month_3` | `number` | 3 month Treasury rate. |
| `month_6` | `number` | 6 month Treasury rate. |
| `year_1` | `number` | 1 year Treasury rate. |
| `year_2` | `number` | 2 year Treasury rate. |
| `year_3` | `number` | 3 year Treasury rate. |
| `year_5` | `number` | 5 year Treasury rate. |
| `year_7` | `number` | 7 year Treasury rate. |
| `year_10` | `number` | 10 year Treasury rate. |
| `year_20` | `number` | 20 year Treasury rate. |
| `year_30` | `number` | 30 year Treasury rate. |

---

### `fixedincome.government.yield_curve`

```python
data.fixedincome.government.yield_curve(date=None, rating='aaa', yield_curve_type='spot_rate', use_cache=True, country='united_states')
```

Summary: Yield Curve

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.government.yield_curve` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/government/yield_curve` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `date` | `no` | `string | null` | `-` | A specific date to get data for. By default is the current data. Multiple comma separated items allowed |
| `rating` | `no` | `string` | `aaa` | enum: aaa, all_ratings The rating type, either 'aaa' or 'all_ratings'. |
| `yield_curve_type` | `no` | `string` | `spot_rate` | The yield curve type.; Yield curve type. Nominal and Real Rates are available daily, others are monthly. The closest date to the requested date will be returned. |
| `use_cache` | `no` | `boolean` | `true` | If true, cache the request for four hours. |
| `country` | `no` | `string` | `united_states` | The country to get data. New Zealand, Mexico, Singapore, and Thailand have only monthly data. The nearest date to the requested one will be used. Multiple comma separated items allowed. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `maturity` | `string` | Maturity length of the security. |
| `maturity_years` | `number` | Maturity length, in years, as a decimal. |

---

### `fixedincome.mortgage_indices`

```python
data.fixedincome.mortgage_indices(start_time=None, end_time=None, index='primary', frequency=None, aggregation_method='avg', transform=None)
```

Summary: Mortgage Indices

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.mortgage_indices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/mortgage_indices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `index` | `no` | `string` | `primary` | The specific index, or index group, to query. Default is the 'primary' group. Multiple comma separated items allowed. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert daily data to lower frequency. None = No change a = Annual q = Quarterly m = Monthly w = Weekly d = Daily wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string` | `avg` | A key that indicates the aggregation method used for frequency aggregation. This parameter has no affect if the frequency parameter is not set, default is 'avg'. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the index. |
| `rate` | `number` | Mortgage rate. |

---

### `fixedincome.rate.ameribor`

```python
data.fixedincome.rate.ameribor(start_time=None, end_time=None, maturity='all', frequency=None, aggregation_method=None, transform=None)
```

Summary: Ameribor

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.ameribor` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/ameribor` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `maturity` | `no` | `string` | `all` | Period of AMERIBOR rate. Multiple comma separated items allowed. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert daily data to lower frequency. a = Annual q = Quarterly m = Monthly w = Weekly wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `maturity` | `string` | Maturity length of the item. |
| `rate` | `number` | Interest rate. |
| `title` | `string` | Title of the series. |

---

### `fixedincome.rate.dpcredit`

```python
data.fixedincome.rate.dpcredit(start_time=None, end_time=None, parameter='daily_excl_weekend')
```

Summary: Dpcredit

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.dpcredit` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/dpcredit` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `parameter` | `no` | `string` | `daily_excl_weekend` | FRED series ID of DWPCR data. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | Discount Window Primary Credit Rate. |

---

### `fixedincome.rate.ecb`

```python
data.fixedincome.rate.ecb(start_time=None, end_time=None, interest_rate_type='lending')
```

Summary: Ecb

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.ecb` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/ecb` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `interest_rate_type` | `no` | `string` | `lending` | The type of interest rate. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | European Central Bank Interest Rate. |

---

### `fixedincome.rate.effr`

```python
data.fixedincome.rate.effr(start_time=None, end_time=None, frequency=None, aggregation_method=None, transform=None, effr_only=False)
```

Summary: Effr

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.effr` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/effr` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert daily data to lower frequency. a = Annual q = Quarterly m = Monthly w = Weekly wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |
| `effr_only` | `no` | `boolean` | `false` | Return data without quantiles, target ranges, and volume. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | Effective federal funds rate. |
| `target_range_upper` | `number` | Upper bound of the target range. |
| `target_range_lower` | `number` | Lower bound of the target range. |
| `percentile_1` | `number` | 1st percentile of the distribution. |
| `percentile_25` | `number` | 25th percentile of the distribution. |
| `percentile_75` | `number` | 75th percentile of the distribution. |
| `percentile_99` | `number` | 99th percentile of the distribution. |
| `volume` | `number` | The trading volume. The notional volume of transactions (Billions of $). |
| `intraday_low` | `number` | Intraday low. This field is only present for data before 2016. |
| `intraday_high` | `number` | Intraday high. This field is only present for data before 2016. |
| `standard_deviation` | `number` | Standard deviation. This field is only present for data before 2016. |
| `revision_indicator` | `string` | Indicates a revision of the data for that date. |

---

### `fixedincome.rate.effr_forecast`

```python
data.fixedincome.rate.effr_forecast(long_run=False)
```

Summary: Effr Forecast

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.effr_forecast` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/effr_forecast` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `long_run` | `no` | `boolean` | `false` | Flag to show long run projections |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `range_high` | `number` | High projection of rates. |
| `central_tendency_high` | `number` | Central tendency of high projection of rates. |
| `median` | `number` | Median projection of rates. |
| `range_midpoint` | `number` | Midpoint projection of rates. |
| `central_tendency_midpoint` | `number` | Central tendency of midpoint projection of rates. |
| `range_low` | `number` | Low projection of rates. |
| `central_tendency_low` | `number` | Central tendency of low projection of rates. |

---

### `fixedincome.rate.estr`

```python
data.fixedincome.rate.estr(start_time=None, end_time=None, frequency=None, aggregation_method=None, transform=None)
```

Summary: Estr

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.estr` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/estr` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert daily data to lower frequency. a = Annual q = Quarterly m = Monthly w = Weekly d = Daily wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | Volume-weighted trimmed mean rate. |
| `percentile_25` | `number` | Rate at 25th percentile of volume. |
| `percentile_75` | `number` | Rate at 75th percentile of volume. |
| `volume` | `number` | The trading volume. (Millions of EUR). |
| `transactions` | `integer` | Number of transactions. |
| `number_of_banks` | `integer` | Number of active banks. |
| `large_bank_share_of_volume` | `number` | The percent of volume attributable to the 5 largest active banks. |

---

### `fixedincome.rate.iorb`

```python
data.fixedincome.rate.iorb(start_time=None, end_time=None)
```

Summary: Iorb

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.iorb` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/iorb` |
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
| `rate` | `number` | IORB rate. |

---

### `fixedincome.rate.overnight_bank_funding`

```python
data.fixedincome.rate.overnight_bank_funding(start_time=None, end_time=None, frequency=None, aggregation_method=None, transform=None)
```

Summary: Overnight Bank Funding

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.overnight_bank_funding` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/overnight_bank_funding` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert daily data to lower frequency. a = Annual q = Quarterly m = Monthly w = Weekly wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | Overnight Bank Funding Rate. |
| `percentile_1` | `number` | 1st percentile of the distribution. |
| `percentile_25` | `number` | 25th percentile of the distribution. |
| `percentile_75` | `number` | 75th percentile of the distribution. |
| `percentile_99` | `number` | 99th percentile of the distribution. |
| `volume` | `number` | The trading volume. The notional volume of transactions (Billions of $). |
| `revision_indicator` | `string` | Indicates a revision of the data for that date. |

---

### `fixedincome.rate.sofr`

```python
data.fixedincome.rate.sofr(start_time=None, end_time=None, frequency=None, aggregation_method=None, transform=None)
```

Summary: Sofr

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.sofr` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/sofr` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert daily data to lower frequency. a = Annual q = Quarterly m = Monthly w = Weekly wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string | null` | `-` | A key that indicates the aggregation method used for frequency aggregation. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | Effective federal funds rate. |
| `percentile_1` | `number` | 1st percentile of the distribution. |
| `percentile_25` | `number` | 25th percentile of the distribution. |
| `percentile_75` | `number` | 75th percentile of the distribution. |
| `percentile_99` | `number` | 99th percentile of the distribution. |
| `volume` | `number` | The trading volume. The notional volume of transactions (Billions of $). |
| `average_30d` | `number` | 30-Day Average SOFR. |
| `average_90d` | `number` | 90-Day Average SOFR. |
| `average_180d` | `number` | 180-Day Average SOFR. |
| `index` | `number` | SOFR index as 2018-04-02 = 1. |

---

### `fixedincome.rate.sonia`

```python
data.fixedincome.rate.sonia(start_time=None, end_time=None, parameter='rate')
```

Summary: Sonia

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.rate.sonia` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/rate/sonia` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `parameter` | `no` | `string` | `rate` | Period of SONIA rate. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | SONIA rate. |

---

### `fixedincome.spreads.tcm`

```python
data.fixedincome.spreads.tcm(start_time=None, end_time=None, maturity='3m')
```

Summary: Tcm

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.spreads.tcm` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/spreads/tcm` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `maturity` | `no` | `string | null` | `3m` | The maturity |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | TreasuryConstantMaturity Rate. |

---

### `fixedincome.spreads.tcm_effr`

```python
data.fixedincome.spreads.tcm_effr(start_time=None, end_time=None, maturity='10y')
```

Summary: Tcm Effr

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.spreads.tcm_effr` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/spreads/tcm_effr` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `maturity` | `no` | `string | null` | `10y` | The maturity |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | Selected Treasury Constant Maturity Rate. |

---

### `fixedincome.spreads.treasury_effr`

```python
data.fixedincome.spreads.treasury_effr(start_time=None, end_time=None, maturity='3m')
```

Summary: Treasury Effr

| Field | Value |
|---|---|
| Endpoint ID | `fixedincome.spreads.treasury_effr` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/fixedincome/spreads/treasury_effr` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `maturity` | `no` | `string | null` | `3m` | The maturity |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `rate` | `number` | SelectedTreasuryBill Rate. |
