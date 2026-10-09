# CHANGELOG — btc-eth-sol-perp-trend-v1

Rule: one parameter change per version, with the prediction written **before**
the version is run. A version without a sandbox run has no results line.

## 1.0.0 — frozen (2026-10-09)

* Package as uploaded: `draft_id 91b4392b-6bf2-4d6c-9765-9dfd86f732ef`,
  sandbox run `pbrun-5e06c2a50923` (completed).
* Result (strategy basis, 2024-10-09 → 2026-10-09): 42 trades, WR 28.6%,
  expectancy −0.403 R, PF 0.44, net −251.30 USDT (−16.75% of budget),
  maxDD 16.75%, Sharpe −1.42. Verdict NEGATIVE_NET_EXPECTANCY; cost
  sensitivity REJECTED (negative already at 0x costs).
* Short-side research (same code, `side_mode: short_only`): 43 trades,
  −0.074 R, PF 0.88 → shorts stay disabled.
* Full detail: `DESIGN.md` §7. No parameter was changed after seeing results.

Pre-run fixes recorded for traceability (all before the final run, none
based on performance):

1. Entry limit moved from "= close" to "close − 1 tick" because the engine
   fills a limit at the close as a taker on the next bar.
2. `data_requirements.required_bar_fields: [funding_rate]` removed — the
   platform's bootstrap replay feeds plain OHLCV and failed on it.
3. Explicit funding degradation (filter not applied + fallback rate, both
   counted) because funding history is only ~90 days deep.

## 1.1.0 — candidate, NOT RUN

Single change: `time_stop_hours` 8 → 16.

Prediction (written before any run): time stops were 23 of 42 exits and
the gross expectancy was negative, which suggests the 2R target is rarely
reached inside 8 bars. Doubling the holding window should convert some time
stops into take profits or stops. Expected direction: take-profit count up,
trade count unchanged (same triggers), funding cost roughly doubled.
Falsifier: expectancy stays ≤ 0 R on ≥ 30 trades → the problem is the
trigger, not the holding time, and 1.2.0 should change the trigger instead.

## 1.2.0 — candidate, NOT RUN (only if 1.1.0 fails)

Single change: `adx_min` 25 → 30.

Prediction: fewer, stronger-trend signals; trade count drops by roughly a
third, so a 30-trade verdict may need a longer window. Falsifier: expectancy
does not improve while trade count drops → ADX strength is not the missing
ingredient.

## Not planned

* Any change to `risk_per_trade_usdt`, `leverage` or `margin_budget` — these
  scale PnL but cannot change the sign of expectancy.
* Enabling shorts without a fresh short-only run that shows ≥ 30 trades with
  positive net expectancy.
