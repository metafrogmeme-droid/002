# My Playbooks

List the currently enabled Playbook deployments for the authenticated user.

## `GET /api/v1/playbook/my-playbooks`

**Auth**: `ACCESS-KEY` header from the Bitget OpenAPI credential. Missing it returns 401.

### Success Response

```json
[
  {
    "instance_id": "e1f2g3-...",
    "strategy_id": "strategy-...",
    "version_id": "version-...",
    "playbook_name": "btc-ema-crossover",
    "display_name": "BTC EMA Crossover",
    "version": "1.0.0",
    "strategy_display_name": "BTC EMA Crossover",
    "version_owner_id": "creator-principal-id",
    "status": "active",
    "execution_mode": "follow_trade",
    "follow_trade_supported": true,
    "channel": "telegram",
    "chat_id": "123456789",
    "reminder_id": "reminder-id"
  }
]
```

Returns the caller's active deployments. `strategy_id` is the stable strategy
tree; `version_id` is the immutable published artifact that scheduled runs
execute with the instance's `config_overrides`.

The list should be enough for Telegram to distinguish non-trading basket
subscriptions from managed follow-trade strategies and explain whether live
trade permission is currently active.
