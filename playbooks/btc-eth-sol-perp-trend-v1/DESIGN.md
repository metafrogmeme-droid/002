# DESIGN — btc-eth-sol-perp-trend-v1

Design record for the Playbook. Everything numeric in the "Backtest results"
section comes from the GetAgent sandbox run listed there; nothing is estimated
by hand. Values that could not be derived are marked `PENDING` with the reason.

Local files not in the uploaded package: `DESIGN.md`, `CHANGELOG.md`.

---

## 1. Base strategy and why

**Chosen base: EMA + ADX trend pullback-resume (long-only).**
Rejected alternative: mean reversion.

Reasons:

1. The specification already mandates a trend/volatility regime filter (ADX
   plus ATR percentile), a fixed-R stop and a 2R take profit. Those exits are
   asymmetric (small stop, larger target) and fit a continuation thesis; a
   mean-reversion book wants the opposite (tight target, wide stop or none).
2. A pullback-to-EMA20 entry inside an ADX-confirmed trend gives a natural,
   data-defined stop (below the pullback, 1.5x ATR) and a limit entry *at or
   better than* the signal price that is reachable rather than chased.
3. Mean reversion on 1H perps is dominated by funding and fee drag because the
   target is usually inside one ATR; with taker exits and 0.06% fees the 2R
   target is structurally hard to hit. The trend base keeps costs below 20% of
   the modelled gross (sandbox: 50.2 USDT costs vs 201 USDT gross loss).

Timeframe: 1H bars for everything (regime, trigger, ATR). One timeframe keeps
the replay and the live decision identical and avoids 15m look-ahead issues
when stitched into the hourly schedule.

Short side: disabled in v1. See section 7 — the short-side research run did
not show positive net expectancy.

---

## 2. Parameter table

Sources: `spec` = fixed by the task specification; `Bitget` = public
`/api/v2/mix/market/contracts` response of 2026-10-09; `design` = author
choice, rationale given; `derived` = computed from other parameters.

| Name | Value | Rationale | Source |
|---|---|---|---|
| trading_symbols | BTCUSDT, ETHUSDT, SOLUSDT | Required universe; all `symbolStatus=normal` | spec / Bitget |
| margin_budget | 1500 USDT | 3 positions x up to ~500 USDT isolated margin at 5x; denominator for strategy-basis return | design |
| leverage | 5 | Cap from spec; sizing reduces qty when margin at 5x would exceed the budget share | spec |
| risk_per_trade_usdt | 15 | Fixed loss at stop; qty = 15 / stop distance | spec |
| adx_period / adx_min | 14 / 25 | ADX(14) ≥ 25 is the conventional "trend present" line; below it the regime is `range` | spec (period) / design (threshold) |
| atr_period | 14 | ATR(14) for stop and volatility percentile | spec |
| atr_pct_lookback_bars | 720 | 30 days of 1H bars: long enough to span one volatility cycle, short enough to adapt | design |
| atr_pct_min / atr_pct_max | 20 / 90 | Below p20 = `trend_lowvol` (targets rarely reached); above p90 = `trend_blowoff` (stops too wide, slippage) | design |
| ema_fast / ema_slow | 20 / 50 | EMA20 is the pullback line, EMA50 confirms direction | design |
| volume_avg_bars / volume_multiple | 20 / 1.5 | Trigger bar volume ≥ 1.5x 20-bar average | spec |
| stop_atr_multiple | 1.5 | Stop = entry − 1.5 x ATR(14), preset on the entry order | spec |
| take_profit_r | 2.0 | Fixed 2R target (chosen over trailing: deterministic, cheap to replay, maker exit) | spec (choose one) |
| entry_ttl_hours | 4 | Unfilled limit entry cancelled after 4 bars | spec |
| time_stop_hours | 8 | Position flattened if neither stop nor target hit within 8h of fill | spec |
| max_concurrent_positions | 3 (1 per symbol) | Caps margin use and correlated exposure | spec |
| daily_pause_loss_usdt / daily_stop_loss_usdt | 30 / 40 | 2R pause, then flatten and block the UTC day at ~2.7R | spec |
| max_consecutive_losses | 5 | Halt entries for 24h after 5 straight losing closes | spec |
| funding_window_minutes | 15 | No new entries within ±15 min of 00/08/16 UTC settlement | spec |
| max_funding_rate_pct | 0.03 | Skip longs when the current 8h rate > +0.03% | spec |
| funding_fallback_rate_pct | 0.01 | Charged per settlement when no funding row exists (history only covers ~90 days); counted as *estimated* | design (see §6) |
| slippage_ticks | 1 | 1 tick charged on every taker fill (stop, time stop, daily stop) | spec |
| side_mode | long_only | Shorts disabled pending positive short-side evidence | spec |
| backtest_lookback_days | 730 | ≥ 2 years of 1H bars | spec |
| walk_forward_train_months / test_months | 12 / 3 | Anchored folds; parameters frozen, nothing fitted per fold | spec (stated split) |
| schedule | cron `1 * * * *` UTC | Runs one minute after each hourly close so the last closed 1H bar is final | design |
| Entry limit price | floor(close, tick) − 1 tick | At or better than the signal price and a resting (maker) order | spec / design |
| Tick / min qty / max lever (BTC) | 0.1 / 0.0001 / 150 | Public contract config | Bitget |
| Tick / min qty / max lever (ETH) | 0.01 / 0.01 / 150 | Public contract config | Bitget |
| Tick / min qty / max lever (SOL) | 0.001 / 0.1 / 100 | Public contract config | Bitget |
| Fees (maker / taker) | 0.02% / 0.06% | Public contract config; account tier `PENDING (verify in account)` | Bitget |

---

## 3. Flow

```
scan      every hourly run (live) / every closed bar (replay), per symbol
  │       1000 closed 1H bars, latest funding rate, data freshness
  ▼
filter    regime = f(ADX14, ATR14/close percentile over 720 bars)
  │         ADX < 25                      -> range            (no trade)
  │         ADX ≥ 25, ATR pct < 20        -> trend_lowvol     (no trade)
  │         ADX ≥ 25, ATR pct > 90        -> trend_blowoff    (no trade)
  │         ADX ≥ 25, 20 ≤ ATR pct ≤ 90   -> trend_tradable
  │       plus: not inside ±15 min of 00/08/16 UTC; funding ≤ +0.03%;
  │             not halted / paused; < 3 open; no open/pending on symbol
  ▼
trigger   EMA20 > EMA50, previous bar low ≤ EMA20 (pullback touched),
  │       this bar closes above EMA20, volume ≥ 1.5 x avg20
  ▼
order     qty = 15 / (1.5 x ATR14), rounded down to size step, ≥ minTradeNum,
  │       margin = qty x price / 5 (isolated); qty reduced if margin would
  │       exceed the per-slot budget; limit BUY at floor(close) − 1 tick,
  │       stop-market at entry − 1.5 ATR and limit TP at entry + 2 x stop
  │       distance attached to the same order (bracket in replay,
  │       preset TP/SL on the entry order live); entry cancelled after 4h
  ▼
manage    funding accrued at every settlement while open; time stop at 8h
  │       after fill; daily realised PnL tracked per UTC day: ≤ −30 pause
  │       entries, ≤ −40 flatten + block day; 5 consecutive losses -> 24h halt;
  │       stale data / foreign positions handled as described in §6
  ▼
exit      stop loss (taker, 1 tick slippage) | take profit (maker) |
  │       time stop (taker) | daily stop (taker) | end of data (replay only)
  ▼
log       one record per action with the schema in §5; replay writes
          output/trade_log.json, trades.json, backtest_report.json,
          equity_curve.csv; live records go through
          runtime.emit_signal_or_follow(reason_code, reason_text)
```

---

## 4. Assumptions and falsifiers

| # | Assumption | What would falsify it | Status after sandbox run |
|---|---|---|---|
| A1 | In an ADX-confirmed uptrend with normal volatility, a volume-confirmed close back above EMA20 after a pullback is followed, within 8h, by a move of ≥ 2 x 1.5 ATR more often than it loses 1.5 ATR | Net expectancy ≤ 0 on ≥ 30 trades with costs modelled | **Falsified on 2024-10 → 2026-10**: 42 trades, −0.40R net, −0.32R gross |
| A2 | A limit 1 tick under the signal close fills within 4 bars without destroying the edge | Many expiries or fills only on bars that keep falling (adverse selection) | 42/42 filled, 0 expiries in replay; live fill rate `PENDING` |
| A3 | The 8h time stop removes dead positions cheaply | Time stops dominate the loss column | Time stop = 23/42 exits (55%), the largest exit class |
| A4 | Costs are not the reason for failure | Gross expectancy > 0 and net ≤ 0 | Gross expectancy already negative (−0.32R), so costs are not the primary cause |
| A5 | The three symbols behave alike under the filter | One symbol positive, others negative | All three negative (BTC −0.38R, ETH −0.47R, SOL −0.36R) |
| A6 | Funding never flips the sign of a trade | Funding ≥ 20% of gross | Funding 11.2 USDT of 50.2 USDT costs; 35 of 36 settlements charged at the fallback rate (see §6) |
| A7 | Shorts are not a free improvement | Short-only replay ≥ 30 trades with positive net expectancy | Short-only: 43 trades, −0.07R net, PF 0.88 (sandbox research run) → stays disabled |

---

## 5. Per-action log schema

Replay (`output/trade_log.json` → `actions[]`, `trades[]`) and live
(`.state/perp_trend_state.json` → `log[]`, also printed as
`{"action_log": …}`) share these fields; live records are produced inside
`runtime.emit_signal_or_follow(... reason_code=..., reason_text=...)` callbacks.

| Field | Meaning |
|---|---|
| `ts` / `ts_iso` | Decision time (bar close in replay, wall clock live) |
| `symbol` | e.g. `BTCUSDT` |
| `side` | `long` (`short` only in research mode) |
| `action` | `entry_submit`, `entry_fill`, `entry_expired`, `exit_fill`, `funding`, `skip`, `halt`, `alert` |
| `reason_code` | One of the `RC_*` codes in `src/features.py` (`ENTRY_SUBMIT`, `ENTRY_FILL`, `ENTRY_EXPIRED`, `EXIT_TAKE_PROFIT`, `EXIT_STOP_LOSS`, `EXIT_TIME_STOP`, `EXIT_DAILY_STOP`, `EXIT_END_OF_DATA`, `SKIP_REGIME`, `SKIP_FUNDING_WINDOW`, `SKIP_FUNDING_RATE`, `SKIP_VOLUME`, `SKIP_MAX_POSITIONS`, `SKIP_DAILY_PAUSE`, `SKIP_HALTED`, `SKIP_SIZE_BELOW_MIN`, `SKIP_STALE_DATA`, `SKIP_PENDING_ENTRY`, `HALT_CONSECUTIVE_LOSSES`, `HALT_DAILY_STOP`, `HALT_STALE_DATA`, `ALERT_FOREIGN_POSITION`, `WATCH_NO_SIGNAL`) |
| `intended_price` | Limit price sent (entry) / signal close |
| `entry_fill_price`, `exit_fill_price` | Actual fills |
| `stop_price`, `tp_price`, `stop_distance` | Preset exits |
| `qty`, `notional_usdt`, `margin_usdt`, `risk_usdt`, `size_reduced` | Sizing result |
| `fees_usdt` | Sum of commissions on the trade |
| `funding_usdt`, `funding_settlements`, `funding_estimated_settlements` | Funding charged and how many settlements used the fallback rate |
| `slippage_usdt` | 1 tick x qty per taker fill |
| `gross_pnl_usdt`, `net_pnl_usdt`, `r_multiple` | Net = gross − fees − funding − slippage |
| `exit_reason` | Reason code of the closing fill |
| `funding_rate_at_signal`, `funding_filter_applied` | Rate seen at entry; `false` when no funding row was available |
| `atr_at_signal`, `adx_at_signal`, `atr_pct_rank_at_signal`, `volume_ratio_at_signal` | Feature snapshot |
| `entry_order_id` / live order ids | Exchange / engine identifiers |

---

## 6. Deviations, degradations and operational notes

* **Funding history depth.** Both the public and the managed Bitget funding
  endpoints return ~90 days (539 rows at 4h). Over a 730-day replay the
  funding rate is therefore known for ~11.8% of bars. Policy: when no funding
  row exists, the funding-rate filter is *not applied* (`funding_filter_applied
  = false`, counted in `entries_without_funding_read`) and each settlement is
  charged at `funding_fallback_rate_pct` = 0.01%/8h (counted in
  `funding_settlements_estimated`). Live runs fail closed instead: no funding
  read → no entry. Sandbox counts: 41 of 42 entries without a funding read; 35
  of 36 settlements estimated.
* **`required_bar_fields` removed.** Declaring `funding_rate` under
  `data_requirements` made the platform's own bootstrap replay (which feeds
  plain OHLCV) fail. The strategy now takes funding from the injected feature
  frame, then a cache written by `main_backtest.py`, and otherwise degrades
  as above.
* **Entry price.** Spec says "at or better than the signal price". A limit
  exactly at the close is marketable on the next bar and fills as taker in
  the engine, so the limit is placed 1 tick below the close (maker). This is
  stated here because it changes fee and fill behaviour.
* **Time stop semantics.** The engine delivers bar closes; the time stop fires
  on the first bar close ≥ fill time + 8h, implemented as 7 completed bars
  after the fill bar.
* **Halts in replay are not sticky across runs**; live halts persist in
  `.state`.
* **Stale data.** Live, per symbol: if the last closed bar is older than
  2 intervals, or the data fetch itself took > 60 s, the symbol is skipped
  (`SKIP_STALE_DATA` in the log, `HALT_STALE_DATA` as the emitted reason code)
  and no decision is made for it that run. The spec's "stale > 60 s" is
  approximated this way because the Playbook only sees closed 1H bars
  (`closed_only=True`), not a tick stream; the SDK freshness rule applies on
  top.
* **Foreign positions** (positions on the three symbols not opened by this
  Playbook) are alert-only: logged with `ALERT_FOREIGN_POSITION`, never
  modified, and they count toward the 1-per-symbol cap.
* **One-way position mode** on the Bitget sub-account is assumed.
* **Account fee tier** `PENDING (verify in account)`; the replay uses the
  public maker 0.02% / taker 0.06%.
* **Managed kline path** could not be probed from the authoring environment
  (HTTP 403); it was verified inside the sandbox instead (probe block below).

---

## 7. Backtest results (GetAgent sandbox)

### 7.1 Final long-only run (this package)

* `draft_id` (temporary package): `91b4392b-6bf2-4d6c-9765-9dfd86f732ef`
* `strategy_id`: `71690cc4-5d8f-4f50-b793-01f01b712f88`
* `run_id`: `pbrun-5e06c2a50923` — status `completed`, 125 s active runtime
  (data phase 53.4 s, replay 3.3 s)
* Window: 2024-10-09 03:00 UTC → 2026-10-09 19:00 UTC (730.7 days eligible
  after warm-up; 54 549 bars across 3 symbols)
* Data probe (per symbol): 18 183 klines, 761.6 days coverage, not truncated
  by the time budget; funding 539 rows from 2026-07-12 (coverage 11.8%).

Strategy basis (net of fees, funding, slippage; denominator 1 500 USDT):

| Metric | Value |
|---|---|
| Trades | 42 (BTC 17, ETH 14, SOL 11) |
| Win rate | 28.6% |
| Avg / expectancy per trade | −0.403 R (−5.98 USDT) |
| Profit factor | 0.44 |
| Net PnL | −251.30 USDT (−16.75% of budget) |
| Gross PnL | −201.08 USDT |
| Costs | 50.22 USDT = fees 38.84 + funding 11.24 (mostly estimated) + slippage 0.14 |
| Max drawdown (closed trades) | 251.30 USDT (16.75% of budget) |
| Sharpe (daily PnL / budget, annualised) | −1.42 |
| Exits | time stop 23, stop loss 15, take profit 4 |
| Halts | 1 daily stop (2024-10-15, −62.5 USDT day), 2 consecutive-loss halts |
| Verdict | **NEGATIVE_NET_EXPECTANCY** (≥ 30 trades, so a verdict is allowed) |

Engine (account basis, fees only, 100 000 USDT balance): net −239.93 USDT,
−0.24%, 84 fills / 42 positions, long ratio 1.0 — consistent with the
strategy-basis numbers once funding and slippage are added.

### 7.2 Walk-forward (anchored, 12m train / 3m test, parameters frozen)

| Fold | Train window | n | WR | avg R | PF | maxDD % | Sharpe | Test window | n | WR | avg R | PF | maxDD % | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2024-10-09 → 2025-10-09 | 23 | 39.1% | −0.22 | 0.67 | 6.85 | −0.73 | 2025-10-09 → 2026-01-09 | 3 | 33.3% | −0.76 | 0.03 | 2.34 | −2.72 |
| 1 | 2024-10-09 → 2026-01-09 | 26 | 38.5% | −0.28 | 0.59 | 7.28 | −0.92 | 2026-01-09 → 2026-04-09 | 7 | 0.0% | −0.89 | 0.00 | 6.13 | −4.40 |
| 2 | 2024-10-09 → 2026-04-09 | 33 | 30.3% | −0.41 | 0.44 | 13.41 | −1.44 | 2026-04-09 → 2026-07-09 | 8 | 25.0% | −0.23 | 0.61 | 2.89 | −1.18 |
| 3 | 2024-10-09 → 2026-07-09 | 41 | 29.3% | −0.38 | 0.47 | 15.66 | −1.41 | 2026-07-09 → 2026-10-09 | 1 | 0.0% | −1.49 | 0.00 | 1.49 | −1.98 |

Out-of-sample aggregate (2025-10-09 → 2026-10-09): 19 trades, WR 15.8%,
−0.62 R, PF 0.20, net −176.18 USDT, maxDD 11.8% of budget, Sharpe −2.47.
Every individual fold has < 30 trades → **no per-fold verdict**; the OOS
aggregate is also below 30 trades. Nothing was re-fitted per fold.

### 7.3 Cost sensitivity (same 42 trades)

| Cost multiplier | Expectancy R | PF | Net PnL | maxDD % | Sharpe |
|---|---|---|---|---|---|
| 0x | −0.323 | 0.51 | −201.08 | 13.41 | −1.17 |
| 1x | −0.403 | 0.44 | −251.30 | 16.75 | −1.42 |
| 2x | −0.484 | 0.38 | −301.51 | 20.10 | −1.65 |

Decision: **REJECTED_NEGATIVE_EXPECTANCY_AT_2X_COSTS** (and already negative
at 0x, i.e. the signal itself has no edge in this window). No parameter was
tuned after seeing these numbers; v1 is frozen as uploaded.

### 7.4 Short-side research run

Same package with `side_mode: short_only` (draft `1849f49f-d6cf-4942-9e32-
fef57a303259`, run `pbrun-e8dcee8a8c8f`). The run's final status is
`failed` because the platform's bootstrap replay rejected the then-declared
`required_bar_fields` (fixed afterwards); the strategy-basis metrics emitted
by `main_backtest.py` before that step were recorded by the platform:
43 trades, WR 34.9%, expectancy −0.074 R, PF 0.88, net −46.33 USDT,
maxDD 11.1% of budget, Sharpe −0.22, OOS 20 trades at −0.31 R,
REJECTED at 2x costs. Shorts therefore remain disabled.

### 7.5 Forward (live) criteria — fixed in advance

PASS = PF ≥ 1.3 AND Sharpe ≥ 0.5 after ≥ 30 live trades; FAIL = PF ≤ 1.1
→ stop the Playbook. Given 7.1–7.3 the Playbook does **not** qualify for a
live trial as v1.

---

## 8. Status

* Local validation: `scripts/validate.py` → PASSED.
* Upload: temporary package only. Not confirmed as draft, not published, no
  subscription, nothing started or stopped.
* Verdict: v1 is a documented negative result. Candidate single-parameter
  follow-ups and their predictions are in `CHANGELOG.md`; none has been run.
