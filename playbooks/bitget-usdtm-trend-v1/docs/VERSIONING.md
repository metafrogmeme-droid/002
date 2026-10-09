# Versioning and v1 freeze record

## Rules

1. A version is frozen at activation. A frozen version is never edited. Any
   change, including "just a threshold", creates a new version.
2. Each new version changes exactly ONE frozen parameter (or one structural
   rule). Changing two things at once makes the result unattributable.
3. A written prediction (template below) is committed BEFORE the new version
   is backtested or run. The prediction states direction, rough magnitude, and
   the observation that would falsify it.
4. The frozen hash covers the trading parameters only. Deployment/evaluation
   keys (`margin_budget`, `halt_reset_after_ts_ms`, `cost_multiplier`,
   `trade_start`, `trade_end`, `warmup_days`, `wf_*`, `require_funding_data`,
   `backtest_halt_resume_hours`, `bar_ts_convention`) are excluded so that the
   0x/1x/2x and window variants stay hash-identical to v1.
5. Verify the hash locally with `python3 playbooks/tools/param_hash.py`
   (uses the same code as the Playbook) and in the sandbox: every report
   carries `param_hash`. If they differ, the run is not v1.
6. The code is frozen too, not just the parameters. At activation record the
   git commit of the package in the table below.

## v1 freeze record

| Field | Value |
|---|---|
| Version | v1 (manifest `version: "1.0.0"`; the field exists only because the validator requires it) |
| Param hash (SHA-256, canonical JSON of frozen params) | `012777723df4636f4e05e9def7b09e390d40bded2f6eb04e0149797f28938bf2` |
| Package git commit at freeze | PENDING (record at activation) |
| FROZEN_AT (UTC) | PENDING (record at activation) |
| Activated by | PENDING (user) |
| Pre-activation validation status | PENDING (no backtest has been run; see validation-protocol.md) |

### Frozen parameters (v1)

| Parameter | Value |
|---|---|
| symbols | BTCUSDT, ETHUSDT, SOLUSDT |
| timeframe | 1h |
| ema_fast / ema_slow | 20 / 50 |
| adx_period / adx_min | 14 / 25.0 |
| atr_period | 14 |
| atr_pct_lookback_bars | 2160 |
| atr_pct_min_history_bars | 500 |
| atr_pct_rank_low / high | 20.0 / 90.0 |
| volume_lookback_bars / volume_mult | 20 / 1.5 |
| entry_offset_atr | 0.0 |
| stop_atr_mult | 1.5 |
| tp_r_mult | 2.0 |
| risk_usdt | 15.0 |
| leverage_cap | 5 |
| margin_mode | isolated |
| entry_expiry_hours | 4.0 |
| time_stop_hours | 8.0 |
| funding_window_minutes | 15 |
| funding_hours_utc | 0, 8, 16 |
| funding_adverse_max | 0.0003 |
| max_concurrent / max_per_symbol | 3 / 1 |
| daily_pause_usdt | 30.0 |
| hard_stop_usdt | 40.0 |
| max_consecutive_losses | 5 |
| stale_data_seconds | 60 |
| entry_max_signal_age_minutes | 15 |
| allow_short | false |
| short_enable_min_trades | 30 |
| maker_fee / taker_fee | 0.0002 / 0.0006 |
| slippage_ticks | 1 |

Forward criteria, fixed now and not changeable for v1:

- PASS = profit factor >= 1.3 AND Sharpe >= 0.5 after >= 30 live trades.
- FAIL = profit factor <= 1.1 (after >= 30 live trades) -> stop; do not tune v1.
- Anything in between = continue collecting trades; no parameter changes.
- Cost sensitivity: net expectancy <= 0 R at 2x costs in the pre-activation
  backtest -> reject v1 before activation.
- No verdict of any kind with fewer than 30 trades.

## v2 prediction template (copy to `docs/predictions/v2.md` BEFORE running v2)

```
Version: v2
Based on: v1 (hash 012777723df4636f4e05e9def7b09e390d40bded2f6eb04e0149797f28938bf2)
Date written (UTC):            <fill>
Written before running?        yes / no  (if no, the version is void)

Single change:
  parameter:                   <name>
  v1 value -> v2 value:        <old> -> <new>
  reason (observed in v1 data, cite the v1 report field): <fill>

Prediction (numbers are the author's guess, not a result):
  trades count change:         <direction and rough size>
  win rate:                    <direction>
  average R:                   <direction>
  net expectancy (R):          <direction / sign>
  profit factor:               <direction>
  max drawdown:                <direction>

Falsified if:                  <observation that proves the prediction wrong>
Run on the same pinned window and cost model as v1: yes / no
New param hash:                <fill from tools/param_hash.py>
Outcome (filled in after run): PENDING
Prediction right / wrong:      PENDING
```
