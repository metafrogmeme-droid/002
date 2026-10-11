# USDT-M EMA ADX Long (v2.1)

Long-only trend Playbook for Bitget USDT-M perpetuals. Version label `v2.1`. This is a bugfix of v2, not a strategy change. Strategy parameters are identical to v2: EMA(20)/EMA(50) cross, ADX at least 25, ATR percentile 20 to 80, volume 1.5 times the prior 20 bars, fixed 2R, 8 hour time stop, long only, isolated margin with a 10x cap, 15 USDT at the stop, and the same halt rules. Research switches stay at their defaults: entry style cross, exit style fixed 2R, 4H filter off, research side long, window label full. No candidate is enabled.

The bugfix is in the live and fill path. Closed live trades update the daily realised loss, the cumulative realised loss, and the consecutive-loss count. The 8 hour clock starts at the fill, not at the limit submit. An unfilled limit that would rest across a funding window is cancelled with `ORDER_CANCEL_FUNDING_WINDOW`. Order size is never raised above the planned quantity. If a close profit cannot be read, new entries stop. Replay bars are placed on the instrument tick before the engine fills. Order prices keep the instrument precision, so an ETH price such as 2345.50 is not sent with the trailing zero stripped.

v1 was the 5x package. v2 changed only the isolated-margin leverage hard cap, from 5x to 10x, and skips an order when that liquidation sits inside the stop. EMA, ADX, ATR percentile, volume, and the 2R target were unchanged then and stay unchanged in v2.1.

This package does not claim a win rate, profit factor, Sharpe ratio, drawdown, or expectancy. Those numbers stay PENDING until a sandbox replay returns them from data. Do not activate live trading from this README.

## 策略 / Strategy

The regime filter is trend strength plus a normal volatility band. The Playbook therefore follows trends. It does not fade them.

Traded regime, all of these on the closed 1H bar:

- ADX(14) is at least 25.
- +DI(14) is above −DI(14).
- ATR(14) / close sits in the 20th to 80th percentile of the last 720 closed 1H ratios.
- EMA(20) has just crossed above EMA(50).
- Volume is at least 1.5 times the mean of the previous 20 bars, excluding the signal bar.
- The bar close is outside the funding blackout, and the latest funding rate is not above 0.03% per 8h against a new long.

Sat out:

- ADX below 25 (range).
- ATR percentile below 20 (quiet tape) or above 80 (volatility spike).
- +DI does not lead −DI.
- No fresh bullish EMA cross. A bearish cross logs `SHORTS_DISABLED` and does not open a short.
- Volume below the threshold.
- Within 15 minutes of 00:00, 08:00, or 16:00 UTC, or funding above 0.0003 against the long.
- Any required input missing, stale, or not a finite number (`INVALID_SIGNAL` or `INSUFFICIENT_HISTORY`). No default direction.
- Daily realised loss at or below −30 USDT, cumulative realised loss at or below −40 USDT, five consecutive losses, three open names, or a second position in the same symbol.
- Margin, lot size, or minimum notional cannot fund the fixed 15 USDT stop without raising leverage past 10x.
- The 10x isolated liquidation price is inside the 1.5 × ATR(14) stop (`SKIP_LIQUIDATION_INSIDE_STOP`). Size is not raised to dodge that check.

Universe: BTCUSDT, ETHUSDT, SOLUSDT only. Isolated margin. Leverage hard cap 10x. Scan schedule `5 * * * *` Etc/UTC, one pass each hour at minute 5.

## 开仓 / Entry

Scan the three symbols on the closed 1H bar. Confirm the regime and the cross. Submit a limit buy at the signal close. Attach the stop and the fixed 2R target to that same order. Cancel the limit if it is still unfilled after 4 hours. Also cancel it when the next hour would overlap a funding blackout, because a bar replay cannot cancel inside the hour.

Size = 15 USDT / stop distance, floored to the exchange size step so the loss at the stop is not larger than 15 USDT. Stop = entry minus 1.5 × ATR(14), floored to the tick. If the plan would need more than the remaining margin budget, the Playbook skips the trade.

## 平仓 / Exit

One of three exits, whichever comes first:

- Exchange stop at 1.5 × ATR(14).
- Exchange take profit at 2R (fixed). The partial-plus-trail alternative is not used, because one attached stop and one attached target can be sent with the entry.
- Time stop 8 hours after the fill, then a close of the position this Playbook opened.

End-of-replay flats are tagged `BACKTEST_SHUTDOWN` and are excluded from expectancy.

## 风险 / Risk

- Fixed loss at the stop: 15 USDT. Isolated margin. Leverage never raised above 10x to make a size fit. Quantity stays 15 USDT divided by the stop distance, floored to the size step.
- Pause new entries at −30 USDT daily realised (UTC day, Playbook-attributed). Stop the Playbook at −40 USDT cumulative realised. Existing exchange stops stay; a halt does not flatten.
- Halt after 5 consecutive losses.
- Halt new risk when mark/ticker age is over 60 seconds, or when the newest closed bar is older than two intervals.
- A position in the sub-account that this Playbook did not open is logged and left untouched.
- Costs in the author net: maker 0.02% and taker 0.06% when the fill type says so, 1 tick of slippage each side, and funding. Public Bitget contract config on 2026-10-09 shows makerFeeRate 0.0002 and takerFeeRate 0.0006 for these three symbols. The account VIP tier is PENDING. Cost sensitivity scales fees and slippage by 0, 1, and 2. Funding is charged once. Negative expectancy at 2x costs rejects activation.
- Engine Sharpe uses the replay account and is labeled separately from the author net. The strategy return uses author net divided by `margin_budget` (3000 USDT, a default denominator, not a fitted capital). The account return uses the 100000 USDT engine starting balance. Read `metrics_basis: strategy` as the decision number.

## Flow

scan → filter → trigger → order → manage → exit → log

1. Scan BTCUSDT, ETHUSDT, SOLUSDT 1H bars.
2. Filter regime, funding clock, funding rate, halts, and data validity.
3. Trigger only on a bullish EMA cross that passes every filter.
4. Order a limit bracket with the stop and 2R target attached. Isolated, leverage at most 10x. Skip when isolated liquidation is inside the stop.
5. Manage the 4h cancel, the funding-window cancel, and the one-position-per-symbol cap.
6. Exit at stop, 2R, or 8h.
7. Log the action row below.

## Parameter table

| name | value | rationale | source |
| --- | --- | --- | --- |
| trading_symbols | BTCUSDT, ETHUSDT, SOLUSDT | stated universe | user spec |
| regime filter | ADX(14) 1H and ATR(14)/price percentile | trade trends in a normal vol band; sit out ranges, dead vol, and spikes | user spec |
| adx_min | 25 | Wilder trend-strength convention; not fit on the sample | default |
| atr_pct band | 20 to 80 over 720 closed 1H bars | sit out the quiet and spike tails | default |
| ema_fast / ema_slow | 20 / 50 | cross defines the trigger; not optimized | default |
| volume_mult | 1.5 × prior 20 bars | confirmation required by the spec | user spec |
| side | long only | shorts stay off until a separate test has at least 30 trades and positive net expectancy | user spec; short test PENDING |
| entry | limit at signal close | no market fallback | user spec |
| limit_timeout_hours | 4 | cancel if unfilled | user spec |
| fixed_loss_usdt | 15 | size = 15 / stop distance, floored | user spec |
| leverage cap | 10, isolated | hard cap; skip rather than raise leverage or size | user spec, v2 |
| stop | 1.5 × ATR(14), attached | exchange-side, no post-fill gap | user spec |
| take profit | fixed 2R | one attached target with the stop | chosen from the two allowed exits |
| time_stop_hours | 8 | trend holding period | user spec |
| max_concurrent | 3, and 1 per symbol | inventory cap | user spec |
| daily_pause_usdt | −30 realised, UTC day | pause new entries | user spec |
| playbook_stop_usdt | −40 cumulative realised | stop the Playbook; not a second daily limit | user spec plus assumption |
| max_consecutive_losses | 5 | halt | user spec |
| stale_ticker_seconds | 60 | plus the skill's two-interval bar freshness check | user spec and skill |
| funding blackout | ±15 min at 00:00, 08:00, 16:00 UTC | no new risk around funding | user spec |
| funding_against_max | 0.0003 | skip if funding is above 0.03%/8h against the long | user spec |
| maker_fee / taker_fee | 0.0002 / 0.0006 | matches public contract config; VIP tier unknown | data; tier PENDING |
| slippage_ticks | 1 each side | charged in the author net | user spec |
| margin_budget | 3000 USDT | platform return denominator; skip if an order needs more | default |
| engine starting balance | 100000 USDT | replay wallet, not strategy capital | default |
| window | 2024-10-09T00:00:00Z to 2026-10-09T00:00:00Z | at least two years of 1H bars | user spec |
| walk_forward_split | 2026-04-09T00:00:00Z | train 18 months, test 6 months; parameters not fit on train | user spec |
| forward PASS | PF ≥ 1.3 and Sharpe ≥ 0.5 after ≥ 30 live trades | fixed before any run | user spec |
| forward FAIL | PF ≤ 1.1 after that sample | stop | user spec |
| schedule | `5 * * * *` Etc/UTC | hourly at minute 5, after the prior 1H bar has closed | kept from v1 |
| price_tick | BTC 0.1, ETH 0.01, SOL 0.001 | pricePlace and priceEndStep from public contracts | data |
| size_step / min_qty | BTC 0.0001, ETH 0.01, SOL 0.1 | minTradeNum and sizeMultiplier | data |
| min_notional_usdt | 5 | minTradeUSDT | data |
| fee_tier_status | PENDING | Trade SDK has no fee-tier method; ACCESS-KEY is the GetAgent control-plane key | PENDING |
| version_label | v2.1 | bugfix of v2; strategy parameters identical to v2 | user spec |

## Assumptions and what would falsify them

- Assumption: a high-ADX, +DI-led tape continues more often than it snaps back, after costs. Falsifier: test-window net expectancy per trade flips sign versus the train window, or 2x-cost expectancy is not positive.
- Assumption: ADX ≥ 25 and the 20–80 ATR percentile are reasonable gates, not fitted edges. Falsifier: the traded subset has negative net expectancy while the sat-out subset would have been positive. That result would reject v1; it would not authorize a silent retune.
- Assumption: the public default fee schedule is what this account pays. Falsifier: the account tier differs. Until the tier is verified, activation stays off.
- Assumption: an isolated long liquidates after an adverse move of 1/leverage of entry when maintenance is ignored. The public contract payload has no maintenance field, so none is invented. At 10x that optimistic distance is one tenth of entry. If the 1.5 × ATR stop is at least that far, the order is skipped and logged `SKIP_LIQUIDATION_INSIDE_STOP`. Liquidation is not allowed to replace the stop. Falsifier: a live isolated liquidation fills before the logged stop on an order this check allowed.
- Assumption: −40 USDT is a cumulative Playbook stop, persisted, with no auto-resume. Falsifier: the operator intended a daily −40 USDT stop. v1 implements cumulative.
- Assumption: one hourly live pass may submit only one new entry, because the platform follows the last actionable signal. Falsifier: the sandbox or live runner executes every emitted signal. The backtest can enter more than one symbol on the same bar; live can lag that.
- Assumption: managed funding history covers the declared window. Falsifier: the funding series starts later than the kline window. Author net then stays PENDING. Missing funding is not filled with zero.
- Assumption: a bracket order can carry the stop and target at submit. Falsifier: the sandbox rejects the bracket. The Playbook then logs `ORDER_REJECTED` and does not send a naked order.

Walk-forward prediction, written before any replay: the test-window net expectancy per trade has the same sign as the train window if the edge is stable. A sign flip falsifies stability. This prediction does not claim either sign is positive.

v2 leverage prediction, written before the 10x replay: 10x does not change R expectancy; it only changes whether the stop sits outside liquidation. Trade count and net expectancy in R are predicted to stay the same as the 5x replay (17 trades, 1x expectancy -0.07888825482119473 R, 2x expectancy -0.1600857319901629 R). Any difference is a liquidation skip, not a better signal. A higher cap can also release an order that 5x skipped for margin; that is still not a better signal.

Next strategy step, not implemented in v2: keep EMA, ADX, the ATR percentile band, the volume multiple, and the 2R target frozen. The 5x sample is a reject (negative 2x expectancy, 17 trades, under 30). The next development is to leave that signal unchanged until one pre-declared change can be measured on its own. Prediction for that later step: retuning a gate on this sample will not establish an edge. The expected result of leaving the signal frozen is that another replay of the same signal still fails the same gates.

## Log schema

One JSON object per line in `output/action_log.jsonl`:

| field | meaning |
| --- | --- |
| timestamp | UTC ISO time |
| symbol | BTCUSDT, ETHUSDT, SOLUSDT, or the symbol that was checked |
| side | `long` or `none` |
| intended_price | limit, stop, or target the Playbook meant to use; null if none |
| filled_price | fill price; null if the action did not fill |
| fees | fee in USDT; null if unknown |
| funding | funding in USDT for this event; null if unknown |
| reason_code | stable code from `src/reasons.py` |
| detail | short text, may be empty |

Quiet bars (`FILTER_NO_CROSS`, `INSUFFICIENT_HISTORY`) are not logged. No live or replay log has been produced in this package yet. Actual rows stay PENDING until a run writes them.

## Validation status

PENDING. Local unit tests check the decision rules. They are not a backtest. Trades, win rate, average R, net expectancy, profit factor, max drawdown, and Sharpe are not invented here.

Bitget's own `crypto.futures.funding_rate` still does not cover 2024-10-09. Its earliest row remains 2026-07-12T00:00:00Z. A different catalog endpoint does. `crypto.futures.funding_weighted` (provider coinglass, base symbols BTC, ETH, and SOL, interval 1d, weight_type volume) returned 730 daily rows from 2024-10-09 through 2026-10-08 for each symbol, with no gap above 36 hours. Pair symbols such as BTCUSDT return an empty body on that endpoint. The 4h interval of the same endpoint did not start on 2024-10-09. The two-year replay uses the daily weighted series. It is a cross-exchange volume-weighted rate, not Bitget's settlement print. The value is a percent display and is divided by 100 before the 0.0003 gate and before the funding charge. A missing day is a gap and blocks the two-year metrics. It is not filled with zero. The declared window stays 2024-10-09 through 2026-10-09.

Sandbox run `pbrun-5b6eea8a28ee` replayed 17520 1H klines from 2024-10-09T00:00:00Z through 2026-10-08T23:00:00Z and 730 daily weighted funding rows from 2024-10-09T00:00:00Z through 2026-10-08T00:00:00Z for BTC, ETH, and SOL. The strategy log in that run's signal reports 17 closed trades, win rate 0.4117647058823529, average R and 1x net expectancy -0.07888825482119473 R, 0x expectancy 0.0023092223477735106 R, 2x expectancy -0.1600857319901629 R, profit factor 0.8514079646539923, max drawdown 2.403103333502609 percent of the 3000 USDT budget, and Sharpe -0.152. The same run's Nautilus report lists 0 orders and 0 fills, with account net pnl 0. The daily rate is joined as-of, so the 08:00 and 16:00 settlements reuse that day's 00:00 print. Seventeen trades is below 30. The 2x expectancy is negative. Walk-forward train and test figures were not returned. Do not activate.

Activation still requires a verified fee tier and a later live sample of at least 30 trades with PF ≥ 1.3 and Sharpe ≥ 0.5. Live trades are 0.

Sandbox run `pbrun-3ed23945e11e` is the v2 replay at leverage 10. It returned the same strategy-log figures as the 5x run: 17 closed trades, win rate 0.4117647058823529, average R and 1x net expectancy -0.07888825482119473 R, 0x expectancy 0.0023092223477735106 R, 2x expectancy -0.1600857319901629 R, profit factor 0.8514079646539923, max drawdown 2.403103333502609 percent of the 3000 USDT budget, author net pnl -19.737553510004314, and Sharpe -0.152. `SKIP_LIQUIDATION_INSIDE_STOP` counts were BTCUSDT 0, ETHUSDT 0, SOLUSDT 0. Walk-forward on that same payload: train 14 trades, expectancy -0.18129553073061996 R; test 3 trades, expectancy 0.3990123660894564 R. The test sign is not the train sign, and 3 trades is not a sample. The engine account on this run moved from 100000 to 99980.85383894 USDT across 111 points, with 34 fills and 17 positions. That engine summary matches the already published 0.0.1 snapshot. It is not an improvement. Verdict `do_not_activate`. Fee tier remains PENDING. Live trades remain 0.
