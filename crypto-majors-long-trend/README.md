# BTCUSDT Isolated Long Trend

Sleeve A crypto perpetual Playbook for one isolated Bitget sub-account. Official
replay symbol is BTCUSDT. ETHUSDT and SOLUSDT are the same correlation cluster
and may be selected live, but they do not replace the BTCUSDT two-year evidence
package.

Performance figures that do not come from a completed sandbox replay or live
fill log are **PENDING**. Displayed ROI is not the optimisation target.

## Contract spec (live, 2026-10-09T18:30:32Z)

Pulled from Bitget public `USDT-FUTURES` contract, ticker, and funding APIs.
User-tier fees are not on the public contract row.

| Field | BTCUSDT | ETHUSDT | SOLUSDT | Source |
| --- | --- | --- | --- | --- |
| Status | normal perpetual | normal perpetual | normal perpetual | live spec |
| Max leverage (exchange) | 150 | 150 | 100 | live spec |
| Playbook leverage cap | 5 | 5 | 5 | sleeve A default |
| Margin mode | isolated | isolated | isolated | required |
| Funding interval | 8h | 8h | 8h | live spec |
| Trading hours | 24/7 | 24/7 | 24/7 | live spec (`offTime=-1`) |
| Weekend / holiday close | none | none | none | live spec |
| Tick | 0.1 | 0.01 | 0.001 | live spec (`pricePlace`) |
| Min size | 0.0001 | 0.01 | 0.1 | live spec |
| Min notional | 5 USDT | 5 USDT | 5 USDT | live spec |
| Listed maker / taker | 0.0002 / 0.0006 | 0.0002 / 0.0006 | 0.0002 / 0.0006 | live spec |
| User-tier maker / taker | PENDING | PENDING | PENDING | needs ACCESS-KEY |
| 24h quote volume | 2,254,548,234 USDT | 1,519,602,335 USDT | 284,611,362 USDT | live ticker |
| Bid / ask / spread | 82464.1 / 82464.2 / 0.0121 bps | 2482.92 / 2482.93 / 0.0403 bps | 109.506 / 109.507 / 0.0913 bps | live ticker |

Sleeve B stock perps (AAPL/NVDA/TSLA/META class) are tradable RWA contracts but
opened 2026-02-02, so a two-year perp replay is UNSUPPORTED. Sleeve C ETF perps
are the same (SPY/QQQ opened 2026-02; DIA opened 2024-10-02, still under two
years at authoring). Sleeve D metals (XAU opened 2025-12-12, XAG 2026-01-07)
cannot satisfy two-year perp history. Sleeve E FX/oil symbols requested were
not listed; SPXUSDT exists but opened 2024-10-29. Sleeve F spot accumulation
has no stop and conflicts with the 15 USDT isolated-stop contract.

## 策略 / Strategy

Long-only trend pullback on BTCUSDT USDT-FUTURES. The regime layer (directional
movement plus a volatility-percentile gate) must be valid or the Playbook
issues NO TRADE. Shorts are disabled until a separate thirty-trade short-side
test shows positive net expectancy.

v1 take-profit style is fixed 2R. The trail alternative is not active.

## 开仓 / Entry

Scan the selected symbol on closed one-hour bars. Require an upside regime,
volatility inside the allowed percentile band, and a pullback that tags the
fast average while the close holds above it. Size equals 15 USDT divided by
stop distance, then capped by margin budget times leverage. Place an isolated
limit at the fast average. Cancel if unfilled after four hours. Skip if spread
is above 5 bps, 24h volume is below 50M USDT, data is stale, funding blackout
is active, or expected funding over the planned hold exceeds 0.1R.

## 平仓 / Exit

Stop is 1.5 times ATR(14) plus one tick, attached to the entry. Take profit is
2R. Time-stop is eight hours. The Playbook does not average down and does not
close a position it did not open.

## Parameters

| name | value | rationale | source |
| --- | --- | --- | --- |
| trading_symbols | BTCUSDT | official replay + live default | live spec |
| symbol options | BTCUSDT, ETHUSDT, SOLUSDT | sleeve A universe, one cluster | live spec |
| leverage | 5 | sleeve A cap | default / sleeve A |
| leverage_cap | 5 | never exceed sleeve cap | default |
| margin_budget | 500 | isolated cap and return denominator | default |
| risk_usdt | 15 | loss at stop | required |
| adx_period / atr_period | 14 / 14 | sleeve A regime | required |
| ema_fast_period / ema_slow_period | 21 / 55 | pullback vs trend | default |
| adx_min | 22 | skip weak trend | default |
| atr_pct_lo / atr_pct_hi | 25 / 80 | skip dead or chaotic vol | default |
| percentile_lookback | 168 | one week of 1H ranks | default |
| stop_atr_mult | 1.5 | attached stop | required |
| tp_r_multiple | 2.0 | v1 chooses fixed 2R | required (one of two) |
| time_stop_hours | 8 | trend sleeve A | required |
| limit_ttl_hours | 4 | unfilled cancel | required |
| spread_max_bps | 5 | sleeve A liquidity | required |
| volume_min_usdt | 50000000 | [X]=50 from live majors >> 50M | default |
| funding_blackout_min | 15 | 8h settlement rule | required |
| funding_cost_max_r | 0.1 | skip expensive holds | required |
| daily_pause_usdt / playbook_stop_usdt | 30 / 40 | daily brakes | required |
| consecutive_loss_halt | 5 | streak halt | required |
| stale_data_sec | 60 | live ticker/bar halt | required |
| maker_fee / taker_fee | 0.0002 / 0.0006 | listed contract rates | live spec |
| user-tier fees | PENDING | needs bound account | PENDING |
| bound subaccount tradability | PENDING | `check_symbol_support` at live | PENDING |
| NET expectancy / PF / Sharpe / DD | PENDING | no sandbox run in this environment | PENDING |

Only `trading_symbols`, `leverage`, and `margin_budget` are subscriber-editable.
Everything else is frozen at v1.

## Flow

scan closed 1H bars and live ticker → filter spread, volume, freshness, halt,
funding, cluster occupancy, foreign positions → trigger regime plus pullback →
size 15 / stop distance on isolated margin → place limit with attached stop and
2R take profit → manage TTL cancel and eight-hour time-stop → exit on stop, 2R,
or time-stop → log reason code, intended vs filled price, fees, funding.

## 风险 / Risk

Whipsaw in ranges that still pass the regime gate. Stopped pullbacks through
the cash-risk stop. Funding flips during the hold. Gap fills through the limit
or stop. A lost `.state` file makes every open position look foreign, so the
Playbook alerts and does not touch it. Run only on an isolated sub-account.

## Assumptions and what falsifies them

| Assumption | Falsifier |
| --- | --- |
| Upside pullbacks in an ADX trend have positive NET R after fees, one tick, and funding | OOS or live NET expectancy_R ≤ 0 after ≥30 trades |
| Listed 2/6 bps fees bound this account | User-tier fees higher; 2x cost sensitivity negative |
| 50M USDT volume floor is conservative for these majors | Live 24h volume < 50M or spread > 5 bps |
| Isolated `place_order` is executable on the bound sub-account | Live order reject / `check_symbol_support` false |
| BTCUSDT 1H Bitget history covers 2024-10-09 to 2026-10-09 | Managed kline returns empty / 4xx |
| One crypto-major position is enough | Operator enables a second correlated sleeve |

## Validation contract

- Window: 2024-10-09 to 2026-10-09, 1H Bitget BTCUSDT perps.
- Walk-forward split: IS 2024-10-09 to 2026-04-08 / OOS 2026-04-09 to 2026-10-09.
- Report trades, win rate, avg R, net expectancy R, PF, max DD, Sharpe. No
  verdict under 30 trades.
- Cost sensitivity 0x / 1x / 2x listed fees plus funding. Negative at 2x → reject.
- Forward: PASS = PF ≥ 1.3 AND Sharpe ≥ 0.5 after ≥30 live trades. FAIL = PF ≤ 1.1 → stop.
- Metrics use strategy-budget NET, not displayed account ROI.

Replay numbers: **PENDING** until a GetAgent sandbox run completes. This
authoring environment has no ACCESS-KEY and cannot execute `getagent.backtest`.

## Versioning

v1 is frozen at activation. Each later version changes ONE parameter and must
write the predicted effect before the change.

## Per-action log

Live writes `/workspace/.state/action_log.jsonl` with timestamp, symbol, side,
intended vs filled price, fees, funding, and reason code.

## Isolated sub-account

Bind this Playbook to a dedicated Bitget isolated sub-account on the GetAgent
page. This package does not create, start, stop, or flatten subscriptions.
