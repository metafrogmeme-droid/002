# Trade Market Reference

Market capability checks before order placement.

These signatures are written against the `getagent.trade` public contract.
Runner-managed identity kwargs (`user_id`, `channel`, `trace_id`) are
intentionally omitted from the author-facing signatures below.

## Contents
- [`trade.market.check_symbol_support`](#trademarketcheck-symbol-support)

## Method reference

### `trade.market.check_symbol_support`

```python
trade.market.check_symbol_support(symbols)
```

Summary: Check which trading pairs are tradable for the current subaccount.

Use this before placing orders or advertising follow-trade support for a new
symbol. Pass exchange-native tradable pairs only (`BTCUSDT`, `RAAPLUSDT`,
`AAPLUSDT`, `XAUUSDT`), not CCXT unified symbols with `/` or `:`.

For authoring-time market discovery, use Bitget's official public config APIs
before writing the strategy. Query each user-requested tradable asset to confirm
market-level support and the exact exchange-native symbol:

```bash
curl "https://api.bitget.com/api/v2/spot/public/symbols?symbol=RAAPLUSDT"
curl "https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES&symbol=AAPLUSDT"
```

The public config APIs answer exchange-level support: spot rows with
`status: online` and contract rows with `symbolStatus: normal` are listed
markets. `trade.market.check_symbol_support(...)` is still the managed
Playbook/TradeSDK check for the current bound account or subaccount.

RWA naming follows Bitget market conventions:

- spot RWA symbols use an `R` prefix before the asset code, e.g. `RAAPLUSDT`
- RWA contract symbols omit the `R` prefix, e.g. `AAPLUSDT`, `XAUUSDT`

If support is absent for the exact symbol/market, do not silently convert the
package to `selection_basket`; either resolve the correct tradable symbol or
state that the requested instrument is not follow-tradable.

| Param | Required | Type | Default |
|---|---|---|---|
| `symbols` | `yes` | `list[str] | tuple[str, ...]` | - |

Returns: `CheckSymbolSupportResult`

---
