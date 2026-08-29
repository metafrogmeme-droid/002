# BTC EMA Crossover Demo

A minimal trend-following Playbook on BTC perpetual futures, used as an
end-to-end walkthrough of the GetAgent Playbook Creator skill.

## 策略 / Strategy

This Playbook captures sustained directional moves on BTC perpetual futures.
It runs on 1-hour bars and bets on the assumption that, once a trend forms,
price tends to travel along that trend in a relatively clean direction
rather than chopping back and forth.

The decision is driven by alignment between two moving averages of different
horizons. When the shorter horizon clearly leads the longer horizon upward,
the strategy reads it as bullish alignment. When it falls below the longer
horizon, the strategy reads it as bearish alignment.

## 开仓 / Entry

The Playbook opens a long position when the short-horizon trend crosses
above the long-horizon trend, indicating that recent momentum has flipped
in favor of the upside. It opens a short position on the inverse cross.

There is no fading of extremes, no top-picking, and no pyramiding. Only the
crossover event is treated as actionable.

## 平仓 / Exit

A position is closed on the inverse crossover. When the short-horizon
trend retracts below the long-horizon trend (for longs) or back above it
(for shorts), the strategy interprets that as a fade of conviction and
exits the position. Stop loss and take profit are not used in this demo —
the cross alone exits the trade.

## Parameters

Subscribers may tune two parameters at subscription time:

- **leverage** — amplifies both upside and drawdown equally. Higher leverage
  does not make the strategy more selective; it only sizes risk larger.
- **margin_budget** — per-strategy capital cap, used by the platform to size
  orders and to compute the user-facing return percentage.

## How To Read Backtest Metrics

The backtest reports `total_return_pct`, `sharpe_ratio`, `max_drawdown_pct`,
`win_rate`, and `total_trades`. `total_return_pct` is the strategy-budget
return (`net_pnl / margin_budget`); `account_total_return_pct` is the raw
account-level number from the engine. Pay attention to drawdown depth and
total trade count alongside return — a high return on too few trades is not
robust evidence.

## 风险 / Risk

This demo strategy underperforms in choppy, range-bound markets where the
short-horizon trend flips repeatedly without committing to a real trend.
Around major news gaps and persistent funding-rate dislocation it can
produce a string of stops or trapped positions. Past historical performance
is not a guarantee of live profitability — match it against your own risk
tolerance before subscribing, and do not run it with leverage you cannot
afford to draw down.
