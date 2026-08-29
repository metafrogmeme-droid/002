# Run Playbook Backtest / Evaluation

Trigger a single evaluation run. This endpoint is asynchronous: it dispatches
the run and returns a `run_id`; poll `GET /api/v1/playbook/run?run_id=...` until
the run reaches `completed` or `failed`.

## `POST /api/v1/playbook/run`

**Auth**: `ACCESS-KEY` header from the Bitget OpenAPI credential, required on `POST /run` and `GET /run`. Missing it returns 401.

**Content-Type**: `application/json`

### Request

```json
{
  "version_id": "temporary-draft-or-version-id"
}
```

### Supported Use Cases

- creator runs a temporary, draft, or published Playbook to validate a new version
- any authenticated user runs a published Playbook evaluation when `backtest_support = full`

### Backtest Eligibility

The endpoint is only valid for Playbooks whose public contract says they are
fairly replayable on historical data.

- `backtest_support: full` -> allowed
- `backtest_support: none` -> reject with conflict and explain that the strategy is live-only
- `runtime_profile: deterministic` -> allowed today
- `runtime_profile: llm_bounded` -> reject here because this endpoint is historical evaluation only
- `runtime_profile: agentic` -> reject until that runtime exists
- `output_kind: selection_basket` -> reject here because basket snapshots are
  produced by non-trading live/scheduled runs, not historical backtests

### Dispatch Response

```json
{
  "run_id": "e5f6g7h8-...",
  "strategy_id": "strategy-...",
  "version_id": "temporary-draft-or-version-id",
  "status": "pending",
  "dispatched": true
}
```

## `GET /api/v1/playbook/run?run_id=...`

Poll the immutable run record created by `POST /run`.

### Completed Response

```json
{
  "run_id": "e5f6g7h8-...",
  "playbook_id": "a1b2c3d4-...",
  "status": "completed",
  "active_runtime_ms": 12340,
  "signal_output": [
    {
      "type": "signal",
      "action": "long",
      "symbol": "BTCUSDT",
      "confidence": 0.75,
      "metrics": {
        "total_return_pct": 23.5,
        "sharpe_ratio": 1.8,
        "win_rate": 0.62
      }
    }
  ],
  "metrics_output": {
    "total_return_pct": 23.5,
    "sharpe_ratio": 1.8,
    "max_drawdown_pct": 8.4,
    "win_rate": 0.62,
    "total_trades": 41
  },
  "backtest_report": {
    "period_start": "2025-10-01T00:00:00+00:00",
    "period_end": "2026-04-01T00:00:00+00:00"
  },
  "failure_reason": ""
}
```

### Persistence Expectations

Every evaluation run should be stored as immutable history, separate from
subscription execution runs.

Recommended fields to persist:

- `run_kind` (`manual_backtest`)
- `requested_by_principal_id`
- `visibility` (`public` or `owner_only`)
- summary metrics
- report / chart artifact references

The Playbook's official public summary should point at one designated run,
not "whatever run happened last".

### Execution Environment

The Playbook runs in a dedicated `playbook_runtime` sandbox:

- **Timeout**: 180 seconds
- **Memory**: 2GB
- **Network**: Managed data/trade access, plus managed LLM access only when `runtime_profile: llm_bounded` is injected
- **Dependencies**: Only `getagent` + `pandas` + `numpy` (no pip install)
- **Entry point**: Executes the package as `python -m src.main`

For scheduled subscriber runs, the system executes the Playbook **once per enabled user**.
Each run gets that user's own:

- `principal_id`
- Telegram `chat_id`
- trade-proxy `bg_uid`
- trade-proxy base URL

That scheduled execution history should not be treated as the same thing as a
public backtest.

### Permissions

- Owner can run temporary, draft, and published Playbooks they control
- Any authenticated user can run published Playbooks when `backtest_support = full`
- Users must not be allowed to run temporary or draft versions they do not own

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Missing `ACCESS-KEY` header |
| 403 | Caller cannot evaluate this Playbook version, access key revoked, or principal not found / inactive |
| 404 | `version_id` not found |
| 409 | Playbook is live-only or uses a runtime profile that cannot run historical evaluation yet |
| 503 | Sandbox pool not available |

### On Failure

`status` is `"failed"` and `failure_reason` contains the error message
(truncated to 2000 chars). Common causes:

- Data fetch timeout (exchange API unreachable)
- `src/main.py` runtime exception
- Timeout kill (exceeded 180 seconds)
