# BTC Net Expectancy

**Research status:** rejected and fail-closed. `activation_eligible` is `false`;
live execution emits `RESEARCH_VALIDATION_FAILED` and places no order. Do not
activate this package unless a later, separately validated version passes every
declared evidence gate.

## 策略 / Strategy

This is one long-only Sleeve A Playbook for the Bitget `BTCUSDT` USDT perpetual. It seeks hourly momentum recoveries after pullbacks inside a rising long-term trend, only when trend strength and the volatility regime agree. It is designed for an isolated sub-account dedicated to this Playbook. It never opens shorts. Missing, stale, invalid, or unsupported data produces `NO TRADE`.

The live liquidity gate requires spread at or below 5 bps and 24-hour quote volume at or above the configured floor. The funding gate blocks new orders within 15 minutes of an 8-hour settlement and whenever expected funding over the planned hold exceeds 0.1R. Contract support, sub-account existence, leverage, tick, lot, minimum notional, and position ownership are checked before mutation.

## 开仓 / Entry

The signal requires a 1-hour momentum recovery, a rising long-term trend, ADX trend strength, and ATR-percentile regime filters. The Playbook submits a long limit order one tick below the latest price. It risks 15 USDT at a stop 1.5 times ATR from entry, caps leverage at 5x, uses isolated margin, and attaches stop-loss and fixed 2R take-profit trigger prices to the entry. Unfilled orders expire after four hours.

Only one symbol is declared, so the one-position and crypto-major correlation limits are inherently respected. The Playbook also refuses a new entry when the sub-account already has three positions, when any position cannot be attributed to this Playbook, after the daily pause threshold, after the total stop threshold, or after five consecutive losses.

## 平仓 / Exit

An attached stop limits the planned pre-gap loss, while the fixed take-profit exits at 2R. A trend trade also has an eight-hour time stop. The strategy never touches a position that its persistent state does not identify as its own; it emits an alert instead. Exchange gaps and execution latency can still create a realised loss larger than the intended 15 USDT.

## 风险 / Risk

The principal risks are failed pullback recoveries, limit non-fills, gaps through stops, fee-tier differences, unmodelled funding, stale feeds, and state loss. The strategy stops creating entries at a 30 USDT daily realised loss and halts at a 40 USDT Playbook loss. Five consecutive losses also halt entries. Forward acceptance is fixed before activation: pass only after at least 30 live trades with profit factor at least 1.3 and Sharpe at least 0.5; profit factor at or below 1.1 is a failure and requires stopping the Playbook.

Backtest return is not the objective. The decision metric is net expectancy in R after fees, one-tick slippage, and funding. Any metric not produced by actual replay or live records remains `PENDING`. No verdict is allowed with fewer than 30 trades.

## Tunable parameters

- `leverage`: capital efficiency, capped at 5x; it does not change cash risk at the stop.
- `margin_budget`: capacity ceiling and denominator for displayed strategy return.
- `risk_usdt`: intended cash loss at the stop.
- `min_24h_volume_usdt`: minimum live quote turnover.
- `max_spread_bps`: maximum live bid-ask spread.

Version 1 is frozen only when the user activates it. Any later version must change exactly one parameter and record its prediction before testing.
