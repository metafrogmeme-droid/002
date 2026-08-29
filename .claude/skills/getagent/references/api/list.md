# List Playbooks

List existing Playbooks for creator or consumer flows.

## `GET /api/v1/playbook/list`

**Auth**: Optional for the default published catalog, required for private states such as `draft`. Authenticated calls to the prod OpenAPI gateway use `ACCESS-KEY`.

### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | no | Filter by status. Default: `published`. Options: `draft`, `published`, `deprecated` |

### Request Examples

Endpoint is the fixed GetAgent prod OpenAPI URL. For authenticated calls, substitute `<access_key>` with the value the user provided in chat.

```bash
# List all published Playbooks (no auth)
curl -s "https://api.bitget.com/api/v1/playbook/list"

# List own drafts (auth required)
curl -s \
  -H "ACCESS-KEY: <access_key>" \
  "https://api.bitget.com/api/v1/playbook/list?status=draft"
```

### Response Shape

Published Playbooks should surface enough metadata for public `list / view`
surfaces to distinguish what kind of evidence the user can trust.

Recommended fields:

- identity: `strategy_id`, `version_id`, `name`, `display_name`, `version`, `description`
- public behavior: `output_kind`, `decision_mode`, `backtest_support`, `execution_mode`
- public evidence: `official_evidence_kind`, `official_metrics`
- subscription hint: `follow_trade_supported`

### Success Response

```json
[
  {
    "strategy_id": "strategy-...",
    "version_id": "version-...",
    "name": "btc-ema-crossover",
    "display_name": "BTC EMA Crossover",
    "version": "1.0.0",
    "status": "published",
    "description": "Trend following strategy based on EMA 12/26 crossover",
    "trading_symbols": ["BTCUSDT"],
    "tags": ["trend", "ema", "btc"],
    "output_kind": "trade_strategy",
    "decision_mode": "deterministic",
    "backtest_support": "full",
    "execution_mode": "follow_trade",
    "follow_trade_supported": true,
    "official_evidence_kind": "backtest",
    "official_metrics": {
      "total_return_pct": 23.5,
      "sharpe_ratio": 1.8,
      "max_drawdown_pct": 8.4,
      "win_rate": 0.62,
      "total_trades": 41
    }
  }
]
```

### Public Display Rules

- `backtest_support: full`
  - show official backtest summary in list / detail
- `backtest_support: none`
  - do not show fake Sharpe / win rate / total return
  - show `official_evidence_kind` such as `paper` or `live`
  - explain that the strategy is live-only because the core decision cannot be fairly replayed
- `output_kind: selection_basket`
  - show it as a callout/watchlist product, not as an auto-trading strategy
  - read current holdings from the product basket surface, not from historical trades

Returns max 100 results, ordered by creation time descending.
