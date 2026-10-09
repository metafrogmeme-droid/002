# Playbook `crypto-perp-regime-long` v1 — design, validation, verdict

SLEEVE: **A (crypto perps)**: BTCUSDT, ETHUSDT, SOLUSDT (USDT-M).
Status: **REJECT under the stated rules. Shipped DISARMED (`live_armed=false`). Not published, not subscribed.**

Data-source labels used throughout:

- `[LIVE]`: Bitget public REST pulled 2026-10-09 18:29Z (`research/out/live_spec.json`).
- `[HIST]`: Bitget 1H klines, snapshot in `research/data/` (2024-04 to 2026-10).
- `[OFFLINE]`: `research/engine.py`, the conservative simulator (see assumptions).
- `[PLATFORM]`: GetAgent managed sandbox replay (Nautilus), run `pbrun-cb15fa38df4b`.
- `PENDING`: not derivable from live contract data or a backtest.

## 0. Contract specification (per symbol) `[LIVE]`

| Item | BTCUSDT | ETHUSDT | SOLUSDT |
|---|---|---|---|
| Status | normal | normal | normal |
| Max leverage (contract) | 150x | 150x | 100x |
| Leverage used (rule cap) | 5x | 5x | 5x |
| Margin mode | isolated (forced in order call) | same | same |
| Funding interval | 8h (next 2026-10-10 00:00Z) | 8h | 8h |
| Funding rate at pull | 0.0068% | see spec file | see spec file |
| Hours / closures | 24/7, `offTime=-1`, `limitOpenTime=-1` | same | same |
| Price tick | 0.1 | 0.01 | 0.001 |
| Min size | 0.0001 BTC | 0.01 ETH | 0.1 SOL |
| Min notional | 5 USDT | 5 USDT | 5 USDT |
| Maker / taker fee (contract default) | 0.02% / 0.06% | same | same |
| 24h volume (USDT) | 2.26B | 1.52B | 285M |
| Top-of-book spread (bps) | 0.012 | 0.04 | 0.091 |

Fee tier of the bound sub-account: **PENDING** (needs the authenticated fee-rate endpoint). The contract default rates above are used, with a cost-sensitivity sweep.

Funding interval is read from the contract (8h). It is re-checked at runtime against `mark_price` and the order is skipped if the schedule differs.

## 1. Global rules, as implemented (`src/rules.py`, `src/main_live.py`)

Long-only. No short module exists. Shorts would need a separate test of at least 30 trades with positive net expectancy, which has not been done.

| Rule | Implementation | Reason code |
|---|---|---|
| Invalid or no signal means no trade | `valid` flag False (warm-up or NaN) gives no order | `no_signal` |
| Liquidity gate | spread > 5 bps or 24h volume < 10M USDT gives skip | `spread_gate`, `volume_gate` |
| Risk per trade | 15 USDT at stop | |
| Size | `qty = 15 / stop_distance`, rounded down to lot step | `below_min_size` |
| Margin | isolated, leverage 5x, margin cap 500 USDT | `margin_cap` |
| Stop | 1.5 x ATR(14), attached to the entry order | |
| Take profit | fixed 2R, attached to the entry order | |
| Entry | limit at signal close, cancelled after 4h | `entry_expired` |
| Concurrency | at most 3 total, 1 per symbol, 1 per correlation cluster (BTC/ETH/SOL are one cluster, so effectively 1 open position) | `cluster_gate` |
| Daily pause | at -30 USDT realised, entries pause until 00:00Z | `daily_pause` |
| Playbook stop | at -40 USDT cumulative realised | `playbook_stop` |
| Halts (alert, no new entries) | 5 consecutive losses; data stale > 60s; foreign position | `halt_*` |
| Foreign position | detected, alert raised, **never touched** | `halt_foreign_position` |
| Funding | no entries within +/-15 min of 00/08/16 UTC; skip if expected funding over hold > 0.1R | `funding_window`, `funding_cap` |
| Costs | all offline results net of fee, 1-tick adverse slippage, funding | |

## 2. Sleeve A module

Regime inputs: ADX(14) on 1H, and ATR% percentile rank over 720 bars. Three entry modules exist in the code.

- **T** (trend pullback): off in v1.
- **M** (mean reversion, 2h time stop): off in v1.
- **B** (Donchian-48 breakout continuation): **on in v1**. Conditions: first break of the 48-bar high, ADX >= 30, ATR% rank >= 0.5, close > EMA200, +DI > -DI. Time stop 8h.

Why B only: in walk-forward round 1, T and M had negative train expectancy in every fold (flat, no trades). B was the only family with positive in-sample expectancy in round 2.

## 3. Parameter table

| Name | Value | Rationale | Source |
|---|---|---|---|
| symbols | BTC, ETH, SOL USDT-M | sleeve A definition | default |
| leverage | 5 | sleeve cap | default (rule) |
| risk_usdt | 15 | rule | default (rule) |
| stop_atr_mult | 1.5 | rule | default (rule) |
| atr_period | 14 | rule (Wilder) | default (rule) |
| tp_r_mult | 2.0 | rule option 1 | default (rule) |
| adx_period / adx_trend_min | 14 / 30 | trend regime | data (best of 32 in-sample, see section 6) |
| atr_pct_window / break_rank_min | 720 / 0.5 | volatility regime | default (not tuned) |
| break_lookback | 48 | 2-day Donchian | default (not tuned) |
| ema_slow | 200 | trend filter | default |
| time_stop_hours_trend | 8 | rule | default (rule) |
| entry_cancel_hours | 4 | rule | default (rule) |
| funding_blackout_min | 15 | rule | default (rule) |
| funding_cap_r | 0.1 | rule | default (rule) |
| funding_rate_assumed | 0.0001 per 8h | conservative vs. live 0.0068% | live spec / default |
| min_volume_24h_usdt | 10,000,000 | the template's `[X]` was blank | **PENDING** (user to confirm) |
| max_spread_bps | 5 | rule (sleeve A) | default (rule) |
| daily_pause_usdt / stop_playbook_usdt | 30 / 40 | rule | default (rule) |
| max_consecutive_losses | 5 | rule | default (rule) |
| stale_seconds | 60 | rule | default (rule) |
| margin_budget | 500 USDT | caps notional at 2500 (5x) | default; P99 modelled margin 454 |
| maker/taker fee | 0.02% / 0.06% | contract default | live spec; account tier **PENDING** |
| cron | `*/15 * * * *` UTC | platform minimum is 15 min | platform constraint |
| live_armed | false | safety interlock | default |

## 4. Flow

1. **Scan**: every 15 min, read positions, pending orders, equity. Rebuild state from `.state/regime_long_state.json`. Reconcile pending and open orders. Apply time-stop and entry-expiry closes.
2. **Filter**: risk gates (daily pause, playbook stop, halts, stale data, foreign position). Then per symbol: last closed 1H bar, signal validity, spread and volume gate, funding schedule and window.
3. **Trigger**: B conditions on the closed bar. No intrabar signals.
4. **Order**: `build_plan` computes limit price, stop, TP, quantity, margin and funding cost. If every gate passes, `emit_signal_or_follow` places an isolated limit order with attached TP/SL. The `live_armed` interlock currently blocks this step.
5. **Manage**: pending cancelled at 4h or when the next bar enters a funding blackout. Time stop at 8h holding.
6. **Exit**: stop, TP, or time stop (`close_all_positions`).
7. **Log**: one row per action (schema below).

### Per-action log schema

`ts_utc, symbol, side, action, intended_price, filled_price, qty, fee_usdt, funding_usdt, realised_pnl_usdt, reason_code, gate_values`

`filled_price`, `fee_usdt` and `funding_usdt` depend on the live response shape and are **PENDING**: the live path has never been run against real fills.

## 5. Validation

Setup: 1H bars `[HIST]`, from 2024-04-10 (data start, 2024-04 to 2026-10, about 2.5y). Anchored walk-forward with a 1-year first train window and 3-month test folds. 8 boundaries incl. the data start, giving 6 test folds. Selection rule: highest train net expectancy (R) with >= 30 train trades and above a threshold (0 in round 1, +0.05R in round 2). If none, stay flat. Parameter grid: 7 configs in round 1, 32 in round 2.

`[OFFLINE]` engine assumptions: strict trade-through limit fills (low < limit), +1 tick adverse slippage on every fill, taker exit fees, stop wins ties, TP only after the fill bar, modelled funding 0.01% per 8h, cost multiplier m scales fee, slippage and funding.

### Walk-forward results

| Round | Outcome |
|---|---|
| R1 (T, M families, 7 configs) | All folds flat. Every config had negative train net expectancy. 0 OOS trades. **No verdict.** |
| R2 (adds B, HTF filter, 32 configs) | Stitched OOS: **27 trades** (< 30, so **no verdict**). Net expectancy -0.208R at 1x (95% CI [-0.53, +0.14]), PF 0.54, win rate 29.6%, net -82.6 USDT, max DD 158 USDT, daily Sharpe -0.78. At 0x cost: -0.147R. The -40 USDT kill switch trips from every start date tested (18 of 18). Max 8 consecutive losses. |
| R2 null test (300 random-entry sims) | OOS observed -0.208R vs null mean -0.051R. 17.7% of null runs fall below observed. Not distinguishable from random. |
| Frequency | About 1.5 OOS trades per month, so about 600 days to reach 30 live trades. |

### Candidate v1 (B@30): in-sample only, post hoc

v1 is the best of 32 configs on the full in-sample period. It is **selection-biased and is not an OOS result**.

| Cost multiplier | Trades | Net exp (R) | PF | Net PnL (USDT) | Max DD (USDT) | Daily Sharpe |
|---|---|---|---|---|---|---|
| 0x | 130 | +0.098 | 1.23 | +189.7 | 115 | 0.60 |
| **1x** | 130 | **+0.032** | **1.07** | +62.9 | 160 | 0.20 |
| 2x | 130 | **-0.033** | 0.93 | -63.9 | 213 | -0.21 |

- 1x 95% CI on net expectancy is [-0.16, +0.22]. It includes zero.
- Gross edge is about 0.10R per trade. Costs consume about 0.065R (fees 0.060R + funding 0.005R). The edge is thinner than plausible cost error.
- Exits at 1x: stop 45 (-1.06R), time stop 58 (0.00R), TP 27 (+1.93R).
- By symbol at 1x: BTC -0.038R (57 trades), ETH +0.073R (38), SOL +0.103R (35).
- Time stability: first half +0.031R, second half +0.034R. Quarterly expectancy ranges from -0.32R (2026Q1) to +0.30R (2026Q2), at most 26 trades per quarter.
- Random-entry null (400 sims): mean -0.083R. v1 at 1x is above 94.5% of null runs, but this is in-sample best-of-32 so it overstates the edge.

**Verdict: REJECT.**

- Your rule says negative at 2x cost means reject. v1 is negative at 2x.
- PF 1.07 at 1x is at or below the fixed FAIL threshold (PF <= 1.1).
- The only genuinely out-of-sample test (R2) is negative on too few trades to give a verdict.

### Platform backtest vs conservative engine

`[PLATFORM]` run `pbrun-cb15fa38df4b`: 99 positions, 198 fills, net +125.6 USDT, PF 1.42, daily Sharpe 0.40, window 2024-11-09 to 2026-09-22. The platform shows about +25% on the 500 USDT margin budget.

The same window through the offline engine (`research/out/platform_window_crosscheck.json`):

| Engine variant | Trades | Net PnL | PF | Net exp (R) |
|---|---|---|---|---|
| Nautilus-like (bar-path optimism, no slippage, no funding) | 93 | +132.9 | 1.21 | +0.096 |
| Conservative 1x incl. funding | 92 | +67.0 | 1.10 | +0.049 (CI [-0.19, +0.29]) |
| Conservative 2x | 92 | -21.5 | 0.97 | -0.016 |
| Frictionless | 92 | +155.6 | 1.26 | +0.114 |

The platform's displayed number is the "displayed ROI" you asked me not to optimise for. It comes from OHLC bar-path replay (TP-first ordering, TP in the fill bar, maker TP fills, no slippage) with no funding modelled. Even on the platform window the 2x-cost result is negative. The platform's own PF of 1.42 is not reproduced by any variant I could build, so it is **unreconciled**.

## 6. Assumptions and what falsifies each

| Assumption | Falsified by |
|---|---|
| A1. Breakout continuation with ADX >= 30 has a small positive gross edge (about 0.1R) on BTC/ETH/SOL 1H | Live gross expectancy <= 0 after 30 trades; or the null test showing random entries match it |
| A2. Costs about 0.065R per trade (fee 0.06R, funding 0.005R) | Realised fee + funding + slippage per trade > 0.10R. This would erase the edge entirely |
| A3. Limit entries at signal close fill and are not adversely selected | Fill rate < 50%, or filled trades have materially worse expectancy than unfilled signals (not measured offline) |
| A4. 1-tick slippage is representative | Realised slippage > 1 tick on stop exits |
| A5. Contract default fees (0.02%/0.06%) apply to the sub-account | Authenticated fee-rate endpoint shows a different tier (**PENDING**) |
| A6. Funding is about 0.01% per 8h and symmetric over the hold | Funding > 0.03% per 8h for sustained periods (long-biased cost) |
| A7. Past regime (2024-2026) resembles future | Rolling 3-month expectancy < -0.1R for two consecutive quarters (2026Q1 was already -0.32R) |
| A8. 5x leverage with 500 USDT margin never binds | A `margin_cap` skip appears in the log |
| A9. BTC/ETH/SOL as one cluster (1 open or pending position at a time) | Offline engine uses the same one-position rule. Spread gate is not modelled offline (no historical L1 data); live may skip more trades. A materially lower live fill/trade count falsifies the frequency estimate |

## 7. Forward criteria (fixed now)

- **PASS**: PF >= 1.3 AND Sharpe >= 0.5 after >= 30 live trades.
- **FAIL**: PF <= 1.1 (after >= 30 live trades) means stop.
- Between: continue, no verdict.
- At the observed frequency this takes about 600 days. Offline v1 PF is 1.07 at 1x, so the prior is that it FAILs.
- Hard stops independent of the above: -40 USDT cumulative realised, 5 consecutive losses.

## 8. Versioning

v1 is frozen at activation. Each later version changes ONE parameter, with a written prediction first. Predictions below are written now and **not yet tested**:

| Version | Single change | Prediction (falsifiable) |
|---|---|---|
| v2 | `adx_trend_min` 30 to 35 | Trades fall by about 40%. Net expectancy rises only if the gross edge is concentrated in the strongest trends; I expect no significant change (CI overlaps v1). |
| v3 | `tp_r_mult` 2.0 to 1.5 | Win rate rises, avg win falls. Net expectancy unchanged within CI, because 27 of 130 trades reach TP. |
| v4 | Drop BTC from symbols | BTC was -0.038R in-sample. Prediction: pooled net expectancy rises by about +0.02R, below detectability at about 100 trades. |

## 9. PENDING list

1. Account fee tier from the authenticated fee endpoint.
2. `trade.market.check_symbol_support` for the bound sub-account (not run).
3. The `[X]` 24h volume threshold: 10M USDT is my placeholder.
4. Live response shapes for fills, equity, order id. The live path (`main_live.py`) is **not exercised against a real account**.
5. Live funding interval via the SDK at runtime (currently read from the public contract).
6. OOS evidence: none with >= 30 trades exists.
7. Data provenance beyond Bitget klines (no mark-price or index history, funding history not used; constant 0.01% modelled).
8. Fill-rate of limit entries (A3).
9. Unreconciled gap: platform PF 1.42 vs best offline reproduction 1.21.

## 10. Reproduce

```
cd research
python3 -m pytest -q tests          # 9 tests, rules + engine + incremental stream equality
python3 run_wfa.py r1 ; python3 run_wfa.py r2
python3 diag_v1.py ; python3 reconcile.py
```
