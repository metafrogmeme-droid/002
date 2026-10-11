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

## Round 2, written before any new run

Published baseline is v2.1, server 0.0.3, replay `pbrun-d51101dff3a2`: 17 trades, 0x +0.0023092223477735106 R, 1x −0.07888825482119473 R, 2x −0.1600857319901629 R. Train 14 trades, 1x −0.18129553073061996 R. Test 3 trades, 1x +0.3990123660894564 R. Full-sample cost drag, 1x minus 0x, is −0.08119747716896824 R per trade. Train 0x was not returned, so train drag is predicted from that full-sample drag, not from a train 0x I do not have.

Gates are unchanged: full period ≥ 30 trades, 1x > 0, 2x ≥ 0, and a test-window expectancy with the same positive sign as train. Risk, the 10x isolated cap, and the 15 USDT stop are not changed. A combination is not listed here. It will be appended only after each of its pieces has improved train 1x versus −0.18129553073061996 R on its own, and before that combination is run.

| id | one change versus v2.1 | predicted trades | predicted 0x R | predicted 1x R | predicted cost drag (1x − 0x) |
| --- | --- | --- | --- | --- | --- |
| T4 | Signal, ADX, ATR, the 1.5×ATR stop, and volume use 4H bars instead of 1H. Thresholds stay the numbers in v2.1. The hourly scan stays; a decision happens only on a newly closed 4H bar. The time stop becomes 32 hours, which is 8 bars, the same bar count as the 8 hour stop on 1H. That clock change is part of this timeframe change, not a second knob. | Train count falls well below 14. Four times fewer bars, and crosses are rarer. | Stays near zero. This is not predicted to create a gross edge. | Improves on −0.181 because the drag shrinks, and is not predicted to be positive. | Roughly half of −0.081, toward about −0.04. A 4H ATR stop is wider, the 15 USDT risk buys less notional, and the fee is a smaller fraction of R. |
| MX | The 2R target is a resting reduce-only limit, post-only when the bracket call accepts that flag. The stop stays a taker stop-market. Entries stay the v2.1 cross. | Stays near 14 if the order is accepted. If post-only is rejected, the run fails or the count falls. | Unchanged, because 0x does not charge fees. | Stays near −0.181. The author net already charges the maker rate when the exit is the target. If post-only turns a gap-through target into a stop or a time stop, 1x gets worse. | Author drag stays near −0.081. Whether the engine itself charges maker on those target fills is not known yet. If the fills are taker, MX is PENDING and is not an improvement. |
| A | Enter on a tag of EMA20 inside an established uptrend (prior close above EMA20, EMA20 above EMA50), instead of only a fresh cross. The bar-construction failure from the last attempt is fixed before this measurement. | Train count rises above 14. | Stays at or below zero. A looser entry in the same regime is not predicted to mint a gross edge. | Stays negative. | Stays near −0.081. The stop is still 1.5×ATR(14) on 1H. |
| F4 | Keep the 1H v2.1 cross and require the EMA50 slope of 4H closes, built from those 1H closes, to be up. Re-measured because bar construction changed after `pbrun-7f9e501109e6`. | Stays near that run's 10 trades. | Slightly above the 1x figure. | Stays slightly positive, near +0.02826434385871241 R. The later v2.1 cross replay did not move the 17-trade sample, so this filter's sign is predicted to hold. | Stays near −0.07 to −0.081. 2x stays negative, as in −0.04597315507182499 R on that earlier train run. |

None of these four is predicted to pass the full-period gates. T4 is the one predicted to cut the cost drag. F4 is the one predicted to show a positive train 1x, on a sample too small to trust and with 2x still negative.
