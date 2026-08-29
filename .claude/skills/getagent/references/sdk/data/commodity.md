# Commodity Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`commodity.petroleum_status_report`](#commoditypetroleum-status-report)
- [`commodity.price.spot`](#commoditypricespot)
- [`commodity.psd_data`](#commoditypsd-data)
- [`commodity.psd_report`](#commoditypsd-report)
- [`commodity.short_term_energy_outlook`](#commodityshort-term-energy-outlook)
- [`commodity.weather_bulletins`](#commodityweather-bulletins)
- [`commodity.weather_bulletins_download`](#commodityweather-bulletins-download)

## Endpoint reference

### `commodity.petroleum_status_report`

```python
data.commodity.petroleum_status_report(start_time=None, end_time=None, category='balance_sheet', table=None, use_cache=True)
```

Summary: Petroleum Status Report

| Field | Value |
|---|---|
| Endpoint ID | `commodity.petroleum_status_report` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/commodity/petroleum_status_report` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `category` | `no` | `string` | `balance_sheet` | enum: balance_sheet, inputs_and_production, refiner_blender_net_production, crude_petroleum_stocks, gasoline_fuel_stocks, total_gasoline_by_sub_padd, distillate_fuel_oil_stocks, imports, imports_by_country, weekly_estimates, spot_prices_crude_gas_heating, spot_prices_diesel_jet_fuel_propane, retail_prices The group of data to be returned. The default is the balance sheet. |
| `table` | `no` | `string | null` | `-` | The specific table element within the category to be returned, default is 'stocks', if the category is 'weekly_estimates', else 'all'. Note: Choices represent all available tables from the entire collection and are not all available for every category. Invalid choices will raise a ValidationError with a message indicating the valid choices for the selected category. Choices are: all conventional_gas crude crude_production crude_production_avg diesel ethanol_plant_production ethanol_plant_production_avg exports exports_avg heating_oil imports imports_avg imports_by_country imports_by_country_avg inputs_and_utilization inputs_and_utilization_avg jet_fuel monthly net_imports_inc_spr_avg net_imports_incl_spr net_production net_production_avg net_production_by_product net_production_by_production_avg product_by_region product_by_region_avg product_supplied product_supplied_avg propane rbob refiner_blender_net_production refiner_blender_net_production_avg stocks supply supply_avg ulta_low_sulfur_distillate_reclassification ulta_low_sulfur_distillate_reclassification_avg weekly Multiple comma separated items allowed. |
| `use_cache` | `no` | `boolean` | `true` | Subsequent requests for the same source data are cached for the session using ALRU cache. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `table` | `string` | Table name for the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `order` | `integer` | Presented order of the data, relative to the table. |
| `title` | `string` | Title of the data. |
| `value` | `integer` | Value of the data. |
| `unit` | `string` | Unit or scale of the data. |

---

### `commodity.price.spot`

```python
data.commodity.price.spot(start_time=None, end_time=None, commodity='all', frequency=None, aggregation_method='eop', transform=None)
```

Summary: Spot

| Field | Value |
|---|---|
| Endpoint ID | `commodity.price.spot` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/commodity/price/spot` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `commodity` | `no` | `string` | `all` | enum: wti, brent, natural_gas, jet_fuel, propane, heating_oil, diesel_gulf_coast, diesel_ny_harbor, diesel_la, gasoline_ny_harbor, gasoline_gulf_coast, rbob, all Commodity name associated with the EIA spot price commodity data, default is 'all'. |
| `frequency` | `no` | `string | null` | `-` | Frequency aggregation to convert high frequency data to lower frequency. None = No change a = Annual q = Quarterly m = Monthly w = Weekly d = Daily wef = Weekly, Ending Friday weth = Weekly, Ending Thursday wew = Weekly, Ending Wednesday wetu = Weekly, Ending Tuesday wem = Weekly, Ending Monday wesu = Weekly, Ending Sunday wesa = Weekly, Ending Saturday bwew = Biweekly, Ending Wednesday bwem = Biweekly, Ending Monday |
| `aggregation_method` | `no` | `string` | `eop` | enum: avg, sum, eop A key that indicates the aggregation method used for frequency aggregation. This parameter has no affect if the frequency parameter is not set. avg = Average sum = Sum eop = End of Period |
| `transform` | `no` | `string | null` | `-` | Transformation type None = No transformation chg = Change ch1 = Change from Year Ago pch = Percent Change pc1 = Percent Change from Year Ago pca = Compounded Annual Rate of Change cch = Continuously Compounded Rate of Change cca = Continuously Compounded Annual Rate of Change log = Natural Log |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `commodity` | `string` | Commodity name. |
| `price` | `number` | Price of the commodity. |
| `unit` | `string` | Unit of the commodity price. |

---

### `commodity.psd_data`

```python
data.commodity.psd_data(report_id='world_crop_production_summary', commodity=None, attribute=None, country=None, aggregate_regions=False, start_year=None, end_year=None)
```

Summary: Psd Data

| Field | Value |
|---|---|
| Endpoint ID | `commodity.psd_data` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/commodity/psd_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `report_id` | `no` | `string | null` | `world_crop_production_summary` | Report ID to retrieve. Gets the current report for the given commodity and subject. These are predefined tables that are part of the PDF publication data. This parameter is ignored if 'commodity' is provided. Use the 'commodity' parameter for time series data. Valid reports are: almonds_summary, almonds_supply_distribution, apples_selected_countries, apples_supply_distribution, barley_area_yield_production, barley_regional, barley_supply_disappearance, barley_world_production_consumption_stocks, barley_world_trade, beef_veal_production, beef_veal_trade, butter_production_consumption, butter_trade, cattle_stocks, cattle_trade, cheese_production_consumption, cheese_trade, cherries_selected_countries, cherries_supply_distribution, chicken_production, chicken_trade, china_grain_supply_demand, coarse_grains_area_yield_production, coarse_grains_regional, coarse_grains_world_production_consumption_stocks, coarse_grains_world_trade, coffee_arabica_production, coffee_consumption, coffee_ending_stocks, coffee_exports_green_bean, coffee_exports_soluble, coffee_exports_total, coffee_imports_green_bean, coffee_imports_soluble, coffee_imports_total, coffee_production, coffee_robusta_production, coffee_summary, coffee_summary_2, coffee_summary_3, coffee_summary_4, copra_palm_kernel_palm_oil_production, corn_area_yield_production, corn_barley_supply_demand, corn_regional, corn_supply_disappearance, corn_world_production_consumption_stocks, corn_world_trade, cotton_area_yield_production, cotton_area_yield_production_fcr, cotton_by_country, cotton_by_country_2, cotton_foreign_supply, cotton_monthly_changes, cotton_supply_distribution, cotton_supply_distribution_2, cotton_us_supply, cotton_world_supply, cotton_world_supply_use, cotton_world_supply_use_2, cottonseed_area_yield_production, eu_grain_supply_demand, grains_summary_comparison, grapefruit_selected_countries, grapes_selected_countries, grapes_supply_distribution, lemons_limes_selected_countries, milk_cow_numbers, milk_production_consumption, nonfat_dry_milk_production_consumption, nonfat_dry_milk_trade, oats_area_yield_production, oats_regional, oats_world_production_consumption_stocks, oats_world_trade, oilseeds_area_yield_production, oilseeds_china, oilseeds_eu, oilseeds_india, oilseeds_middle_east, oilseeds_products_world_supply_demand, oilseeds_southeast_asia, oilseeds_us_supply_distribution, oilseeds_world_commodity_view, oilseeds_world_country_view, orange_juice_supply_distribution, oranges_selected_countries, oranges_selected_countries_2, other_europe_grain_supply_demand, palm_coconut_fishmeal_world_supply_demand, palm_oil_world_supply, peaches_nectarines_selected_countries, peaches_nectarines_supply_distribution, peanut_area_yield_production, pears_selected_countries, pears_supply_distribution, pistachios_summary, pistachios_supply_distribution, pork_production, pork_trade, protein_meals_world_commodity_view, protein_meals_world_country_view, raisins_selected_countries, raisins_supply_distribution, rapeseed_area_yield_production, rapeseed_products_world_supply, rapeseed_products_world_supply_demand, rice_area_yield_production, rice_regional, rice_supply_demand, rice_world_production_consumption_stocks, rice_world_trade, russia_barley, russia_corn, russia_grain_supply_demand, russia_wheat, rye_area_yield_production, rye_regional, rye_world_production_consumption_stocks, rye_world_trade, sorghum_area_yield_production, sorghum_regional, sorghum_supply_disappearance, sorghum_world_production_consumption_stocks, sorghum_world_trade, soybean_meal_world_supply, soybean_oil_world_supply, soybeans_area_yield_production, soybeans_argentina_supply_distribution, soybeans_brazil_supply_distribution, soybeans_products_world_supply_demand, soybeans_products_world_trade, soybeans_us_supply_distribution, soybeans_world_supply, sugar_ending_stocks, sugar_imports_exports, sugar_production_consumption, sunflower_area_yield_production, sunflower_products_world_supply, sunflower_products_world_supply_demand, swine_stocks, swine_trade, tangerines_mandarins_selected_countries, us_grains_supply_distribution, vegetable_oils_minor_world_supply, vegetable_oils_world_commodity_view, vegetable_oils_world_country_view, walnuts_summary, walnuts_supply_distribution, wheat_area_yield_production, wheat_coarse_grains_supply_demand, wheat_coarse_grains_world_supply_demand, wheat_flour_products_world_trade, wheat_regional, wheat_supply_disappearance, wheat_world_production_consumption_stocks, whole_milk_powder_production_consumption, whole_milk_powder_trade, world_crop_production_summary |
| `commodity` | `no` | `string | null` | `-` | Commodity name to filter the data. If provided, retrieves time series data for the given commodity. Supplying both 'report_id' and 'commodity' will prioritize 'commodity' for time series data. Valid commodities are: almonds, apples, barley, beef, broiler, butter, cattle, cheese, cherries, chicken, coffee, corn, cotton, dry_whole_milk_powder, fluid_milk, grapefruit, grapes, lemons_limes, meal_copra, meal_cottonseed, meal_fish, meal_palm_kernel, meal_peanut, meal_rapeseed, meal_soybean, meal_sunflowerseed, millet, mixed_grain, nonfat_dry_milk, oats, oil_coconut, oil_cottonseed, oil_olive, oil_palm, oil_palm_kernel, oil_peanut, oil_rapeseed, oil_soybean, oil_sunflowerseed, oilseed_copra, oilseed_cottonseed, oilseed_palm_kernel, oilseed_peanut, oilseed_rapeseed, oilseed_soybean, oilseed_sunflowerseed, orange_juice, oranges, peaches_nectarines, pears, pistachios, pork, rice, rye, sorghum, sugar, swine, tangerines_mandarins, walnuts, wheat |
| `attribute` | `no` | `string | array | null` | `-` | accepts array values Attribute to filter the data. If None, retrieves all available attributes for the commodity. Parameter is ignored when commodity is None. Valid attributes depend on the commodity, an invalid choice will show the available attributes for the entered commodity. All attributes choices are: annual_pct_change_per_cap_cons, arabica_production, area_harvested, area_planted, balance, bean_exports, bean_imports, bearing_trees, beef_cows_beg_stocks, beet_sugar_production, begin_stock_ctrl_app, begin_stock_other, beginning_stocks, calf_slaughter, cane_sugar_production, catch_for_reduction, commercial_production, consumption_change, cow_change, cow_slaughter, cows_in_milk, cows_milk_production, crush, cy_exp_to_us, cy_exports, cy_imp_from_us, cy_imports, dairy_cows_beg_stocks, deliv_to_processors, dom_consump_ctrl_app, dom_consump_other, dom_leaf_consumption, domestic_consumption, domestic_use, end_stocks_ctrl_app, end_stocks_other, ending_stocks, export_change, exportable_production, exports, exports_percent_production, extr_rate, factory_use_consum, farm_sales_weight_prod, feed_dom_consumption, feed_use_dom_consum, feed_waste_dom_cons, filter_production, fluid_use_dom_consum, food_use_dom_cons, for_processing, fresh_dom_consumption, fresh_dom_consumption_alt, fsi_consumption, human_consumption, human_dom_consumption, import_change, imports, imports_percent_consumption, industrial_dom_cons, intra_eu_exports, intra_eu_exports_alt, intra_eu_imports, inventory_balance, inventory_change, inventory_reference, loss, loss_and_residual, milling_rate, my_exp_to_eu, my_imp_from_eu, my_imp_from_us, non_bearing_trees, non_comm_production, non_filter_production, other_disappearance, other_exports, other_foreign_cons, other_imports, other_milk_production, other_production, other_slaughter, other_use_losses, per_capita_consumption, population, prod_from_table_grapes, prod_from_wine_grapes, production, production_change, production_to_cows, production_to_sows, raw_exports, raw_imports, refined_exp_raw_val, refined_imp_raw_val, roast_ground_exports, roast_ground_imports, robusta_production, rough_production, rst_ground_dom_consum, seed_to_lint_ratio, slaughter_reference, slaughter_to_inventory, slaughter_to_total_supply, sme, soluble_dom_cons, soluble_exports, soluble_imports, sow_beginning_stocks, sow_change, sow_slaughter, stocks_to_use, stocks_to_use_months, total_disappearance, total_disappearance_alt, total_distribution, total_grape_crush, total_slaughter, total_supply, total_trees, total_use, total_utilization, ty_exports, ty_imp_from_us, ty_imports, us_leaf_dom_cons, us_leaf_imports, utilization_for_alcohol, utilization_for_sugar, weights, withdrawal_from_market, yield Multiple comma separated items allowed. |
| `country` | `no` | `string | array | null` | `-` | accepts array values Country code(s) to filter the data. If None, retrieves data for all countries. Parameter is ignored when commodity is None. Valid country codes include: afghanistan, albania, algeria, angola, argentina, armenia, australia, austria, azerbaijan, bahamas, bahrain, bangladesh, barbados, belarus, belgium, belize, benin, bhutan, bolivia, bosnia_and_herzegovina, botswana, brazil, brunei, bulgaria, burkina_faso, burma, burundi, cabo_verde, cambodia, cameroon, canada, caribbean, central_african_republic, central_america, chad, chile, china, colombia, comoros, congo_brazzaville, congo_kinshasa, costa_rica, cote_divoire, croatia, cuba, cyprus, czech_republic, czechia, denmark, djibouti, dominica, dominican_republic, east_asia, ecuador, egypt, el_salvador, equatorial_guinea, eritrea, estonia, eswatini, ethiopia, eu, eu_15, eu_25, european_union, fiji, finland, former_soviet_union, france, gabon, gambia, georgia, germany, ghana, greece, guatemala, guinea, guinea_bissau, guyana, haiti, honduras, hong_kong, hungary, iceland, india, indonesia, iran, iraq, ireland, israel, italy, ivory_coast, jamaica, japan, jordan, kazakhstan, kenya, kosovo, kuwait, kyrgyzstan, laos, latvia, lebanon, lesotho, liberia, libya, lithuania, luxembourg, macau, macedonia, madagascar, malawi, malaysia, maldives, mali, malta, mauritania, mauritius, mexico, middle_east, moldova, mongolia, montenegro, morocco, mozambique, myanmar, namibia, nepal, netherlands, new_caledonia, new_zealand, nicaragua, niger, nigeria, north_africa, north_america, north_korea, north_macedonia, norway, oceania, oman, other_europe, pakistan, panama, papua_new_guinea, paraguay, peru, philippines, poland, portugal, puerto_rico, qatar, reunion, romania, russia, rwanda, samoa, sao_tome_and_principe, saudi_arabia, senegal, serbia, seychelles, sierra_leone, singapore, slovakia, slovenia, solomon_islands, somalia, south_africa, south_america, south_asia, south_korea, south_sudan, southeast_asia, spain, sri_lanka, sub_saharan_africa, sudan, suriname, swaziland, sweden, switzerland, syria, taiwan, tajikistan, tanzania, thailand, togo, tonga, trinidad_and_tobago, tunisia, turkey, turkmenistan, uganda, ukraine, united_arab_emirates, united_kingdom, united_states, uruguay, uzbekistan, vanuatu, venezuela, vietnam, world, yemen, zambia, zimbabwe Multiple comma separated items allowed. |
| `aggregate_regions` | `no` | `boolean` | `false` | Whether to include regional and world aggregates in the data. Parameter is ignored when 'commodity' is None. |
| `start_year` | `no` | `integer | null` | `-` | Start year for filtering time series data. None returns from the beginning of the series. Parameter is ignored when 'commodity' is None. |
| `end_year` | `no` | `integer | null` | `-` | End year for filtering time series data. If None, returns up to the most recent year. Parameter is ignored when 'commodity' is None. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `region` | `string` | Region group category. |
| `country` | `string` | Country or area name. |
| `commodity` | `string` | Commodity name. |
| `attribute` | `string` | Name of the row value. |
| `marketing_year` | `string` | Marketing year for the commodity. |
| `value` | `number` | Value for the commodity attribute in the given marketing year. |
| `unit` | `string` | Unit of measurement for the value. |

---

### `commodity.psd_report`

```python
data.commodity.psd_report(commodity=..., year=..., month=...)
```

Summary: Psd Report

| Field | Value |
|---|---|
| Endpoint ID | `commodity.psd_report` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/commodity/psd_report` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `commodity` | `yes` | `string` | `-` | Commodity for the report. |
| `year` | `yes` | `integer` | `-` | Year of the report. |
| `month` | `yes` | `integer` | `-` | Month of the report. |

---

### `commodity.short_term_energy_outlook`

```python
data.commodity.short_term_energy_outlook(start_time=None, end_time=None, symbol=None, table='01', frequency='month')
```

Summary: Short Term Energy Outlook

| Field | Value |
|---|---|
| Endpoint ID | `commodity.short_term_energy_outlook` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/commodity/short_term_energy_outlook` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. If provided, overrides the 'table' parameter to return only the specified symbol from the STEO API. Multiple comma separated items allowed. |
| `table` | `no` | `string` | `01` | enum: 01, 02, 03a, 03b, 03c, 03d, 03e, 04a, 04b, 04c, 04d, 05a, 05b, 06, 07a, 07b, 07c, 07d1, 07d2, 07e, 08, 09a, 09b, 09c, 10a, 10b The specific table within the STEO dataset. Default is '01'. When 'symbol' is provided, this parameter is ignored. 01: US Energy Markets Summary 02: Nominal Energy Prices 03a: World Petroleum and Other Liquid Fuels Production, Consumption, and Inventories 03b: Non-OPEC Petroleum and Other Liquid Fuels Production 03c: World Petroleum and Other Liquid Fuels Production 03d: World Crude Oil Production 03e: World Petroleum and Other Liquid Fuels Consumption 04a: US Petroleum and Other Liquid Fuels Supply, Consumption, and Inventories 04b: US Hydrocarbon Gas Liquids (HGL) and Petroleum Refinery Balances 04c: US Regional Motor Gasoline Prices and Inventories 04d: US Biofuel Supply, Consumption, and Inventories 05a: US Natural Gas Supply, Consumption, and Inventories 05b: US Regional Natural Gas Prices 06: US Coal Supply, Consumption, and Inventories 07a: US Electricity Industry Overview 07b: US Regional Electricity Retail Sales 07c: US Regional Electricity Prices 07d1: US Regional Electricity Generation, Electric Power Sector 07d2: US Regional Electricity Generation, Electric Power Sector, continued 07e: US Electricity Generating Capacity 08: US Renewable Energy Consumption 09a: US Macroeconomic Indicators and CO2 Emissions 09b: US Regional Macroeconomic Data 09c: US Regional Weather Data 10a: Drilling Productivity Metrics 10b: Crude Oil and Natural Gas Production from Shale and Tight Formations |
| `frequency` | `no` | `string` | `month` | enum: month, quarter, annual The frequency of the data. Default is 'month'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `table` | `string` | Table name for the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `order` | `integer` | Presented order of the data, relative to the table. |
| `title` | `string` | Title of the data. |
| `value` | `integer` | Value of the data. |
| `unit` | `string` | Unit or scale of the data. |

---

### `commodity.weather_bulletins`

```python
data.commodity.weather_bulletins(year=2026, month=None, week=None)
```

Summary: Weather Bulletins

| Field | Value |
|---|---|
| Endpoint ID | `commodity.weather_bulletins` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/commodity/weather_bulletins` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `year` | `no` | `integer` | `2026` | Year of the data. Default is the current year. |
| `month` | `no` | `integer | null` | `-` | Month of the data. If not provided, data for the entire year is returned. |
| `week` | `no` | `integer | null` | `-` | Numeric week of the data, relative to the month. If not provided, data for the entire month is returned. |

---

### `commodity.weather_bulletins_download`

```python
data.commodity.weather_bulletins_download(, body=...)
```

Summary: Weather Bulletins Download

| Field | Value |
|---|---|
| Endpoint ID | `commodity.weather_bulletins_download` |
| HTTP | `POST` |
| Path | `/inner/v1/agent-data/commodity/weather_bulletins_download` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `body` | `yes` | `string | object | array` | `-` | URLs for reports to download. Multiple comma separated items allowed |
