# USDT-M EMA ADX Long (v1)

Long-only trend Playbook for Bitget USDT-M perpetuals. Version label `v1` (manifest `1.0.0`). Frozen at activation. A later version may change one parameter, and only after a written prediction of its effect.

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
- Margin, lot size, or minimum notional cannot fund the fixed 15 USDT stop without raising leverage past 5x.

Universe: BTCUSDT, ETHUSDT, SOLUSDT only. Isolated margin. Leverage hard cap 5x.

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

- Fixed loss at the stop: 15 USDT. Isolated margin. Leverage never raised above 5x to make a size fit.
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
4. Order a limit bracket with the stop and 2R target attached. Isolated, leverage at most 5x.
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
| leverage cap | 5, isolated | hard cap; skip rather than raise leverage | user spec |
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
| schedule | `5 * * * *` Etc/UTC | one hour after the bar open, so the prior hour has closed | default |
| price_tick | BTC 0.1, ETH 0.01, SOL 0.001 | pricePlace and priceEndStep from public contracts | data |
| size_step / min_qty | BTC 0.0001, ETH 0.01, SOL 0.1 | minTradeNum and sizeMultiplier | data |
| min_notional_usdt | 5 | minTradeUSDT | data |
| fee_tier_status | PENDING | Trade SDK has no fee-tier method; ACCESS-KEY is the GetAgent control-plane key | PENDING |
| version_label | v1 | freeze at activation; no v2 in this package | user spec |

## Assumptions and what would falsify them

- Assumption: a high-ADX, +DI-led tape continues more often than it snaps back, after costs. Falsifier: test-window net expectancy per trade flips sign versus the train window, or 2x-cost expectancy is not positive.
- Assumption: ADX ≥ 25 and the 20–80 ATR percentile are reasonable gates, not fitted edges. Falsifier: the traded subset has negative net expectancy while the sat-out subset would have been positive. That result would reject v1; it would not authorize a silent retune.
- Assumption: the public default fee schedule is what this account pays. Falsifier: the account tier differs. Until the tier is verified, activation stays off.
- Assumption: 5x isolated liquidation (about a 20% adverse move before extra margin) is wider than the 1.5 × ATR stop, so the stop hits first. Falsifier: an isolated liquidation fills before the stop.
- Assumption: −40 USDT is a cumulative Playbook stop, persisted, with no auto-resume. Falsifier: the operator intended a daily −40 USDT stop. v1 implements cumulative.
- Assumption: one hourly live pass may submit only one new entry, because the platform follows the last actionable signal. Falsifier: the sandbox or live runner executes every emitted signal. The backtest can enter more than one symbol on the same bar; live can lag that.
- Assumption: managed funding history covers the declared window. Falsifier: the funding series starts later than the kline window. Author net then stays PENDING. Missing funding is not filled with zero.
- Assumption: a bracket order can carry the stop and target at submit. Falsifier: the sandbox rejects the bracket. The Playbook then logs `ORDER_REJECTED` and does not send a naked order.

Walk-forward prediction, written before any replay: the test-window net expectancy per trade has the same sign as the train window if the edge is stable. A sign flip falsifies stability. This prediction does not claim either sign is positive.

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

Sandbox run `pbrun-f7897e91b6f8` on draft `2e317d26-a835-4111-8b29-cf605dab5459` returned 17520 1H klines from 2024-10-09T00:00:00Z through 2026-10-08T23:00:00Z and funding only from 2026-08-29. Author net metrics are PENDING. Engine totals of zero are an empty sample.

Activation requires a two-year replay with funding coverage, at least 30 trades, positive net expectancy at 1x and 2x costs, a defined profit factor, a finite engine Sharpe, a verified fee tier, and a later live sample of at least 30 trades that passes PF ≥ 1.3 and Sharpe ≥ 0.5. Current verdict: do not activate.
