# CHANGELOG — btc-eth-sol-regime-long

Rules:
- v1 is frozen as described in `SPEC.md`.
- Each later version changes exactly ONE parameter.
- The prediction for a version is written here, with a date, BEFORE the version is run.
- After the run, the outcome is appended underneath the prediction. The prediction is never edited.

## v1 — frozen (2026-10-09)

- Base: `ema_adx_trend`, long only (`allow_short: false`).
- `adx_trend_min = 30`, refit on 2025-10-01..2026-10-01 from the grid {20, 25, 30}.
- All other values are spec defaults, as listed in the parameter table in `SPEC.md`: EMA 20/50, ATR/ADX 14, ATR-rank band 20–90 over 720 bars, volume ≥ 1.5× the 20-bar average, 20-bar Donchian breakout, 15 USDT risk, stop 1.5×ATR, TP 2R, time stop 8h, entry TTL 4h, leverage cap 5x isolated, max 3 concurrent, daily pause −30 / stop −40 USDT, halt after 5 consecutive losses.
- Validation verdict: **REJECT**. Out-of-sample net expectancy was −0.004R at 1x costs and −0.070R at 2x. Not activated.

Package engineering changes that do not change any strategy parameter:
- Replay signals are computed inside the strategy from plain OHLCV (a trailing window of 1015 bars). The managed engine replays `backtest.yaml` without custom columns. The local Nautilus harness reproduces the earlier feature-frame result exactly: 240 trades, −0.0093R.
- Replay-only `unknown_funding_policy: allow`, because historical funding is unavailable to the managed engine for most of the window. Live always blocks on unknown funding.

## v2 candidate — NOT RUN (prediction written 2026-10-09)

**Single change:** take-profit mode goes from a fixed 2R target to 50% closed at 1.5R and the rest trailed at 1×ATR(14). Everything else stays exactly as in v1.

**Why this parameter:** 120 of 296 out-of-sample exits (41%) were time stops, against 59 at TP (3 of them gap fills) and 117 at SL (including stops hit in the fill bar). Gross average R is +0.067. Positions often run in the right direction but stall before 2R. Taking half at 1.5R should convert some time-stop exits into partial wins.

**Prediction (to be checked against the same walk-forward out-of-sample window, 1x costs):**
- Win rate rises from 0.392 to roughly 0.45–0.50.
- Net expectancy changes by less than ±0.05R. The extra exit order adds about 0.03R of taker fees per trade, which offsets most of the gain.
- At 2x costs, net expectancy stays negative.
- So the most likely verdict is still REJECT. v2 would be accepted only if net expectancy is > 0 at 2x costs over ≥ 30 out-of-sample trades.

**Falsified if:** the win rate does not rise by at least 0.04, or net expectancy at 1x moves by more than +0.05R. The second case would mean the edge sits in the 1.5R–2R region and deserves a closer look rather than being dismissed as noise.

Other one-parameter candidates (not scheduled; one at a time, each with its own prediction before it is run):
- `volume_mult` 1.5 → 2.0
- `time_stop_hours` 8 → 12
- removing BTC from the universe (BTC was −0.190R out-of-sample). This was observed in-sample, so it needs a fresh out-of-sample window before it can count.
