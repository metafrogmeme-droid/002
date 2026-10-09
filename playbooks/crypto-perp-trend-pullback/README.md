# Crypto Majors Trend Pullback (BTC/ETH/SOL perps, long-only)

Sleeve A of the GetAgent sub-account plan: crypto USDT perpetuals on Bitget
(`BTCUSDT`, `ETHUSDT`, `SOLUSDT`). Version v1. Every number this Playbook
reports is net of fees, slippage and funding.

## 策略 / Strategy

The strategy tries to buy short dips inside an hourly uptrend on the three
most liquid crypto perpetuals. A coin counts as trending up when trend
strength (ADX) is high, the positive directional line leads the negative one,
price is above the slower moving average, and the faster average is above the
slower one. Volatility also has to sit in a normal range compared with the
last month, which filters out dead and panicked markets.

All three coins belong to the same correlation cluster ("crypto majors"), so
the Playbook holds at most one position or one resting entry at a time. When
more than one coin qualifies in the same hour, it takes the one with the
strongest trend.

## 开仓 / Entry

- Long only. Shorts stay disabled until a separate short-side test with at
  least 30 trades shows positive net expectancy.
- The entry is a limit buy half an ATR below the last close. If it hasn't
  filled after 4 hours, it is cancelled.
- Size is set so that hitting the stop loses 15 USDT before costs:
  qty = 15 / (entry - stop). Margin mode is isolated and leverage is capped at 5x.
  Because size comes from the fixed risk, changing leverage only changes how
  much margin is locked, not the loss at the stop.
- An entry is skipped when any of these is true: the bid/ask spread is wider
  than 5 bps, 24h quote volume is under 100M USDT, the signal bar closes within
  15 minutes of an 8-hour funding settlement, expected funding over the planned
  hold is more than 0.1R, the order can't meet the exchange minimum or would
  need more than leverage x margin budget, or any input is missing or stale. A
  missing or invalid signal always means no trade.

## 平仓 / Exit

- The stop (1.5 x ATR(14) on 1H below the entry) and take-profit (fixed 2R)
  are attached to the entry order, so they live on the exchange from the
  moment it fills.
- Time stop: a position that hasn't hit either level after 8 hours is closed
  at market.
- If the stop order is missing on a live position, the position is closed
  right away (`EXIT_SAFETY_NO_SL`).

## Halts and pauses

- At -30 USDT realised loss in a UTC day, new entries pause until the next day.
- At -40 USDT realised loss in a day, the Playbook halts. It stops opening
  trades and asks you to stop the instance in the GetAgent page. The Playbook
  can't stop itself.
- 5 losing trades in a row also halts the Playbook.
- If market data is more than 60 seconds old, nothing new is opened that
  cycle.
- If the account holds any position or order this Playbook didn't open, it
  sends an alert and halts entries without touching that position.

## Parameters

- `trading_symbols`: any subset of BTCUSDT, ETHUSDT, SOLUSDT. Fewer symbols
  means fewer trades, so it takes longer to reach a verdict.
- `leverage` (1-5): sets the isolated margin per trade and the notional cap.
  It does not change the risk per trade.
- `margin_budget` (USDT): the capital cap used to size margin and to compute
  return %.

All other values are fixed for v1 and are listed in `manifest.yaml`
`strategy_config`. Each later version may change only one parameter, and the
expected effect has to be written down before the change is tested.

## How to read the backtest

The sandbox run uses Bitget 1H candles and Bitget funding history over the
24 months from 2024-10-01 to 2026-10-01. It reports trades, win rate, average
R, net expectancy R, profit factor, max drawdown, and Sharpe (daily net PnL
over the margin budget, annualised with sqrt(365)). Costs are shown at 0x, 1x
and 2x. A version is rejected if it is negative at 2x, and no verdict is given
on fewer than 30 trades. The walk-forward uses four sequential 6-month folds,
plus an in-sample/out-of-sample split at 2025-10-01. Parameters were set
before looking at any results and nothing was fitted. Return % is net PnL
divided by the margin budget.

## 风险 / Risk

Trend pullbacks can keep falling. Choppy, range-bound markets produce strings
of time stops and small losses, and fast moves can fill the stop well beyond
its level. Fees are about 0.06R per round trip at the base fee tier, so the
strategy needs a real directional edge to be profitable. Live funding, fills
and fee tier can be worse than modelled. Past results do not guarantee future
results.
