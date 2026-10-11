# Candidate results

Pre-registration is `research/PREREG.md`. These figures are the sandbox returns. A missing row is an engine failure, not a zero.

Train window ends 2026-04-09T00:00:00Z. v2 train baseline from `pbrun-3ed23945e11e`: 14 trades, 1x −0.18129553073061996 R.

| id | run | trades | 1x R | 2x R | PF | note |
| --- | --- | --- | --- | --- | --- | --- |
| A pullback | pbrun-b9110768871e | unmeasured | unmeasured | unmeasured | unmeasured | Engine error: `high was < open`. Earlier attempts: `low was > open`, then SOL/ETH price precision. No trade count was returned. |
| B partial trail | pbrun-7f34a9bf1a73 | 14 | −0.21579425936784685 | −0.2976959503612861 | 0.6319141565029784 | Train. Engine fills 52, positions 14. Two brackets, so fills are not 2× trades. |
| C ADX 20 | pbrun-593652f44410 | 19 | −0.15974827797326407 | −0.23869086847039242 | 0.714571232047673 | Train. Fills 38, positions 19, identity agrees. |
| D 4H filter | pbrun-7f9e501109e6 | 10 | 0.02826434385871241 | −0.04597315507182499 | 1.053183037533984 | Train. Fills 20, positions 10, identity agrees. Best train 1x among measured candidates. |
| E mean reversion | pbrun-9da7c16191f6 | 30 | −0.10351508064636446 | −0.18538093752185575 | 0.6173695974275952 | Train. Fills 60, positions 30, identity agrees. |

Chosen full-period run is D, `pbrun-acf972cf66e8`:

- full trades 12, 1x 0.15628608279967598 R, 0x 0.23503965827638876 R, 2x 0.07753250732296328 R, PF 1.35098222806014
- train 10 trades, 1x 0.02826434385871241 R
- test 2 trades, 1x 0.796394777504494 R
- engine fills 24, positions 12, identity agrees

Gate: full trades 12 < 30. Fail. Not published.

Short mirror `pbrun-e1eaa27d0f6a` full period: 9 trades, 1x 0.13670191223353906 R, 0x 0.23373782752335448 R, 2x 0.039665996943723726 R, PF 1.4899302917856638. Fills 18, positions 9. Trades 9 < 30. Shorts stay off.
