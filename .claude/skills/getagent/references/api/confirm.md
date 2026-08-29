# Confirm Playbook Draft

Confirm the final temporary Playbook artifact and save it as a draft. Use this
after the package has passed the required sandbox evaluation and the user agrees
that this is the version to keep.

## `POST /api/v1/playbook/confirm`

**Auth**: `ACCESS-KEY` header from the Bitget OpenAPI credential. Missing it returns 401.

**Content-Type**: `application/json`

### Request

```json
{
  "temporary_id": "temporary-playbook-id"
}
```

For backward compatibility, the server also accepts `draft_id` or `playbook_id`
with the same value.

### Success Response

```json
{
  "strategy_id": "strategy-...",
  "draft_id": "draft-playbook-id",
  "name": "btc-ema-crossover",
  "status": "draft",
  "suggested_version": "1.0.1"
}
```

The id does not change during confirmation. The same package id that was used
for the final backtest becomes the draft id used by `publish`.

### When To Call

Call `confirm` only after:

1. local validation passed,
2. required sandbox backtests completed successfully,
3. you summarized the results for the user, and
4. the user accepted this package as the final draft to keep.

Do not confirm every failed iteration. Upload replaces older temporary artifacts
automatically; confirm is the boundary where the final package becomes visible
as a draft.

### Error Responses

| Status | Description |
|--------|-------------|
| 401 | Missing `ACCESS-KEY` header |
| 403 | Not the Playbook owner, access key revoked, or principal not found / inactive |
| 404 | temporary id not found |
| 409 | The package is neither `temporary` nor already `draft` |
