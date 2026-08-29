# Crypto Spot Momentum Trader

This package is a backtestable and follow-trade capable crypto spot Playbook. It
can replay Bitget spot OHLCV through the managed backtest engine and can place a
spot market buy when the subscription is running in `follow_trade` mode.

## What It Does

- Uses `output_kind: trade_strategy`
- Trades Bitget crypto spot `BGBUSDT`
- Uses `backtest_support: full` with `backtest.yaml` for historical replay
- Emits one managed signal per run
- Uses `runtime.emit_signal_or_follow(...)` so orders require the managed live
  trade-permission gate
- Uses `trade.helpers.compute_qty(..., market="spot")` before spot order
  placement

## 策略 / Strategy

The Playbook tracks BGB spot momentum with a transparent EMA crossover replay
strategy. Historical runs use `backtest.yaml` and the Nautilus-backed managed
engine. Live runs use recent Bitget spot candles to confirm that momentum is
positive and recent drawdown remains controlled before emitting an actionable
signal.

## 开仓 / Entry

When BGB passes the momentum and drawdown gates, the Playbook emits a `long`
signal. In follow-trade mode, the runtime calls the trade callback and the
package places a spot market buy sized from the configured USDT budget.

## 平仓 / Exit

Historical replay exits when the fast EMA crosses back below the slow EMA. The
live follow-trade path is intentionally entry-only for this test package: if BGB
no longer qualifies, it emits `hold` and does not add exposure.

## 风险 / Risk

Momentum can reverse suddenly, market orders can suffer slippage, and spot
inventory may remain exposed after a signal weakens. Backtest performance does
not include all live execution frictions. This package is meant for controlled
testing and should use small budgets until live behavior is reviewed.

## Run Local Validation

From the repository root:

```bash
python3 skills/getagent/scripts/validate.py skills/getagent/examples/crypto-spot-momentum-trader
```
