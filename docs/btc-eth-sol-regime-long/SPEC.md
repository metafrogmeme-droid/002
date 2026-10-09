# btc-eth-sol-regime-long — v1 specification

Package: `playbooks/btc-eth-sol-regime-long/`
Research / local backtest: `research/btc_eth_sol_playbook/`
Status: **v1 frozen, validation verdict REJECT — do not activate.** Not published, not subscribed.

Every number below is labelled with the engine that produced it:

- **LOCAL-RESEARCH-ENGINE**: `research/btc_eth_sol_playbook/engine.py` + `run_validation.py` (portfolio simulator, walk-forward). Reproduce with `python fetch_data.py && python run_validation.py`.
- **LOCAL-NAUTILUS-HARNESS**: `research/btc_eth_sol_playbook/nautilus_harness.py`. It runs the Playbook's own `strategy.py` in NautilusTrader 1.231 on the same local data.
- **GETAGENT-NAUTILUS-ENGINE**: the GetAgent managed backtest of the uploaded draft package (see "GetAgent run" below).

Only LOCAL-RESEARCH-ENGINE ran the walk-forward. The two Nautilus engines replay the frozen v1 parameters, so their numbers are an implementation cross-check, not an out-of-sample test.

## 1. Market fit

Universe: BTCUSDT, ETHUSDT and SOLUSDT USDT-M perpetuals. Run it in an isolated sub-account.

The regime is evaluated on every closed 1H bar (`features.classify_regime`):

| Regime | Condition | Traded? |
|---|---|---|
| TREND | ADX(14) ≥ `adx_trend_min` (v1: 30) AND ATR(14)/close percentile over the last 720 bars in [20, 90] | **Yes, long only** |
| RANGE | ADX(14) < 20 AND ATR percentile ≤ 90 | No: mean reversion was rejected (see section 2) |
| SIT_OUT | ADX between the range and trend thresholds, OR ATR percentile < 20 (dead) or > 90 (extreme) | No |

Time share of each regime (train window 2023-10..2024-10 at ADX 25, LOCAL-RESEARCH-ENGINE):

| Symbol | TREND | RANGE | SIT_OUT |
|---|---|---|---|
| BTC | 0.384 | 0.284 | 0.332 |
| ETH | 0.361 | 0.277 | 0.362 |
| SOL | 0.323 | 0.307 | 0.370 |

Funding rules:
- No entries within ±15 min of the 00/08/16 UTC settlements. A time-stop exit that falls inside that window is deferred until the window ends.
- An entry is skipped when funding against the position is above 0.03% per 8h. Rates on symbols with other funding intervals are normalised to 8h.
- If funding is unknown, the entry is skipped (fail closed). The single exception is backtest replay with `unknown_funding_policy: allow`, where history is missing. It is counted as `funding_unknown_allowed_replay` in the ledger.

## 2. Signal

**Base: EMA-ADX trend breakout, long only.** I chose it on the train window only (2023-10-01..2024-10-01). There, trend-long produced 130 trades at −0.062R. Mean reversion in the RANGE regime produced only 23 trades (below the 30-trade minimum, so ineligible) at −0.264R. The regime filter also gives the trend regime more bars than the range regime on all three symbols. Neither base was profitable in training; trend was the less bad, eligible choice.

Entry trigger, all evaluated on the **closed 1H bar**:
1. regime == TREND
2. EMA(20) > EMA(50)
3. +DI(14) > −DI(14)
4. close > highest high of the previous 20 bars (Donchian breakout)
5. volume ≥ 1.5 × average volume of the previous 20 bars

Order: a limit buy at the signal close, cancelled if not filled within 4h.

AI signal handling: the Playbook is `runtime_profile: deterministic`, so it calls no LLM. Every candidate action still passes through `features.validate_signal(action, allowed)`. A missing, unknown or disallowed action (for example "short" while `allow_short=false`) returns NO_TRADE with reason `INVALID_SIGNAL`. It never falls back to a default direction.

Shorts: tested separately (section 6, stage 4). The walk-forward out-of-sample short test produced 281 trades at −0.053R, so `allow_short: false`.

## 3. Risk

| Rule | Implementation |
|---|---|
| Size | qty = floor(15 USDT / (entry − stop)), so the loss at the stop is ≤ 15 USDT before fees and slippage |
| Margin / leverage | isolated; `change_leverage(5)`; hard cap `HARD_MAX_LEVERAGE = 5` in `risk.py` (config cannot raise it); skip if margin > margin_budget / 3 |
| Stop | entry − 1.5 × ATR(14); attached exchange-side to the entry order (`sl_trigger_price`) |
| Take profit | fixed 2R, attached exchange-side (`tp_trigger_price`) |
| Time stop | 8h (trend), market close |
| Concurrency | max 3 open/pending, max 1 per symbol |
| Daily loss | realised ≤ −30 USDT → pause new entries for the UTC day and cancel pending entries; ≤ −40 USDT → Playbook stop (latched) |

## 4. Halts

| Trigger | Reason code | Effect |
|---|---|---|
| 5 consecutive losing trades | `HALT_CONSECUTIVE_LOSSES` | latched; no new entries until state is reset by the user |
| Ticker older than 60 s, or newest closed bar older than 2h | `HALT_STALE_DATA` | no actions on this run |
| Position in the sub-account that the Playbook did not open | `HALT_FOREIGN_POSITION` | alert and block new entries; the foreign position is never modified |
| State file unreadable / PnL of a close not resolvable | `HALT_STATE_UNREADABLE` / `PNL_UNRESOLVED` | fail closed |

## 5. Costs

Maker 0.02% (limit entry), taker 0.06% (stop, time stop, take profit), 1 tick of slippage on taker fills, and funding charged at each settlement while a position is held. All results are net of these. **The user's actual fee tier is PENDING**: the GetAgent API does not expose it, so these are Bitget's public default rates.

## Parameter table (v1)

| Name | Value | Rationale | Source |
|---|---|---|---|
| trading_symbols | BTC, ETH, SOL USDT | spec universe; most liquid perps | default (spec) |
| timeframe | 1H closed bars | spec; enough samples for ≥30 trades | default (spec) |
| base_strategy | ema_adx_trend | the only eligible base in training (mean reversion had 23 trades) | data (train 2023-10..2024-10) |
| ema_fast / ema_slow | 20 / 50 | standard trend pair; not tuned to avoid overfitting | default |
| adx_period / atr_period | 14 / 14 | spec | default (spec) |
| adx_trend_min | **30** | walk-forward fits were 30, 20, 25, 25 (unstable); v1 refit on the last 12m gave 30 | data (refit 2025-10..2026-10) |
| adx_range_max | 20 | conventional "no trend" level; only defines RANGE / SIT_OUT | default |
| atr_rank_window | 720 bars (30 days) | percentile over about one month of hourly bars | default |
| atr_rank_min / max | 20 / 90 | sit out dead and extreme volatility | default |
| volume_avg_period / volume_mult | 20 / 1.5 | spec | default (spec) |
| breakout_lookback | 20 | Donchian channel the same length as the volume window | default |
| entry order | limit at signal close, TTL 4h | spec | default (spec) |
| risk_per_trade_usdt | 15 | spec | default (spec) |
| max_leverage | 5 (hard cap) | spec | default (spec) |
| margin_budget | 1500 USDT (user-editable) | 3 slots × 500 USDT margin covers most stop distances at 5x | default |
| stop_atr_mult | 1.5 | spec | default (spec) |
| tp_r_multiple | 2.0 | spec option A (fixed 2R); simpler to attach exchange-side than a trail | default (spec) |
| time_stop_hours | 8 | spec (trend) | default (spec) |
| max_concurrent | 3, 1 per symbol | spec | default (spec) |
| daily_pause_usdt / daily_stop_usdt | 30 / 40 | spec | default (spec) |
| max_consecutive_losses | 5 | spec | default (spec) |
| funding_block_minutes | 15 | spec | default (spec) |
| funding_max_against_8h | 0.0003 | spec | default (spec) |
| funding_interval_hours | 8 for each symbol | Bitget's current interval for these perps | data (Bitget funding history) |
| stale_data_seconds | 60 | spec | default (spec) |
| allow_short | false | short out-of-sample test was negative | data (stage 4) |
| maker / taker fee | 0.02% / 0.06% | public default | **PENDING** (user tier) |
| slippage | 1 tick on taker fills | spec | default (spec) |

## Flow (`main_live.py`, cron at minutes 2/17/32/47 UTC)

1. **Scan**: load state from `.state/regime_long_state.json`. Fetch ticker, 1H klines and funding for the 3 symbols. Halt the run (`HALT_STALE_DATA`) if data is stale.
2. **Reconcile**: read `pending_orders`, `current_position` and `fills`. Detect entry fills (`ENTRY_FILLED`) and closes (`EXIT_TP` / `EXIT_SL` / `EXIT_OTHER`, with PnL taken from fills: profit − fees − funding). Update `RiskState`. Any unknown position raises `HALT_FOREIGN_POSITION`.
3. **Filter**: run-level blocks (latched halt, daily pause/stop), then per symbol: regime, symbol busy, max concurrent, funding window, funding against or unknown.
4. **Trigger**: on the first tick after a bar closes, read the signal for that bar and run it through `validate_signal`. Then `plan_entry` computes limit, stop, TP and quantity, plus the leverage/margin check.
5. **Order**: inside `runtime.emit_signal_or_follow(execute_trade=...)`, call `change_leverage(5, isolated)` and then `place_order(limit, isolated, tp_trigger_price, sl_trigger_price)`. The stop and TP are attached to the entry order.
6. **Manage**: cancel an entry after 4h unfilled (`ENTRY_TTL_EXPIRED`), or when paused or halted (`PAUSE_CANCEL`).
7. **Exit**: exchange-side TP/SL, or a time stop at 8h (`TIME_STOP`, market `close_position`; deferred while inside the funding window).
8. **Log**: every action above appends one row to `.state/action_log.jsonl` (capped at 5000 lines) and `output/action_log.json`. The replay writes the same schema to `output/replay_ledger.json`.

## Log schema (`src/action_log.py`)

Fields: `ts_utc, ts_ms, run_id, mode, seq, symbol, action, side, intended_price, filled_price, qty, fee_usdt, funding_usdt, realized_pnl_usdt, r_multiple, order_id, reason_code, detail`.

Actions: `SIGNAL, NO_TRADE, ORDER_PLACED, ORDER_CANCELLED, ENTRY_FILLED, EXIT, HALT, ALERT, STATE`.
Reason codes are an enumerated set (`REASON_CODES`), and `make_row` raises an error on any unknown code. The set is: ENTRY_SIGNAL, NO_SIGNAL, INVALID_SIGNAL, REGIME_SIT_OUT, FUNDING_WINDOW, FUNDING_AGAINST, FUNDING_UNKNOWN, SYMBOL_BUSY, MAX_CONCURRENT, DAILY_PAUSE, PLAYBOOK_STOP_DAILY_LOSS, HALT_CONSECUTIVE_LOSSES, HALT_STALE_DATA, HALT_FOREIGN_POSITION, HALT_STATE_UNREADABLE, PNL_UNRESOLVED, SIZE_EXCEEDS_LEVERAGE_CAP, QTY_BELOW_MIN, ENTRY_TTL_EXPIRED, ORDER_GONE_UNFILLED, PAUSE_CANCEL, TIME_STOP, EXIT_TP, EXIT_SL, EXIT_OTHER, ORDER_REJECTED, FOLLOW_NOT_EXECUTED.

## 6. Validation

Data: Bitget USDT-M 1H candles, 2023-10-01..2026-10-01 (plus 40 days of indicator warmup). Funding comes from Bitget history for about the last 90 days. Before that, the Binance USDT-M funding archive is used as a **proxy**. Its correlation with Bitget over 243 overlapping settlements was only 0.24 (BTC), 0.35 (ETH) and 0.51 (SOL), so funding cost in older periods is approximate (it was 12 USDT of 311 USDT total costs). Sharpe = mean/std of daily realised PnL / 1500 USDT × √365.

Walk-forward: 12-month train, 6-month test, 6-month step, with `adx_trend_min` fitted from {20, 25, 30} on each train window. The stitched out-of-sample test window is **2024-10-01..2026-10-01 (24 months)**.

### LOCAL-RESEARCH-ENGINE — stitched out-of-sample, 24 months

| Run | Trades | Win rate | Avg R (gross) | Net exp. (R) | PF | Max DD USDT (R) | Sharpe | Net USDT |
|---|---|---|---|---|---|---|---|---|
| Long, costs 0x | 304 | 0.414 | 0.063 | +0.063 | 1.137 | 390.4 (26.0R) | 0.46 | +286.6 |
| **Long, costs 1x** | **296** | **0.392** | **0.067** | **−0.004** | **0.993** | **518.2 (34.5R)** | **−0.03** | **−15.5** |
| Long, costs 2x | 294 | 0.378 | 0.070 | −0.070 | 0.871 | 698.0 (46.5R) | −0.52 | −309.0 |
| Short, 1x (stage 4) | 281 | 0.377 | 0.007 | −0.053 | 0.895 | 366.4 (24.4R) | −0.43 | −224.5 |
| Mean reversion long, 1x (shown for transparency) | 118 | 0.441 | −0.081 | −0.150 | 0.595 | 268.0 (17.9R) | −1.26 | −265.4 |

At 1x: fees 298.1, slippage 1.3, funding 12.1 USDT, against a gross of +296.0 USDT. The edge before costs is about +0.06R per trade, and fees consume all of it. By symbol: BTC −0.190R, ETH +0.140R, SOL +0.030R. Each fold is shown in `research/btc_eth_sol_playbook/results/validation_report.md`.

### v1 frozen parameters (ADX 30) over 2024-10..2026-10 — NOT out-of-sample (the refit window overlaps it)

| Engine | Costs | Trades | Win rate | Net exp. (R) | PF | Max DD USDT | Sharpe | Net USDT |
|---|---|---|---|---|---|---|---|---|
| LOCAL-RESEARCH-ENGINE | 0x | 232 | 0.397 | +0.068 | 1.147 | 282.6 | 0.45 | +236.5 |
| LOCAL-RESEARCH-ENGINE | 1x | 231 | 0.377 | +0.002 | 1.004 | 383.5 | 0.01 | +6.5 |
| LOCAL-RESEARCH-ENGINE | 2x | 229 | 0.367 | −0.064 | 0.883 | 535.0 | −0.43 | −220.4 |
| LOCAL-NAUTILUS-HARNESS | 1x | 240 | 0.392 | −0.009 | 0.981 | n/a | n/a | −33.3 |
| LOCAL-NAUTILUS-HARNESS, no funding data | 1x minus funding | 241 | — | −0.011 | 0.978 | n/a | n/a | −40.1 |
| **GETAGENT-NAUTILUS-ENGINE** (run `pbrun-56f44d2b2d30`) | 1x, funding known for about 11% of the window | **216** | **0.394** | **−0.021** | **0.957** | **410.2 (27.3R)** | **−0.15** | **−69.5** |

The Nautilus engines charge more fees than the research engine (about 320–365 vs 300 USDT) because some limit entries cross the book and fill as taker.

### GetAgent run

Draft `dfaf4b16-c4b5-4987-997e-7ead47fd7df9`, run `pbrun-56f44d2b2d30`, status completed. It was uploaded and backtested only: not published, not activated, not subscribed. A key-free summary is in `research/btc_eth_sol_playbook/results/getagent_runs.json`.

- **Strategy ledger** (`main_backtest.py`; 40 days of warmup; Bitget funding through the SDK): 216 trades, win rate 0.394, gross avg +0.078R, **net −0.021R**, PF 0.957, net −69.5 USDT, max DD 410.2 USDT (27.3R), Sharpe −0.15. Costs: fees 321.5, funding 0.4, slippage 0.9 USDT. Exits: 96 time stop, 79 SL, 41 TP. Halts (replay resumes the next day): 9 daily pauses, 3 daily stops, 12 consecutive-loss halts.
- **Platform replay of `backtest.yaml`** (platform-fetched OHLCV, no warmup, no funding, account basis 100 000 USDT): 215 positions / 430 fills, net −42.5 USDT, account Sharpe −0.08. The platform also reports PF 1.158 and win rate 0.414. These conflict with its own negative net PnL and are probably computed before fees, so they are not used for the verdict.
- **Funding coverage in the sandbox:** the SDK serves Bitget funding only from 2026-07-12. The Binance fallback returned nothing older, so funding is known for about 11% of the window. Elsewhere the replay allows entries (202 such cases, counted in the ledger) and charges no funding. Locally, funding was 12 USDT of 311 USDT total costs, so this barely moves the result.
- **SDK funding units:** `data.crypto.futures.funding_rate` returns **percent** (for example, BTC `0.01` = 0.01% per 8h; probe run `pbrun-a62ac10fa011`), although the SDK docs say decimal. The package now detects the unit per series (`features.funding_unit_scale`) in both the backtest and live paths. The earlier run `pbrun-8c98cc373371` read the rates as decimals and blocked 24 entries wrongly (199 trades, −0.069R); it is superseded.
- Earlier run `pbrun-d395634cb477` failed because the platform's replay does not supply custom `required_bar_fields`. The strategy now computes signals from plain OHLCV.

### Verdict (section 6 rules)

- ≥ 30 trades: yes (296 out-of-sample).
- Net expectancy at 1x: −0.004R (not positive).
- Net expectancy at 2x: −0.070R, so **REJECT**.
- Cross-check: GETAGENT-NAUTILUS-ENGINE with v1 parameters gives −0.021R at 1x (216 trades), so it agrees.

**Verdict: REJECT. Do not activate v1.** The package is uploaded as a draft only so the GetAgent engine can reproduce the result.

Forward criteria (fixed now, apply only if a later version passes the backtest and the user activates it):
- **PASS**: PF ≥ 1.3 AND Sharpe ≥ 0.5 after ≥ 30 live trades.
- **FAIL**: PF ≤ 1.1 at any review after ≥ 30 live trades, which means stop the Playbook.
- Between the two: keep running without changes until the next 30 trades.

## Assumptions and what would falsify them

| Assumption | Falsified by |
|---|---|
| Hourly breakouts in a TREND regime have positive gross follow-through | gross avg R ≤ 0 out-of-sample (currently +0.067R, so this holds, but the edge is too thin to cover costs) |
| Limit entries at the signal close mostly fill as maker | live `fills` showing taker fees on most entries (the Nautilus harness already suggests partial taker fills) |
| Fees are 0.02% / 0.06% | the user's real fee tier is higher. At 2x costs the strategy loses money |
| Binance funding is a usable proxy for Bitget's older history | a full Bitget funding history giving a materially different funding cost |
| Exchange-side TP/SL attach to the entry and survive partial fills | an SDK response or live position with no TP/SL after a fill |
| 1-tick slippage on stops | live stop fills averaging more than 1 tick beyond the trigger |
| `.state/` persists between cron runs | the risk state resetting between runs (the consecutive-loss counter would never reach 5) |
| The regime filter improves on the raw breakout | the same breakout without the regime filter having equal or better net expectancy (not yet tested; a candidate one-parameter test) |

## PENDING / unverified

- **Fee tier**: the user's actual maker/taker rates. Not exposed by the API.
- **Live SDK response shapes**: `fills` (profit / feeDetail fields), `place_order` side/tradeSide literals in one-way vs hedge mode, and `current_position` fields. Coded defensively against the skill docs but not exercised against a live account (we are not activating).
- **Live funding per trade** is estimated from rate × notional at each settlement, not read from the account bill.
- **Funding history** before about 90 days ago is a Binance proxy locally, and unavailable in the GetAgent sandbox.
- **SDK funding units:** detected per series because the SDK returns percent, contrary to its docs. If the platform switches to decimals, the detector follows automatically; the detected unit is logged.
- **Bar timestamp convention** in the managed replay is assumed to be the bar open time, as the data SDK documents (`bar_ts_is_open: true`). It is not independently verified inside the managed engine.
