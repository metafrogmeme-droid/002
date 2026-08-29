# Trade Execution Patterns

Use these patterns before reading the full namespace reference.

## Pattern 1: Signal first, follow-trade execution second

```python
from getagent import runtime


def run() -> None:
    decision = build_live_decision()

    runtime.emit_signal_or_follow(
        action=decision.action,
        symbol=decision.symbol,
        confidence=decision.confidence,
        metrics=decision.metrics,
        meta=decision.meta,
        execute_trade=lambda: execute_trade(decision),
    )
```

`runtime.emit_signal_or_follow(...)` always emits the signal. It calls
`execute_trade` only when the current subscription is `follow_trade` and the
signal action is actionable.

## Symbol policy for tradable markets

Trade SDK calls use exchange-native tradable pairs with no slash or colon. Use
the same symbol that appears in `manifest.trading_symbols`, emitted signals, and
`backtest.yaml`.

- Crypto examples: `BTCUSDT`, `ETHUSDT`.
- Bitget RWA spot examples: `RAAPLUSDT`, `RTSLAUSDT` (`R` prefix before the
  asset code).
- Bitget RWA contract examples: `AAPLUSDT`, `TSLAUSDT`, `XAUUSDT` (no `R`
  prefix).

Asset class does not change the execution contract. If the symbol is tradable,
use the same guarded follow-trade pattern for RWA stock tokens or metals as for
crypto.

## Pattern 2: Spot market buy from quote budget

```python
from getagent import trade

symbol = trade.helpers.normalize_trading_symbol("BTC")
qty_plan = trade.helpers.compute_qty(
    symbol=symbol,
    market="spot",
    budget_amount="100",
)
result = trade.spot.market_buy(symbol=symbol, qty=qty_plan.qty)
if not trade.is_success(result):
    raise RuntimeError(f"spot market buy failed: {result}")
```

## Pattern 3: Contract long from margin budget

```python
from getagent import trade

symbol = trade.helpers.normalize_trading_symbol("BTC")
leverage = 5
qty_plan = trade.helpers.compute_qty(
    symbol=symbol,
    market="contract",
    budget_amount="20",
    leverage=leverage,
)
tpsl_plan = trade.helpers.resolve_contract_tpsl(
    symbol=symbol,
    side="long",
    leverage=leverage,
)
result = trade.contract.open_long_market(
    symbol=symbol,
    qty=qty_plan.qty,
    leverage=leverage,
    tp_trigger_price=tpsl_plan.tp_trigger_price,
    sl_trigger_price=tpsl_plan.sl_trigger_price,
)
if not trade.is_success(result):
    raise RuntimeError(f"contract open failed: {result}")
```

For percentage-based TP/SL strategy settings, compute concrete trigger prices
from the reference price first, then pass `tp_trigger_price` and
`sl_trigger_price` into `resolve_contract_tpsl(...)`. Do not invent helper kwargs
such as `tp_pct_override` or `sl_pct_override`; the helper only accepts the
documented keyword-only parameters.

## Pattern 4: PRE-CHECK -> EXECUTE -> POST-CHECK

Use this for cancel, close, and TP/SL modification flows.

1. PRE-CHECK:
   - query `pending_orders(...)`, `plan_pending_orders(...)`, or `current_position(...)`
   - use selector helpers to choose the exact target; for contract positions,
     use `find_contract_position(...)` when a flat account is a normal branch
2. EXECUTE:
   - call the mutation with the selected `order_id` or live `hold_side`
3. POST-CHECK:
   - query live state again and verify the mutation took effect

## Hard rules

- Never import `trade_sdk` directly in Playbook code.
- Never hardcode `user_id`, `base_url`, or `channel`.
- Never convert quote or margin budgets to qty manually.
- Never call trade mutation APIs outside the callback passed to
  `runtime.emit_signal_or_follow(...)`; the managed permission gate decides
  whether to call it.
- Never modify or close a position without checking live state first.
- Never assume `select_contract_position(...)` returns `.found`; it raises when
  no position exists. First live ticks commonly start flat.
