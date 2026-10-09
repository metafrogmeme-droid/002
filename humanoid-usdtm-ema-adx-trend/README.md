# HUMANOID USDT-M EMA-ADX Trend

Long-only Bitget USDT-M Playbook for `BTCUSDT`, `ETHUSDT`, and `SOLUSDT`
perpetual contracts. It is designed for an isolated sub-account and optimises
for verifiable **net** expectancy after fees, one-tick slippage, and funding —
not displayed ROI.

Activation status: **inactive**. Official GetAgent sandbox evidence is PENDING
until an ACCESS-KEY is provided and a historical run actually completes.

## 策略 / Strategy

The Playbook captures the middle of bullish trends on the three major USDT-M
perps. A regime filter sits on 1H ADX(14) and a rolling ATR(14)/price
percentile:

- **Traded:** ADX(14) ≥ 25 (sample median on the 2024-10-09 to 2026-10-09 1H
  Bitget history is about 24.5–24.9 across the three symbols) **and** the
  rolling ATR/price percentile is inside 20–90.
- **Sat out:** ADX below 25 (range / chop) **or** ATR/price percentile below 20
  (dead tape) **or** above 90 (crisis / gap risk).
- **No-trade clock:** ±15 minutes around funding at 00:00 / 08:00 / 16:00 UTC.
- **Funding veto:** skip a new long when the next known funding print is above
  0.03% / 8h (longs pay positive funding). If the next print is unknown, do
  not invent a rate; do not skip and do not charge.

Base style is **EMA-ADX Trend Following**, not mean reversion. ADX is a
trend-strength meter. The complementary low-ADX half of the sample is exactly
the regime this Playbook sits out, so fading that half would be a different
product. Shorts stay disabled: no separate short-side test with ≥30 trades and
positive net expectancy exists.

## 开仓 / Entry

Timeframe: 1H. Trigger, not a guess:

1. Fast EMA(12) is above slow EMA(26). EMA 21/55 and 20/50 were train-only candidates; 12/26 won on train NET E.
2. ADX(14) is at or above 25 and a new setup episode has just begun (regime
   just became tradeable while the EMA stack is bullish).
3. Volume confirms at ≥ 1.5× the 20-bar average within 4 hours of setup.
4. Funding window and funding-rate veto are clear.
5. Optional live AI layer: if invoked and it returns invalid / no signal,
   **no trade**. The AI never supplies a missing direction.

Entry is a **limit** at the signal close. Unfilled after 4 hours → cancel.
Size = `15 USDT / (1.5 × ATR(14))`, isolated margin, leverage hard-capped at 5x.
Stop is attached on the same order (exchange-side TPSL, no post-fill gap).

## 平仓 / Exit

- Stop: 1.5 × ATR(14) below entry, attached to the entry order.
- Take profit (the one chosen): 50% at 1.5R, trail the rest at 1 × ATR(14).
- Time stop: 8 hours (trend).
- Max 3 concurrent positions, 1 per symbol.
- Pause new entries at −30 USDT daily realised; stop the Playbook at −40 USDT.
- Halt: 5 consecutive losses; market-data quote stale > 60s; any position in
  the sub-account this Playbook did not open (alert, do not touch).

## Parameter table

| name | value | rationale | source |
| --- | --- | --- | --- |
| universe | BTCUSDT, ETHUSDT, SOLUSDT | User spec; Bitget `symbolStatus=normal` USDT-M perps | data (Bitget contracts API 2026-10-09) |
| entry_timeframe | 1H | Matches the ADX/ATR regime filter | default (user spec) |
| fast_period | 12 | Highest train NET E among candidates with ≥30 trades | data (train WF) |
| slow_period | 26 | Paired with 12; beat 21/55 and 20/50 on train NET E | data (train WF) |
| adx_period | 14 | User spec | default (user spec) |
| adx_min | 25 | 2y 1H ADX median ≈ 24.5–24.9 | data |
| atr_period | 14 | User spec | default (user spec) |
| atr_pct_lo / atr_pct_hi | 20 / 90 | Sit out dead tape and crisis tails | default, aligned to rolling percentile |
| volume_mult | 1.5 × 20-bar avg | User spec; confirm participation | default (user spec) |
| volume_confirm_bars | 4 | Same horizon as limit TTL; “confirm” not same-bar only | default |
| risk_usdt | 15 | Fixed loss at stop | default (user spec) |
| stop_atr_mult | 1.5 | User spec; attached to entry | default (user spec) |
| tp_style | 50% at 1.5R + trail 1×ATR | Lets trends pay more than a hard 2R clip | default (chosen of the two allowed) |
| time_stop_hours | 8 | Trend time stop | default (user spec) |
| limit_ttl_hours | 4 | Cancel unfilled limits | default (user spec) |
| funding_skip_rate | 0.0003 / 8h | Skip longs that would pay > 0.03% | default (user spec) |
| leverage_cap | 5x isolated | User spec; schema max=5 | default (user spec) |
| max_concurrent | 3 (1 per symbol) | User spec | default (user spec) |
| daily_pause / playbook_stop | −30 / −40 USDT | User spec | default (user spec) |
| maker / taker | 0.0002 / 0.0006 | Bitget VIP0 futures + public contract `makerFeeRate`/`takerFeeRate` | data (docs + contracts API) |
| account fee tier | PENDING | Cannot read the bound account without ACCESS-KEY | PENDING |
| slippage | 1 tick | User spec; ticks from `pricePlace`/`priceEndStep` | default + data |
| shorts_enabled | false | No ≥30-trade positive-E short test | data (absent) |
| activation_status | inactive | Test split <30 trades; 2x-cost E negative on that sample; no sandbox run | data |

## Flow

`scan → filter → trigger → order → manage → exit → log`

1. **scan** 1H OHLCV + last known funding for each symbol.
2. **filter** regime, funding clock, funding rate, stale quote, daily/playbook
   halt, alien-position alert, concurrency.
3. **trigger** bullish EMA stack + ADX regime episode + volume confirm.
4. **order** isolated limit with exchange-side SL (and first TP price) attached.
5. **manage** fill/cancel at 4h, 50% at 1.5R, trail remainder, time stop.
6. **exit** on stop / TP / time / playbook halt. Do not touch alien inventory.
7. **log** timestamp, symbol, side, intended vs filled price, fees, funding,
   reason code.

## Assumptions and what would falsify them

| assumption | falsifier |
| --- | --- |
| Elevated ADX plus a bullish EMA stack has positive NET E after costs | Walk-forward test ≥30 trades with NET E ≤ 0 at 1x costs |
| Sitting out low ADX removes more losers than winners | Same window, low-ADX book shows higher NET E than the traded book |
| Limit + attached SL avoids post-fill gap risk | Live fills show SL attached after fill or missing |
| VIP0 2/6 bps is the right cost book until the account tier is known | Authenticated fee-tier read differs; re-run cost book |
| Funding history gaps are not silently filled with zeros | Any replay that charges invented funding |

## Validation status (authoring-time, Bitget public 1H)

Coverage actually fetched: 17,455 1H bars per symbol from 2024-10-09 00:00 UTC
to 2026-10-09 17:00 UTC. Public funding history only covers about 90 days
(2026-07-12 to 2026-10-09, 270 prints/symbol). Official managed kline probe
returned HTTP 403 from this environment. GetAgent sandbox run: PENDING (no
ACCESS-KEY in session; screenshot key was not used).

Walk-forward split, frozen before the test read: train 2024-10-09 → 2026-03-09,
test 2026-03-09 → 2026-10-09. Candidate EMAs were scored on **train only**.

Train 1x costs (chosen 12/26, ADX 25, ATR percentile 20–90):

- trades 51, win rate 0.4902, avg R / NET E 0.1846 R, PF 1.486, max DD −77.24 USDT, Sharpe 0.848
- halted on five consecutive losses (the specified halt)

Test 1x costs:

- trades 25 — **no verdict** (<30)
- observed only: win rate 0.52, NET E 0.0079 R, PF 1.020, max DD −49.99 USDT, Sharpe 0.030
- halted on five consecutive losses

Cost sensitivity on the test window (still <30 trades, so not a formal reject):

- 0x: 5 trades, NET E −0.481 R (halted on playbook stop; sample too small)
- 1x: 25 trades, NET E +0.0079 R, PF 1.020
- 2x: 25 trades, NET E −0.0439 R, PF 0.898

User rule: negative expectancy at 2x → reject. The 2x book is negative but
under 30 trades, so this is a **soft reject / do not activate**, not a
fabricated pass. Forward live gate (fixed now): PASS = PF ≥ 1.3 AND Sharpe ≥ 0.5
after ≥30 live trades; FAIL = PF ≤ 1.1 → stop.

## How to read backtest metrics

`total_return_pct` on GetAgent cards is `net_pnl / margin_budget`. Engine
account percentages use the venue starting balance. Prefer NET expectancy in R,
profit factor, trade count, and max DD in USDT over a headline ROI. A result
with fewer than 30 trades is not a verdict.

## 风险 / Risk

Whipsaw after ADX just crosses into a trend, clustered stops that trip the
five-loss halt, funding windows that skip the best hours, and 8-hour time stops
that cut trends that needed more time. Isolated 5x still loses the full 15 USDT
risk unit when the stop is hit, plus fees and slippage. Alien positions in the
sub-account are a process failure — the Playbook alerts and will not flatten
them. Past replay is not live profit.

## Versioning

v1 is frozen at activation (which has not happened). Each later version may
change **one** parameter and must write a predicted effect before that run.
