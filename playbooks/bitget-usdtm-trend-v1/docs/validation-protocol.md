# Pre-activation validation protocol (v1)

Status: NOTHING IN THIS FILE HAS BEEN RUN. The GetAgent SDK
(`getagent.data`, `getagent.backtest`, `getagent.runtime`) exists only inside
the GetAgent sandbox, so no backtest could be produced while authoring. Every
result field below is `PENDING`. Do not fill one in from memory or from a
different run; copy it from the downloaded `output/backtest_report.json`.

Running this protocol needs the user's own Bitget OpenAPI `ACCESS-KEY`, which
was deliberately not available to the author. Never write the key into any
package file, the README, a variants folder or git. Pass it only on the command
line of the curl calls below (shell history/clipboard are the user's call).

## 0. Local checks (no key needed)

```
python3 .claude/skills/getagent/scripts/validate.py playbooks/bitget-usdtm-trend-v1
python3 playbooks/tests/test_logic.py              # logic tests, synthetic data
python3 playbooks/tools/param_hash.py              # must print the hash in VERSIONING.md
```

## 1. Generate the run variants (pins one window for every variant)

Pick ONE end date (UTC midnight, a past date) and reuse it everywhere.

```
python3 playbooks/tools/make_validation_variants.py --end <YYYY-MM-DD> --months 24 \
    --out playbooks/_variants
```

This writes three tarballs, `...-cost0x`, `...-cost1x`, `...-cost2x`. They
differ only in `cost_multiplier`, `trade_start`, `trade_end` and `name`; the
tool refuses to write a variant whose frozen-parameter hash differs from v1.
The run API takes only `version_id`, so per-run overrides are impossible and
each variant needs its own upload. Tarballs contain only `README.md`,
`manifest.yaml`, `backtest.yaml`, `src/`.

If the 1x run exceeds the sandbox runtime limit (the SKILL says the sandbox is
bounded; the 3-symbol 24-month 1h replay is untested), regenerate with
`--chunks 3` and run the chunk packages at 1x, then pool the
`playbook_trades.json` ledgers by hand. Walk-forward rows and the 0x/2x runs
then need the same chunking. Record that this fallback was used.

## 2. Probes to run BEFORE trusting any result

Each of these is an unverified platform assumption; if one fails, stop and fix
the package (which makes it a new pre-activation iteration, not a v2).

| Probe | How | Passing condition |
|---|---|---|
| Kline coverage | Run any variant; read `data_coverage` in the report | Every symbol: >= 24 months + warmup of 1h bars, no large gaps |
| Funding data | Read `funding_source` / `funding_modelled` in the report | Rows for all 3 symbols at 00/08/16 UTC; the run fails loudly otherwise (`require_funding_data: true`) |
| Funding symbol/interval semantics | Compare returned rates with Bitget history for 3 dates | Rates match, `interval="1h"` returns 8-hourly settlements as assumed |
| Bar timestamp convention | Compare a known bar's open/close/volume to the exchange | Timestamp = bar OPEN (`bar_ts_convention: open`); if it is close time, v1 code is wrong and must be fixed before running |
| Venue name | The run does not fail with an unknown venue | `BITGET` accepted by the runner |
| Runtime | `active_runtime_ms` in the run response | Within the sandbox limit |
| Engine funding | Report field `funding_modelled` | Funding is charged analytically from history; the engine itself is not assumed to charge it |
| Trade count | `playbook_report.pooled_all_trades.trades` | Compare with `reason_counts` (signals vs orders vs fills); a large gap means entry fills are being missed |

## 3. Cost sensitivity: 0x / 1x / 2x

Upload and run the three cost variants on the same pinned window.

```
# per variant (substitute the key at call time; do not save it)
curl -X POST -H "ACCESS-KEY: <access_key>" \
  -F "package=@playbooks/_variants/bitget-usdtm-trend-v1-cost1x.tar.gz" \
  "https://api.bitget.com/api/v1/playbook/upload"          # -> draft_id
curl -X POST -H "ACCESS-KEY: <access_key>" -H "Content-Type: application/json" \
  -d '{"version_id":"<draft_id>"}' "https://api.bitget.com/api/v1/playbook/run"   # -> run_id
curl -H "ACCESS-KEY: <access_key>" \
  "https://api.bitget.com/api/v1/playbook/run?run_id=<run_id>"   # poll until completed
```

Uploading a newer package of the same strategy deletes the previous temporary
one, so run and download each variant's report before uploading the next. The
`name` differs per variant, which may avoid this; do not rely on it.

`cost_multiplier` scales maker/taker fees in the engine (and the analytic
slippage and funding costs in the ledger). Each report also contains
`cost_sensitivity_repriced_same_trades` for 0x/1x/2x, an approximation that
reprices the same trade list; trust the three real runs where they differ
(the same entries are not guaranteed to fill at different costs).

Decision rule (fixed now): net expectancy (R) at 2x costs `<= 0` -> REJECT v1.
Fewer than 30 trades -> no verdict.

## 4. Walk-forward

Strategy parameters are not fitted in v1, so walk-forward here measures
stability across regimes, not out-of-sample selection. Train/test split:
12 months train / 3 months test, rolled by 3 months, over the 24-month window:
4 test windows (months 13-15, 16-18, 19-21, 22-24). Computed automatically in
`playbook_report.walk_forward` from the single full-window run (the same
ledger sliced by entry time); the train rows are in-sample reference only. A
3-month window of this strategy may hold fewer than 30 trades; any window
below 30 trades gets no verdict, and the pooled out-of-sample set is the one
judged.

## 5. Results (all PENDING)

Source: `output/backtest_report.json`, field `playbook_report`. Window:
PENDING. param_hash: PENDING (must equal VERSIONING.md).

Pooled out-of-sample (months 13-24), 1x costs:

| Field | Result |
|---|---|
| Trades | PENDING |
| Win rate | PENDING |
| Avg R (gross) | PENDING |
| Net expectancy (R) | PENDING |
| Profit factor | PENDING |
| Max drawdown (realised-only) | PENDING |
| Sharpe (daily realised, sqrt 365) | PENDING |

Cost sensitivity (net expectancy R):

| Costs | Trades | Net expectancy (R) | PF | Verdict |
|---|---|---|---|---|
| 0x | PENDING | PENDING | PENDING | n/a |
| 1x | PENDING | PENDING | PENDING | n/a |
| 2x | PENDING | PENDING | PENDING | PENDING (REJECT if <= 0) |

Walk-forward windows:

| Test window | Trades | Net expectancy (R) | PF | Sharpe |
|---|---|---|---|---|
| months 13-15 | PENDING | PENDING | PENDING | PENDING |
| months 16-18 | PENDING | PENDING | PENDING | PENDING |
| months 19-21 | PENDING | PENDING | PENDING | PENDING |
| months 22-24 | PENDING | PENDING | PENDING | PENDING |

Short side (disabled): a separate short-side test is PENDING and is not
possible with this package version (`load_params` refuses `allow_short: true`).
Enabling it requires a new version with the gate: >= 30 short trades with
positive net expectancy.

## 6. Forward (live) criteria, fixed now

Counted on live trades from the isolated sub-account after activation:

- PASS = PF >= 1.3 AND Sharpe >= 0.5 after >= 30 live trades.
- FAIL = PF <= 1.1 after >= 30 live trades -> stop the Playbook (the user does
  this in the GetAgent page; the Playbook never stops itself).
- Between: keep collecting; no tuning of v1.
- Fewer than 30 trades: no verdict.

Live results: PENDING.
