# Error Responses

Error response format for all Playbook API endpoints.

## Standard Format

```json
{
  "detail": "Error description"
}
```

Or with structured error list:

```json
{
  "detail": {
    "errors": [
      "manifest.yaml: missing 'name'",
      "src/main.py: blocked import 'requests' (line 3)"
    ]
  }
}
```

## Authentication Contract

Every authenticated Playbook endpoint on the prod OpenAPI gateway requires the following header. Missing it returns 401:

- `ACCESS-KEY` — Bitget OpenAPI access key for the caller
- `X-GetAgent-Install-Id` — optional anonymous UUID printed by
  `python3 scripts/telemetry.py install-id`; it is not a credential

`X-User-Id`, `X-Api-Key`, and `X-Principal-Id` are **not** prod OpenAPI client credentials here. The gateway resolves the caller from `ACCESS-KEY`; do not use backend-internal identity headers in client code.

If an access key is revoked or cannot resolve to an active principal, authenticated endpoints return 403.

## HTTP Status Codes

| Status | Meaning | Common Scenario |
|--------|---------|-----------------|
| 200 | Success | Normal response |
| 401 | Unauthorized | Missing `ACCESS-KEY` header |
| 403 | Forbidden | Access key has been revoked, principal not found / inactive, or caller is not the resource owner |
| 404 | Not Found | draft_id or version_id does not exist |
| 409 | Conflict | Status doesn't allow operation; user already has another active Playbook; Playbook is live-only; or the declared runtime profile is not currently executable |
| 413 | Payload Too Large | Upload exceeds 10MB |
| 422 | Validation Failed | Incomplete structure, missing fields, blocked imports, etc. |
| 503 | Service Unavailable | Sandbox pool not ready |

## Validation Error Details (422)

The upload endpoint returns 422 for:

**Structure**
- `Missing manifest.yaml`
- `Missing src/main.py`

**Fields**
- `manifest.yaml: missing 'name'`
- `manifest.yaml: invalid name 'My Strategy' (must be DNS label format)`
- `manifest.yaml: decision_mode must be one of ['agentic', 'deterministic', 'llm_assisted']`
- `manifest.yaml: live-only playbooks cannot default to execution_mode 'follow_trade' unless runtime_profile is 'llm_bounded'`
- `manifest.yaml: runtime_profile 'llm_bounded' requires backtest_support = 'none'`
- `manifest.yaml: output_kind 'selection_basket' must not declare execution_mode`
- `src/**: output_kind=selection_basket requires emitting runtime.emit_signal(..., meta={'basket': [...]})`
- `backtest.yaml is only allowed when manifest.yaml sets backtest_support = 'full'`

**Code**
- `src/main.py syntax error at line 5: invalid syntax`
- `src/main.py: blocked import 'requests' (line 3)`
- `src/main.py: disallowed import 'some_unknown_lib' (line 7)`

## Handling Recommendations

1. **401** — Make sure `ACCESS-KEY` is sent.
2. **403 revoked key** — The access key was revoked server-side; mint a new one and retry.
3. **409 publish status conflict** — Publish only a draft that has the required evidence; do not bump `manifest.version`
4. **409 backtest/runtime conflict** — Check `backtest_support` and `runtime_profile`. If the strategy is `none` or `llm_bounded`, use paper/live evidence instead of historical backtest claims
5. **422 validation failed** — Fix each error in the `errors` list and re-upload
6. **503 sandbox unavailable** — Wait or contact ops
