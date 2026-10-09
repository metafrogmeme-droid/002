# Bitget USDT-M Trend v1 (long-only, ADX-gated)

Status: authored and locally validated only. No backtest and no live run has
been performed. Every performance field is PENDING (see "PENDING items" below and
`docs/validation-protocol.md`). Nothing in this document is evidence of edge.

## 策略 / Strategy

A deterministic, long-only trend-following Playbook for Bitget USDT-M
perpetuals on three symbols: BTCUSDT, ETHUSDT, SOLUSDT. It is meant to run in
an isolated sub-account with isolated margin. The aim is a positive net
expectancy after fees, slippage and funding, which is a hypothesis to be
tested, not a claim.

Why trend following and not mean reversion: the regime filter admits a market
only when the 1H ADX(14) is at least 25, i.e. when the market is already
trending. A mean-reversion entry fades moves, which is the opposite of the
condition the filter selects for. A fixed-R take-profit and a time stop also
fit a breakout-into-trend trade. If the filter does not actually select
trending conditions, that is a falsifier (see "Assumptions and falsifiers").

Why long-only: the short side is disabled by a config flag
(`allow_short: false`). It is not just default-off; the code refuses to start
with `allow_short: true` in v1. It may only be enabled in a later version
after a separate short-side test shows at least 30 short trades with positive
net expectancy.

Why no AI/LLM layer: an LLM layer would force `runtime_profile: llm_bounded`
and `backtest_support: none`, so the strategy could not be backtested, and a
no-signal or malformed LLM answer is a new failure mode. This package is
deterministic (`runtime_profile: deterministic`, `backtest_support: full`). If
an LLM layer is added in a future version, an invalid or missing answer must
mean NO TRADE and never a default direction.

Contract details (tick, lot step, minimum quantity, minimum notional) come from
the Bitget public config endpoint, retrieved 2026-10-09:
`GET https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES&symbol=<SYMBOL>`

| Symbol | Price tick | Qty step | Min qty | Min notional | Default maker / taker |
|---|---|---|---|---|---|
| BTCUSDT | 0.1 | 0.0001 | 0.0001 | 5 USDT | 0.02% / 0.06% |
| ETHUSDT | 0.01 | 0.01 | 0.01 | 5 USDT | 0.02% / 0.06% |
| SOLUSDT | 0.001 | 0.1 | 0.1 | 5 USDT | 0.02% / 0.06% |

The fee rates are the public default tier. The user's own tier is PENDING.

### Regimes traded vs sat out

Traded (all three must hold on the last closed 1H bar):

- ADX(14) >= 25 (trend strength present).
- ATR(14)/close percentile rank within [20, 90] over the previous 2160 bars
  (90 days). Below 20: volatility too compressed, the 1.5 ATR stop would sit
  inside the noise relative to costs and the position would be capped by the
  leverage limit. Above 90: volatility spike, stops fill badly.
- Not inside +-15 minutes of a funding settlement (00:00, 08:00, 16:00 UTC).
- Latest settled funding rate not above +0.03% per 8h (adverse to a long).

Sat out: ranging or low-ADX markets, compressed or extreme volatility, funding
windows, adverse funding, warm-up (fewer than 500 history bars for the
percentile), stale data. The thresholds are defaults, not values derived from
data ("Parameters", source column). Calibrating them is PENDING and has to happen
as new versions with written predictions (`docs/VERSIONING.md`).

## 开仓 / Entry

Evaluated on each closed 1H bar, per symbol. A long entry needs ALL of:

1. Structure: EMA(20) > EMA(50), close > EMA(20), and +DI(14) > -DI(14).
2. Trigger: the structure just became true on this bar (it was false on the
   previous bar). A trend that is already running does not re-trigger.
3. Regime: ADX(14) >= 25 and ATR% rank within [20, 90].
4. Volume confirmation: bar volume >= 1.5 x the average of the previous 20 bars.
5. Funding checks as above.
6. Risk gates pass (see 风险 / Risk) and a slot is free: at most 3 open
   positions or orders in total and 1 per symbol.
7. Sizing passes: quantity = 15 USDT / stop distance, rounded DOWN to the lot
   step. The trade is skipped if the result is below the minimum quantity or
   minimum notional, or if notional / equity would exceed 5x, or margin for
   all open orders would not fit.

The order is a limit buy at the signal bar close (rounded down to the tick),
placed by the live run at most 15 minutes after the bar closes (older signals
are skipped), and cancelled if unfilled after 4 hours or if a funding window
is about to start. The exchange-side stop-loss and take-profit are preset on
the entry order itself, so there is no unprotected gap after the fill.
Scheduled runs happen every 15 minutes (UTC).

## 平仓 / Exit

- Stop-loss: 1.5 x ATR(14) below the entry, preset on the entry order
  (exchange-side).
- Take-profit: fixed 2R (2 x stop distance above entry), preset on the entry
  order. Chosen over "50% at 1.5R plus trailing" because it is the simpler
  rule and the exchange supports it as a preset, so there is no partial-fill
  or trailing-order state to manage and the R-multiple of every trade is exact.
- Time stop: a position still open 8 hours after entry is closed at market by
  the Playbook, and its exchange-side orders are cancelled.
- A halt (see 风险 / Risk) never closes anything. It only stops new entries.

## 风险 / Risk

- Fixed risk at the stop: 15 USDT per trade (before fees and slippage; the
  realised loss on a stop is somewhat larger).
- Isolated margin, leverage cap 5x (hard-coded: the code refuses a larger
  value).
- Max 3 concurrent positions, 1 per symbol.
- Pause new entries when the realised PnL of the UTC day is at or below -30
  USDT.
- Latch a halt of new entries at -40 USDT daily realised.
- Halt after 5 consecutive losses.
- Halt when market data is stale by more than 60 seconds.
- Halt (alert only, do not touch) when the sub-account holds any position this
  Playbook did not open. Position ownership comes from the Playbook's own
  ledger. If the ledger is unavailable, the check fails closed (halt).
- Fail closed everywhere: if realised-PnL data cannot be read, or data fetch
  fails, no new entries are made.
- Halting means "stop emitting new entries and alert". The Playbook never
  flattens positions (other than its own 8h time stop) and never disables or
  stops its own subscription. Resuming after a halt is manual: raise
  `halt_reset_after_ts_ms` (a user setting) to a timestamp later than the halt.
- Main market risks: trend entries are repeatedly stopped out in choppy
  markets that briefly pass the ADX gate; gaps and fast moves can fill the
  stop worse than planned; fees and funding can exceed the expected edge when
  stops are tight.

## Flow (b) (scan -> filter -> trigger -> order -> manage -> exit -> log)

Each scheduled live run (every 15 min):

1. Reconcile: read positions, open orders and recent fills. Update the ledger
   (`.state/ledger.json`) with fills, exits and realised PnL.
2. Manage: cancel entries unfilled for 4h or approaching a funding window;
   time-stop positions older than 8h.
3. Gate: foreign position, state or PnL unavailable, latched halt, 5 losses,
   daily pause or stop. If any gate trips, log an alert and skip step 4-6.
4. Scan: for each symbol in order BTC, ETH, SOL: fetch closed 1H bars, update
   indicators, check data freshness.
5. Filter and trigger: regime, structure transition, volume, funding.
6. Order: size, verify exchange rules, place the limit entry with preset
   SL/TP in isolated margin, verify the SL is attached, cancel the order and
   alert if the verification fails.
7. Log: every decision and action is a structured record ("Per-action log schema") printed
   as a JSON line and written to `output/playbook_actions.json`. A final watch
   summary is always emitted, even after an error.

The backtest runs the same logic inside a Nautilus strategy
(`src/strategy.py`) using a bracket order: limit entry with 4h expiry, TP,
SL, and the time stop.

## Parameters (a)

Source column: `data` = derived from exchange data, `default` = conventional or
author default not tuned on any data, `PENDING` = needs verification or
calibration by the user/sandbox. No value is tuned on backtest results.

| Name | Value | Rationale | Source |
|---|---|---|---|
| symbols | BTCUSDT, ETHUSDT, SOLUSDT | Spec universe; exchange-native names | data (contract endpoint) |
| tick / qty step / min qty / min notional | per table above | Rounding and skip rules | data (Bitget public contracts, 2026-10-09) |
| timeframe | 1h | Spec | default |
| ema_fast / ema_slow | 20 / 50 | Common trend structure pair | default (calibration PENDING) |
| adx_period / adx_min | 14 / 25 | Wilder default; 25 is the usual "trending" cut | default (calibration PENDING) |
| atr_period | 14 | Wilder default; spec | default |
| atr_pct_lookback_bars | 2160 | 90 days of 1H bars for the percentile | default (calibration PENDING) |
| atr_pct_min_history_bars | 500 | Minimum sample before a percentile is trusted | default |
| atr_pct_rank_low / high | 20 / 90 | Sit out compressed and spiking volatility | default (calibration PENDING) |
| volume_lookback_bars / volume_mult | 20 / 1.5 | Spec | default |
| entry_offset_atr | 0 | Limit at signal close; no tuning in v1 | default |
| stop_atr_mult | 1.5 | Spec | default |
| tp_r_mult | 2.0 | Spec (fixed 2R) | default |
| risk_usdt | 15 | Spec | default |
| leverage_cap | 5 | Spec, hard-capped in code | default |
| margin_mode | isolated | Spec | default |
| margin_budget (user setting) | 1000 USDT | Equity basis for the leverage check and Sharpe; the sub-account's real equity is not read | PENDING (user sets) |
| entry_expiry_hours | 4 | Spec | default |
| time_stop_hours | 8 | Spec | default |
| funding_window_minutes / hours | 15 / 00, 08, 16 UTC | Spec | default |
| funding_adverse_max | 0.03% per 8h | Spec | default |
| max_concurrent / max_per_symbol | 3 / 1 | Spec | default |
| daily_pause_usdt / hard_stop_usdt | 30 / 40 | Spec | default |
| max_consecutive_losses | 5 | Spec | default |
| stale_data_seconds | 60 | Spec | default |
| entry_max_signal_age_minutes | 15 | A limit placed long after the signal bar is a different trade | default |
| allow_short | false | Spec; refused if true | default |
| short_enable_min_trades | 30 | Spec gating rule for a later version | default |
| maker_fee / taker_fee | 0.02% / 0.06% | Public default tier | PENDING (user tier) |
| slippage_ticks | 1 per fill | Spec | default |
| cost_multiplier | 1.0 | Used for the 0x/1x/2x runs; excluded from the hash | default |
| walk-forward | 12m train / 3m test / 3m step | Spec example; v1 has no fitted parameters | default |
| halt_reset_after_ts_ms (user setting) | 0 | Manual resume after a halt | default |

The hash of the frozen trading parameters is in `docs/VERSIONING.md`.

## Per-action log schema (d)

Every decision and action produces one record with these fields:

| Field | Meaning |
|---|---|
| timestamp | ISO-8601 UTC time of the record |
| ts_ms | Same, in milliseconds |
| symbol | Exchange-native symbol, or `*` for account-level events |
| side | `long` (v1 is long-only) |
| action | e.g. `no_trade`, `place_entry`, `entry_fill`, `cancel_entry`, `close`, `time_stop_close`, `exit`, `alert`, `signal_only` |
| reason_code | One value of the `ReasonCode` enum |
| intended_price | The price the plan intended (entry limit, stop, etc.) |
| filled_price | Actual fill price when known, else null |
| qty | Quantity |
| fee_usdt | Fee paid, when known, else null |
| funding_usdt | Funding charged, when known (null if the fill payload does not expose it, with `funding_source: unavailable` in detail) |
| pnl_usdt | Realised PnL, when known |
| detail | Free-form object with context (stop, TP, expiry, rates, ...) |

`ReasonCode` (defined in `src/logic.py`): SIGNAL_LONG_ENTRY, ORDER_PLACED,
ORDER_FILLED, ORDER_REJECTED, ORDER_EXPIRED_UNFILLED,
ORDER_CANCELLED_FUNDING_WINDOW, EXIT_STOP_LOSS, EXIT_TAKE_PROFIT,
EXIT_TIME_STOP, EXIT_UNKNOWN, EXIT_FORCED_END_OF_TEST, NO_SIGNAL,
REGIME_WARMUP, REGIME_ADX_LOW, REGIME_ATR_PCT_LOW, REGIME_ATR_PCT_HIGH,
NO_TRADE_FUNDING_WINDOW, SKIP_FUNDING_RATE_ADVERSE, SKIP_FUNDING_UNAVAILABLE,
SKIP_VOLUME_NOT_CONFIRMED, SKIP_MAX_CONCURRENT, SKIP_SYMBOL_OCCUPIED,
SKIP_BELOW_MIN_QTY, SKIP_INVALID_STOP, SKIP_LEVERAGE_CAP,
SKIP_MARGIN_INSUFFICIENT, SKIP_SIGNAL_STALE, SKIP_ALREADY_EVALUATED,
SKIP_CONFIG_MISMATCH, SKIP_SL_NOT_ATTACHED, PAUSE_DAILY_LOSS,
HALT_DAILY_LOSS_STOP, HALT_CONSEC_LOSSES, HALT_STALE_DATA,
HALT_FOREIGN_POSITION, HALT_PNL_UNAVAILABLE, HALT_STATE_UNAVAILABLE,
HALT_MARGIN_MODE_MISMATCH, HALT_DATA_ERROR, RESUME_SIMULATED_MANUAL_RESET.

In backtests the same records are written to `output/playbook_actions.json`
(capped at 25000), the closed-trade ledger to `output/playbook_trades.json`.

## Assumptions and falsifiers (c)

| Assumption | Falsified if |
|---|---|
| A 1H EMA/DI structure transition under ADX >= 25 leads to continuation larger than costs | Net expectancy (R) at 1x costs is <= 0 on the pooled out-of-sample trades with >= 30 trades |
| The ADX/ATR% regime filter improves trade quality | Trades rejected by the filter (not run in v1; needs an unfiltered variant) would have done as well; or ADX-passing trades show no better expectancy than the same trigger without the filter |
| The edge survives realistic costs | Net expectancy (R) <= 0 at 2x costs -> reject v1 |
| Volume >= 1.5x confirms real participation | Entries below the threshold perform the same (needs a variant) |
| Fixed 2R is a reachable target within the 8h time stop | A large share of trades end by time stop with a negative result and few reach TP |
| The edge is not one regime or one symbol | Walk-forward test windows disagree in sign, or one symbol carries all profit |
| Long-only is the right bias | A separate short-side test shows >= 30 trades with positive net expectancy (short side then needs its own version) |
| Limit entry at the signal close fills often enough, and fills are not adversely selected | Fill rate low (many `ORDER_EXPIRED_UNFILLED`), or filled trades are worse than unfilled ones would have been |
| The exchange-side SL/TP attach with the entry | `sl_attached` post-check fails in live logs |
| Funding and fees are as modelled | Live fees/funding per trade differ materially from the backtest ledger |
| Bar timestamps are bar OPEN times | Probe in `docs/validation-protocol.md` shows close times |
| Daily and consecutive-loss gates can be computed from fills | Fills expose no realised-PnL field; the Playbook halts fail-closed instead (`HALT_PNL_UNAVAILABLE`) |

## Deviations / platform limitations (e)

Items that differ from the request or could not be verified without the
sandbox and a key.

1. No results. The SDK only exists in the sandbox, so no backtest could be run
   during authoring. Everything is PENDING. Only pure logic and a synthetic
   Nautilus smoke run were tested locally (not performance evidence).
2. No per-run parameters. The run API accepts only a version id, so 0x/1x/2x
   cost runs and window splits are separate package uploads, generated by
   `playbooks/tools/make_validation_variants.py`.
3. Sandbox time limit. A 24-month three-symbol run may exceed it. The tooling
   has a chunked fallback; unverified.
4. Funding in backtests is modelled analytically from historical settlement
   rates, charged at settlement bars. It is not assumed that the Nautilus
   engine charges funding. The run fails if the funding data is unavailable
   (`require_funding_data`). Which symbol form and interval the funding
   endpoint wants is unverified (both are probed).
5. Slippage is analytic: 1 tick on both the entry fill and the exit fill. A
   maker entry is assumed to fill at its limit price plus the slippage tick.
6. Fees are the public default tier, not the user's. Tier is PENDING.
7. "Stop the Playbook at -40 USDT" is implemented as a latched halt of new
   entries (alert), because a Playbook must not stop or disable itself via
   the API. The -40 is read as a daily realised loss. Only the user can stop
   the subscription, from the GetAgent page. In backtests the latched halt
   auto-resumes after 72 hours to simulate a manual reset, otherwise one halt
   would end the whole test; live halts do not auto-resume.
8. Short side: the config flag exists but v1 refuses `true`. The required
   short-side test is not possible with this version.
9. The 5-loss and daily-loss gates read realised PnL from the last 100 fills.
   The fill payload field names for profit and fee are not verified; if they
   are missing the Playbook halts fail-closed. Per-trade funding may be absent
   from live fill data (recorded as unavailable).
10. Equity basis is the `margin_budget` user setting (default 1000 USDT), not
    the real sub-account equity, for the 5x leverage check and the Sharpe
    denominator. Set it to the sub-account's allocated amount.
11. The ledger lives in `.state/ledger.json`. Whether that path persists across
    scheduled runs is unverified; if it does not, the foreign-position check
    fails closed and the Playbook never enters.
12. Cancelling an unfilled entry is logged as action `close` (and
    `cancel_entry`) with reason codes. The platform's action semantics for a
    cancel are not verified.
13. Entry orders are limit orders at the signal close. The SDK has no
    post-only flag, so a live entry can fill as taker (higher fee than
    modelled). The backtest assumes the maker rate.
14. Max drawdown and the equity curve are realised-only (closed trades, no
    mark-to-market inside a trade), so they understate intra-trade drawdown.
    Sharpe is computed from daily realised PnL over `margin_budget`.
15. When more than one symbol triggers on the same bar and slots are limited,
    priority is symbol order (BTC, ETH, SOL), which is arbitrary.
16. Hedge vs one-way position mode and the `trade_side` handling are not
    verified; check the sub-account mode before activation.
17. The venue name `BITGET` in `backtest.yaml` and the kline timestamp
    convention (assumed open time) are unverified platform assumptions.
18. `manifest.yaml` contains `version: "1.0.0"` only because this validator
    requires it; the real version is assigned at publish.
19. All indicator and regime thresholds are defaults, not values derived from
    data.
20. The README, `docs/` and `tests/`, `tools/` are not uploaded: the upload
    archive contains `README.md`, `manifest.yaml`, `backtest.yaml` and `src/`
    only. Tests and tools live outside the package under `playbooks/`.

## Cost model and validation

Taker 0.06% / maker 0.02% (default tier), 1 tick slippage per fill, funding
charged. Entries are maker, exits taker (the stop and time stop are market
orders; the take-profit is a market-if-touched order). All reported metrics
are net. Required before activation: at least 2 years of 1H data, walk-forward
12m train / 3m test / 3m step, cost runs at 0x/1x/2x, no verdict under 30
trades, and reject if the 2x-cost net expectancy is negative. Forward
criteria (fixed): PASS = PF >= 1.3 and Sharpe >= 0.5 after >= 30 live
trades; FAIL = PF <= 1.1 -> stop. Full procedure: `docs/validation-protocol.md`.
Versioning: `docs/VERSIONING.md` (v1 is frozen at activation; one parameter
changes per version, with a written prediction first).

Results (all PENDING): trades, win rate, average R, net expectancy (R),
profit factor, max drawdown, Sharpe, 0x/1x/2x costs, walk-forward windows.

## How to read the backtest metrics

`output/backtest_report.json` reports strategy-level metrics computed from the
Playbook's own closed-trade ledger (`metrics_basis: strategy`), net of fees,
slippage and funding. Percentages are relative to `margin_budget`, not
account equity. They are realised-only. The engine's own raw statistics are
kept under the report for reference but are not the headline.

## PENDING items and next steps (f)

Needs the user's own Bitget OpenAPI ACCESS-KEY (never put in files):

1. Run the local checks: validator, `playbooks/tests/test_logic.py`.
2. Verify the fee tier of the sub-account (maker/taker) and set the fee values
   if different, as a pre-activation iteration before freeze.
3. Confirm the sub-account's position mode (one-way vs hedge) and that it is
   isolated-margin capable.
4. Generate the variants and upload them (`docs/validation-protocol.md`).
5. Run the probes (kline coverage, funding endpoint, bar timestamp convention,
   venue name, runtime), then the 0x/1x/2x runs and read the walk-forward
   rows.
6. Fill in every PENDING result from the real report. No verdict under 30
   trades; reject on negative net expectancy at 2x.
7. Decide `margin_budget` and set it in the Playbook user config.
8. Only if the pre-activation criteria hold: record the freeze in
   `docs/VERSIONING.md` (commit, time, activator), then subscribe in the
   GetAgent page. Starting, stopping, and halt-reset are the user's actions;
   this package never enables, starts, or stops a Playbook.
9. After activation, evaluate only on the fixed forward criteria. Any change
   becomes v2 with one changed parameter and a written prediction first.
10. Calibrate the default thresholds (ADX, ATR% band, EMA pair) only through
    new versions.
