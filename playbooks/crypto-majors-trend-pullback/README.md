# Crypto Majors Trend Pullback (Long-Only)

Sleeve A (crypto perpetuals) Playbook for Bitget USDT-FUTURES: `BTCUSDT`,
`ETHUSDT`, `SOLUSDT`. Built to be judged on verifiable net expectancy, not on
displayed ROI. Every figure the Playbook reports is derived from real Bitget
bars replayed through the managed engine, net of fees, one tick of slippage on
taker fills, and funding.

## 策略 / Strategy

The Playbook runs on closed 1-hour bars. It only trades in the direction of an
established uptrend and only buys pullbacks. The regime read requires trend
strength (ADX) above a threshold, directional pressure favouring buyers
(+DI above -DI), price above the long-horizon EMA, and the current ATR-to-price
ratio sitting inside a healthy percentile band of its trailing month (not dead,
not panicked). The three majors are treated as one correlation cluster, so at
most one pending order or open position exists across all three at any time;
when several qualify, the strongest ADX wins.

Shorts are disabled. They may only be enabled in a later version after a
separate short-side test of at least thirty trades shows positive net
expectancy. If the indicator layer cannot produce a valid reading (warm-up,
missing or stale data), the answer is always "no trade".

## 开仓 / Entry

When the regime is active and price is not over-extended above the fast EMA,
a limit buy is rested at the fast EMA (or at the close if price is already
below it). The order is cancelled if it has not filled after four hours. Entries
are skipped within fifteen minutes of a funding settlement, when expected
funding over the planned hold exceeds one tenth of the risk unit, when the
spread or 24-hour volume fails the liquidity gate (live only), while a daily
loss pause, daily hard stop or consecutive-loss halt is active, and while any
position this Playbook did not open is present (that position is reported and
never touched).

Position size is risk-based: quantity equals the configured USDT risk divided
by the stop distance (1.5 x ATR), then capped so that notional never exceeds
margin budget x leverage, quantised to the exchange step and rejected if below
exchange minimums. Margin mode is isolated; leverage is capped at 5x.

## 平仓 / Exit

A stop-loss (entry minus 1.5 x ATR) and a take-profit at 2R (entry plus 3 x ATR)
are attached to the entry order so they exist exchange-side from the first fill.
A time stop closes at market any position still open eight hours after the fill.
Realised results feed the circuit breakers: new entries pause for the rest of
the UTC day at -30 USDT realised, a daily hard stop at -40 USDT blocks entries
and alerts the user to stop the Playbook from the GetAgent page (the Playbook
cannot stop itself), and five consecutive losses trigger a cooldown halt.

## Parameters

- `trading_symbols` — subset of BTCUSDT / ETHUSDT / SOLUSDT. Fewer symbols
  means fewer candidates for the single cluster slot.
- `leverage` — isolated-margin leverage, 1 to 5. It changes margin consumed,
  not risk at the stop.
- `margin_budget` — per-strategy capital cap and the denominator for the
  displayed return. Too small a budget caps the risk-based size (reported as
  `SIZE_CAPPED_BY_MARGIN_BUDGET`).
- `risk_per_trade_usdt` — USDT lost if the stop is hit; every outcome scales
  with it.
- `min_24h_volume_usdt` — liquidity floor for live entries.

Internal parameters (ADX / ATR / EMA periods, thresholds, exit multiples,
funding and circuit-breaker limits, replay window) are declared in
`strategy_config` so they are visible and versioned; v1 is frozen at
activation and each later version changes exactly one of them with a written
prediction first.

## How To Read Backtest Metrics

The platform shows `total_return_pct` as net PnL divided by `margin_budget`.
This Playbook overrides `net_pnl` with the figure net of engine fees, modelled
slippage and funding. `validation_report.json` in the run artifacts carries the
full table: trades, win rate, average R, net expectancy in R, profit factor,
max drawdown, Sharpe (daily returns on the margin budget, annualised) at 0x,
1x and 2x costs, plus fixed-parameter fold statistics and per-symbol numbers.
No verdict is issued under thirty trades. A negative result at 2x costs is a
rejection. Forward criteria are fixed in advance: PASS when profit factor is at
least 1.3 and Sharpe at least 0.5 after thirty live trades; FAIL and stop when
profit factor is at or below 1.1.

The replay strategy computes every indicator bar by bar from raw OHLCV, so the
platform's independent re-run of the strategy class (its official order, fill
and position evidence) uses the same logic as this Playbook's own report. The
incremental indicators are checked against the vectorised live-path
indicators on every run (`indicator_parity_incremental_vs_vectorised`).
Funding history is read from the sidecar written during the run, then from the
data SDK, and if neither is available the funding gate is switched off and
`funding_known: false` is reported rather than guessed.

## 风险 / Risk

The strategy underperforms in choppy, range-bound markets where trend
readings flip and pullbacks run through the stop. It can take a string of
losses during liquidation cascades that gap through stop levels, and a time
stop can exit just before a move resumes. Funding and slippage estimates are
modelled, not guaranteed; live fills can be worse. Historical results are not a
promise of future returns. Run it only in an isolated sub-account with capital
you can afford to draw down.
