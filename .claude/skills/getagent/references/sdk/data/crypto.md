# Crypto Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`crypto.asset_platforms`](#cryptoasset-platforms)
- [`crypto.categories`](#cryptocategories)
- [`crypto.coin_history`](#cryptocoin-history)
- [`crypto.coin_info`](#cryptocoin-info)
- [`crypto.coin_tickers`](#cryptocoin-tickers)
- [`crypto.defi.fees.historical`](#cryptodefifeeshistorical)
- [`crypto.defi.fees.overview`](#cryptodefifeesoverview)
- [`crypto.defi.fees.protocol_fees`](#cryptodefifeesprotocol-fees)
- [`crypto.defi.tvl.chains`](#cryptodefitvlchains)
- [`crypto.defi.tvl.historical`](#cryptodefitvlhistorical)
- [`crypto.defi.tvl.protocol_history`](#cryptodefitvlprotocol-history)
- [`crypto.defi.tvl.protocols`](#cryptodefitvlprotocols)
- [`crypto.defi.volumes.chain_volume`](#cryptodefivolumeschain-volume)
- [`crypto.defi.volumes.dex_overview`](#cryptodefivolumesdex-overview)
- [`crypto.defi.volumes.protocol_volume`](#cryptodefivolumesprotocol-volume)
- [`crypto.derivatives_tickers`](#cryptoderivatives-tickers)
- [`crypto.dex.boosted_tokens`](#cryptodexboosted-tokens)
- [`crypto.dex.latest_pairs`](#cryptodexlatest-pairs)
- [`crypto.dex.pair_details`](#cryptodexpair-details)
- [`crypto.dex.search`](#cryptodexsearch)
- [`crypto.dex.token_orders`](#cryptodextoken-orders)
- [`crypto.dex.token_pairs`](#cryptodextoken-pairs)
- [`crypto.dex.token_profiles`](#cryptodextoken-profiles)
- [`crypto.etf.flows`](#cryptoetfflows)
- [`crypto.etf.holdings`](#cryptoetfholdings)
- [`crypto.institutional.company_flow`](#cryptoinstitutionalcompany-flow)
- [`crypto.institutional.country_flow`](#cryptoinstitutionalcountry-flow)
- [`crypto.institutional.mining_company_flow`](#cryptoinstitutionalmining-company-flow)
- [`crypto.exchange_info`](#cryptoexchange-info)
- [`crypto.exchange_rates`](#cryptoexchange-rates)
- [`crypto.exchange_tickers`](#cryptoexchange-tickers)
- [`crypto.exchange_volume_chart`](#cryptoexchange-volume-chart)
- [`crypto.exchanges`](#cryptoexchanges)
- [`crypto.futures.funding_rate`](#cryptofuturesfunding-rate)
- [`crypto.futures.funding_weighted`](#cryptofuturesfunding-weighted)
- [`crypto.futures.kline`](#cryptofutureskline)
- [`crypto.futures.liquidation_aggregated_map`](#cryptofuturesliquidation-aggregated-map)
- [`crypto.futures.liquidation_heatmap`](#cryptofuturesliquidation-heatmap)
- [`crypto.futures.liquidation_max_pain`](#cryptofuturesliquidation-max-pain)
- [`crypto.futures.liquidations`](#cryptofuturesliquidations)
- [`crypto.futures.long_short_ratio`](#cryptofutureslong-short-ratio)
- [`crypto.futures.long_short_top_account_ratio`](#cryptofutureslong-short-top-account-ratio)
- [`crypto.futures.long_short_top_position_ratio`](#cryptofutureslong-short-top-position-ratio)
- [`crypto.futures.mark_price`](#cryptofuturesmark-price)
- [`crypto.futures.open_interest`](#cryptofuturesopen-interest)
- [`crypto.futures.open_interest_history`](#cryptofuturesopen-interest-history)
- [`crypto.futures.order_book`](#cryptofuturesorder-book)
- [`crypto.futures.taker_volume`](#cryptofuturestaker-volume)
- [`crypto.futures.ticker`](#cryptofuturesticker)
- [`crypto.futures.trades`](#cryptofuturestrades)
- [`crypto.global_defi`](#cryptoglobal-defi)
- [`crypto.global_market`](#cryptoglobal-market)
- [`crypto.hyperliquid.account_long_short_ratio`](#cryptohyperliquidaccount-long-short-ratio)
- [`crypto.hyperliquid.account_long_short_ratio_by_tag`](#cryptohyperliquidaccount-long-short-ratio-by-tag)
- [`crypto.hyperliquid.position_distribution_by_tag`](#cryptohyperliquidposition-distribution-by-tag)
- [`crypto.hyperliquid.symbol_position`](#cryptohyperliquidsymbol-position)
- [`crypto.hyperliquid.user_position`](#cryptohyperliquiduser-position)
- [`crypto.hyperliquid.wallet_pnl_distribution`](#cryptohyperliquidwallet-pnl-distribution)
- [`crypto.hyperliquid.wallet_position_distribution`](#cryptohyperliquidwallet-position-distribution)
- [`crypto.hyperliquid.whale_alert`](#cryptohyperliquidwhale-alert)
- [`crypto.hyperliquid.smart_money_alert`](#cryptohyperliquidsmart-money-alert)
- [`crypto.hyperliquid.whale_position`](#cryptohyperliquidwhale-position)
- [`crypto.market`](#cryptomarket)
- [`crypto.market_dominance`](#cryptomarket-dominance)
- [`crypto.nft_info`](#cryptonft-info)
- [`crypto.nft_list`](#cryptonft-list)
- [`crypto.onchain.active_addresses`](#cryptoonchainactive-addresses)
- [`crypto.onchain.dexes`](#cryptoonchaindexes)
- [`crypto.onchain.exchange_flows`](#cryptoonchainexchange-flows)
- [`crypto.onchain.stablecoin_flow`](#cryptoonchainstablecoin-flow)
- [`crypto.onchain.dex_liquidity_flow`](#cryptoonchaindex-liquidity-flow)
- [`crypto.onchain.fund_flow`](#cryptoonchainfund-flow)
- [`crypto.onchain.holder_statics`](#cryptoonchainholder-statics)
- [`crypto.onchain.hyperliquid_liquidation_map`](#cryptoonchainhyperliquid-liquidation-map)
- [`crypto.onchain.liquidity`](#cryptoonchainliquidity)
- [`crypto.onchain.networks`](#cryptoonchainnetworks)
- [`crypto.onchain.pool_detail`](#cryptoonchainpool-detail)
- [`crypto.onchain.pool_ohlcv`](#cryptoonchainpool-ohlcv)
- [`crypto.onchain.pool_trades`](#cryptoonchainpool-trades)
- [`crypto.onchain.pools`](#cryptoonchainpools)
- [`crypto.onchain.search_pools`](#cryptoonchainsearch-pools)
- [`crypto.onchain.token_data`](#cryptoonchaintoken-data)
- [`crypto.onchain.token_info`](#cryptoonchaintoken-info)
- [`crypto.onchain.token_price`](#cryptoonchaintoken-price)
- [`crypto.onchain.token_unlock_event`](#cryptoonchaintoken-unlock-event)
- [`crypto.onchain.trading_signal`](#cryptoonchaintrading-signal)
- [`crypto.onchain.whale_transactions`](#cryptoonchainwhale-transactions)
- [`crypto.options.open_interest`](#cryptooptionsopen-interest)
- [`crypto.options.volume`](#cryptooptionsvolume)
- [`crypto.search`](#cryptosearch)
- [`crypto.sentiment.crypto_fear_greed`](#cryptosentimentcrypto-fear-greed)
- [`crypto.spot.exchange_volume`](#cryptospotexchange-volume)
- [`crypto.spot.kline`](#cryptospotkline)
- [`crypto.spot.order_book`](#cryptospotorder-book)
- [`crypto.spot.price_spread`](#cryptospotprice-spread)
- [`crypto.spot.taker_volume`](#cryptospottaker-volume)
- [`crypto.spot.footprint_history`](#cryptospotfootprint-history)
- [`crypto.spot.ticker`](#cryptospotticker)
- [`crypto.spot.trades`](#cryptospottrades)
- [`crypto.supported_currencies`](#cryptosupported-currencies)
- [`crypto.token_price`](#cryptotoken-price)
- [`crypto.treasury`](#cryptotreasury)
- [`crypto.trending`](#cryptotrending)
- [`crypto.indicators.bitcoin_nupl`](#cryptoindicatorsbitcoin-nupl)
- [`crypto.indicators.bitcoin_sopr`](#cryptoindicatorsbitcoin-sopr)
- [`crypto.indicators.coinbase_premium_index`](#cryptoindicatorscoinbase-premium-index)
- [`crypto.indicators.hyperliquid_whale_sentiment`](#cryptoindicatorshyperliquid-whale-sentiment)
- [`crypto.indicators.technical_indicators`](#cryptoindicatorstechnical-indicators)
- [`crypto.exchange.big_trades`](#cryptoexchangebig-trades)
- [`crypto.exchange.trade_pressure`](#cryptoexchangetrade-pressure)

## Endpoint reference

### `crypto.asset_platforms`

```python
data.crypto.asset_platforms()
```

Summary: Asset Platforms

| Field | Value |
|---|---|
| Endpoint ID | `crypto.asset_platforms` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/asset_platforms` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `platform_id` | `string` | Platform identifier (e.g. 'ethereum', 'polygon-pos'). |
| `chain_identifier` | `integer` | EVM chain ID (e.g. 1 for Ethereum mainnet). |
| `name` | `string` | Platform display name. |
| `shortname` | `string` | Platform short name. |
| `native_coin_id` | `string` | CoinGecko ID of the native coin (e.g. 'ethereum'). |

---

### `crypto.categories`

```python
data.crypto.categories()
```

Summary: Categories

| Field | Value |
|---|---|
| Endpoint ID | `crypto.categories` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/categories` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `category_id` | `string` | Category identifier. |
| `name` | `string` | Category name. |
| `market_cap` | `number` | Total market capitalization of the category in USD. |
| `market_cap_change_24h` | `number` | 24-hour market cap change percentage. |
| `volume_24h` | `number` | 24-hour trading volume in USD. |
| `top_3_coins` | `array` | Icon URLs of the top 3 coins in this category. |

---

### `crypto.coin_history`

```python
data.crypto.coin_history(symbol=..., date=...)
```

Summary: Coin History

| Field | Value |
|---|---|
| Endpoint ID | `crypto.coin_history` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/coin_history` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Cryptocurrency ticker symbol (e.g. 'BTC'). |
| `date` | `yes` | `string` | `-` | Snapshot date in dd-mm-yyyy format (e.g. '30-12-2022'). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | CoinGecko coin identifier. |
| `symbol` | `string` | Coin ticker symbol. |
| `name` | `string` | Coin name. |
| `date` | `string` | Snapshot date in dd-mm-yyyy format. |
| `price` | `number` | Price in USD at the snapshot date. |
| `market_cap` | `number` | Market capitalization in USD. |
| `total_volume` | `number` | 24h trading volume in USD. |
| `image` | `string` | Coin thumbnail image URL. |

---

### `crypto.coin_info`

```python
data.crypto.coin_info(symbol=...)
```

Summary: Coin Info

| Field | Value |
|---|---|
| Endpoint ID | `crypto.coin_info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/coin_info` |
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
| `id` | `string` | Coin identifier. |
| `symbol` | `string` | Coin ticker symbol. |
| `name` | `string` | Coin name. |
| `description` | `string` | Coin description. |
| `homepage` | `string` | Official homepage URL. |
| `image` | `string` | Coin logo URL. |
| `market_cap_rank` | `integer` | Market capitalization rank. |
| `current_price` | `number` | Current price in USD. |
| `market_cap` | `number` | Market capitalization in USD. |
| `total_volume` | `number` | 24-hour trading volume in USD. |
| `high_24h` | `number` | 24-hour high price in USD. |
| `low_24h` | `number` | 24-hour low price in USD. |
| `price_change_24h` | `number` | Absolute price change over 24 hours. |
| `price_change_percentage_24h` | `number` | Percentage price change over 24 hours. |
| `circulating_supply` | `number` | Circulating supply. |
| `total_supply` | `number` | Total supply. |
| `max_supply` | `number` | Maximum supply. |
| `ath` | `number` | All-time high price in USD. |
| `atl` | `number` | All-time low price in USD. |
| `genesis_date` | `string` | Date the coin was first created. |
| `categories` | `array` | Categories the coin belongs to. |
| `sentiment_votes_up_percentage` | `number` | Percentage of positive sentiment votes. |
| `sentiment_votes_down_percentage` | `number` | Percentage of negative sentiment votes. |
| `coingecko_rank` | `integer` | CoinGecko popularity rank. |
| `developer_score` | `number` | Developer activity score. |
| `community_score` | `number` | Community engagement score. |
| `liquidity_score` | `number` | Liquidity score. |

---

### `crypto.coin_tickers`

```python
data.crypto.coin_tickers(symbol=...)
```

Summary: Coin Tickers

| Field | Value |
|---|---|
| Endpoint ID | `crypto.coin_tickers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/coin_tickers` |
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
| `exchange` | `string` | Exchange name. |
| `exchange_id` | `string` | Exchange identifier. |
| `base` | `string` | Base currency symbol. |
| `target` | `string` | Quote/target currency symbol. |
| `last_price` | `number` | Last traded price. |
| `volume` | `number` | 24h trading volume in base currency. |
| `bid_ask_spread_percentage` | `number` | Bid-ask spread as a percentage. |
| `trust_score` | `string` | Trust score: 'green', 'yellow', or 'red'. |
| `trade_url` | `string` | Direct URL to trade this pair. |
| `last_traded_at` | `string` | Last trade timestamp. |
| `converted_last_usd` | `number` | Last price converted to USD. |
| `converted_volume_usd` | `number` | 24h volume converted to USD. |

---

### `crypto.defi.fees.historical`

```python
data.crypto.defi.fees.historical()
```

Summary: Historical

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.fees.historical` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/fees/historical` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Date of the record. |
| `total_fees` | `number` | Total fees across all protocols in USD. |
| `daily_fees` | `number` | Daily fees in USD. |

---

### `crypto.defi.fees.overview`

```python
data.crypto.defi.fees.overview()
```

Summary: Overview

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.fees.overview` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/fees/overview` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `name` | `string` | Protocol name. |
| `disabled` | `boolean` | Whether the protocol is disabled. |
| `display_name` | `string` | Display name. |
| `module` | `string` | Module identifier. |
| `category` | `string` | Protocol category. |
| `logo` | `string` | Logo URL. |
| `chains` | `array` | Supported blockchain networks. |
| `total_24h` | `number` | Total fees in last 24 hours (USD). |
| `total_48h_to_24h` | `number` | Total fees 48h to 24h ago (USD). |
| `change_1d` | `number` | 24h fees change percentage. |
| `total_7d` | `number` | Total fees in last 7 days (USD). |
| `change_7d` | `number` | 7d fees change percentage. |
| `total_30d` | `number` | Total fees in last 30 days (USD). |
| `change_30d` | `number` | 30d fees change percentage. |

---

### `crypto.defi.fees.protocol_fees`

```python
data.crypto.defi.fees.protocol_fees(protocol=...)
```

Summary: Protocol Fees

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.fees.protocol_fees` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/fees/protocol_fees` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `protocol` | `yes` | `string` | `-` | Protocol slug identifier. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Date of the record. |
| `total_fees` | `number` | Total fees collected in USD. |
| `daily_fees` | `number` | Daily fees collected in USD. |
| `revenue` | `number` | Protocol revenue in USD. |

---

### `crypto.defi.tvl.chains`

```python
data.crypto.defi.tvl.chains(chain=None)
```

Summary: Chains

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.tvl.chains` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/tvl/chains` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `chain` | `no` | `string | null` | `-` | Specific blockchain network. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Date of the TVL record. |
| `chain` | `string` | Blockchain network identifier. |
| `tvl` | `number` | Total Value Locked in USD. |
| `token_symbol` | `string` | Native token symbol. |
| `token_price` | `number` | Native token price in USD. |

---

### `crypto.defi.tvl.historical`

```python
data.crypto.defi.tvl.historical()
```

Summary: Historical

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.tvl.historical` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/tvl/historical` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Date of the TVL record. |
| `tvl` | `number` | Total Value Locked across all protocols in USD. |

---

### `crypto.defi.tvl.protocol_history`

```python
data.crypto.defi.tvl.protocol_history(protocol=...)
```

Summary: Protocol History

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.tvl.protocol_history` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/tvl/protocol_history` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `protocol` | `yes` | `string` | `-` | Protocol slug identifier. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Date of the TVL record. |
| `tvl` | `number` | Total Value Locked in USD. |
| `chain` | `string` | Specific chain (if applicable). |

---

### `crypto.defi.tvl.protocols`

```python
data.crypto.defi.tvl.protocols()
```

Summary: Protocols

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.tvl.protocols` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/tvl/protocols` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `name` | `string` | Protocol name. |
| `slug` | `string` | Protocol slug identifier. |
| `symbol` | `string` | Protocol token symbol. |
| `category` | `string` | Protocol category. |
| `chain` | `string` | Primary blockchain network. |
| `chains` | `array` | All blockchain networks the protocol is on. |
| `tvl` | `number` | Total Value Locked in USD. |
| `change_1h` | `number` | TVL change percentage over 1 hour. |
| `change_1d` | `number` | TVL change percentage over 1 day. |
| `change_7d` | `number` | TVL change percentage over 7 days. |
| `mcap` | `number` | Market capitalization in USD. |
| `url` | `string` | Protocol website URL. |
| `logo` | `string` | Protocol logo URL. |

---

### `crypto.defi.volumes.chain_volume`

```python
data.crypto.defi.volumes.chain_volume(chain=...)
```

Summary: Chain Volume

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.volumes.chain_volume` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/volumes/chain_volume` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `chain` | `yes` | `string` | `-` | Blockchain network identifier. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Date of the record. |
| `chain` | `string` | Blockchain network. |
| `daily_volume` | `number` | Daily trading volume in USD. |
| `total_volume` | `number` | Cumulative trading volume in USD. |

---

### `crypto.defi.volumes.dex_overview`

```python
data.crypto.defi.volumes.dex_overview(exclude_total_data_chart=True, exclude_total_data_chart_breakdown=True, data_type='dailyVolume')
```

Summary: Dex Overview

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.volumes.dex_overview` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/volumes/dex_overview` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `exclude_total_data_chart` | `no` | `boolean | null` | `true` | Exclude total data chart arrays. |
| `exclude_total_data_chart_breakdown` | `no` | `boolean | null` | `true` | Exclude total data chart breakdown arrays. |
| `data_type` | `no` | `string | null` | `dailyVolume` | Data type (dailyVolume, totalVolume). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `name` | `string` | DEX protocol name. |
| `disabled` | `boolean` | Whether the DEX is disabled. |
| `display_name` | `string` | Display name. |
| `module` | `string` | Module identifier. |
| `category` | `string` | DEX category. |
| `logo` | `string` | Logo URL. |
| `chains` | `array` | Supported blockchain networks. |
| `total_24h` | `number` | Total volume in last 24 hours (USD). |
| `total_48h_to_24h` | `number` | Total volume 48h to 24h ago (USD). |
| `change_1d` | `number` | 24h volume change percentage. |
| `total_7d` | `number` | Total volume in last 7 days (USD). |
| `change_7d` | `number` | 7d volume change percentage. |
| `total_30d` | `number` | Total volume in last 30 days (USD). |
| `change_30d` | `number` | 30d volume change percentage. |

---

### `crypto.defi.volumes.protocol_volume`

```python
data.crypto.defi.volumes.protocol_volume(protocol=...)
```

Summary: Protocol Volume

| Field | Value |
|---|---|
| Endpoint ID | `crypto.defi.volumes.protocol_volume` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/defi/volumes/protocol_volume` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `protocol` | `yes` | `string` | `-` | Protocol slug identifier. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Date of the record. |
| `daily_volume` | `number` | Daily trading volume in USD. |
| `total_volume` | `number` | Cumulative trading volume in USD. |

---

### `crypto.derivatives_tickers`

```python
data.crypto.derivatives_tickers()
```

Summary: Derivatives Tickers

| Field | Value |
|---|---|
| Endpoint ID | `crypto.derivatives_tickers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/derivatives_tickers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `market` | `string` | Exchange or market name. |
| `symbol` | `string` | Contract symbol. |
| `index_id` | `string` | Index identifier. |
| `price` | `number` | Current price. |
| `price_percentage_change_24h` | `number` | 24h price change percentage. |
| `contract_type` | `string` | Contract type (e.g. 'perpetual', 'futures'). |
| `index` | `number` | Index price. |
| `basis` | `number` | Basis (futures price - index price) percentage. |
| `spread` | `number` | Bid-ask spread percentage. |
| `funding_rate` | `number` | Current funding rate. |
| `open_interest` | `number` | Open interest in USD. |
| `volume_24h` | `number` | 24h trading volume in USD. |
| `last_traded_at` | `string` | Last trade timestamp. |
| `expired_at` | `string` | Contract expiry timestamp (for dated futures). |

---

### `crypto.dex.boosted_tokens`

```python
data.crypto.dex.boosted_tokens()
```

Summary: Boosted Tokens

| Field | Value |
|---|---|
| Endpoint ID | `crypto.dex.boosted_tokens` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/dex/boosted_tokens` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `token_address` | `string` | Token contract address. |
| `chain_id` | `string` | Blockchain network identifier. |
| `description` | `string` | Token description. |
| `website_url` | `string` | Official website URL. |
| `twitter_url` | `string` | Twitter profile URL. |
| `telegram_url` | `string` | Telegram group URL. |
| `discord_url` | `string` | Discord server URL. |
| `logo_url` | `string` | Token logo image URL. |

---

### `crypto.dex.latest_pairs`

```python
data.crypto.dex.latest_pairs(query=...)
```

Summary: Latest Pairs

| Field | Value |
|---|---|
| Endpoint ID | `crypto.dex.latest_pairs` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/dex/latest_pairs` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `yes` | `string` | `-` | Search query (token name, symbol, or address). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `chain_id` | `string` | Blockchain network identifier. |
| `dex_id` | `string` | DEX platform identifier (e.g., uniswap, pancakeswap). |
| `pair_address` | `string` | Trading pair contract address. |
| `base_token_address` | `string` | Base token contract address. |
| `base_token_symbol` | `string` | Base token symbol. |
| `base_token_name` | `string` | Base token name. |
| `quote_token_address` | `string` | Quote token contract address. |
| `quote_token_symbol` | `string` | Quote token symbol. |
| `quote_token_name` | `string` | Quote token name. |
| `price_usd` | `number` | Current price in USD. |
| `volume_24h` | `number` | 24-hour trading volume in USD. |
| `liquidity_usd` | `number` | Total liquidity in USD. |
| `price_change_24h` | `number` | 24-hour price change percentage. |
| `fdv` | `number` | Fully diluted valuation in USD. |

---

### `crypto.dex.pair_details`

```python
data.crypto.dex.pair_details(chain_id=..., pair_addresses=...)
```

Summary: Pair Details

| Field | Value |
|---|---|
| Endpoint ID | `crypto.dex.pair_details` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/dex/pair_details` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `chain_id` | `yes` | `string` | `-` | Blockchain network identifier (e.g., ethereum, bsc, polygon). |
| `pair_addresses` | `yes` | `string` | `-` | Comma-separated pair addresses (max 30). Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `chain_id` | `string` | Blockchain network identifier. |
| `dex_id` | `string` | DEX platform identifier (e.g., uniswap, pancakeswap). |
| `pair_address` | `string` | Trading pair contract address. |
| `base_token_address` | `string` | Base token contract address. |
| `base_token_symbol` | `string` | Base token symbol. |
| `base_token_name` | `string` | Base token name. |
| `quote_token_address` | `string` | Quote token contract address. |
| `quote_token_symbol` | `string` | Quote token symbol. |
| `quote_token_name` | `string` | Quote token name. |
| `price_usd` | `number` | Current price in USD. |
| `price_native` | `number` | Price in native token. |
| `volume_24h` | `number` | 24-hour trading volume in USD. |
| `volume_24h_buys` | `number` | 24-hour buy volume in USD. |
| `volume_24h_sells` | `number` | 24-hour sell volume in USD. |
| `transactions_24h_buys` | `integer` | Number of buy transactions in 24 hours. |
| `transactions_24h_sells` | `integer` | Number of sell transactions in 24 hours. |
| `liquidity_usd` | `number` | Total liquidity in USD. |
| `price_change_5m` | `number` | 5-minute price change percentage. |
| `price_change_1h` | `number` | 1-hour price change percentage. |
| `price_change_6h` | `number` | 6-hour price change percentage. |
| `price_change_24h` | `number` | 24-hour price change percentage. |
| `fdv` | `number` | Fully diluted valuation in USD. |

---

### `crypto.dex.search`

```python
data.crypto.dex.search(query=...)
```

Summary: Search

| Field | Value |
|---|---|
| Endpoint ID | `crypto.dex.search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/dex/search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `yes` | `string` | `-` | Search query (token name, symbol, or address). |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `chain_id` | `string` | Blockchain network identifier. |
| `dex_id` | `string` | DEX platform identifier (e.g., uniswap, pancakeswap). |
| `pair_address` | `string` | Trading pair contract address. |
| `base_token_address` | `string` | Base token contract address. |
| `base_token_symbol` | `string` | Base token symbol. |
| `base_token_name` | `string` | Base token name. |
| `quote_token_address` | `string` | Quote token contract address. |
| `quote_token_symbol` | `string` | Quote token symbol. |
| `quote_token_name` | `string` | Quote token name. |
| `price_usd` | `number` | Current price in USD. |
| `volume_24h` | `number` | 24-hour trading volume in USD. |
| `liquidity_usd` | `number` | Total liquidity in USD. |
| `price_change_24h` | `number` | 24-hour price change percentage. |
| `fdv` | `number` | Fully diluted valuation in USD. |

---

### `crypto.dex.token_orders`

```python
data.crypto.dex.token_orders(chain_id=..., token_address=...)
```

Summary: Token Orders

| Field | Value |
|---|---|
| Endpoint ID | `crypto.dex.token_orders` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/dex/token_orders` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `chain_id` | `yes` | `string` | `-` | Blockchain network identifier (e.g., ethereum, bsc, polygon). |
| `token_address` | `yes` | `string` | `-` | Token contract address. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `order_type` | `string` | Order type: 'buy' or 'sell'. |
| `price` | `number` | Order price. |
| `amount` | `number` | Order amount. |
| `total` | `number` | Total value. |
| `timestamp` | `string` | Order timestamp. |
| `status` | `string` | Order status. |
| `chain_id` | `string` | Chain identifier. |
| `token_address` | `string` | Token address. |
| `payment_timestamp` | `integer` | Payment timestamp (ms). |

---

### `crypto.dex.token_pairs`

```python
data.crypto.dex.token_pairs(token_addresses=...)
```

Summary: Token Pairs

| Field | Value |
|---|---|
| Endpoint ID | `crypto.dex.token_pairs` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/dex/token_pairs` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `token_addresses` | `yes` | `string` | `-` | Comma-separated token addresses (max 30). Multiple comma separated items allowed |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `chain_id` | `string` | Blockchain network identifier. |
| `dex_id` | `string` | DEX platform identifier (e.g., uniswap, pancakeswap). |
| `pair_address` | `string` | Trading pair contract address. |
| `base_token_address` | `string` | Base token contract address. |
| `base_token_symbol` | `string` | Base token symbol. |
| `base_token_name` | `string` | Base token name. |
| `quote_token_address` | `string` | Quote token contract address. |
| `quote_token_symbol` | `string` | Quote token symbol. |
| `quote_token_name` | `string` | Quote token name. |
| `price_usd` | `number` | Current price in USD. |
| `volume_24h` | `number` | 24-hour trading volume in USD. |
| `liquidity_usd` | `number` | Total liquidity in USD. |
| `price_change_24h` | `number` | 24-hour price change percentage. |
| `fdv` | `number` | Fully diluted valuation in USD. |

---

### `crypto.dex.token_profiles`

```python
data.crypto.dex.token_profiles()
```

Summary: Token Profiles

| Field | Value |
|---|---|
| Endpoint ID | `crypto.dex.token_profiles` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/dex/token_profiles` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `token_address` | `string` | Token contract address. |
| `chain_id` | `string` | Blockchain network identifier. |
| `description` | `string` | Token description. |
| `website_url` | `string` | Official website URL. |
| `twitter_url` | `string` | Twitter profile URL. |
| `telegram_url` | `string` | Telegram group URL. |
| `discord_url` | `string` | Discord server URL. |
| `logo_url` | `string` | Token logo image URL. |

---

### `crypto.etf.flows`

```python
data.crypto.etf.flows(symbol=..., ticker=None, startTime=None, endTime=None, etf_name=None)
```

Summary: ETF Flows — cryptocurrency ETF holding and net-flow data

| Field | Value |
|---|---|
| Endpoint ID | `crypto.etf.flows` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/etf/flows` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Two providers with different schemas. **bitget_data** returns per-ETF holding snapshots with 1d/7d/30d net flows. **coinglass** returns daily aggregated net-flow time series. |

#### Query parameters

Parameters differ by provider.

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Token symbol, e.g. `BTC`, `ETH`, `SOL`, `XRP`, `HYPE`. |
| `ticker` | `no` | `string / null` | `-` | ETF ticker filter, e.g. `IBIT`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `provider` | `no` | `string` | `bitget_data` | - |

**coinglass** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Supported: `BTC`, `ETH`, `SOL`, `XRP`, `HYPE` (and aliases `bitcoin`, `ethereum`, `solana`). |
| `etf_name` | `no` | `string / null` | `-` | Specific ETF name to query. If omitted, returns aggregated data. |
| `provider` | `no` | `string` | `coinglass` | Requires CoinGlass API key. |

#### Response fields

**bitget_data** provider:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Token symbol. |
| `etf_name` | `string` | ETF name. |
| `ticker` | `string` | ETF ticker symbol, e.g. `IBIT`. |
| `primary_exchange` | `string` | Primary listing exchange, e.g. `NYSE`. |
| `holding_balance` | `number` | Current holding balance. |
| `net_flow_1d` | `number` | Net flow over the last 1 day. |
| `net_flow_7d` | `number` | Net flow over the last 7 days. |
| `net_flow_30d` | `number` | Net flow over the last 30 days. |
| `ts` | `string` | Data timestamp. |

**coinglass** provider:

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Datetime of the data point (UTC). |
| `symbol` | `string` | Token symbol. |
| `etf_name` | `string / null` | ETF name. `null` when aggregated across all ETFs. |
| `net_flow` | `number` | Daily net flow in USD. |
| `total_aum` | `number` | Total assets under management in USD (when available). |

---

### `crypto.etf.holdings`

```python
data.crypto.etf.holdings(symbol=..., etf_name=None)
```

Summary: Holdings

| Field | Value |
|---|---|
| Endpoint ID | `crypto.etf.holdings` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/etf/holdings` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Currently supports BTC and ETH. |
| `etf_name` | `no` | `string | null` | `-` | Specific ETF name to query. If not provided, returns all ETFs. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `etf_name` | `string` | ETF name. |
| `holdings` | `number` | ETF holdings amount in native cryptocurrency units. |
| `holdings_value` | `number` | ETF holdings value in USD. |
| `percentage` | `number` | Percentage of total cryptocurrency supply held by this ETF. |

---

### `crypto.exchange_info`

```python
data.crypto.exchange_info(exchange_id=...)
```

Summary: Exchange Info

| Field | Value |
|---|---|
| Endpoint ID | `crypto.exchange_info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/exchange_info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `exchange_id` | `yes` | `string` | `-` | CoinGecko exchange ID e.g. 'binance'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `exchange_id` | `string` | Exchange identifier. |
| `name` | `string` | Exchange name. |
| `year_established` | `integer` | Year the exchange was established. |
| `country` | `string` | Country of registration. |
| `description` | `string` | Exchange description. |
| `trust_score` | `integer` | Trust score (1-10). |
| `trust_score_rank` | `integer` | Trust score rank. |
| `trade_volume_24h_btc` | `number` | 24h trade volume in BTC. |
| `trade_volume_24h_btc_normalized` | `number` | 24h normalized trade volume in BTC. |
| `url` | `string` | Exchange website URL. |
| `image` | `string` | Exchange logo URL. |
| `has_trading_incentive` | `boolean` | Whether the exchange has trading incentives. |

---

### `crypto.exchange_rates`

```python
data.crypto.exchange_rates()
```

Summary: Exchange Rates

| Field | Value |
|---|---|
| Endpoint ID | `crypto.exchange_rates` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/exchange_rates` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `currency` | `string` | Currency identifier (e.g. 'usd', 'eth', 'ltc'). |
| `name` | `string` | Currency display name. |
| `unit` | `string` | Currency unit symbol (e.g. '$', 'BTC'). |
| `rate` | `number` | Exchange rate against BTC. |
| `currency_type` | `string` | Type: 'fiat', 'crypto', or 'commodity'. |

---

### `crypto.exchange_tickers`

```python
data.crypto.exchange_tickers(exchange_id=..., page=None)
```

Summary: Exchange Tickers

| Field | Value |
|---|---|
| Endpoint ID | `crypto.exchange_tickers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/exchange_tickers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `exchange_id` | `yes` | `string` | `-` | CoinGecko exchange ID e.g. 'binance'. |
| `page` | `no` | `integer | null` | `-` | Page number for paginated results. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `exchange` | `string` | Exchange name. |
| `exchange_id` | `string` | Exchange identifier. |
| `base` | `string` | Base currency symbol. |
| `target` | `string` | Quote/target currency symbol. |
| `last_price` | `number` | Last traded price. |
| `volume` | `number` | 24h trading volume in base currency. |
| `bid_ask_spread_percentage` | `number` | Bid-ask spread as a percentage. |
| `trust_score` | `string` | Trust score: 'green', 'yellow', or 'red'. |
| `trade_url` | `string` | Direct URL to trade this pair. |
| `last_traded_at` | `string` | Last trade timestamp. |
| `converted_last_usd` | `number` | Last price converted to USD. |
| `converted_volume_usd` | `number` | 24h volume converted to USD. |

---

### `crypto.exchange_volume_chart`

```python
data.crypto.exchange_volume_chart(exchange_id=..., days=1)
```

Summary: Exchange Volume Chart

| Field | Value |
|---|---|
| Endpoint ID | `crypto.exchange_volume_chart` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/exchange_volume_chart` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `exchange_id` | `yes` | `string` | `-` | CoinGecko exchange ID e.g. 'binance'. |
| `days` | `no` | `integer` | `1` | Data up to N days ago. Values: 1/7/14/30/60/90/180/365. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `timestamp` | `string` | Timestamp of the data point. |
| `volume_btc` | `number` | Exchange volume in BTC. |

---

### `crypto.exchanges`

```python
data.crypto.exchanges(per_page=100, page=1)
```

Summary: Exchanges

| Field | Value |
|---|---|
| Endpoint ID | `crypto.exchanges` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/exchanges` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `per_page` | `no` | `integer` | `100` | Number of results per page. Default 100, max 250. |
| `page` | `no` | `integer` | `1` | Page number. Default 1. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `exchange_id` | `string` | Exchange identifier. |
| `name` | `string` | Exchange name. |
| `year_established` | `integer` | Year the exchange was established. |
| `country` | `string` | Country of registration. |
| `description` | `string` | Exchange description. |
| `trust_score` | `integer` | Trust score (1-10). |
| `trust_score_rank` | `integer` | Trust score rank. |
| `trade_volume_24h_btc` | `number` | 24h trade volume in BTC. |
| `trade_volume_24h_btc_normalized` | `number` | 24h normalized trade volume in BTC. |
| `url` | `string` | Exchange website URL. |
| `image` | `string` | Exchange logo URL. |
| `has_trading_incentive` | `boolean` | Whether the exchange has trading incentives. |

---

### `crypto.futures.funding_rate`

```python
data.crypto.futures.funding_rate(symbol=..., exchange='binance', interval='4h', limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None)
```

Summary: Funding Rate

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.funding_rate` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/funding_rate` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Backs data.funding_rate.fetch() today. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `exchange` | `no` | `string | null` | `binance` | Exchange identifier. Supported: binance, bitget. |
| `interval` | `no` | `string` | `4h` | Aggregation interval for funding-rate data. Supported values: 5m, 15m, 1h, 4h, 1d. |
| `limit` | `no` | `integer | null` | `1000` | Maximum number of records to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. Defaults to 90 when neither days nor start_date is specified. |

> **Time range**: Maximum window is **90 days**. The window is automatically clamped if start/end exceeds this limit.

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `timestamp` | `string` | Timestamp of the current funding period (UTC). |
| `funding_rate` | `number` | Funding rate as a decimal (e.g., 0.0001 = 0.01%). Multiplied ×100 for percent display. |
| `next_funding_time` | `string` | Next funding settlement time (UTC). |
| `estimated_rate` | `number` | Estimated next funding rate. |
| `exchange` | `string` | Exchange name. |
| `fr_open` | `number` | Funding rate at interval start. |
| `fr_high` | `number` | Highest funding rate during interval. |
| `fr_low` | `number` | Lowest funding rate during interval. |

#### Verified Playbook usage notes

- Coinglass funding endpoints expect base-asset symbols such as `BTC`, not pair symbols such as `BTCUSDT`.
- Do not build rolling funding z-scores from this endpoint unless a data probe confirms enough historical rows for the target symbol.

---

### `crypto.futures.funding_weighted`

```python
data.crypto.futures.funding_weighted(symbol=..., interval='4h', start_time=None, end_time=None, weight_type='volume', limit=100)
```

Summary: Funding Weighted

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.funding_weighted` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/funding_weighted` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `interval` | `no` | `string | null` | `4h` | Time interval for the data. Default is '4h' (typical funding rate interval). |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `weight_type` | `no` | `string` | `volume` | Weighting method: 'oi' for open interest weighting, 'volume' for volume weighting. |
| `limit` | `no` | `integer` | `100` | Number of records to return. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `weighted_funding_rate` | `number` | Funding rate weighted by open interest across all exchanges. |
| `average_funding_rate` | `number` | Simple average funding rate across all exchanges. |
| `weight_by_oi` | `boolean` | Whether the rate is weighted by open interest. |
| `fr_open` | `number` | Weighted funding rate at interval start. |
| `fr_high` | `number` | Highest weighted funding rate during interval. |
| `fr_low` | `number` | Lowest weighted funding rate during interval. |
| `fr_close` | `number` | Weighted funding rate at interval end. |

#### Verified Playbook usage notes

- Coinglass expects base-asset symbols such as `BTC`, not pair symbols such as `BTCUSDT`.
- `weight_type` defaults to `"volume"` in the upstream API. Pass it explicitly when the strategy depends on a particular weighting method.
- Probe the requested `interval`, `weight_type`, and `limit` before using this as a replay feature; do not assume it has enough history for rolling z-scores.

---

### `crypto.futures.kline`

```python
data.crypto.futures.kline(symbol=..., interval='1d', exchange='binance', limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None, vs_currency='usd', data_type='ohlc', exchanges=None, closed_only=True)
```

Summary: Kline

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.kline` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/kline` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Backs contract OHLCV fetches today. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `interval` | `no` | `string` | `1d` | Candlestick interval. Supported values: 5m, 15m, 1h, 4h, 1d. |
| `exchange` | `no` | `string` | `binance` | Exchange identifier. Supported: binance, bitget. |
| `limit` | `no` | `integer | null` | `1000` | Maximum number of candles to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. |
| `vs_currency` | `no` | `string` | `usd` | Target currency for prices. Default is 'usd'. |
| `data_type` | `no` | `string` | `ohlc` | enum: ohlc, market_chart Data type: 'ohlc' for OHLC candles, 'market_chart' for close-only price history. |
| `exchanges` | `no` | `array | string | null` | `-` | accepts array values To limit the query to a subset of exchanges e.g. ['POLONIEX', 'GDAX'] Multiple comma separated items allowed. |
| `closed_only` | `no` | `boolean` | `true` | **SDK-side parameter, not sent upstream.** When `true` (default) the SDK drops bars that have not closed yet (`open_time + interval > now`). Pass `false` to keep the forming candle. |

> **Time range**: Maximum window is **90 days**. Longer requests are silently clamped — never assume the full range came back; verify the earliest returned `time`.

> **Kline semantics** (verified behavior — read before writing fetch logic):
>
> - **The raw upstream response includes the currently-forming candle.** Its OHLCV drifts on every call until the bar closes, so decisions made on it repaint. The SDK removes it by default (`closed_only=True`); pass `closed_only=False` only when you explicitly want the live partial bar, and never trade on that bar's close.
> - **Bar timestamps are open time.** The canonical `time` field is the bar's open time as a millisecond Unix epoch (UTC); a bar covers `[time, time + interval)` and is final only once `time + interval <= now`. The legacy `date` string mirrors the open time.
> - **`limit` is capped at 1000 and truncation is silent, anchored to the window end.** When the requested window holds more than `limit` bars you receive the most recent `limit` bars, not the earliest. Paginate with `start_time`/`end_time` chunks instead of raising `limit`.
> - **`end_time` is a loose upper bound.** The response may include bars at or beyond `end_time`. Clip client-side and de-duplicate by `time` when stitching pages.
> - **Freshness check for live strategies:** after fetching, assert the newest closed bar is recent (refuse to act when `now - (last_time + interval) > 2 * interval`) so a stalled feed cannot silently drive decisions.
> - On SDK builds that predate `closed_only`, filter manually: `df = df[df.index + pd.Timedelta(interval) <= pd.Timestamp.now(tz="UTC")]`.

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
| `exchange` | `string` | Exchange the data was fetched from. |
| `symbol` | `string` | Trading pair symbol. |
| `interval` | `string` | Candlestick interval. |

#### Verified Playbook usage notes

- **Exchange resolution required**: before passing `exchange=` to this endpoint, call `data.crypto.market(symbol="BTC/USDT", market_type="perpetual", exchange=<target>)` and verify the symbol has an active row for that exchange. An unsupported symbol+exchange combination returns an empty response. Extract `exchange_id` from the market response as the exchange-native symbol and `exchange` as the exchange identifier for this call.
- Coinglass returns OHLCV fields and does not include Binance raw `quote_volume` / `taker_buy_quote_volume`; derive or omit those features unless a probe proves the fields exist.

---

### `crypto.futures.liquidation_aggregated_map`

```python
data.crypto.futures.liquidation_aggregated_map(symbol=..., range='1d')
```

Summary: Liquidation Aggregated Map

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.liquidation_aggregated_map` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/liquidation_aggregated_map` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `range` | `no` | `string` | `1d` | Time range for liquidation map data. Supported values: 1d, 7d, 30d.; Time range for liquidation map data. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol to get data for. |
| `liquidation_price` | `number` | Liquidation price level. |
| `liquidation_intensity` | `number` | Liquidation intensity at this price level (in USD). |

#### Verified Playbook usage notes

- Coinglass expects base-asset symbols such as `BTC`, not pair symbols such as `BTCUSDT`.
- `range` defaults to `"1d"`; probe the exact range before using the response shape in a strategy.
- Use this as context unless the probe confirms a stable time axis suitable for backtest replay.

---

### `crypto.futures.liquidation_heatmap`

```python
data.crypto.futures.liquidation_heatmap(symbol=..., price_range='5%')
```

Summary: Liquidation Heatmap

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.liquidation_heatmap` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/liquidation_heatmap` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `price_range` | `no` | `string | null` | `5%` | Price range for heatmap ('5%', '10%', '20%'). Default is '5%'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol to get data for. |
| `current_price` | `number` | Current market price. |
| `price_level` | `number` | Price level for potential liquidations. |
| `long_liquidation_amount` | `number` | Estimated long position liquidation amount at this price level (in USD). |
| `short_liquidation_amount` | `number` | Estimated short position liquidation amount at this price level (in USD). |
| `total_liquidation_amount` | `number` | Total liquidation amount at this price level (in USD). |

---

### `crypto.futures.liquidation_max_pain`

```python
data.crypto.futures.liquidation_max_pain(range='24h')
```

Summary: Liquidation Max Pain

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.liquidation_max_pain` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/liquidation_max_pain` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `range` | `no` | `string` | `24h` | Time range for liquidation data. Supported values: 12h, 24h, 48h, 3d, 7d, 14d, 30d.; Time range for liquidation data. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol to get data for. |
| `price` | `number` | Current market price. |
| `long_max_pain_liq_level` | `number` | Long position maximum pain liquidation intensity (in USD). |
| `long_max_pain_liq_price` | `number` | Long position maximum pain liquidation price. |
| `short_max_pain_liq_level` | `number` | Short position maximum pain liquidation intensity (in USD). |
| `short_max_pain_liq_price` | `number` | Short position maximum pain liquidation price. |

#### Verified Playbook usage notes

- `range` defaults to `"24h"` and the endpoint is market-wide; it has no `symbol` parameter in the current OpenAPI spec.
- Use this as context unless the probe confirms the returned fields and time axis match the replay contract.

---

### `crypto.futures.liquidations`

```python
data.crypto.futures.liquidations(symbol=None, interval='1d', exchange=None, limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None)
```

Summary: Liquidations

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.liquidations` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/liquidations` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Planned future replacement for data.liquidations.fetch(). |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Crypto symbol. If None, returns total market liquidations. |
| `interval` | `no` | `string | null` | `1d` | Aggregation interval. Supported values: 5m, 15m, 1h, 4h, 1d. |
| `exchange` | `no` | `string | null` | `-` | Exchange identifier. Supported: binance, bitget. |
| `limit` | `no` | `integer | null` | `1000` | Maximum number of records to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. |

> **Time range**: Maximum window is **90 days**. The window is automatically clamped if start/end exceeds this limit.

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `long_liquidations` | `number` | Total long liquidations in USD. |
| `short_liquidations` | `number` | Total short liquidations in USD. |
| `total_liquidations` | `number` | Total liquidations (long + short) in USD. |
| `exchange` | `string` | Exchange name. |

#### Verified Playbook usage notes

- Use base-asset symbols for Coinglass, e.g. `symbol="BTC"`, not `symbol="BTCUSDT"`.
- Verified non-empty combinations: `symbol="BTC", interval="1h"` and `interval="1d"`.
- Returned fields include `long_liquidations`, `short_liquidations`, `total_liquidations`, `exchange`, `symbol`, and `date`.

---

### `crypto.futures.long_short_ratio`

```python
data.crypto.futures.long_short_ratio(symbol=..., interval='5m', exchange='binance', limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None)
```

Summary: Long Short Ratio

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.long_short_ratio` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/long_short_ratio` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Planned future replacement for data.long_short_ratio.fetch(). |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Trading pair symbol (e.g., BTCUSDT) |
| `interval` | `no` | `string` | `5m` | enum: 5m, 15m, 1h, 4h, 1d Data granularity interval. |
| `exchange` | `no` | `string` | `binance` | Exchange identifier. Supported: binance, bitget. |
| `limit` | `no` | `integer | null` | `1000` | Maximum number of records to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. |

> **Time range**: Maximum window is **90 days**. The window is automatically clamped if start/end exceeds this limit.

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Trading pair symbol. |
| `long_short_ratio` | `number` | Long to short ratio. |
| `long_account` | `number` | Long account percentage. |
| `short_account` | `number` | Short account percentage. |
| `timestamp` | `integer` | Unix timestamp. |
| `exchange` | `string` | Exchange name. |

---

### `crypto.futures.long_short_top_account_ratio`

```python
data.crypto.futures.long_short_top_account_ratio(symbol=..., interval='5m', exchange='binance', limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None)
```

Summary: Long Short Top Account Ratio

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.long_short_top_account_ratio` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/long_short_top_account_ratio` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Trading pair symbol (e.g., BTCUSDT) |
| `interval` | `no` | `string` | `5m` | enum: 5m, 15m, 1h, 4h, 1d Data granularity interval. |
| `exchange` | `no` | `string` | `binance` | Exchange identifier. Supported: binance, bitget. |
| `limit` | `no` | `integer | null` | `1000` | Maximum number of records to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. |

> **Time range**: Maximum window is **90 days**. The window is automatically clamped if start/end exceeds this limit.

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Trading pair symbol. |
| `long_short_ratio` | `number` | Long to short ratio. |
| `long_account` | `number` | Long account percentage. |
| `short_account` | `number` | Short account percentage. |
| `timestamp` | `integer` | Unix timestamp. |
| `exchange` | `string` | Exchange name. |

---

### `crypto.futures.long_short_top_position_ratio`

```python
data.crypto.futures.long_short_top_position_ratio(symbol=..., interval='5m', exchange='binance', limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None)
```

Summary: Long Short Top Position Ratio

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.long_short_top_position_ratio` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/long_short_top_position_ratio` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Trading pair symbol (e.g., BTCUSDT) |
| `interval` | `no` | `string` | `5m` | enum: 5m, 15m, 1h, 4h, 1d Data granularity interval. |
| `exchange` | `no` | `string` | `binance` | Exchange identifier. Supported: binance, bitget. |
| `limit` | `no` | `integer | null` | `1000` | Maximum number of records to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. |

> **Time range**: Maximum window is **90 days**. The window is automatically clamped if start/end exceeds this limit.

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Trading pair symbol. |
| `long_short_ratio` | `number` | Long to short ratio. |
| `long_account` | `number` | Long account percentage. |
| `short_account` | `number` | Short account percentage. |
| `timestamp` | `integer` | Unix timestamp. |
| `exchange` | `string` | Exchange name. |

---

### `crypto.futures.mark_price`

```python
data.crypto.futures.mark_price(symbol=None, exchange='binance')
```

Summary: Mark Price

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.mark_price` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/mark_price` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Trading pair symbol (e.g., BTCUSDT). If not provided, returns all symbols. |
| `exchange` | `no` | `string` | `binance` | enum: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid Exchange to fetch data from. Supported: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Trading pair symbol. |
| `mark_price` | `number` | Mark price. |
| `index_price` | `number` | Index price. |
| `estimated_settle_price` | `number` | Estimated settlement price. |
| `last_funding_rate` | `number` | Last funding rate. |
| `next_funding_time` | `integer` | Next funding time (Unix timestamp). |
| `time` | `integer` | Current timestamp. |
| `interest_rate` | `number` | Interest rate. |

---

### `crypto.futures.open_interest`

```python
data.crypto.futures.open_interest(symbol=..., interval='1h', exchange='binance', unit='coin', limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None)
```

Summary: Open Interest

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.open_interest` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/open_interest` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Intended future replacement for the current placeholder in getagent.data. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `interval` | `no` | `string` | `1h` | enum: 5m, 15m, 1h, 4h, 1d Aggregation interval for open interest data. |
| `exchange` | `no` | `string` | `binance` | enum: binance, bitget Exchange identifier. Supported: binance, bitget. |
| `unit` | `no` | `string` | `coin` | enum: coin, usd Unit for OI values: 'coin' returns coin-denominated OI (oi_open/oi_high/oi_low/oi_close), 'usd' returns USDT-denominated OI. Both raw sets (open_value/high_value/low_value/close_value) are always included. |
| `limit` | `no` | `integer` | `1000` | Maximum number of records to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. |

> **Time range**: Maximum window is **90 days**. The window is automatically clamped if start/end exceeds this limit.

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Trading pair symbol. |
| `exchange` | `string` | Exchange identifier. |
| `interval` | `string` | Aggregation interval. |
| `open_interest` | `number` | Open interest in base currency (oi_close when unit='coin', or close_value when unit='usd'). |
| `oi_open` | `number` | Open interest at interval start (coin-denominated when unit='coin', USD when unit='usd'). |
| `oi_high` | `number` | Highest open interest during interval. |
| `oi_low` | `number` | Lowest open interest during interval. |
| `oi_close` | `number` | Open interest at interval end. |
| `open_value` | `number` | Open interest value in USD at interval start (always included). |
| `high_value` | `number` | Highest OI value in USD during interval (always included). |
| `low_value` | `number` | Lowest OI value in USD during interval (always included). |
| `close_value` | `number` | OI value in USD at interval end (always included). |

---

### `crypto.futures.open_interest_history`

```python
data.crypto.futures.open_interest_history(symbol=..., interval='1h', exchange='binance', unit='coin', limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None)
```

Summary: Open Interest History

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.open_interest_history` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/open_interest_history` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Trading pair symbol (e.g., BTCUSDT) |
| `interval` | `no` | `string` | `1h` | Aggregation interval for open interest data. Supported values: 5m, 15m, 1h, 4h, 1d. |
| `exchange` | `no` | `string` | `binance` | Exchange identifier. Supported: binance, bitget. |
| `unit` | `no` | `string` | `coin` | enum: coin, usd Unit for OI values: 'coin' returns coin-denominated OI (oi_open/oi_high/oi_low/oi_close), 'usd' returns USDT-denominated OI (open_value/high_value/low_value/close_value). |
| `limit` | `no` | `integer | null` | `1000` | Maximum number of records to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. |

> **Time range**: Maximum window is **90 days**. The window is automatically clamped if start/end exceeds this limit.

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Trading pair symbol. |
| `exchange` | `string` | Exchange identifier. |
| `interval` | `string` | Aggregation interval. |
| `oi_open` | `number` | Open interest at interval start (coin or USD depending on unit). |
| `oi_high` | `number` | Highest open interest during interval. |
| `oi_low` | `number` | Lowest open interest during interval. |
| `oi_close` | `number` | Open interest at interval end. |
| `open_value` | `number` | Open interest value in USD at interval start (always included). |
| `high_value` | `number` | Highest OI value in USD during interval (always included). |
| `low_value` | `number` | Lowest OI value in USD during interval (always included). |
| `close_value` | `number` | OI value in USD at interval end (always included). |

---

### `crypto.futures.order_book`

```python
data.crypto.futures.order_book(symbol=..., limit=20, exchange='binance')
```

Summary: Order Book

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.order_book` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/order_book` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer` | `20` | Depth of the order book — number of bid and ask levels to return. |
| `exchange` | `no` | `string` | `binance` | Exchange to fetch data from. Supported: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid. |

---

### `crypto.futures.taker_volume`

```python
data.crypto.futures.taker_volume(symbol=..., interval='1h', limit=30, start_time=None, end_time=None, exchange='Binance')
```

Summary: Taker Volume

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.taker_volume` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/taker_volume` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Trading pair symbol (e.g., BTCUSDT) |
| `interval` | `no` | `string` | `1h` | Aggregation interval (5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d) |
| `limit` | `no` | `integer | null` | `30` | Number of results (max 500). |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `exchange` | `no` | `string` | `Binance` | Exchange name (e.g. Binance, OKX, Bybit). Can be obtained from support-exchange-pair endpoint. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `buy_sell_ratio` | `number` | Taker buy to sell volume ratio. |
| `buy_vol` | `number` | Taker buy volume. |
| `sell_vol` | `number` | Taker sell volume. |
| `timestamp` | `integer` | Unix timestamp. |

#### Verified Playbook usage notes

- Returned fields include `timestamp`, `buy_vol`, `sell_vol`, and `buy_sell_ratio`.
- For replay feature frames, use `timestamp` as the feature datetime index unless a probe shows the service returned a normalized `date` column.

---

### `crypto.futures.ticker`

```python
data.crypto.futures.ticker(symbol=..., exchange='binance', vs_currency='usd', include_market_data=True)
```

Summary: Ticker

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.ticker` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/ticker` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Backs contract price latest fetches today. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `exchange` | `no` | `string` | `binance` | enum: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid Exchange to fetch data from. Supported: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid. |
| `vs_currency` | `no` | `string` | `usd` | Target currency for prices. Default is 'usd'. |
| `include_market_data` | `no` | `boolean` | `true` | Use /coins/markets for richer data (market cap, volume, 24h change). Set to False to use /simple/price for a faster, lighter response. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `exchange` | `string` | Exchange or venue the data was fetched from. |
| `timestamp` | `string` | Timestamp of the ticker snapshot (UTC). |
| `last` | `number` | Last traded price. |
| `open` | `number` | The open price (24h rolling window). |
| `high` | `number` | The high price (24h rolling window). |
| `low` | `number` | The low price (24h rolling window). |
| `bid` | `number` | Current best bid price. |
| `ask` | `number` | Current best ask price. |
| `vwap` | `number` | Volume Weighted Average Price over the period. |
| `volume` | `number` | The trading volume (base currency, 24h). |
| `quote_volume` | `number` | 24h trading volume in quote currency. |
| `prev_close` | `number` | The previous close price. |
| `change` | `number` | Absolute price change over 24h. |
| `change_percent` | `number` | Percentage price change over 24h. |
| `market_cap` | `number` | Market capitalization in quote currency. |
| `bid_volume` | `number` | Volume at the best bid. |
| `ask_volume` | `number` | Volume at the best ask. |
| `average` | `number` | Average of open and last price. |
| `coin_id` | `string` | CoinGecko coin identifier. |
| `market_cap_rank` | `integer` | Market cap rank. |
| `fully_diluted_valuation` | `number` | Fully diluted valuation in quote currency. |
| `circulating_supply` | `number` | Circulating supply. |
| `total_supply` | `number` | Total supply. |

---

### `crypto.futures.trades`

```python
data.crypto.futures.trades(symbol=..., limit=100, exchange='binance')
```

Summary: Trades

| Field | Value |
|---|---|
| Endpoint ID | `crypto.futures.trades` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/futures/trades` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer` | `100` | Number of most recent trades to return. |
| `exchange` | `no` | `string` | `binance` | Exchange to fetch data from. Supported: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `trade_id` | `string` | Exchange-assigned trade ID. |
| `symbol` | `string` | Trading pair symbol. |
| `timestamp` | `string` | Trade execution time (UTC). |
| `side` | `string` | Taker side: buy or sell. |
| `price` | `number` | Execution price. |
| `amount` | `number` | Trade size in base currency. |
| `cost` | `number` | Trade value in quote currency (price × amount). |
| `taker_or_maker` | `string` | Whether the trade was executed as taker or maker. |

---

### `crypto.global_defi`

```python
data.crypto.global_defi()
```

Summary: Global Defi

| Field | Value |
|---|---|
| Endpoint ID | `crypto.global_defi` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/global_defi` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `defi_market_cap` | `number` | Total DeFi market capitalization in USD. |
| `eth_market_cap` | `number` | Ethereum market capitalization in USD. |
| `defi_to_eth_ratio` | `number` | Ratio of DeFi market cap to ETH market cap. |
| `trading_volume_24h` | `number` | 24h DeFi trading volume in USD. |
| `defi_dominance` | `number` | DeFi dominance as a percentage of total crypto market. |
| `top_coin_name` | `string` | Name of the top DeFi coin by market cap. |
| `top_coin_defi_dominance` | `number` | Top DeFi coin's dominance within the DeFi market. |

---

### `crypto.global_market`

```python
data.crypto.global_market()
```

Summary: Global Market

| Field | Value |
|---|---|
| Endpoint ID | `crypto.global_market` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/global_market` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `active_cryptocurrencies` | `integer` | Total number of active cryptocurrencies. |
| `markets` | `integer` | Total number of markets (trading pairs). |
| `total_market_cap_usd` | `number` | Total cryptocurrency market cap in USD. |
| `total_volume_usd` | `number` | Total 24h trading volume in USD. |
| `btc_dominance` | `number` | Bitcoin market dominance percentage. |
| `eth_dominance` | `number` | Ethereum market dominance percentage. |
| `market_cap_change_percentage_24h_usd` | `number` | 24h market cap change percentage. |
| `defi_volume_24h` | `number` | DeFi 24h trading volume in USD. |
| `defi_market_cap` | `number` | DeFi total market cap in USD. |
| `defi_dominance` | `number` | DeFi dominance percentage of total market. |
| `top_coin_name` | `string` | Name of the top DeFi coin. |
| `top_coin_defi_dominance` | `number` | Top DeFi coin's dominance percentage. |

---

### `crypto.hyperliquid.account_long_short_ratio`

```python
data.crypto.hyperliquid.account_long_short_ratio(symbol=None, interval='1d', limit=1000, start_time=None, end_time=None)
```

Summary: Account Long Short Ratio

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.account_long_short_ratio` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/account_long_short_ratio` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. |
| `interval` | `no` | `string` | `1d` | Data time interval. |
| `limit` | `no` | `integer` | `1000` | Number of records to return. |
| `start_time` | `no` | `integer | null` | `-` | Start timestamp in milliseconds. |
| `end_time` | `no` | `integer | null` | `-` | End timestamp in milliseconds. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `global_account_long_count` | `integer` | Number of accounts holding long positions. |
| `global_account_short_count` | `integer` | Number of accounts holding short positions. |
| `global_account_total_count` | `integer` | Total number of accounts. |
| `global_account_long_percent` | `number` | Percentage of long accounts. |
| `global_account_short_percent` | `number` | Percentage of short accounts. |
| `global_account_long_short_ratio` | `number` | Long to short account ratio. |

---

### `crypto.hyperliquid.account_long_short_ratio_by_tag`

```python
data.crypto.hyperliquid.account_long_short_ratio_by_tag(symbol=..., interval='10m', wallet_tag='Shrimp', limit=1000, start_time=None, end_time=None)
```

Summary: Account Long Short Ratio By Tag

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.account_long_short_ratio_by_tag` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/account_long_short_ratio_by_tag` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `interval` | `no` | `string` | `10m` | Data time interval. |
| `wallet_tag` | `no` | `string` | `Shrimp` | Wallet tag for grouping. |
| `limit` | `no` | `integer` | `1000` | Number of records to return. |
| `start_time` | `no` | `integer | null` | `-` | Start timestamp in milliseconds. Historical data starts from 2026-03-20 00:00:00 UTC. |
| `end_time` | `no` | `integer | null` | `-` | End timestamp in milliseconds. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `group_name` | `string` | Wallet tag group name. |
| `account_long_count` | `integer` | Number of long accounts. |
| `account_short_count` | `integer` | Number of short accounts. |
| `short_position_usd` | `number` | Short position value in USD. |
| `long_position_usd` | `number` | Long position value in USD. |

---

### `crypto.hyperliquid.position_distribution_by_tag`

```python
data.crypto.hyperliquid.position_distribution_by_tag(interval='10m', wallet_tag='Shrimp', limit=1000, start_time=None, end_time=None)
```

Summary: Position Distribution By Tag

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.position_distribution_by_tag` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/position_distribution_by_tag` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `interval` | `no` | `string` | `10m` | Data time interval. |
| `wallet_tag` | `no` | `string` | `Shrimp` | Wallet tag for grouping. |
| `limit` | `no` | `integer` | `1000` | Number of records to return. |
| `start_time` | `no` | `integer | null` | `-` | Start timestamp in milliseconds. Historical data starts from 2026-03-20 00:00:00 UTC. |
| `end_time` | `no` | `integer | null` | `-` | End timestamp in milliseconds. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `group_name` | `string` | Wallet tag group name. |
| `all_address_count` | `integer` | Total address count. |
| `position_address_count` | `integer` | Address count with positions. |
| `bias_score` | `number` | Long/short bias score. |
| `bias_remark` | `string` | Sentiment label. |
| `minimum_amount` | `number` | Minimum position range. |
| `maximum_amount` | `number` | Maximum position range. |
| `long_position_usd` | `number` | Long position value in USD. |
| `short_position_usd` | `number` | Short position value in USD. |
| `position_usd` | `number` | Total position value in USD. |
| `profit_address_count` | `integer` | Profitable address count. |
| `loss_address_count` | `integer` | Loss address count. |

---

### `crypto.hyperliquid.symbol_position`

```python
data.crypto.hyperliquid.symbol_position(symbol=..., current_page=1)
```

Summary: Symbol Position

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.symbol_position` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/symbol_position` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `current_page` | `no` | `integer` | `1` | Current page number. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `user` | `string` | User wallet address. |
| `symbol` | `string` | Trading symbol. |
| `position_size` | `number` | Position size (positive for long, negative for short). |
| `entry_price` | `number` | Entry price. |
| `mark_price` | `number` | Current mark price. |
| `liq_price` | `number` | Liquidation price. |
| `leverage` | `integer` | Leverage multiplier. |
| `margin_balance` | `number` | Margin balance in USD. |
| `position_value_usd` | `number` | Position value in USD. |
| `unrealized_pnl` | `number` | Unrealized profit and loss in USD. |
| `funding_fee` | `number` | Funding fee in USD. |
| `margin_mode` | `string` | Margin mode (cross or isolated). |
| `create_time` | `string` | Position creation time. |
| `update_time` | `string` | Last update time. |
| `total_pages` | `integer` | Total number of pages. |
| `current_page` | `integer` | Current page number. |

---

### `crypto.hyperliquid.user_position`

```python
data.crypto.hyperliquid.user_position(user_address=...)
```

Summary: User Position

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.user_position` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/user_position` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `user_address` | `yes` | `string` | `-` | User wallet address. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `margin_summary` | `object` | Margin summary including account value, total position, and margin used. |
| `cross_margin_summary` | `object` | Cross margin summary. |
| `cross_maintenance_margin_used` | `number` | Cross maintenance margin used. |
| `withdrawable` | `number` | Withdrawable balance. |
| `asset_positions` | `array` | List of asset positions with details. |

---

### `crypto.hyperliquid.wallet_pnl_distribution`

```python
data.crypto.hyperliquid.wallet_pnl_distribution()
```

Summary: Wallet Pnl Distribution

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.wallet_pnl_distribution` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/wallet_pnl_distribution` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `group_name` | `string` | PNL tier label (money_printer, smart_money, grinder, humble_earner, exit_liquidity, semi_rekt, full_rekt, giga_rekt). |
| `all_address_count` | `integer` | Total address count. |
| `position_address_count` | `integer` | Address count with positions. |
| `position_address_percent` | `number` | Percentage of addresses with positions. |
| `bias_score` | `number` | Long/short bias score. |
| `bias_remark` | `string` | Sentiment label (bearish, slightly_bearish, indecisive, bullish, very_bullish). |
| `minimum_amount` | `number` | Minimum PNL range. |
| `maximum_amount` | `number` | Maximum PNL range. |
| `long_position_usd` | `number` | Long position value in USD. |
| `short_position_usd` | `number` | Short position value in USD. |
| `long_position_usd_percent` | `number` | Long position value percentage. |
| `short_position_usd_percent` | `number` | Short position value percentage. |
| `position_usd` | `number` | Total position value in USD. |
| `profit_address_count` | `integer` | Profitable address count. |
| `loss_address_count` | `integer` | Loss address count. |
| `profit_address_percent` | `number` | Profitable address percentage. |
| `loss_address_percent` | `number` | Loss address percentage. |

---

### `crypto.hyperliquid.wallet_position_distribution`

```python
data.crypto.hyperliquid.wallet_position_distribution()
```

Summary: Wallet Position Distribution

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.wallet_position_distribution` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/wallet_position_distribution` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Two providers with different parameter support. **bitget_data** accepts `symbol`/`startTime`/`endTime` filters. **coinglass** takes no query parameters (always returns the latest full snapshot) and requires a CoinGlass API key. |

#### Query parameters

Parameters differ by provider.

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Trading symbol filter, e.g. `BTC`. Returns all symbols when omitted. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). Returns the latest snapshot when omitted. |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). Returns the latest snapshot when omitted. |
| `provider` | `no` | `string` | `bitget_data` | - |

**coinglass** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `provider` | `no` | `string` | `coinglass` | No additional filters. Requires CoinGlass API key. |

#### Response fields

Same schema for both providers:

| Field | Type | Notes |
|---|---|---|
| `group_name` | `string` | Position tier label (shrimp, fish, dolphin, apex_predator, small_whale, whale, tidal_whale, leviathan). |
| `all_address_count` | `integer` | Total address count. |
| `position_address_count` | `integer` | Address count with positions. |
| `position_address_percent` | `number` | Percentage of addresses with positions. |
| `bias_score` | `number` | Long/short bias score. |
| `bias_remark` | `string` | Sentiment label (bearish, slightly_bearish, indecisive, bullish, very_bullish). |
| `minimum_amount` | `number / null` | Minimum position range. May be `null` (bitget_data only; coinglass always returns a number). |
| `maximum_amount` | `number / null` | Maximum position range. May be `null` (bitget_data only; coinglass always returns a number). |
| `long_position_usd` | `number` | Long position value in USD. |
| `short_position_usd` | `number` | Short position value in USD. |
| `long_position_usd_percent` | `number` | Long position value percentage. |
| `short_position_usd_percent` | `number` | Short position value percentage. |
| `position_usd` | `number` | Total position value in USD. |
| `profit_address_count` | `integer` | Profitable address count. |
| `loss_address_count` | `integer` | Loss address count. |
| `profit_address_percent` | `number` | Profitable address percentage. |
| `loss_address_percent` | `number` | Loss address percentage. |

---

### `crypto.hyperliquid.whale_alert`

```python
data.crypto.hyperliquid.whale_alert()
```

Summary: Whale Alert

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.whale_alert` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/whale_alert` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Two providers with different parameter support. **bitget_data** accepts `symbol`/`wallet_address`/`min_transaction_value`/`startTime`/`endTime`/`page`/`size` filters. **coinglass** takes no query parameters and requires a CoinGlass API key. |

#### Query parameters

Parameters differ by provider.

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Trading symbol filter, e.g. `BTC`. Returns all symbols when omitted. |
| `wallet_address` | `no` | `string / null` | `-` | Wallet address filter. |
| `min_transaction_value` | `no` | `number / null` | `-` | Minimum position value in USD, e.g. `1000000`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `page` | `no` | `integer` | `1` | Page number (1-based). |
| `size` | `no` | `integer` | `20` | Page size, max `500`. |
| `provider` | `no` | `string` | `bitget_data` | - |

**coinglass** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `provider` | `no` | `string` | `coinglass` | No additional filters. Requires CoinGlass API key. |

#### Response fields

**bitget_data** provider:

| Field | Type | Notes |
|---|---|---|
| `user` | `string` | User wallet address. |
| `symbol` | `string` | Trading symbol. |
| `position_size` | `number / null` | Position size (positive for long, negative for short). May be `null`. |
| `entry_price` | `number / null` | Entry price. May be `null` on close. |
| `liq_price` | `number / null` | Liquidation price. May be `null` after close. |
| `position_value_usd` | `number / null` | Position value in USD. May be `null`. |
| `position_action` | `integer / null` | Position action type (1: open, 2: close). May be `null`. |
| `create_time` | `string / null` | Record creation time. May be `null`. |

**coinglass** provider:

| Field | Type | Notes |
|---|---|---|
| `user` | `string` | User wallet address. |
| `symbol` | `string` | Trading symbol. |
| `position_size` | `number` | Position size (positive for long, negative for short). |
| `entry_price` | `number` | Entry price. |
| `liq_price` | `number / null` | Liquidation price. May be `null`. |
| `position_value_usd` | `number` | Position value in USD. |
| `position_action` | `integer` | Position action type (1: open, 2: close). |
| `create_time` | `string` | Position creation time. |

---

### `crypto.hyperliquid.smart_money_alert`

```python
data.crypto.hyperliquid.smart_money_alert(wallet_address=..., symbol=None, min_transaction_value=None, startTime=None, endTime=None, page=1, size=20)
```

Summary: Smart Money Alert — Hyperliquid position-change alerts for a specific wallet address

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.smart_money_alert` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/smart_money_alert` |
| SDK | `supported` |
| Host | `supported` |
| Notes | bitget_data provider only. Same underlying feed as `crypto.hyperliquid.whale_alert`, filtered to a required wallet address. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `wallet_address` | `yes` | `string` | `-` | Wallet address to track. |
| `symbol` | `no` | `string / null` | `-` | Trading symbol filter, e.g. `BTC`. Returns all symbols when omitted. |
| `min_transaction_value` | `no` | `number / null` | `-` | Minimum position value in USD, e.g. `500000`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `page` | `no` | `integer` | `1` | Page number (1-based). |
| `size` | `no` | `integer` | `20` | Page size, max `500`. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `user` | `string` | User wallet address. |
| `symbol` | `string` | Trading symbol. |
| `position_size` | `number / null` | Position size (positive for long, negative for short). May be `null`. |
| `entry_price` | `number / null` | Entry price. May be `null` on close. |
| `liq_price` | `number / null` | Liquidation price. May be `null` after close. |
| `position_value_usd` | `number / null` | Position value in USD. May be `null`. |
| `position_action` | `integer / null` | Position action type (1: open, 2: close). May be `null`. |
| `create_time` | `string / null` | Record creation time. May be `null`. |

---

### `crypto.hyperliquid.whale_position`

```python
data.crypto.hyperliquid.whale_position()
```

Summary: Whale Position

| Field | Value |
|---|---|
| Endpoint ID | `crypto.hyperliquid.whale_position` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/hyperliquid/whale_position` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `user` | `string` | User wallet address. |
| `symbol` | `string` | Trading symbol. |
| `position_size` | `number` | Position size (positive for long, negative for short). |
| `entry_price` | `number` | Entry price. |
| `mark_price` | `number` | Current mark price. |
| `liq_price` | `number` | Liquidation price. |
| `leverage` | `integer` | Leverage multiplier. |
| `margin_balance` | `number` | Margin balance in USD. |
| `position_value_usd` | `number` | Position value in USD. |
| `unrealized_pnl` | `number` | Unrealized profit and loss in USD. |
| `funding_fee` | `number` | Funding fee in USD. |
| `margin_mode` | `string` | Margin mode (cross or isolated). |
| `create_time` | `string` | Position creation time. |
| `update_time` | `string` | Last update time. |

---

### `crypto.institutional.company_flow`

```python
data.crypto.institutional.company_flow(symbol=None, company_name=None, country=None, startTime=None, endTime=None)
```

Summary: Company Flow — non-mining company BTC holding and flow data

| Field | Value |
|---|---|
| Endpoint ID | `crypto.institutional.company_flow` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/institutional/company_flow` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Token symbol, e.g. `BTC`. |
| `company_name` | `no` | `string / null` | `-` | Company name filter, e.g. `Strategy`. |
| `country` | `no` | `string / null` | `-` | Country filter, e.g. `US`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `provider` | `no` | `string` | `bitget_data` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Token symbol. |
| `company_name` | `string` | Company name. |
| `holding_balance` | `number` | Current holding balance in native tokens. |
| `net_flow_1d` | `number` | Net flow over the last 1 day. |
| `net_flow_7d` | `number` | Net flow over the last 7 days. |
| `net_flow_30d` | `number` | Net flow over the last 30 days. |
| `ts` | `string` | Data timestamp. |

---

### `crypto.institutional.country_flow`

```python
data.crypto.institutional.country_flow(symbol=None, country=None, startTime=None, endTime=None)
```

Summary: Country Flow — country-level BTC holding and flow data

| Field | Value |
|---|---|
| Endpoint ID | `crypto.institutional.country_flow` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/institutional/country_flow` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Token symbol, e.g. `BTC`. |
| `country` | `no` | `string / null` | `-` | Country code or name, e.g. `US`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `provider` | `no` | `string` | `bitget_data` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Token symbol. |
| `country` | `string` | Country code or name. |
| `holding_balance` | `number` | Current holding balance in native tokens. |
| `net_flow_1d` | `number` | Net flow over the last 1 day. |
| `net_flow_7d` | `number` | Net flow over the last 7 days. |
| `net_flow_30d` | `number` | Net flow over the last 30 days. |
| `ts` | `string` | Data timestamp. |

---

### `crypto.institutional.mining_company_flow`

```python
data.crypto.institutional.mining_company_flow(symbol=None, company_name=None, startTime=None, endTime=None)
```

Summary: Mining Company Flow — crypto mining company BTC holding and flow data

| Field | Value |
|---|---|
| Endpoint ID | `crypto.institutional.mining_company_flow` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/institutional/mining_company_flow` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Token symbol, e.g. `BTC`. |
| `company_name` | `no` | `string / null` | `-` | Mining company name filter, e.g. `Marathon`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `provider` | `no` | `string` | `bitget_data` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Token symbol. |
| `company_name` | `string` | Mining company name. |
| `holding_balance` | `number` | Current holding balance in native tokens. |
| `net_flow_1d` | `number` | Net flow over the last 1 day. |
| `net_flow_7d` | `number` | Net flow over the last 7 days. |
| `net_flow_30d` | `number` | Net flow over the last 30 days. |
| `ts` | `string` | Data timestamp. |

---

### `crypto.market`

```python
data.crypto.market(symbol=None, exchange=None, base=None, market_type=None, is_rwa=None, category=None, page=None, size=None)
```

Summary: Market — trading instrument info. Supports two providers: **ccxt** (live exchange data via CCXT library) and **bitget_data** (internal `upex_market_info` table via AGENT_DATA_QUERY service).

| Field | Value |
|---|---|
| Endpoint ID | `crypto.market` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/market` |
| SDK | `supported` |
| Host | `supported` |
| Notes | For Bitget exchange queries, RWA r-prefix mapping may appear in CCXT/unified market metadata (e.g. TSLA/USDT → rTSLA/USDT). Do not copy that unified symbol into `manifest.trading_symbols`, `backtest.yaml`, or trade calls; package contracts must use the confirmed exchange-native pair such as `RTSLAUSDT` for spot or `TSLAUSDT` for contract. |

#### Query parameters

Parameters differ by provider. All parameters are optional unless noted.

**ccxt** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `exchange` | `yes` | `string` | `binance` | Exchange to query. enum: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid. |
| `symbol` | `no` | `string / null` | `-` | Trading pair symbol (e.g. 'BTC/USDT'). Filters results to this symbol. |
| `base` | `no` | `string / null` | `-` | Base currency filter (e.g. 'BTC'). |
| `market_type` | `no` | `string / null` | `-` | enum: spot, perpetual, future, option. Market type filter. |
| `is_rwa` | `no` | `boolean / null` | `-` | Filter by Real World Asset status. Populated only for bitget exchange. |

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Trading pair symbol (e.g. 'BTC/USDT'). Returns all market entries for this symbol across exchanges. |
| `exchange` | `no` | `string / null` | `-` | Exchange identifier (e.g. 'binance', 'bitget'). Returns all tradable pairs on this exchange. |
| `base` | `no` | `string / null` | `-` | Base currency filter (e.g. 'BTC'). |
| `market_type` | `no` | `string / null` | `-` | enum: spot, perpetual, future, option. Market type filter. |
| `is_rwa` | `no` | `boolean / null` | `-` | Filter by Real World Asset status. True = RWA only; False = exclude RWA. |
| `category` | `no` | `string / null` | `-` | Filter by asset category (e.g. 'Stocks', 'ETF', 'Commodity'). |
| `page` | `no` | `integer / null` | `1` | Page number (1-based). |
| `size` | `no` | `integer / null` | `20` | Number of rows per page. Maximum 200. |

#### Response fields

Common fields (all providers):

| Field | Type | Notes |
|---|---|---|
| `exchange` | `string` | Exchange identifier (e.g. 'binance', 'bitget'). |
| `symbol` | `string` | Unified trading pair symbol (e.g. 'BTC/USDT', 'BTC/USDT:USDT'). |
| `base` | `string` | Base currency (e.g. 'BTC'). |
| `quote` | `string` | Quote currency (e.g. 'USDT'). |
| `market_type` | `string` | Market type: spot, perpetual, future, or option. |
| `is_rwa` | `boolean / null` | Whether the instrument is a Real World Asset (stock/ETF/commodity) contract. Populated by ccxt (bitget exchange only) and bitget_data. |
| `category` | `string / null` | Asset category (e.g. 'Stocks', 'ETF', 'Commodity'). bitget_data only. |

Extended fields — **ccxt** provider only:

| Field | Type | Notes |
|---|---|---|
| `settle` | `string / null` | Settlement currency for derivatives (e.g. 'USDT' for linear, 'BTC' for inverse). |
| `active` | `boolean / null` | Whether the market is currently active/tradable. |
| `linear` | `boolean / null` | True for linear (USDT-margined) contracts. |
| `inverse` | `boolean / null` | True for inverse (coin-margined) contracts. |
| `contract_size` | `number / null` | Contract multiplier — size of one contract in base currency (derivatives only). |
| `expiry` | `string / null` | Expiry datetime for dated futures/options (UTC). |
| `exchange_id` | `string / null` | Exchange-native instrument ID (e.g. 'BTCUSDT'). |
| `taker` | `number / null` | Taker fee rate (e.g. 0.001 = 0.1%). |
| `maker` | `number / null` | Maker fee rate (e.g. 0.001 = 0.1%). |
| `precision_price` | `number / null` | Minimum price tick size. |
| `precision_amount` | `number / null` | Minimum order size in base currency. |

Extended fields — **bitget_data** provider only:

Core fields (all market types):

| Field | Type | Notes |
|---|---|---|
| `symbol_type` | `string / null` | Asset type of the trading pair: crypto, metal, stock, or commodity. |
| `status` | `string / null` | Market status: listed, online, limit_open, limit_close, offline, or restrictedAPI. |
| `launch_time` | `string / null` | Launch time of the trading pair (Unix ms timestamp). |
| `off_time` | `string / null` | Trading halt time (Unix ms timestamp). Empty string if not configured. |
| `limit_open_time` | `string / null` | Restricted open time (Unix ms timestamp). Non-empty means the symbol is under maintenance. |
| `price_precision` | `string / null` | Number of allowed decimal places for price. |
| `quantity_precision` | `string / null` | Number of allowed decimal places for quantity. |
| `quote_precision` | `string / null` | Number of allowed decimal places for the quote currency amount in market orders. |
| `price_multiplier` | `string / null` | Price step for derivatives orders (used together with price_precision). |
| `quantity_multiplier` | `string / null` | Quantity step for derivatives orders (used together with quantity_precision). |
| `min_order_qty` | `string / null` | Minimum order quantity in base currency (derivatives only). |
| `max_order_qty` | `string / null` | Maximum quantity for a single limit order in base currency. '0' means unlimited. |
| `min_order_amount` | `string / null` | Minimum order value in quote currency. |
| `max_market_order_qty` | `string / null` | Maximum quantity for a single market order in base currency. |
| `max_symbol_order_num` | `string / null` | Maximum number of outstanding orders per symbol per account. |
| `max_position_num` | `string / null` | Maximum number of open positions per symbol per account. |
| `buy_limit_price_ratio` | `string / null` | Buy limit price ratio relative to market price (max buy price cap). |
| `sell_limit_price_ratio` | `string / null` | Sell limit price ratio relative to market price (min sell price floor). |
| `maker_fee_rate` | `string / null` | Maker (limit order) fee rate as a decimal (e.g. '0.0002' = 0.02%). |
| `taker_fee_rate` | `string / null` | Taker (market order) fee rate as a decimal (e.g. '0.0002' = 0.02%). |

Derivatives-only fields (perpetual / futures; `null` for spot):

| Field | Type | Notes |
|---|---|---|
| `min_leverage` | `string / null` | Minimum leverage. |
| `max_leverage` | `string / null` | Maximum leverage. |
| `max_crossed_leverage` | `string / null` | Maximum leverage in cross-margin mode. |
| `max_isolated_leverage` | `string / null` | Maximum leverage in isolated-margin mode. |

---

### `crypto.market_dominance`

```python
data.crypto.market_dominance(symbol=None, interval='1d')
```

Summary: Market Dominance

| Field | Value |
|---|---|
| Endpoint ID | `crypto.market_dominance` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/market_dominance` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. If not provided, returns top cryptocurrencies. |
| `interval` | `no` | `string | null` | `1d` | Time interval for the data. Default is '1d'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `dominance` | `number` | Market dominance percentage (market cap / total market cap * 100). |
| `market_cap` | `number` | Market capitalization in USD. |
| `total_market_cap` | `number` | Total cryptocurrency market capitalization in USD. |

---

### `crypto.nft_info`

```python
data.crypto.nft_info(nft_id=...)
```

Summary: Nft Info

| Field | Value |
|---|---|
| Endpoint ID | `crypto.nft_info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/nft_info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `nft_id` | `yes` | `string` | `-` | CoinGecko NFT ID e.g. 'pudgy-penguins'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | CoinGecko NFT collection ID. |
| `name` | `string` | NFT collection name. |
| `symbol` | `string` | NFT collection symbol. |
| `contract_address` | `string` | NFT contract address. |
| `asset_platform_id` | `string` | Asset platform identifier. |
| `image` | `string` | Small image URL for the collection. |
| `description` | `string` | Collection description. |
| `floor_price_usd` | `number` | Floor price in USD. |
| `market_cap_usd` | `number` | Market cap in USD. |
| `volume_24h_usd` | `number` | 24h volume in USD. |
| `floor_price_change_24h_pct` | `number` | Floor price 24h percentage change in USD. |
| `number_of_unique_addresses` | `integer` | Number of unique holder addresses. |
| `total_supply` | `number` | Total supply of the NFT collection. |

---

### `crypto.nft_list`

```python
data.crypto.nft_list(per_page=None, page=None)
```

Summary: Nft List

| Field | Value |
|---|---|
| Endpoint ID | `crypto.nft_list` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/nft_list` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `per_page` | `no` | `integer | null` | `-` | Number of results per page. |
| `page` | `no` | `integer | null` | `-` | Page number for paginated results. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | CoinGecko NFT collection ID. |
| `contract_address` | `string` | NFT contract address. |
| `name` | `string` | NFT collection name. |
| `asset_platform_id` | `string` | Asset platform identifier (e.g. 'ethereum'). |
| `symbol` | `string` | NFT collection symbol. |

---

### `crypto.onchain.active_addresses`

```python
data.crypto.onchain.active_addresses(symbol=..., interval='1d')
```

Summary: Active Addresses

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.active_addresses` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/active_addresses` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `interval` | `no` | `string | null` | `1d` | Time interval for the data. Default is '1d'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `active_addresses` | `integer` | Number of active addresses on the blockchain network. |
| `new_addresses` | `integer` | Number of new addresses created. |
| `sending_addresses` | `integer` | Number of addresses sending transactions. |
| `receiving_addresses` | `integer` | Number of addresses receiving transactions. |

---

### `crypto.onchain.dexes`

```python
data.crypto.onchain.dexes(network=..., page=None)
```

Summary: Dexes

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.dexes` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/dexes` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `network` | `yes` | `string` | `-` | Network identifier, e.g. 'eth', 'bsc'. |
| `page` | `no` | `integer | null` | `-` | Page number for pagination. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | DEX identifier. |
| `name` | `string` | DEX name. |

---

### `crypto.onchain.exchange_flows`

```python
data.crypto.onchain.exchange_flows(symbol=..., exchange=None, startTime=None, endTime=None)
```

Summary: Exchange Flows — per-exchange cryptocurrency balance and flow data

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.exchange_flows` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/exchange_flows` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Two providers with different schemas. **bitget_data** returns per-exchange balance snapshots with 1d/7d/30d balance changes. **coinglass** returns aggregated inflow/outflow time series derived from exchange balance history. |

#### Query parameters

Parameters differ by provider.

**bitget_data** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Token symbol, e.g. `BTC`. |
| `exchange` | `no` | `string / null` | `-` | Exchange name filter, e.g. `Binance`, `Coinbase`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `provider` | `no` | `string` | `bitget_data` | - |

**coinglass** provider:

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Base-asset symbol, e.g. `BTC`. |
| `exchange` | `no` | `string / null` | `-` | Specific exchange to query. If omitted, returns aggregated data across all exchanges. |
| `provider` | `no` | `string` | `coinglass` | Requires CoinGlass API key. |

#### Response fields

**bitget_data** provider:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Token symbol. |
| `exchange` | `string` | Exchange name, e.g. `Binance`, `Coinbase`. |
| `total_balance` | `number` | Total asset balance on the exchange (in native tokens). |
| `balance_change_1d` | `number` | Balance change over the last 24 hours (in native tokens). |
| `balance_change_percent_1d` | `number` | Balance change percentage over the last 24 hours. |
| `balance_change_7d` | `number` | Balance change over the last 7 days (in native tokens). |
| `balance_change_percent_7d` | `number` | Balance change percentage over the last 7 days. |
| `balance_change_30d` | `number` | Balance change over the last 30 days (in native tokens). |
| `balance_change_percent_30d` | `number` | Balance change percentage over the last 30 days. |
| `ts` | `string` | Data timestamp. |

**coinglass** provider:

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Datetime of the data point (UTC). |
| `symbol` | `string` | Token symbol. |
| `exchange` | `string / null` | Exchange name. `null` when aggregated across all exchanges. |
| `inflow` | `number` | Amount flowing into exchanges (in native tokens). Derived from balance delta. |
| `outflow` | `number` | Amount flowing out of exchanges (in native tokens). Derived from balance delta. |
| `net_flow` | `number` | Net flow (inflow − outflow). |

---

### `crypto.onchain.stablecoin_flow`

```python
data.crypto.onchain.stablecoin_flow(startTime=None, endTime=None)
```

Summary: Stablecoin Flow — stablecoin holding and flow data

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.stablecoin_flow` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/stablecoin_flow` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `provider` | `no` | `string` | `bitget_data` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Stablecoin symbol. |
| `total_supply` | `number` | Total stablecoin supply. |
| `net_flow_1d` | `number` | Net flow over the last 1 day. |
| `net_flow_7d` | `number` | Net flow over the last 7 days. |
| `net_flow_30d` | `number` | Net flow over the last 30 days. |
| `ts` | `string` | Data timestamp. |

---

### `crypto.onchain.dex_liquidity_flow`

```python
data.crypto.onchain.dex_liquidity_flow(symbol=None, token_address=None, chain_name=None, startTime=None, endTime=None)
```

Summary: Dex Liquidity Flow — DEX liquidity pool holding and flow data

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.dex_liquidity_flow` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/dex_liquidity_flow` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string / null` | `-` | Token symbol, e.g. `ETH`, `USDT`. |
| `token_address` | `no` | `string / null` | `-` | Token contract address. |
| `chain_name` | `no` | `string / null` | `-` | Blockchain network name, e.g. `ETH`, `ethereum`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `provider` | `no` | `string` | `bitget_data` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Token symbol. |
| `token_address` | `string` | Token contract address. |
| `chain_name` | `string` | Blockchain network name. |
| `holding_balance` | `number` | Pool liquidity in USD from DexScreener. Returns `-1` when DexScreener association is unavailable. |
| `net_flow_1h` | `number` | Net flow over the last 1 hour. |
| `net_flow_4h` | `number` | Net flow over the last 4 hours. |
| `net_flow_1d` | `number` | Net flow over the last 1 day. |
| `net_flow_7d` | `number` | Net flow over the last 7 days. |
| `net_flow_30d` | `number` | Net flow over the last 30 days. |
| `ts` | `string` | Data timestamp. |

---

### `crypto.onchain.fund_flow`

```python
data.crypto.onchain.fund_flow(symbol=...)
```

Summary: Fund Flow

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.fund_flow` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/fund_flow` |
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
| `time` | `string` | Data timestamp. |
| `sell_amount_24h` | `number` | Total sell amount in token units over 24 hours. |
| `sell_value_24h` | `number` | Total sell value in USD over 24 hours. |
| `buy_amount_24h` | `number` | Total buy amount in token units over 24 hours. |
| `buy_value_24h` | `number` | Total buy value in USD over 24 hours. |
| `cex_inflow_1h` | `number` | CEX inflow amount over 1 hour. |
| `cex_outflow_1h` | `number` | CEX outflow amount over 1 hour. |
| `cex_inflow_6h` | `number` | CEX inflow amount over 6 hours. |
| `cex_outflow_6h` | `number` | CEX outflow amount over 6 hours. |
| `cex_inflow_24h` | `number` | CEX inflow amount over 24 hours. |
| `cex_outflow_24h` | `number` | CEX outflow amount over 24 hours. |

---

### `crypto.onchain.holder_statics`

```python
data.crypto.onchain.holder_statics(symbol=...)
```

Summary: Holder Statics

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.holder_statics` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/holder_statics` |
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
| `time` | `string` | Data timestamp. |
| `chain` | `string` | Blockchain network name. |
| `token_address` | `string` | Token contract address on the chain. |
| `holders` | `integer` | Total number of token holders. |
| `hold_hhi` | `number` | Herfindahl-Hirschman Index for holder concentration. |
| `total_supply` | `number` | Total token supply. |
| `circulating_supply` | `number` | Circulating token supply. |
| `cex_amount` | `number` | Amount held by centralized exchanges. |
| `dex_pool_amount` | `number` | Amount in DEX liquidity pools. |
| `staking_amount` | `number` | Amount staked. |
| `lending_amount` | `number` | Amount in lending protocols. |
| `top_100_address_hold_percentage` | `number` | Percentage held by top 100 addresses. |

---

### `crypto.onchain.hyperliquid_liquidation_map`

```python
data.crypto.onchain.hyperliquid_liquidation_map(symbol=...)
```

Summary: Hyperliquid Liquidation Map

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.hyperliquid_liquidation_map` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/hyperliquid_liquidation_map` |
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
| `symbol` | `string` | Symbol to get data for. |
| `liquidation_price` | `number` | Liquidation price level. |
| `liquidation_intensity` | `number` | Liquidation intensity at this price level (in USD). |

---

### `crypto.onchain.liquidity`

```python
data.crypto.onchain.liquidity(symbol=..., chain=None)
```

Summary: Liquidity

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.liquidity` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/liquidity` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `chain` | `no` | `string | null` | `-` | Blockchain network (e.g., 'BSC', 'ETH', 'SOL'). If not provided, returns all chains. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `time` | `string` | Data timestamp. |
| `symbol` | `string` | Symbol to get data for. |
| `chain` | `string` | Blockchain network name. |
| `token_address` | `string` | Token contract address on the chain. |
| `price` | `number` | Token price in USD. |
| `liquidity` | `number` | Aggregated DEX liquidity amount in USD. |

---

### `crypto.onchain.networks`

```python
data.crypto.onchain.networks(page=None)
```

Summary: Networks

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.networks` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/networks` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `page` | `no` | `integer | null` | `-` | Page number for pagination. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | Network identifier, e.g. 'eth', 'bsc'. |
| `name` | `string` | Network name. |
| `coingecko_asset_platform_id` | `string` | CoinGecko asset platform identifier. |

---

### `crypto.onchain.pool_detail`

```python
data.crypto.onchain.pool_detail(network=..., pool_address=...)
```

Summary: Pool Detail

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.pool_detail` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/pool_detail` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `network` | `yes` | `string` | `-` | Network identifier, e.g. 'eth'. |
| `pool_address` | `yes` | `string` | `-` | Pool address(es). Comma-separated for multi-pool query. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | Pool identifier. |
| `name` | `string` | Pool name, e.g. 'USDC / WETH'. |
| `address` | `string` | Pool contract address. |
| `base_token_price_usd` | `number` | Base token price in USD. |
| `quote_token_price_usd` | `number` | Quote token price in USD. |
| `fdv_usd` | `number` | Fully diluted valuation in USD. |
| `market_cap_usd` | `number` | Market cap in USD. |
| `reserve_in_usd` | `number` | Total reserve in USD. |
| `volume_usd_h_24` | `number` | 24-hour trading volume in USD. |
| `price_change_h_24` | `number` | 24-hour price change percentage. |
| `buys_h_24` | `integer` | Number of buy transactions in the last 24 hours. |
| `sells_h_24` | `integer` | Number of sell transactions in the last 24 hours. |
| `pool_created_at` | `string` | Pool creation timestamp. |

---

### `crypto.onchain.pool_ohlcv`

```python
data.crypto.onchain.pool_ohlcv(network=..., pool_address=..., start_time=None, end_time=None, timeframe='day', aggregate=None, limit=None, currency=None)
```

Summary: Pool Ohlcv

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.pool_ohlcv` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/pool_ohlcv` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `network` | `yes` | `string` | `-` | Network ID e.g. 'eth'. |
| `pool_address` | `yes` | `string` | `-` | Pool contract address. |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `timeframe` | `no` | `string` | `day` | OHLCV timeframe: 'day' or 'hour' or 'minute'. |
| `aggregate` | `no` | `string | null` | `-` | Aggregate period e.g. '1' for 1-day/hour/minute. |
| `limit` | `no` | `integer | null` | `-` | Number of OHLCV data points. |
| `currency` | `no` | `string | null` | `-` | Price currency: 'usd' or 'token'. |

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

---

### `crypto.onchain.pool_trades`

```python
data.crypto.onchain.pool_trades(network=..., pool_address=..., trade_volume_in_usd_greater_than=None)
```

Summary: Pool Trades

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.pool_trades` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/pool_trades` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `network` | `yes` | `string` | `-` | Network ID e.g. 'eth'. |
| `pool_address` | `yes` | `string` | `-` | Pool contract address. |
| `trade_volume_in_usd_greater_than` | `no` | `number | null` | `-` | Filter by minimum trade volume in USD. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `block_timestamp` | `string` | Block timestamp of the trade. |
| `tx_hash` | `string` | Transaction hash. |
| `kind` | `string` | Trade kind: 'buy' or 'sell'. |
| `from_token_symbol` | `string` | Symbol of the source token. |
| `from_token_amount` | `string` | Amount of the source token. |
| `to_token_symbol` | `string` | Symbol of the destination token. |
| `to_token_amount` | `string` | Amount of the destination token. |
| `price_from_in_usd` | `string` | Source token price in USD. |
| `price_to_in_usd` | `string` | Destination token price in USD. |
| `volume_in_usd` | `string` | Trade volume in USD. |

---

### `crypto.onchain.pools`

```python
data.crypto.onchain.pools(list_type=..., network=None, token_address=None, page=None)
```

Summary: Pools

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.pools` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/pools` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `list_type` | `yes` | `string` | `-` | Pool list type: 'trending', 'new', 'top', 'token_pools'. |
| `network` | `no` | `string | null` | `-` | Network ID e.g. 'eth'. Required for 'top' and 'token_pools'. Optional for 'trending' and 'new' (omit for cross-network). |
| `token_address` | `no` | `string | null` | `-` | Token contract address. Required for 'token_pools'. |
| `page` | `no` | `integer | null` | `-` | Page number for pagination. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | Pool identifier. |
| `name` | `string` | Pool name, e.g. 'USDC / WETH'. |
| `address` | `string` | Pool contract address. |
| `base_token_price_usd` | `number` | Base token price in USD. |
| `quote_token_price_usd` | `number` | Quote token price in USD. |
| `fdv_usd` | `number` | Fully diluted valuation in USD. |
| `market_cap_usd` | `number` | Market cap in USD. |
| `reserve_in_usd` | `number` | Total reserve in USD. |
| `volume_usd_h_24` | `number` | 24-hour trading volume in USD. |
| `price_change_h_24` | `number` | 24-hour price change percentage. |
| `buys_h_24` | `integer` | Number of buy transactions in the last 24 hours. |
| `sells_h_24` | `integer` | Number of sell transactions in the last 24 hours. |
| `pool_created_at` | `string` | Pool creation timestamp. |

---

### `crypto.onchain.search_pools`

```python
data.crypto.onchain.search_pools(query=..., network=None, page=None)
```

Summary: Search Pools

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.search_pools` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/search_pools` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `yes` | `string` | `-` | Search query — pool address, token name, symbol, or address. |
| `network` | `no` | `string | null` | `-` | Network identifier to filter results, e.g. 'eth'. |
| `page` | `no` | `integer | null` | `-` | Page number for pagination. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | Pool identifier. |
| `name` | `string` | Pool name, e.g. 'USDC / WETH'. |
| `address` | `string` | Pool contract address. |
| `base_token_price_usd` | `number` | Base token price in USD. |
| `quote_token_price_usd` | `number` | Quote token price in USD. |
| `fdv_usd` | `number` | Fully diluted valuation in USD. |
| `market_cap_usd` | `number` | Market cap in USD. |
| `reserve_in_usd` | `number` | Total reserve in USD. |
| `volume_usd_h_24` | `number` | 24-hour trading volume in USD. |
| `price_change_h_24` | `number` | 24-hour price change percentage. |
| `buys_h_24` | `integer` | Number of buy transactions in the last 24 hours. |
| `sells_h_24` | `integer` | Number of sell transactions in the last 24 hours. |
| `pool_created_at` | `string` | Pool creation timestamp. |

---

### `crypto.onchain.token_data`

```python
data.crypto.onchain.token_data(network=..., address=...)
```

Summary: Token Data

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.token_data` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/token_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `network` | `yes` | `string` | `-` | Network ID e.g. 'eth'. |
| `address` | `yes` | `string` | `-` | Token contract address. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | Token identifier. |
| `name` | `string` | Token name. |
| `symbol` | `string` | Token symbol. |
| `address` | `string` | Token contract address. |
| `decimals` | `integer` | Token decimals. |
| `coingecko_coin_id` | `string` | CoinGecko coin ID. |
| `price_usd` | `number` | Token price in USD. |
| `fdv_usd` | `number` | Fully diluted valuation in USD. |
| `total_reserve_in_usd` | `number` | Total reserve in USD. |
| `volume_usd_h_24` | `number` | 24-hour trading volume in USD. |
| `market_cap_usd` | `number` | Market cap in USD. |

---

### `crypto.onchain.token_info`

```python
data.crypto.onchain.token_info(network=..., address=...)
```

Summary: Token Info

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.token_info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/token_info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `network` | `yes` | `string` | `-` | Network ID e.g. 'eth'. |
| `address` | `yes` | `string` | `-` | Token contract address. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `id` | `string` | Token identifier. |
| `name` | `string` | Token name. |
| `symbol` | `string` | Token symbol. |
| `coingecko_coin_id` | `string` | CoinGecko coin ID. |
| `image_url` | `string` | Token image URL. |
| `description` | `string` | Token description. |
| `websites` | `array` | Official website URLs. |
| `discord_url` | `string` | Discord URL. |
| `telegram_handle` | `string` | Telegram handle. |
| `twitter_handle` | `string` | Twitter/X handle. |

---

### `crypto.onchain.token_price`

```python
data.crypto.onchain.token_price(network=..., addresses=...)
```

Summary: Token Price

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.token_price` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/token_price` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `network` | `yes` | `string` | `-` | Network ID e.g. 'eth'. |
| `addresses` | `yes` | `string` | `-` | Token contract address(es), comma-separated. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `contract_address` | `string` | Token contract address. |
| `price` | `number` | Token price in the target currency. |
| `market_cap` | `number` | Market capitalization. |
| `volume_24h` | `number` | 24-hour trading volume. |
| `change_24h` | `number` | 24-hour price change percentage. |
| `last_updated_at` | `integer` | Last update timestamp (UNIX). |

---

### `crypto.onchain.token_unlock_event`

```python
data.crypto.onchain.token_unlock_event(symbol=...)
```

Summary: Token Unlock Event

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.token_unlock_event` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/token_unlock_event` |
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
| `token_address` | `string` | Token contract address. |
| `total_supply` | `number` | Total token supply. |
| `circulate_supply` | `number` | Current circulating token supply. |
| `unlock_time` | `string` | Scheduled unlock event timestamp. |
| `unlock_amount` | `number` | Number of tokens to be unlocked. |
| `unlock_percentage` | `number` | Percentage of total supply to be unlocked. |

---

### `crypto.onchain.trading_signal`

```python
data.crypto.onchain.trading_signal(symbol=..., signal_types=None)
```

Summary: Trading Signal

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.trading_signal` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/trading_signal` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `signal_types` | `no` | `array | null` | `-` | accepts array values List of signal type IDs to filter. 1=whale large inflow, 2=whale large outflow, 3=net buy signal, 4=net sell signal. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `time` | `string` | Signal timestamp. |
| `symbol` | `string` | Symbol to get data for. |
| `signal_type` | `integer` | Signal type ID. 1=whale large inflow, 2=whale large outflow, 3=net buy signal, 4=net sell signal. |
| `signal_text` | `string` | Human-readable signal description. |

---

### `crypto.onchain.whale_transactions`

```python
data.crypto.onchain.whale_transactions(symbol=..., min_amount=None, interval='1h')
```

Summary: Whale Transactions

| Field | Value |
|---|---|
| Endpoint ID | `crypto.onchain.whale_transactions` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/onchain/whale_transactions` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `min_amount` | `no` | `number | null` | `-` | Minimum transaction amount threshold in USD. If not provided, uses API default. |
| `interval` | `no` | `string | null` | `1h` | Time interval for the data. Default is '1h'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `transaction_count` | `integer` | Number of large transactions (whale transactions). |
| `total_amount` | `number` | Total amount transacted in USD. |
| `average_amount` | `number` | Average transaction amount in USD. |
| `largest_transaction` | `number` | Largest single transaction amount in USD. |

---

### `crypto.options.open_interest`

```python
data.crypto.options.open_interest(symbol=..., interval='1d')
```

Summary: Open Interest

| Field | Value |
|---|---|
| Endpoint ID | `crypto.options.open_interest` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/options/open_interest` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `interval` | `no` | `string | null` | `1d` | Time interval for the data. Default is '1d'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `call_oi` | `number` | Call option open interest. |
| `put_oi` | `number` | Put option open interest. |
| `total_oi` | `number` | Total options open interest (calls + puts). |
| `put_call_oi_ratio` | `number` | Put/Call open interest ratio. |

---

### `crypto.options.volume`

```python
data.crypto.options.volume(symbol=..., interval='1d', option_type='all')
```

Summary: Volume

| Field | Value |
|---|---|
| Endpoint ID | `crypto.options.volume` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/options/volume` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `interval` | `no` | `string | null` | `1d` | Time interval for the data. Default is '1d'. |
| `option_type` | `no` | `string | null` | `all` | Option type: 'call', 'put', or 'all'. Default is 'all'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `call_volume` | `number` | Call option trading volume. |
| `put_volume` | `number` | Put option trading volume. |
| `total_volume` | `number` | Total options trading volume (calls + puts). |
| `put_call_ratio` | `number` | Put/Call volume ratio. |

---

### `crypto.search`

```python
data.crypto.search(query=None)
```

Summary: Search

| Field | Value |
|---|---|
| Endpoint ID | `crypto.search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string | null` | `-` | Search query. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `name` | `string` | Name of the crypto. |
| `exchange` | `string` | The exchange code the crypto trades on. |
| `ico_date` | `string` | The ICO date of the token. |
| `circulating_supply` | `number` | The circulating supply of the token. |
| `total_supply` | `number` | The total supply of the token. |
| `coin_id` | `string` | CoinGecko coin identifier. |
| `market_cap_rank` | `integer` | Market cap rank. |
| `thumb` | `string` | Small icon URL. |

---

### `crypto.sentiment.crypto_fear_greed`

```python
data.crypto.sentiment.crypto_fear_greed(limit=30, interval=None)
```

Summary: Crypto Fear Greed

| Field | Value |
|---|---|
| Endpoint ID | `crypto.sentiment.crypto_fear_greed` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/sentiment/crypto_fear_greed` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `limit` | `no` | `integer` | `30` | Number of days of historical data to return. Default 30. Max 1000. |
| `interval` | `no` | `string | null` | `-` | Time interval for historical data (e.g. '1d', '1h', '4h'). Provider-specific. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Datetime of the index reading. |
| `value` | `integer` | Fear & Greed Index value (0-100). 0 = Extreme Fear, 50 = Neutral, 100 = Extreme Greed. |
| `classification` | `string` | Human-readable classification: 'Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'. |

---

### `crypto.spot.exchange_volume`

```python
data.crypto.spot.exchange_volume(symbol=..., exchange=None)
```

Summary: Exchange Volume

| Field | Value |
|---|---|
| Endpoint ID | `crypto.spot.exchange_volume` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/spot/exchange_volume` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `exchange` | `no` | `string | null` | `-` | Specific exchange to query. If not provided, returns all exchanges. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `exchange` | `string` | Exchange name. |
| `volume` | `number` | Trading volume in USD. |
| `volume_percentage` | `number` | Percentage of total volume across all exchanges. |

---

### `crypto.spot.kline`

```python
data.crypto.spot.kline(symbol=..., interval='1d', exchange='binance', limit=1000, start_time=None, end_time=None, start_date=None, end_date=None, days=None, vs_currency='usd', data_type='ohlc', exchanges=None, closed_only=True)
```

Summary: Kline

| Field | Value |
|---|---|
| Endpoint ID | `crypto.spot.kline` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/spot/kline` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Backs spot OHLCV fetches today. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `interval` | `no` | `string` | `1d` | Candlestick interval. Supported values: 5m, 15m, 1h, 4h, 1d. |
| `exchange` | `no` | `string` | `binance` | Exchange identifier. Supported: binance, bitget. |
| `limit` | `no` | `integer | null` | `1000` | Maximum number of candles to return. Capped at 1000. |
| `start_time` | `no` | `integer | null` | `-` | Start time as Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time as Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `start_date` | `no` | `string | null` | `-` | Start date in YYYY-MM-DD format. Defaults to 90 days ago when neither start_date nor days is specified. |
| `end_date` | `no` | `string | null` | `-` | End date in YYYY-MM-DD format. Defaults to today. |
| `days` | `no` | `integer | null` | `-` | Number of days to look back from end_date (or today). Range: 1–90. Takes precedence over start_date when both are provided. |
| `vs_currency` | `no` | `string` | `usd` | Target currency for prices. Default is 'usd'. |
| `data_type` | `no` | `string` | `ohlc` | enum: ohlc, market_chart Data type: 'ohlc' for OHLC candles, 'market_chart' for close-only price history. |
| `exchanges` | `no` | `array | string | null` | `-` | accepts array values To limit the query to a subset of exchanges e.g. ['POLONIEX', 'GDAX'] Multiple comma separated items allowed. |
| `closed_only` | `no` | `boolean` | `true` | **SDK-side parameter, not sent upstream.** When `true` (default) the SDK drops bars that have not closed yet (`open_time + interval > now`). Pass `false` to keep the forming candle. |

> **Time range**: Maximum window is **90 days**. Longer requests are silently clamped — never assume the full range came back; verify the earliest returned `time`.

> **Kline semantics** (verified behavior — read before writing fetch logic):
>
> - **The raw upstream response includes the currently-forming candle.** Its OHLCV drifts on every call until the bar closes, so decisions made on it repaint. The SDK removes it by default (`closed_only=True`); pass `closed_only=False` only when you explicitly want the live partial bar, and never trade on that bar's close.
> - **Bar timestamps are open time.** The canonical `time` field is the bar's open time as a millisecond Unix epoch (UTC); a bar covers `[time, time + interval)` and is final only once `time + interval <= now`. The legacy `date` string mirrors the open time.
> - **`limit` is capped at 1000 and truncation is silent, anchored to the window end.** When the requested window holds more than `limit` bars you receive the most recent `limit` bars, not the earliest. Paginate with `start_time`/`end_time` chunks instead of raising `limit`.
> - **`end_time` is a loose upper bound.** The response may include bars at or beyond `end_time`. Clip client-side and de-duplicate by `time` when stitching pages.
> - **Freshness check for live strategies:** after fetching, assert the newest closed bar is recent (refuse to act when `now - (last_time + interval) > 2 * interval`) so a stalled feed cannot silently drive decisions.
> - On SDK builds that predate `closed_only`, filter manually: `df = df[df.index + pd.Timedelta(interval) <= pd.Timestamp.now(tz="UTC")]`.

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
| `exchange` | `string` | Exchange the data was fetched from. |
| `symbol` | `string` | Trading pair symbol. |
| `interval` | `string` | Candlestick interval. |

#### Verified Playbook usage notes

- **Exchange resolution required**: before passing `exchange=` to this endpoint, call `data.crypto.market(symbol="BTC/USDT", market_type="spot", exchange=<target>)` and verify the symbol has an active row for that exchange. An unsupported symbol+exchange combination returns an empty response. Extract `exchange_id` from the market response as the exchange-native symbol and `exchange` as the exchange identifier for this call.
- Use this endpoint for spot OHLCV. For contract / futures Playbooks, use `crypto.futures.kline` instead.

---

### `crypto.spot.order_book`

```python
data.crypto.spot.order_book(symbol=..., limit=20, exchange='binance')
```

Summary: Order Book

| Field | Value |
|---|---|
| Endpoint ID | `crypto.spot.order_book` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/spot/order_book` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer` | `20` | Depth of the order book — number of bid and ask levels to return. |
| `exchange` | `no` | `string` | `binance` | Exchange to fetch data from. Supported: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid. |

---

### `crypto.spot.price_spread`

```python
data.crypto.spot.price_spread(symbol=..., interval='1h')
```

Summary: Price Spread

| Field | Value |
|---|---|
| Endpoint ID | `crypto.spot.price_spread` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/spot/price_spread` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `interval` | `no` | `string | null` | `1h` | Time interval for the data. Default is '1h'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. |
| `symbol` | `string` | Symbol to get data for. |
| `max_price` | `number` | Highest price across all exchanges. |
| `min_price` | `number` | Lowest price across all exchanges. |
| `spread` | `number` | Absolute price difference (max - min). |
| `spread_percentage` | `number` | Price spread as a percentage of the average price. |
| `max_exchange` | `string` | Exchange with the highest price. |
| `min_exchange` | `string` | Exchange with the lowest price. |

---

### `crypto.spot.taker_volume`

```python
data.crypto.spot.taker_volume(symbol=..., interval='1h', limit=30, start_time=None, end_time=None, exchange='Binance')
```

Summary: Taker Volume

| Field | Value |
|---|---|
| Endpoint ID | `crypto.spot.taker_volume` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/spot/taker_volume` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Trading pair symbol (e.g., BTCUSDT) |
| `interval` | `no` | `string` | `1h` | Aggregation interval (5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d) |
| `limit` | `no` | `integer | null` | `30` | Number of results (max 500). |
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `exchange` | `no` | `string` | `Binance` | Exchange name (e.g. Binance, OKX, Bybit). Can be obtained from support-exchange-pair endpoint. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `buy_sell_ratio` | `number` | Taker buy to sell volume ratio. |
| `buy_vol` | `number` | Taker buy volume. |
| `sell_vol` | `number` | Taker sell volume. |
| `timestamp` | `integer` | Unix timestamp. |

---

### `crypto.spot.footprint_history`

```python
data.crypto.spot.footprint_history(symbol=..., exchange='Binance', interval='4h', limit=100, start_time=None, end_time=None)
```

Summary: Footprint History — spot market footprint (volume at price) history

| Field | Value |
|---|---|
| Endpoint ID | `crypto.spot.footprint_history` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/spot/footprint_history` |
| Default provider | `coinglass` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Provides historical footprint chart data for spot markets, including active buy and sell volume at each price level within each time bucket. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Trading pair symbol (e.g., `BTCUSDT`). |
| `exchange` | `no` | `string` | `Binance` | Spot exchange name: `Binance`, `OKX`, `Bybit`, `Coinbase`. |
| `interval` | `no` | `string` | `4h` | enum: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `4h`, `6h`, `8h`, `12h`, `1d`, `1w`. |
| `limit` | `no` | `integer / null` | `100` | Number of time buckets to return (max 1000). |
| `start_time` | `no` | `integer / null` | `-` | Start time as Unix timestamp in milliseconds. |
| `end_time` | `no` | `integer / null` | `-` | End time as Unix timestamp in milliseconds. |
| `provider` | `no` | `string` | `coinglass` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `timestamp` | `integer` | Unix timestamp in seconds for the time bucket. |
| `exchange` | `string` | Spot exchange name. |
| `symbol` | `string` | Trading pair symbol. |
| `price_start` | `number` | Start price of the footprint level. |
| `price_end` | `number` | End price of the footprint level. |
| `buy_volume` | `number` | Active buy volume (base asset). |
| `sell_volume` | `number` | Active sell volume (base asset). |
| `buy_volume_quote` | `number` | Active buy volume in quote currency. |
| `sell_volume_quote` | `number` | Active sell volume in quote currency. |
| `buy_volume_usdt` | `number` | Active buy volume in USDT. |
| `sell_volume_usdt` | `number` | Active sell volume in USDT. |
| `buy_trade_count` | `integer` | Number of active buy trades. |
| `sell_trade_count` | `integer` | Number of active sell trades. |

---

### `crypto.spot.ticker`

```python
data.crypto.spot.ticker(symbol=..., exchange='binance', vs_currency='usd', include_market_data=True)
```

Summary: Ticker

| Field | Value |
|---|---|
| Endpoint ID | `crypto.spot.ticker` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/spot/ticker` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Backs spot price latest fetches today. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `exchange` | `no` | `string` | `binance` | enum: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid Exchange to fetch data from. Supported: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid. |
| `vs_currency` | `no` | `string` | `usd` | Target currency for prices. Default is 'usd'. |
| `include_market_data` | `no` | `boolean` | `true` | Use /coins/markets for richer data (market cap, volume, 24h change). Set to False to use /simple/price for a faster, lighter response. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Symbol representing the entity requested in the data. |
| `exchange` | `string` | Exchange or venue the data was fetched from. |
| `timestamp` | `string` | Timestamp of the ticker snapshot (UTC). |
| `last` | `number` | Last traded price. |
| `open` | `number` | The open price (24h rolling window). |
| `high` | `number` | The high price (24h rolling window). |
| `low` | `number` | The low price (24h rolling window). |
| `bid` | `number` | Current best bid price. |
| `ask` | `number` | Current best ask price. |
| `vwap` | `number` | Volume Weighted Average Price over the period. |
| `volume` | `number` | The trading volume (base currency, 24h). |
| `quote_volume` | `number` | 24h trading volume in quote currency. |
| `prev_close` | `number` | The previous close price. |
| `change` | `number` | Absolute price change over 24h. |
| `change_percent` | `number` | Percentage price change over 24h. |
| `market_cap` | `number` | Market capitalization in quote currency. |
| `bid_volume` | `number` | Volume at the best bid. |
| `ask_volume` | `number` | Volume at the best ask. |
| `average` | `number` | Average of open and last price. |
| `coin_id` | `string` | CoinGecko coin identifier. |
| `market_cap_rank` | `integer` | Market cap rank. |
| `fully_diluted_valuation` | `number` | Fully diluted valuation in quote currency. |
| `circulating_supply` | `number` | Circulating supply. |
| `total_supply` | `number` | Total supply. |

---

### `crypto.spot.trades`

```python
data.crypto.spot.trades(symbol=..., limit=100, exchange='binance')
```

Summary: Trades

| Field | Value |
|---|---|
| Endpoint ID | `crypto.spot.trades` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/spot/trades` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Symbol to get data for. |
| `limit` | `no` | `integer` | `100` | Number of most recent trades to return. |
| `exchange` | `no` | `string` | `binance` | Exchange to fetch data from. Supported: binance, bitget, okx, bybit, coinbase, upbit, gateio, kucoin, mexc, htx, cryptocom, bitfinex, bingx, kraken, bitmart, lbank, bitstamp, bithumb, hyperliquid. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `trade_id` | `string` | Exchange-assigned trade ID. |
| `symbol` | `string` | Trading pair symbol. |
| `timestamp` | `string` | Trade execution time (UTC). |
| `side` | `string` | Taker side: buy or sell. |
| `price` | `number` | Execution price. |
| `amount` | `number` | Trade size in base currency. |
| `cost` | `number` | Trade value in quote currency (price × amount). |
| `taker_or_maker` | `string` | Whether the trade was executed as taker or maker. |

---

### `crypto.supported_currencies`

```python
data.crypto.supported_currencies()
```

Summary: Supported Currencies

| Field | Value |
|---|---|
| Endpoint ID | `crypto.supported_currencies` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/supported_currencies` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `currency` | `string` | Supported currency code (e.g. 'usd', 'btc'). |

---

### `crypto.token_price`

```python
data.crypto.token_price(platform_id=..., contract_addresses=..., vs_currencies='usd')
```

Summary: Token Price

| Field | Value |
|---|---|
| Endpoint ID | `crypto.token_price` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/token_price` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `platform_id` | `yes` | `string` | `-` | Asset platform identifier (e.g. 'ethereum', 'binance-smart-chain', 'polygon-pos'). |
| `contract_addresses` | `yes` | `string` | `-` | Comma-separated token contract addresses. |
| `vs_currencies` | `no` | `string` | `usd` | Comma-separated target currencies (e.g. 'usd,btc'). Default is 'usd'. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `contract_address` | `string` | Token contract address. |
| `price` | `number` | Token price in the target currency. |
| `market_cap` | `number` | Market capitalization. |
| `volume_24h` | `number` | 24-hour trading volume. |
| `change_24h` | `number` | 24-hour price change percentage. |
| `last_updated_at` | `integer` | Last update timestamp (UNIX). |

---

### `crypto.treasury`

```python
data.crypto.treasury(symbol=...)
```

Summary: Treasury

| Field | Value |
|---|---|
| Endpoint ID | `crypto.treasury` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/treasury` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Cryptocurrency symbol ('BTC' or 'ETH'). Only Bitcoin and Ethereum are supported. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `name` | `string` | Company or entity name. |
| `symbol` | `string` | Stock ticker symbol of the company. |
| `country` | `string` | Country of the company. |
| `total_holdings` | `number` | Total crypto holdings. |
| `total_entry_value_usd` | `number` | Total entry value in USD. |
| `total_current_value_usd` | `number` | Total current value in USD. |
| `percentage_of_total_supply` | `number` | Percentage of total coin supply held. |

---

### `crypto.trending`

```python
data.crypto.trending()
```

Summary: Trending

| Field | Value |
|---|---|
| Endpoint ID | `crypto.trending` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/trending` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `coin_id` | `string` | CoinGecko coin identifier. |
| `name` | `string` | Coin name. |
| `symbol` | `string` | Coin ticker symbol. |
| `market_cap_rank` | `integer` | Market capitalization rank. |
| `thumb` | `string` | Small icon URL. |
| `price_btc` | `number` | Price denominated in BTC. |
| `score` | `integer` | Trending score (lower is more trending). |

---

### `crypto.indicators.bitcoin_nupl`

```python
data.crypto.indicators.bitcoin_nupl()
```

Summary: Bitcoin NUPL — net unrealized profit/loss history

| Field | Value |
|---|---|
| Endpoint ID | `crypto.indicators.bitcoin_nupl` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/indicators/bitcoin_nupl` |
| Default provider | `coinglass` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Returns full historical NUPL data from CoinGlass. No query filters are supported. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `provider` | `no` | `string` | `coinglass` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Datetime of the NUPL reading (UTC). |
| `price` | `number` | Bitcoin price in USD at the reading time. |
| `net_unpnl` | `number` | Net unrealized profit/loss ratio across the network. |

---

### `crypto.indicators.bitcoin_sopr`

```python
data.crypto.indicators.bitcoin_sopr(holder_type='short')
```

Summary: Bitcoin SOPR — holder spent output profit ratio

| Field | Value |
|---|---|
| Endpoint ID | `crypto.indicators.bitcoin_sopr` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/indicators/bitcoin_sopr` |
| Default provider | `coinglass` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Values above 1 indicate profit-taking; below 1 indicate loss realization. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `holder_type` | `no` | `string` | `short` | enum: `short`, `long`. `short` = short-term holder SOPR; `long` = long-term holder SOPR. |
| `provider` | `no` | `string` | `coinglass` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Datetime of the SOPR reading (UTC). |
| `holder_type` | `string` | Holder cohort: `short` or `long`. |
| `price` | `number` | Bitcoin price in USD at the reading time. |
| `sopr` | `number` | Spent output profit ratio for the selected holder cohort. |

---

### `crypto.indicators.coinbase_premium_index`

```python
data.crypto.indicators.coinbase_premium_index(interval='1d', limit=100, start_time=None, end_time=None)
```

Summary: Coinbase Premium Index — Coinbase vs Binance Bitcoin price premium

| Field | Value |
|---|---|
| Endpoint ID | `crypto.indicators.coinbase_premium_index` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/indicators/coinbase_premium_index` |
| Default provider | `coinglass` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Reflects the price difference between Bitcoin on Coinbase and Binance. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `interval` | `no` | `string` | `1d` | enum: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `4h`, `6h`, `8h`, `12h`, `1d`, `1w`. |
| `limit` | `no` | `integer / null` | `100` | Number of data points to return (max 1000). |
| `start_time` | `no` | `integer / null` | `-` | Start time as Unix timestamp in milliseconds. |
| `end_time` | `no` | `integer / null` | `-` | End time as Unix timestamp in milliseconds. |
| `provider` | `no` | `string` | `coinglass` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | Datetime of the index reading (UTC). |
| `premium` | `number` | Premium amount in USD (Coinbase price minus Binance price). |
| `premium_rate` | `number` | Premium rate as a decimal (e.g. `0.0261` = 2.61%). |
| `coinbase_price` | `number` | Coinbase closing price in USD. |

---

### `crypto.indicators.hyperliquid_whale_sentiment`

```python
data.crypto.indicators.hyperliquid_whale_sentiment(symbol=..., startTime=None, endTime=None, limit=100)
```

Summary: Hyperliquid Whale Sentiment — hourly whale sentiment metrics

| Field | Value |
|---|---|
| Endpoint ID | `crypto.indicators.hyperliquid_whale_sentiment` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/indicators/hyperliquid_whale_sentiment` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Returns long/short position ratios, taker volumes, TWAP volumes, sentiment scores, and labels across multiple time periods (1h to 7d). |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `yes` | `string` | `-` | Token symbol (TAG filter), e.g. `BTC`, `ETH`. |
| `startTime` | `no` | `integer / null` | `-` | Start timestamp in milliseconds (inclusive). |
| `endTime` | `no` | `integer / null` | `-` | End timestamp in milliseconds (inclusive). |
| `limit` | `no` | `integer` | `100` | Number of records to return (max 1000). Ordered by timestamp descending. |
| `provider` | `no` | `string` | `bitget_data` | - |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `timestamp` | `integer` | Reading timestamp in milliseconds. |
| `total_long_position_val` | `number` | Whale total long position value (USD). |
| `total_short_position_val` | `number` | Whale total short position value (USD). |
| `total_long_account_count` | `number` | Number of whale long accounts. |
| `total_short_account_count` | `number` | Number of whale short accounts. |
| `active_whale_count` | `integer` | Number of active whale accounts. |
| `current_price` | `number` | Current price in USD. |

> Additional period-specific fields (e.g. `long_short_position_ratio_1h`, `taker_buy_vol_24h`, `total_score_7d`, `label_1h`) are returned as dynamic attributes.

---

### `crypto.indicators.technical_indicators`

```python
data.crypto.indicators.technical_indicators(symbols=..., intervals=["1d"], columns=None, start_ts=None, end_ts=None, markets=None)
```

Summary: Technical Indicators — per-symbol technical and market-structure indicator time series

| Field | Value |
|---|---|
| Endpoint ID | `crypto.indicators.technical_indicators` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/indicators/technical_indicators` |
| Default provider | `bitget_data` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Coin-centric lookup: specify `symbols` and receive indicator time series. Unlike `crypto.market.screener.scan`, which filters across the market. Current production data coverage: **5m / 15m / 1h only** (4h / 1d have no data yet). |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbols` | `yes` | `list[string]` | `-` | Trading pair symbols in concat format (e.g. `BTCUSDT`). Repeat the key for multiple values: `symbols=BTCUSDT&symbols=ETHUSDT`. |
| `intervals` | `no` | `list[string]` | `["1d"]` | Candlestick intervals. Allowed: `5m`, `15m`, `1h`, `4h`, `1d`. Repeat key for multiple values. |
| `columns` | `no` | `list[string]` | all 39 `_DEFAULT_COLUMNS` | Indicator columns to return. Repeat key for multiple values: `columns=price&columns=rsi_14`. |
| `start_ts` | `no` | `integer` | `-` | Unix millisecond timestamp. Filter rows where `ts >= start_ts`. Independent of whether `ts` is in `columns`. |
| `end_ts` | `no` | `integer` | `-` | Unix millisecond timestamp. Filter rows where `ts <= end_ts`. Independent of whether `ts` is in `columns`. |
| `markets` | `no` | `list[string]` | `["crypto"]` | Market scope. Repeat key for multiple values. |
| `provider` | `no` | `string` | `bitget_data` | - |

> **Symbol format**: Pass symbols in concat format without a slash (`BTCUSDT`). The SDK automatically converts to pair format (`BTC/USDT`) for the downstream call and converts the response back.

#### Default columns (`_DEFAULT_COLUMNS`)

When `columns` is omitted, all 39 columns below are returned:

`symbol`, `ts`, `rsi_14`, `stoch_k`, `stoch_d`, `cci_20`, `williams_r_14`, `mfi_14`,
`ema_20`, `ema_50`, `ema_200`, `sma_20`, `sma_50`,
`macd_line`, `macd_signal`, `macd_hist`,
`bb_upper`, `bb_mid`, `bb_lower`, `bb_pct`,
`atr_14`, `adx_14`,
`ichimoku_base`, `ichimoku_conv`, `ichimoku_span_a`, `ichimoku_span_b`,
`price`, `tech_rating`,
`funding_rate`, `oi_usd`, `oi_change_pct`, `long_short_ratio`, `long_short_ratio_top`,
`label_strong_trend`, `label_accumulation`, `label_washout`,
`label_distribution`, `label_breakout`, `label_volume_spike`

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `symbol` | `string` | Trading pair in concat format (e.g. `BTCUSDT`). |
| `interval` | `string` | K-line interval for this row. |
| `ts` | `integer` | Bar timestamp as Unix milliseconds. The downstream returns ISO-8601; the SDK converts to `int`. |
| `rsi_14` | `number` | RSI(14). |
| `stoch_k` | `number` | Stochastic %K. |
| `stoch_d` | `number` | Stochastic %D. |
| `cci_20` | `number` | CCI(20). |
| `williams_r_14` | `number` | Williams %R(14). |
| `mfi_14` | `number` | Money Flow Index(14). |
| `ema_20` | `number` | EMA(20). |
| `ema_50` | `number` | EMA(50). |
| `ema_200` | `number` | EMA(200). |
| `sma_20` | `number` | SMA(20). |
| `sma_50` | `number` | SMA(50). |
| `macd_line` | `number` | MACD line. |
| `macd_signal` | `number` | MACD signal line. |
| `macd_hist` | `number` | MACD histogram. |
| `bb_upper` | `number` | Bollinger Band upper. |
| `bb_mid` | `number` | Bollinger Band middle. |
| `bb_lower` | `number` | Bollinger Band lower. |
| `bb_pct` | `number` | Bollinger Band %B. |
| `atr_14` | `number` | ATR(14). |
| `adx_14` | `number` | ADX(14). |
| `ichimoku_base` | `number` | Ichimoku base line (Kijun-sen). |
| `ichimoku_conv` | `number` | Ichimoku conversion line (Tenkan-sen). |
| `ichimoku_span_a` | `number` | Ichimoku leading span A (Senkou Span A). |
| `ichimoku_span_b` | `number` | Ichimoku leading span B (Senkou Span B). |
| `price` | `number` | Current price. |
| `tech_rating` | `number` | Aggregated technical rating score. |
| `funding_rate` | `number` | Perpetual funding rate. |
| `oi_usd` | `number` | Open interest in USD. |
| `oi_change_pct` | `number` | Open interest change percentage. |
| `long_short_ratio` | `number` | Long/short ratio (all accounts). |
| `long_short_ratio_top` | `number` | Long/short ratio (top accounts). |
| `label_strong_trend` | `number` | Strong trend label score. |
| `label_accumulation` | `number` | Accumulation label score. |
| `label_washout` | `number` | Washout label score. |
| `label_distribution` | `number` | Distribution label score. |
| `label_breakout` | `number` | Breakout label score. |
| `label_volume_spike` | `number` | Volume spike label score. |

#### Verified Playbook usage notes

- Pass symbols in concat format (`BTCUSDT`), **not** pair format (`BTC/USDT`). The SDK normalises automatically.
- `ts` is always returned as a Unix millisecond `int`, regardless of which columns are requested.
- `start_ts` / `end_ts` filtering is applied via the downstream `filter` parameter and works even when `ts` is not included in `columns`.
- **Do not** request columns `ema_10`, `ema_100`, or `sma_200` — they do not exist. Use `ema_20`, `ema_50`, `ema_200`, `sma_20`, `sma_50`.
- **Do not** request `bb_middle` — the correct column name is `bb_mid`.
- Current production data: `5m`, `15m`, and `1h` intervals have data; `4h` and `1d` are not yet populated.

---


### `crypto.exchange.big_trades`

```python
data.crypto.exchange.big_trades(symbol=None, exchange=None, order_type=None, side=None, start_time=None, end_time=None, page=1, size=20)
```

Summary: Big Trades — large single or aggregated trade events from TDengine table `upex_agent_data_big_trades`

| Field | Value |
|---|---|
| Endpoint ID | `crypto.exchange.big_trades` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/exchange/big_trades` |
| Downstream | `GET {DATA_QUERY_BASE_URL}/inner/agent-data-query/big-order/big-trades` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Returns one record per large trade event, ordered by `ts` descending. `SINGLE` rows populate `single_*` fields; `AGGREGATED` rows populate `agg_*` fields. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string \| null` | `-` | Trading pair in any common form (`BTCUSDT`, `BTC/USDT`, `btcusdt`). SDK normalises to pair form (`BTC/USDT`) before the downstream call. If `None`, returns all symbols. |
| `exchange` | `no` | `string \| null` | `-` | Exchange identifier (lowercase). **Currently only `binance` is supported.** If `None`, returns all supported exchanges. |
| `order_type` | `no` | `string \| null` | `-` | Large-order **record type**: `SINGLE` (one large trade) or `AGGREGATED` (a grouped burst). Case-insensitive — SDK upper-cases before forwarding. If `None`, returns both types. **Not** a limit/market order-type filter. |
| `side` | `no` | `string \| null` | `-` | Trade side: `BUY` or `SELL`. Case-insensitive — SDK upper-cases before forwarding. If `None`, returns both sides. |
| `start_time` | `no` | `integer \| string \| datetime \| null` | `-` | Start time (inclusive). Prefer Unix milliseconds; the SDK also accepts ISO date strings and `datetime` objects. |
| `end_time` | `no` | `integer \| string \| datetime \| null` | `-` | End time (inclusive). Same coercion rules as `start_time`. |
| `page` | `no` | `integer` | `1` | Page number (1-based). |
| `size` | `no` | `integer` | `20` | Rows per page. Maximum `500`. |

> **Symbol format**: Pass `symbol` in concat or pair form; the SDK converts to `BTC/USDT` for the downstream query and returns `symbol` in concat form (`BTCUSDT`).

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `ts` | `integer` | Event timestamp in Unix milliseconds. |
| `side` | `string` | Trade side: `BUY` or `SELL`. |
| `threshold` | `number \| null` | Large-order trigger threshold in USD. |
| `single_trade_id` | `string \| null` | Individual trade ID. Present on `SINGLE` rows. |
| `single_price` | `number \| null` | Individual trade price. Present on `SINGLE` rows. |
| `single_qty` | `number \| null` | Individual trade quantity. Present on `SINGLE` rows. |
| `single_value` | `number \| null` | Individual trade notional value in USD. Present on `SINGLE` rows. |
| `agg_count` | `integer \| null` | Number of trades in the aggregated group. Present on `AGGREGATED` rows. |
| `agg_value` | `number \| null` | Total notional value of the aggregated group in USD. Present on `AGGREGATED` rows. |
| `agg_qty` | `number \| null` | Total quantity of the aggregated group. Present on `AGGREGATED` rows. |
| `symbol` | `string \| null` | Trading pair in concat format (e.g. `BTCUSDT`). |
| `exchange` | `string \| null` | Exchange identifier (e.g. `binance`). |
| `order_type` | `string \| null` | Record type: `SINGLE` or `AGGREGATED`. |

#### Verified Playbook usage notes

- `order_type` selects **record shape** (`SINGLE` vs `AGGREGATED`), not spot/perp order mechanics (`limit` / `market` are invalid here).
- `exchange` is currently limited to `binance`; other values typically return empty results.
- A row is either `SINGLE` (populates `single_*`) or `AGGREGATED` (populates `agg_*`); do not assume both field sets on one row.
- Use `ts` as the feature datetime index. Results are ordered by `ts` descending.
- Pagination is caller-controlled via `page` / `size`; `size` is capped at `500`.
- Example — latest Binance buy-side single large trades for BTC:

```python
rows = data.crypto.exchange.big_trades(
    symbol="BTCUSDT",
    exchange="binance",
    order_type="SINGLE",
    side="BUY",
    size=50,
)
```

---

### `crypto.exchange.trade_pressure`

```python
data.crypto.exchange.trade_pressure(symbol=None, exchange=None, interval=None, start_time=None, end_time=None, page=1, size=20)
```

Summary: Trade Pressure — buy/sell pressure snapshot aggregates from TDengine table `upex_agent_data_trade_pressure`

| Field | Value |
|---|---|
| Endpoint ID | `crypto.exchange.trade_pressure` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/crypto/exchange/trade_pressure` |
| Downstream | `GET {DATA_QUERY_BASE_URL}/inner/agent-data-query/big-order/trade-pressure` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Returns one record per pressure snapshot, ordered by `ts` descending. Each row aggregates buy/sell pressure, order-flow imbalance, and large-order counts for one `symbol` / `exchange` / `interval` bucket. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `symbol` | `no` | `string \| null` | `-` | Trading pair in any common form (`BTCUSDT`, `BTC/USDT`, `btcusdt`). SDK normalises to pair form (`BTC/USDT`) before the downstream call. If `None`, returns all symbols. |
| `exchange` | `no` | `string \| null` | `-` | Exchange identifier (lowercase). **Currently only `binance` is supported.** If `None`, returns all supported exchanges. |
| `interval` | `no` | `string \| null` | `-` | Statistics interval (lowercase). Allowed: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`. If `None`, returns all intervals. |
| `start_time` | `no` | `integer \| string \| datetime \| null` | `-` | Start time (inclusive). Prefer Unix milliseconds; the SDK also accepts ISO date strings and `datetime` objects. |
| `end_time` | `no` | `integer \| string \| datetime \| null` | `-` | End time (inclusive). Same coercion rules as `start_time`. |
| `page` | `no` | `integer` | `1` | Page number (1-based). |
| `size` | `no` | `integer` | `20` | Rows per page. Maximum `500`. |

> **Symbol format**: Pass `symbol` in concat or pair form; the SDK converts to `BTC/USDT` for the downstream query and returns `symbol` in concat form (`BTCUSDT`).

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `ts` | `integer` | Bucket timestamp in Unix milliseconds. |
| `buy_pressure` | `number \| null` | Buy-side pressure value. |
| `sell_pressure` | `number \| null` | Sell-side pressure value. |
| `net_pressure` | `number \| null` | Net pressure (`buy_pressure` − `sell_pressure`). |
| `ofi` | `number \| null` | Order Flow Imbalance indicator. |
| `large_buy_count` | `integer \| null` | Number of large buy orders in the bucket. |
| `large_sell_count` | `integer \| null` | Number of large sell orders in the bucket. |
| `signal` | `string \| null` | Pressure signal label. |
| `symbol` | `string \| null` | Trading pair in concat format (e.g. `BTCUSDT`). |
| `exchange` | `string \| null` | Exchange identifier (e.g. `binance`). |
| `interval` | `string \| null` | Statistics interval: `1m`, `5m`, `15m`, `1h`, `4h`, or `1d`. |

#### Verified Playbook usage notes

- `net_pressure = buy_pressure − sell_pressure`; positive values indicate buy-side dominance, negative values indicate sell-side dominance.
- Pick an `interval` that matches your strategy cadence before using `net_pressure` / `ofi` as replay features.
- `exchange` is currently limited to `binance`; combine with `interval` (e.g. `5m`) for reliable filtering.
- Use `ts` as the feature datetime index. Results are ordered by `ts` descending.
- Pagination is caller-controlled via `page` / `size`; `size` is capped at `500`.
- Example — Binance 5-minute pressure series for BTC over a time window:

```python
rows = data.crypto.exchange.trade_pressure(
    symbol="BTCUSDT",
    exchange="binance",
    interval="5m",
    start_time=1700000000000,
    end_time=1700604800000,
    size=100,
)
```
