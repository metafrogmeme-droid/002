# Trade Account Reference

Account queries and internal balance transfers.

These signatures are written against the `getagent.trade` public contract.
Runner-managed identity kwargs (`user_id`, `channel`, `trace_id`) are
intentionally omitted from the author-facing signatures below.

## Contents
- [`trade.account.subaccount_exists`](#tradeaccountsubaccount-exists)
- [`trade.account.total_value`](#tradeaccounttotal-value)
- [`trade.account.funding_assets`](#tradeaccountfunding-assets)
- [`trade.account.transfer`](#tradeaccounttransfer)

## Method reference

### `trade.account.subaccount_exists`

```python
trade.account.subaccount_exists()
```

Summary: Return True when the trade-proxy subaccount for ``user_id`` exists.

No author-supplied parameters.

Returns: `bool`

---

### `trade.account.total_value`

```python
trade.account.total_value()
```

Summary: Query the unified total-asset snapshot for the current user.

No author-supplied parameters.

Returns: `TotalValueResult`

---

### `trade.account.funding_assets`

```python
trade.account.funding_assets(coin="USDT")
```

Summary: Query current Funding-account balances. Grid Playbooks should use the
USDT row's `available` for executable capacity and
`available + frozen + locked` as the Funding-equity basis for percentage caps.

| Param | Required | Type | Default |
|---|---|---|---|
| `coin` | `no` | `str` | `"USDT"` |

Returns: `FundingAssetsResult`, whose `data` is a list of rows containing
`coin`, `available`, `frozen`, and `locked` decimal strings.

---

### `trade.account.transfer`

```python
trade.account.transfer(from_type, to_type, amount, coin)
```

Summary: Move funds between ``spot`` and ``usdt_futures`` sub-wallets.

| Param | Required | Type | Default |
|---|---|---|---|
| `from_type` | `yes` | `AccountTypeLiteral` | - |
| `to_type` | `yes` | `AccountTypeLiteral` | - |
| `amount` | `yes` | `Any` | - |
| `coin` | `yes` | `str` | - |

Returns: `TransferResult`

---
