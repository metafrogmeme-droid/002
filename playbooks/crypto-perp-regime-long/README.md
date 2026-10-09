# Crypto Perp Regime Long (BTC / ETH / SOL) - v1 forward-test candidate

> **Status: shipped DISARMED.** In offline testing this rule set did not show a statistically reliable positive net
> edge and turned negative at 2x trading costs. Under the author's own pre-registered rule ("negative at 2x -> reject")
> it should not trade real funds. The switch `live_armed` defaults to `false`. Arm it only as a deliberately small
> forward test, knowing the evidence does not support an edge.

## 策略 / Strategy

Long-only breakout continuation on Bitget USDT-margined perpetuals `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, hourly bars.
Bitcoin, ether and solana move together, so the three symbols form one correlation cluster and the Playbook holds at
most **one** position or resting order at a time. The Playbook is deterministic: the same code path (`src/rules.py`)
produces the signal in the historical replay, in offline research and in live execution. There is no AI/LLM layer; if
the signal layer has invalid or insufficient data the result is NO TRADE.

## 开仓 / Entry

All must be true on the last closed hourly bar:

- trend strength (ADX) is above the configured level and positive directional pressure dominates;
- volatility is expanding versus its own trailing history (ATR percentile above the configured rank);
- price is above its long moving average and closes above the highest high of the previous 48 hours for the first time;
- liquidity gates pass (spread, 24h volume), we are not within 15 minutes of a funding settlement, and expected funding
  over the planned hold is at most 0.1R;
- no halt is active and the cluster is free.

The entry is a **limit order** at the signal bar close, cancelled after 4 hours if unfilled (or earlier if a funding
window approaches). Margin mode is isolated. Position size = 15 USDT / stop distance, rounded down to the exchange lot
step; if the required margin exceeds `margin_budget`, the trade is skipped (never shrunk).

## 平仓 / Exit

- Stop loss attached to the entry order at 1.5 x ATR(14) below the entry price.
- Fixed take profit at 2R, attached to the same order.
- Time stop: market close after 8 hours.

## 风险 / Risk

- Pause new entries at -30 USDT realised for the UTC day; stop the Playbook at -40 USDT cumulative.
- Halt on 5 consecutive losses, data older than 60 seconds, or any position this Playbook did not open (alert only; it
  never touches foreign positions).
- Parameters you may change: `leverage` (1-5; does not change risk per trade, only margin and liquidation distance),
  `margin_budget` (per-position margin cap), `live_armed` (default off).
- Main risks: false breakouts and reversals, sideways markets, cost drag (fees, funding, slippage), and gap risk. The
  historical replay does not model funding; the offline research does (see the design document for all numbers and
  what was and was not tested). Expect roughly 4 trades per month, so 30 live trades take about 7 months.
