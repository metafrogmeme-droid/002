# USDT Perpetuals Trend-Following Playbook

An institutional-grade trend-following strategy designed for Bitget USDT-Margined perpetual futures (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`), operated in an isolated sub-account and optimized for positive net expectancy.

## 策略 / Strategy

This Playbook captures sustained directional momentum in liquid crypto perpetual contracts. Market microstructure regimes are classified on the 1-hour timeframe using ADX(14) and ATR(14)/Price percentiles:
- **Trending Regime**: ADX(14) >= 25.0 and ATR(14)/Price between the 20th and 85th historical percentiles. Traded exclusively.
- **Sat Out Regimes**: Compression/Dead range (ADX < 20 or ATR percentile < 20th), choppy range (20 <= ADX < 25), and extreme volatility/exhaustion (ATR percentile > 85th).

The base model implements EMA-ADX Trend Following:
- Fast EMA(12) > Slow EMA(26) on 1H bars.
- 1H Bar Close > EMA(12).
- ADX(14) >= 25.0 indicating strong directional strength.
- Volume confirmation: Current bar volume >= 1.5x of the 20-bar simple moving average volume.
- Funding rate filter: Skip entry if funding rate > +0.03% per 8h against long positions, or within +/-15 minutes of funding settlement (00:00, 08:00, 16:00 UTC).
- Long-only execution: Short positions remain disabled until a distinct short-side model demonstrates >= 30 trades with statistically positive net expectancy.
- Strict validation: If any calculation or external filter returns invalid or ambiguous data, the strategy enforces NO TRADE. Never defaults to an arbitrary direction.

## 开仓 / Entry

The Playbook enters long positions via limit orders at the closing price of the signal candle, cancelling if unfilled after 4 hours:
- Sizing formula: `Position Size = Risk Capital (15 USDT) / Stop Distance`, capped at 5x leverage.
- Stop Distance: `1.5 x ATR(14)` on the entry 1H timeframe.
- Exchange-side protection: Attached directly to the entry order (exchange-side TPSL) with no post-fill unhedged exposure.

## 平仓 / Exit

The exit architecture enforces positive expectancy through disciplined asymmetric exits:
- **Take Profit (TP)**: 50% scale-out at 1.5R (+2.25x ATR distance), remaining 50% trailed at 1.0x ATR from the highest price reached since fill. Alternatively, full limit at 2.0R.
- **Stop Loss (SL)**: Fixed 1.5x ATR initial stop loss.
- **Time Stop**: 8 hours maximum trade duration for trend trades. If neither TP nor SL is triggered within 8 hours, the trade is liquidated at market.
- **Circuit Breakers**:
  - Daily realised loss pause at -30 USDT.
  - Hard Playbook stop at -40 USDT.
  - Consecutive losses halt: 5 consecutive losses triggers strategy pause and diagnostic audit.

## Parameters

Subscribers may configure parameters at subscription:
- `trading_symbols`: Universe of contracts to scan (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`).
- `margin_budget`: Denominator for platform return tracking and maximum capital buffer.
- `leverage`: Hard capped at 5x maximum.
- `risk_per_trade_usdt`: Fixed 15 USDT risk per trade.

## How To Read Backtest Metrics

Key metrics tracked on a per-strategy net basis:
- `win_rate`: Percentage of profitable closed trades.
- `profit_factor`: Ratio of gross profits to gross losses (target >= 1.3).
- `net_expectancy`: Net R-multiple expectation per trade after all fees (0.06% taker, 0.02% maker, 1-tick slippage, and funding drag).
- `max_drawdown_pct`: Maximum peak-to-trough decline on margin budget.
- `sharpe_ratio`: Annualized risk-adjusted excess return.

## 风险 / Risk

The strategy is subject to specific market and operational risks:
- **Whipsaws and False Breakouts**: Choppy sideways regimes can trigger stops before directional continuation occurs.
- **Funding Cost Drag**: Sustained periods of positive funding rates reduce net long expectancy.
- **Execution Slippage**: Fast market events may result in fill prices deviating from limit trigger levels.
- **Data Stale / Exchange Halt**: Stale market data (> 60s) or external unmanaged sub-account positions immediately halt new entries to preserve capital.
