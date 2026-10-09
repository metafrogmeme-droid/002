# Sleeve A BTC Long Trend v1

Long-only BTC perpetual playbook for an isolated sub-account. It rides
established hourly uptrends and buys sharp washout dips, with every trade
carrying a volatility stop and a fixed multiple-of-risk target. It never
shorts, never adds to losers, and holds at most one position because the
whole crypto-majors sleeve counts as a single correlation cluster.

## 策略 / Strategy

The market behavior this playbook bets on is trend persistence in BTC plus
fast snap-backs after panic selling. In a real uptrend, an hourly close that
holds above its slower average while momentum and regime reads agree tends to
keep drifting upward long enough to pay a fixed risk multiple. After a sudden
down flush in an otherwise calm market, exhausted selling tends to bounce
within a couple of hours. Both behaviors are long-only, so in bear markets or
grinding sideways markets the playbook stays flat by design.

Sleeve choice: this package builds sleeve A (crypto perps) only. Sleeves B
through F were evaluated against live Bitget contract data on 2026-10-09 and
deferred for verifiable-expectancy reasons: stock and ETF perps listed in
2026 cannot supply a two-year hourly perp history, so any expectancy claim
would mix underlying-equity data with separately modeled perp basis, funding,
and off-hours spread; metals share the short-history problem; TradFi
FX/index/commodity execution through the playbook trade surface is
unverifiable from the documented SDK and is therefore marked UNSUPPORTED for
now; spot accumulation has no stop and no signal edge, so the
profit-factor/Sharpe pass criteria cannot apply. Each is a falsifiable
statement: show two years of replayable hourly perp data plus executable
trade-surface coverage and the sleeve becomes buildable.

## 开仓 / Entry

A new long is opened only when every gate passes in order: data freshness
(newest closed hourly bar recent), signal validity (all indicator reads
computable, otherwise no trade), volatility regime (extreme-volatility
percentile blocks entries), setup presence (trend alignment or oversold
bounce), funding blackout (no entries near settlement), foreign-position
check (alert and stand down if a position this playbook did not open
exists), cluster limit (one open position maximum), liquidity (trailing
day quote volume and live spread), and funding cost (expected funding over
the planned hold must stay under a tenth of the trade risk). Live entries
are limit orders priced at the signal close and cancelled when the next
hourly cycle replaces them, which implements the four-hour cancel as a
stricter hourly refresh. Backtest replay uses market orders on the same
signals; that difference is disclosed and only makes live fills equal or
better on price.

## 平仓 / Exit

Each position exits at the first of three events: the protective stop below
entry, the profit objective above entry at twice the risk distance, or a
time stop of a few bars for bounce trades and a longer window for trend
trades. Stops and targets are attached to the live entry order through the
trade helper so exchange-side protection exists even if a later cycle is
missed. Time-stop exits and the entry-cancel refresh run on the hourly
schedule. There is no scaling in, no averaging down, and no trailing
adjustment in v1; the single-parameter rule means a trailing variant can
only arrive as a separately predicted v2.

## 风险 / Risk

Position size comes from a fixed USDT risk divided by the stop distance, so
a stopped trade loses about the configured risk amount regardless of
volatility, capped by margin budget times leverage with leverage capped at
five. Daily entries pause once realised losses reach the daily pause level
and the playbook stops for the day at the kill level; five consecutive
losses halt entries; stale data halts everything. Cross-run counters live
in the state file and the per-action log, and the sub-account dashboard is
the authoritative kill switch: because sandbox runs are stateless by
default, the daily and consecutive-loss halts are operator-enforced from
the log until state persistence is confirmed, which is stated here instead
of being silently assumed. Raising leverage amplifies both gains and
drawdowns without improving selectivity; raising the risk amount deepens
every win and every loss proportionally; lowering the trend threshold
produces more trend signals of lower average quality.

Reading the backtest: strategy return divides net PnL by the margin budget
denominator, account return divides by the replay starting balance, and the
two differ by construction. Win rate is meaningless without trade count;
this playbook refuses any verdict under thirty trades. Net expectancy in R
scales average trade PnL by the average losing trade, profit factor divides
gross wins by gross losses, max drawdown is the worst replay equity dip,
and Sharpe describes risk-adjusted consistency. The walk-forward read
splits one frozen-parameter two-year replay into an in-sample segment and a
later out-of-sample holdout, reported side by side with a zero/live/double
fee sensitivity grid. If doubled fees erase the edge, the playbook is
rejected by its own rules.

Main risks: whipsaw chop that stops out entries repeatedly, news gaps
through stops with slippage, funding drag on compensating losing streaks,
and long flat idle stretches in bear markets that tempt manual overrides.
Do not subscribe with money you cannot afford to lose; simulation is not a
promise of live profit.

## Contract spec (live Bitget USDT-FUTURES, pulled 2026-10-09)

| Symbol | Max lev | Margin | Funding | Hours | Tick | Min size | Min USDT | Maker | Taker | 24h vol |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 150x | USDT | 8h | 24/7 | 0.1 | 0.0001 BTC | 5 | 0.0002 | 0.0006 | ~2.26B USDT |
| ETHUSDT | 150x | USDT | 8h | 24/7 | 0.01 | 0.01 ETH | 5 | 0.0002 | 0.0006 | ~1.52B USDT |
| SOLUSDT | 100x | USDT | 8h | 24/7 | 0.001 | 0.1 SOL | 5 | 0.0002 | 0.0006 | ~285M USDT |

RWA perps (AAPL/NVDA/TSLA/META/AMZN/GOOGL/SPY/QQQ/XAU/XAG)USDT are listed and
tradable with 4h or 8h funding but opened in 2026, so they fail the two-year
replay requirement and are excluded from v1. Maker/taker above are the
standard tier from the public config; the exact tier for the operator's
sub-account is PENDING until an API key is bound. Spreads at pull time were
all inside their sleeve gates (BTC ~0.001 bps vs 5 bps gate) and funding was
near zero on every queried symbol; both are re-checked live on every cycle.

## Parameters

| Name | Value | Rationale | Source |
|---|---|---|---|
| trading_symbols | BTCUSDT | deepest history, tightest spread, largest volume | live spec + data |
| entry_timeframe | 1h | matches ADX/ATR regime spec and two-year replay depth | data |
| ema_fast / ema_slow | fast / slow pair | trend alignment without overfitting to one cross | default |
| adx_period / adx_threshold | standard period, trend-grade cutoff | regime definition from sleeve spec | data |
| atr_period / atr_mult | standard period, stop distance | stop spec: 1.5x ATR(14) | data |
| tp_r_mult | fixed two-R target | one fixed exit, no partials in v1 | default |
| rsi_period / rsi_oversold | standard period, washout cutoff | dip-buy trigger in calm regimes | default |
| atr_pct_lookback / atr_pct_max | percentile window, extreme-vol block | skip untradeable volatility | default |
| trend_time_stop / mr_time_stop | longer trend window, short bounce window | sleeve time stops | data |
| leverage | 3 (cap 5) | under the sleeve cap with margin headroom | live spec |
| risk_usdt | 15 | fixed loss at stop per global rule | default |
| margin_budget | 300 | sizes orders, denominates strategy return | default |
| max_positions | 1 | one symbol, one crypto-majors cluster | default |
| funding_interval_h | 8 | settlement blackout math | live spec |
| funding_blackout_min | 15 | no entries around settlement | default |
| max_spread_bps | 5 | sleeve A liquidity gate | data |
| min_24h_volume_usdt | 50M | BTC clears it by ~45x; filters dead feeds | live spec + data |
| daily_pause / kill | -30 / -40 USDT | global halt levels, operator-enforced | default |
| consec_loss_halt | 5 | global halt, operator-enforced | default |

Any value that could not be derived from live contract data or a backtest is
marked PENDING in the upload summary; no performance figure is invented.

## Flow

scan (hourly klines) -> filter (freshness, regime, setup, funding, position,
liquidity, cost) -> trigger (limit order with attached stop/target) ->
manage (exchange-side stop/target plus scheduled time-stop sweep) -> exit
(stop, target, or time) -> log (per-action JSON line with timestamp,
symbol, side, intended vs filled price, fees, funding, reason code).

## Assumptions and falsifiers

- BTCUSDT perpetual history on the replay venue represents executable live
  prices. Falsified if live slippage persistently exceeds one tick plus the
  modeled fees.
- Hourly trend persistence plus washout reversion have positive net
  expectancy after costs. Falsified if out-of-sample profit factor prints at
  or below 1.1 after thirty live trades.
- Funding stays a small fraction of trade risk. Falsified if average funding
  per trade exceeds a tenth of R over any thirty-trade window.
- One-tick slippage plus taker fees bound execution cost. Falsified by the
  double-fee sensitivity run turning negative.
- The sub-account trades only this playbook. Falsified the moment a foreign
  position appears, which halts entries with an alert.

## Per-action log schema

timestamp, symbol, side, kind, intended_price, limit_price/filled_price,
qty, leverage, stop_price, take_profit, fees, funding, reason_code.
Reason codes: SIGNAL_LONG_TREND, SIGNAL_LONG_MR, NO_SETUP,
WARMUP_NO_SIGNAL, STALE_DATA, VOLUME_GATE, SPREAD_GATE, FUNDING_BLACKOUT,
FUNDING_COST, FOREIGN_POSITION, CLUSTER_LIMIT, DAILY_HALT,
CONSEC_LOSS_HALT, INSUFFICIENT_HISTORY.

## Versioning

v1 frozen at activation. Each later version changes exactly one parameter
with a written prediction first. Candidate v2 (prediction pre-registered):
replace the fixed target with half at 1.5R plus a one-ATR trail; predicted
to raise win rate slightly while lowering average R, passing only if net
expectancy and profit factor both improve on the same window.
