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

## Round 2

Pre-registered in `687ca8575a225f40b85b3802e5b8b27028752c8c` before any run. The combination was pre-registered in `d1948b2` after the single-change train runs and before the combination run. v2.1 train baseline stays 14 trades, 1x −0.18129553073061996 R. Cost drag is author 1x minus author 0x. Upload HTTP 200 and run HTTP 200 for every row. The saved poll body code is 200. None of these runs was confirmed or published.

| id | one change | run | trades | 0x R | 1x R | 2x R | cost drag | PF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A pullback | EMA20 tag inside an established uptrend, instead of a fresh cross | pbrun-fb88aa84852e | 31 | −0.009746742276551978 | −0.08986471969338064 | −0.16998269711020933 | −0.08011797741682866 | 0.8004631533582727 |
| T4 | 4H signal, ADX, ATR, stop, and volume; time stop 32 hours (8 bars) | pbrun-5a6190d2af9b | 0 | undefined | undefined | undefined | undefined | undefined |
| MX | 2R target is a post-only reduce-only limit; stop stays a taker stop-market | pbrun-fec6fb63ac8b | 14 | −0.10409235701641426 | −0.18129553073061996 | −0.2584987044448256 | −0.07720317371420571 | 0.6908843492682346 |
| F4 | 4H EMA50 slope must be up on the 1H v2.1 cross | pbrun-b43227c8f807 | 10 | 0.10250184278924986 | 0.02826434385871241 | −0.04597315507182499 | −0.07423749893053744 | 1.053183037533984 |

T4 completed with 0 engine orders, 0 fills, and 0 positions. `coverage_ok` is false because the last 4H bar is 2026-04-08T20:00:00Z, more than two hours before the train end, while 3282 4H bars and 547 funding rows are present. The zero trade count is the engine result. Expectancy is undefined, so T4 did not improve train 1x.

MX `exit_model` is `{"maker_tp":"post_only"}`. Liquidity on that replay: 14 LIMIT BUY TAKER entries, 6 MARKET SELL TAKER, 7 STOP_MARKET SELL TAKER, 1 LIMIT SELL MAKER. The engine charged maker on that one resting target fill. Author 1x equals the v2.1 train baseline, so MX did not improve.

A and F4 each improved train 1x versus −0.18129553073061996 R. The only allowed combination is AF.

AF, `pbrun-9d367631f81e`, train: 27 trades, 0x −0.03854527820408705 R, 1x −0.11879618128266156 R, 2x −0.1990470843612361 R, cost drag −0.08025090307857452 R, PF 0.7284855730811243. Fills 54, positions 27, identity agrees. Its 1x is worse than A alone.

Chosen full-period run is A, because 31 is the unique maximum train trade count and the selection rule is the best train 1x among the candidates with the most trades. One full-period replay, `pbrun-03b498910da3`:

- full: 31 trades, 0x −0.009746742276551978 R, 1x −0.08986471969338064 R, 2x −0.16998269711020933 R, PF 0.8004631533582727, win rate 0.4838709677419355, max drawdown 4.38929305262008% of 3000, net −41.383291255759005 USDT, Sharpe −0.5611, coverage_ok true
- train block inside that run: 31 trades, 1x −0.08986471969338064 R, status OK
- test block: 0 trades, expectancy undefined, status NO_TRADES
- engine account 100000.00000000 → 99959.62437622 across 204 points and 63 unique totals; fills 62, positions 31, identity agrees

Gates: trades 31 ≥ 30 pass; 1x > 0 fail; 2x ≥ 0 fail; test expectancy positive and the same sign as train fail. Not published. Published version stays server 0.0.3.

## Round 2 follow-up

Two harness defects were fixed before any new measurement. The predictions in `687ca85` were not rewritten.

The coverage tail is one bar interval plus one hour. On 1H that is still two hours. A 4H bar timestamp four hours before the window end is inside the tail. Commit `5247869`.

A native 4H bar type still placed no orders after that fix (`pbrun-a90f884eaf4c`, coverage_ok true, 0 orders). The engine stays on 1H bars. When `bar_hours` is 4, the strategy folds four hourly bars and runs the signal only on that closed 4H bar. Commit `df23200`. Bar counts are reported in `dce1eb4`. The published defaults stay 1H, cross, 8 hour time stop, 15 USDT, 10x, and the −40 USDT halt. `window_label: test` is only a replay label (`75add79`).

T4 train, `pbrun-4642bd937f30`, replay mode: fresh train window 2024-10-09 to 2026-04-09, 1H engine bars folded into closed 4H bars, time stop 32 hours. Upload, run, and poll HTTP 200. coverage_ok true. Bars seen 39384. Closed 4H bars 9843. Trades 0. 0x, 1x, 2x, cost drag, and PF are undefined. The drag prediction (about half of −0.081 R) cannot be scored. T4 did not beat the train baseline of −0.18129553073061996 R, so no combination was pre-registered or run.

A fresh test window, `pbrun-94d7e2652b3f`, replay mode: new account from 2026-04-09T00:00:00Z to 2026-10-09T00:00:00Z, halts start at zero, indicators warm up inside the window. This is not the test split inside `pbrun-03b498910da3`, where the −40 USDT halt had already tripped. Upload, run, and poll HTTP 200. Pullback only. 13 trades, 0x −0.14153562640954875 R, 1x −0.23579914583117276 R, 2x −0.3300626652527967 R, cost drag −0.09426351942162401 R, PF 0.5755048528484816, net −45.99068802596161 USDT. Fills 26, positions 13, identity agrees. coverage_ok true. `four_hour_closed` 0, which is the 1H path.

A's full-period numbers stay the continuous replay `pbrun-03b498910da3`: 31 trades, 1x −0.08986471969338064 R, 2x −0.16998269711020933 R. Gates: trades pass; 1x fail; 2x fail; fresh test 1x is negative, so the positive-test gate fails. No other candidate led on train 1x with enough trades to run a second full period. Not published.
