# Crypto Perps Regime Trend-Following Playbook

A quantitative trend-following trading Playbook designed for Bitget USDT perpetual futures (BTCUSDT, ETHUSDT, SOLUSDT).

## 策略 / Strategy

This Playbook is an institutional-grade, long-only regime-filtered trend-following strategy designed for high-liquidity crypto perpetual contracts. The core thesis posits that crypto asset prices display persistent directional momentum once an established trend emerges from a consolidation regime. Rather than engaging in speculative bottom-picking or fading extreme momentum, the strategy filters market conditions using trend strength and volatility metrics to confirm regime alignment before committing capital.

Market regimes are evaluated on the 1-hour timeframe:
- **Trend Strength Gate**: Evaluates directional persistence via Average Directional Index (ADX) over 14 periods. Entries require ADX >= 25, filtering out trendless consolidation phases.
- **Volatility Filter**: Measures ATR(14) expressed as a percentage of price, requiring volatility to fall within healthy historical percentiles (avoiding dead illiquid compression or unmanageable extreme blowout volatility).
- **Directional Trend Trigger**: Employs an exponential moving average (EMA) momentum alignment (12-period fast EMA crossing above 26-period slow EMA).
- **Execution & Liquidity Safeguard**: Enforces a strict liquidity gate (<5 bps bid-ask spread and >$50M 24h volume) and skips entry orders within 15 minutes of the 8-hour funding settlement window or if anticipated funding drag exceeds 0.1R.

## 开仓 / Entry

The Playbook executes long-only entries strictly under full system alignment:
1. **Regime Confirmation**: ADX(14) >= 25 confirming strong trending regime, combined with valid ATR percentile.
2. **Signal Alignment**: EMA 12 crosses above EMA 26 on 1-hour bar close.
3. **Liquidity & Funding Gate**: Bid-ask spread <= 5 bps, 24h volume >= $50M USDT, outside 15-minute funding rate settlement blackout window, and expected funding cost <= 0.1R over hold duration.
4. **Order Execution & Strict Risk Sizing**: Sized dynamically for a fixed risk of 15 USDT at stop. Position size = 15 / (1.5 * ATR(14)). Limit order placed at entry price; auto-cancels if unfilled after 4 hours.
5. **Correlation & Concurrency Limit**: Maximum 3 concurrent positions across the portfolio, strictly 1 per symbol and 1 per correlation cluster (Crypto Majors).

Short entries are disabled in v1 until a separate 30-trade short-side validation test is completed and verified.

## 平仓 / Exit

Exits are governed by strict pre-defined rules attached at order execution:
1. **Initial Stop Loss**: Hard stop loss set at entry price minus 1.5 * ATR(14), attached to the order upon entry.
2. **Take Profit**: Choice of either fixed 2.0R target, or partial scale-out (50% at 1.5R with remainder trailed by 1.0 * ATR(14)).
3. **Time-Based Invalidation Stop**: Maximum hold duration of 8 hours for trend continuation trades. If neither profit target nor stop loss is reached within 8 hours, position is closed to reallocate capital. For mean-reversion transitions, positions are closed after 2 hours.
4. **Portfolio Circuit Breakers**:
   - Daily realised loss pause: New entries halted if realised loss reaches -30 USDT within 24 hours.
   - Emergency system halt: Playbook terminates execution if cumulative loss reaches -40 USDT, or after 5 consecutive losing trades, or if data freshness exceeds 60 seconds.
   - Foreign position isolation: Any position detected not opened by this Playbook generates an immediate alert without modifying external orders.

## Parameters

Subscribers can tune the following parameters within approved boundaries:
- **trading_symbols**: The active contract universe (default: `["BTCUSDT"]`, selectable from `["BTCUSDT", "ETHUSDT", "SOLUSDT"]`).
- **leverage**: Isolated leverage cap (default: 3x, maximum: 5x). Leverage scales notional exposure while capital risk remains capped at 15 USDT per stop.
- **margin_budget**: Dedicated capital allocation for this Playbook (default: 100 USDT). Serves as the authoritative denominator for return percentage calculations.
- **tp_mode**: Take-profit structure selection: `fixed_2r` (full exit at 2R) or `trail_1r` (50% scale-out at 1.5R with trailing ATR stop).

## How To Read Backtest Metrics

The backtest reports `total_return_pct`, `sharpe_ratio`, `max_drawdown_pct`, `win_rate`, `profit_factor`, and `total_trades`.
- `total_return_pct` reflects the net PnL divided by the declared `margin_budget` (strategy basis).
- All reported performance figures reflect net results inclusive of exchange maker/taker fees, 1-tick slippage simulation, and 8-hour funding rates.
- A minimum statistical sample of >=30 trades is required before any validation verdict is rendered. Forward testing criteria requires Profit Factor >= 1.3 and Sharpe >= 0.5 to PASS; Profit Factor <= 1.1 triggers automated decommissioning.

## 风险 / Risk

Trend-following strategies face systematic risk in range-bound, choppy, or directionless market regimes where false breakouts generate sequential stop-outs. Additional operational and structural risks include:
- Rapid gap risk through stop-loss levels during high-impact macroeconomic events.
- Slippage during sudden market volatility cascades.
- Persistent adverse funding rates during crowded market states.
- System halts triggered by daily drawdown circuit breakers (-30 / -40 USDT).

Past performance is not indicative of future returns. Subscribers should verify their risk tolerance and run the Playbook within an isolated sub-account.
