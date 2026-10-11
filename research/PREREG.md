# Pre-registration, written before the candidate runs

The skill validator rejects a `research/` directory inside the Playbook package, so this file lives at `research/PREREG.md` in the repo, next to the package.

v2 stays the published baseline: long-only EMA(20)/EMA(50) cross, ADX ≥ 25, +DI > −DI, ATR percentile 20–80, volume 1.5×, fixed 2R, 8h time stop, 10x isolated cap, 15 USDT at the 1.5×ATR stop. Measured on `pbrun-3ed23945e11e`: 17 trades, 1x expectancy −0.07888825482119473 R, 2x −0.1600857319901629 R. Train through 2026-04-09: 14 trades, −0.18129553073061996 R. Test: 3 trades, +0.3990123660894564 R.

Ranking uses the train window only (execution end = walk-forward split). The test window is not read until one full-period run of the single best train candidate. A pass requires full-period trades ≥ 30, 1x expectancy > 0, 2x expectancy ≥ 0, and a test-window expectancy with that same positive sign.

Short-side replay is separate. It does not enter the ranking. Shorts stay off unless that replay has ≥ 30 trades, 1x expectancy > 0, and 2x expectancy ≥ 0.

| id | one change from v2 | predicted effect |
| --- | --- | --- |
| A pullback | Enter on a tag of EMA20 after the prior close was above it, while EMA20 > EMA50, instead of only on a fresh cross. ADX, DI, ATR band, volume, 2R, and 8h stop stay. | Trade count on train rises above the 14-trade v2 train. The edge was negative, so 1x and 2x expectancy stay ≤ 0. This is not predicted to pass. |
| B partial trail | Exit becomes 50% at 1.5R and a 1×ATR trail on the rest (6R cap only so the second half still has an attached target). Entries stay the v2 cross. | Trade count stays near the v2 count. 2x expectancy stays negative. This is not predicted to pass. |
| C adx 20 | ADX minimum 20 instead of 25. Nothing else changes. | Train trade count rises. Weaker trends are included, so expectancy stays ≤ the v2 train expectancy and 2x stays negative. This is not predicted to pass. |
| D 4h filter | Require the EMA50 slope of 4H closes, built from 1H closes, to be up. The 1H trigger stays the v2 cross. | Train trade count falls below 14. The sign of expectancy stays negative. This is not predicted to pass. |
| E mean reversion | Long only when ADX < 20 and close is at least 1×ATR below EMA20. Time stop is 2h. The trend cross is not used. | Train trade count rises above 30 because the low-ADX regime is common. 2x expectancy stays negative. This is not predicted to pass. |
| S short mirror | Bearish EMA cross, ADX ≥ 25, −DI > +DI, funding skip when the rate is below −0.0003. Longs are not taken in this replay. | Full-period trade count can exceed 17. Net expectancy at 2x stays negative, so shorts stay disabled. |

No other parameter is searched. If every train expectancy is negative, the least-negative train 1x expectancy is still the one full-period run.
