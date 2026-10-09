# BTC/ETH/SOL Regime-Filtered Trend Long

Long-only Playbook for Bitget USDT-M perpetuals BTCUSDT, ETHUSDT and SOLUSDT,
meant to run in an isolated sub-account. It is built to be judged on net
expectancy after fees, slippage and funding, not on displayed return.

**Validation status: REJECTED under the pre-registered rules.** Out-of-sample
walk-forward results were roughly breakeven at 1x costs and negative at 2x
costs. Do not activate it without reading `docs/btc-eth-sol-regime-long/SPEC.md`
in the source repository.

## 策略 / Strategy

The strategy tries to capture short continuation moves inside established
uptrends. It looks at hourly candles and first decides which regime each
market is in:

- **Trend regime (traded):** trend strength (ADX 14 on 1H) at or above the
  threshold, and volatility (ATR 14 as a share of price) between the 20th and
  90th percentile of the last 30 days.
- **Range regime (not traded by this version):** weak trend strength.
- **Sit out:** transitional trend strength, very quiet volatility, or extreme
  volatility.

Only the trend regime is traded, with an EMA-ADX trend-following entry.

## 开仓 / Entry

A long entry signal needs all of these on a closed 1H candle:

- the 20-period EMA is above the 50-period EMA, and +DI is above -DI;
- ADX(14) is at or above the trend threshold and volatility is inside the band;
- the candle closes above the highest high of the previous 20 candles;
- the candle's volume is at least 1.5 times its 20-candle average.

The Playbook then places an isolated-margin limit buy at the signal close,
with stop-loss and take-profit attached to the order on the exchange. The
order is cancelled if it is not filled within 4 hours. No order is placed
within 15 minutes of the 00:00, 08:00 and 16:00 UTC funding settlements, and
none is placed when funding is above 0.03% per 8 hours (longs pay). If the
signal layer produces anything other than a valid long signal, nothing is
traded; there is no default direction. Shorts are disabled.

## 平仓 / Exit

- **Stop loss:** 1.5 x ATR(14) below entry, exchange-side.
- **Take profit:** fixed 2R, exchange-side.
- **Time stop:** any position still open after 8 hours is closed at market.

## Sizing and limits

- Each trade risks a fixed 15 USDT at the stop: size = 15 / stop distance.
- Leverage is capped at 5x and margin is isolated. If the size would need
  more margin than one third of the margin budget, the trade is skipped.
- At most 3 positions or pending entries at once, 1 per symbol.
- New entries pause for the rest of the UTC day at -30 USDT realised. At -40
  USDT realised, or after 5 consecutive losses, the Playbook halts until you
  review it.
- The Playbook also stops acting on stale market data (older than 60 s). If
  it finds a position it did not open, it raises an alert and leaves that
  position alone.

## Parameters

Only `margin_budget` is user-editable. It is the capital reserved for this
Playbook and the denominator for return percentage. Raising it does not
increase the 15 USDT risk per trade; it only gives concurrent positions more
margin room. The default of 1500 USDT allows three positions at the 5x cap.

## How To Read Backtest Metrics

`total_return_pct` is net PnL divided by the margin budget. Net expectancy is
reported in R (1R = 15 USDT). Fees, funding and one tick of slippage on taker
exits are deducted. Read win rate together with the number of trades. The
validation rules give no verdict below 30 trades.

## 风险 / Risk

The edge is thin. In out-of-sample validation, gross profit was roughly
equal to costs. The strategy loses in choppy markets, around news gaps, and
when your real fee tier is worse than 0.02% maker / 0.06% taker. Exchange-side
stops can fill with slippage beyond one tick in fast markets. The daily and
consecutive-loss halts cap how fast losses can build, but they do not prevent
drawdowns. Past backtests do not guarantee future returns.
