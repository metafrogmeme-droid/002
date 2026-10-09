# Authoring-time validation notes

Package: `humanoid-usdtm-ema-adx-trend`
Chosen base: EMA-ADX Trend Following (not mean reversion)
Activation: inactive

These numbers come from Bitget public USDT-M 1H candles
(`/api/v2/mix/market/candles` + `/history-candles`) for 2024-10-09 00:00 UTC
through 2026-10-09 17:00 UTC (17,455 bars/symbol). They are **not** an official
GetAgent sandbox run. Managed inner kline probe returned HTTP 403 here.
ACCOUNT ACCESS-KEY was not available; the screenshot key was not used.

## Walk-forward

- Train: 2024-10-09 → 2026-03-09
- Test: 2026-03-09 → 2026-10-09
- Candidates scored on train only. Chosen: EMA 12/26, ADX min 25, ATR percentile 20–90.

## Train 1x (VIP0 2/6 bps + 1 tick)

trades 51 | win rate 0.4902 | NET E 0.1846 R | PF 1.486 | max DD −77.24 USDT | Sharpe 0.848
halted: five consecutive losses

## Test 1x — no verdict (<30 trades)

trades 25 | win rate 0.52 | NET E 0.0079 R | PF 1.020 | max DD −49.99 USDT | Sharpe 0.030
halted: five consecutive losses

## Test cost book (still <30)

- 0x: 5 trades, NET E −0.481 R
- 1x: 25 trades, NET E +0.0079 R, PF 1.020
- 2x: 25 trades, NET E −0.0439 R, PF 0.898

Do not activate. Official sandbox / publish / subscribe links: PENDING.
