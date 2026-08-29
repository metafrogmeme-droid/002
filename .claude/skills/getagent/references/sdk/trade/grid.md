# `getagent.trade.grid`

Managed Grid bot validation, lifecycle, and detail queries. Import through:

```python
from getagent import trade
```

Use [`../../strategy-bot-orchestration.md`](../../strategy-bot-orchestration.md)
for the required mutation wrapper. The signatures below omit runner-managed
identity and transport context. These eight Python methods are the complete
public Grid surface. They support Spot plus directional (`long`/`short`) and
neutral contract grids. Neutral routing is selected through `grid_type`; there
are no separate public neutral methods. Martingale methods are not available.

## Validate and create

`validate(...)` accepts the shared strategy fields. Funding is mandatory for
Grid investment operations. `slippage` is optional during validation and
creation. `termination_sell` is platform-owned: Spot and directional calls
wire `yes` regardless of the passed value, while neutral calls omit it.

```python
trade.grid.validate(
    *,
    category,
    symbol,
    max_price,
    min_price,
    grid_num,
    grid_order_mode,
    investment_amount,
    investment_coin="",
    funds_source=("funding",),
    slippage="",
    auto_transfer_profits,
    grid_type="",
    leverage=None,
    auto_reserve_margin=None,
    reserved_margin=None,
    trigger_condition="",
    trigger_params=None,
    trigger_price=None,
    termination_condition="",
    termination_params=None,
    termination_sell=None,
    stop_loss=None,
    take_profit=None,
    trailing_grid=None,
    moving_average_gains=None,
    stop_upward_price=None,
    hodl_mode=None,
    market_open=None,
    loss_reserve=None,
)

trade.grid.create_bot(
    *,
    category,
    symbol,
    max_price,
    min_price,
    grid_num,
    grid_order_mode,
    investment_amount,
    investment_coin="",
    funds_source=("funding",),
    slippage="",
    auto_transfer_profits,
    take_profit,
    stop_loss,
    grid_type="",
    leverage=None,
    auto_reserve_margin=None,
    reserved_margin=None,
    trigger_condition="",
    trigger_params=None,
    trigger_price=None,
    termination_condition="",
    termination_params=None,
    termination_sell=None,
    trailing_grid=None,
    moving_average_gains=None,
    stop_upward_price=None,
    hodl_mode=None,
    market_open=None,
    loss_reserve=None,
)
```

Required values:

- `category`: `spot`, `futures`, or `usdt-futures`; `futures` maps to
  `usdt-futures`
- `symbol`: exchange-native symbol such as `BTCUSDT`
- `min_price` and `max_price`: positive decimal text with
  `min_price < max_price`
- `investment_amount`: either a positive scalar paired with
  `investment_coin`, or a non-empty list such as
  `[{"coin": "BTC", "amount": "0.01"}, {"coin": "USDT", "amount": "500"}]`;
  omit `investment_coin` when passing the list form
- Contract investment coin: `USDT`
- `funds_source`: fixed to `["funding"]`; omitting it uses that default
- `grid_num`: positive integer or integer text
- `grid_order_mode`: `arithmetic` or `geometric`
- `slippage`: optional `1%`, `2%`, or `none` for Spot and directional calls;
  omit it for neutral Grid
- `auto_transfer_profits`: boolean or `yes` / `no`
- `take_profit` and `stop_loss`: required positive prices for every creation
- Contract categories require `grid_type`: `long`, `short`, or `neutral`
- Contract creation also requires positive integer `leverage`; Spot rejects it
- Spot omits `grid_type`. `termination_sell` is platform-owned: Spot and
  directional validate/create send `terminationSell=yes`; neutral calls omit
  it. Author input is ignored in all cases.

Optional condition values:

- `trigger_condition`: `instant`, `price`, `rsi`, or `boll`
- `termination_condition`: `rsi` or `boll`
- `trigger_params` / `termination_params`: mapping with
  `indicator_length`, `threshold`, `multiplier`, and/or `interval`
- indicator intervals: `1m`, `3m`, `5m`, `15m`, `30m`, `1H`, `4H`, `1D`
- `trigger_condition="price"` requires `trigger_price`
- `auto_reserve_margin="no"` uses `reserved_margin` for directional
  contracts
- `trailing_grid="yes"` uses `moving_average_gains`; `stop_upward_price`
  limits upward movement for long/spot grids and downward movement for shorts
- `hodl_mode` is Spot-only; `market_open` and `loss_reserve` are
  contract-only
- Do not enable both `hodl_mode` and `auto_transfer_profits`

Neutral contract Grid accepts the common range, count, investment, funding,
profit-transfer, leverage, trigger-price, TP, and SL fields. It rejects
`slippage`, trigger/termination condition blocks, moving Grid fields,
reserve-margin fields, `hodl_mode`, `market_open`, and `loss_reserve`.
Validation may omit leverage and TP/SL; creation requires all three.

Call `validate(...)` before `create_bot(...)`. Validation returns an envelope
whose `data` may contain `valid`, `reason`, and `minInvestment`; creation
returns `data.botId`. Always check envelopes with `trade.is_success(...)`.

## Mutation methods

Every method in this section must be the only Trade mutation inside the
`execute=` callback of `runtime.execute_strategy_bot_action(...)`.

```python
trade.grid.modify_bot(
    *,
    bot_id,
    take_profit,
    stop_loss,
    category="",
    symbol="",
    grid_type="",
    grid_order_mode="",
    investment_amount=None,
    investment_coin="",
    funds_source=None,
    trigger_condition="",
    termination_sell=None,
    termination_condition="",
    termination_params=None,
    auto_reserve_margin=None,
    reserved_margin=None,
    slippage="",
    trailing_grid=None,
    hodl_mode=None,
    loss_reserve=None,
    auto_transfer_profits=None,
)

trade.grid.modify_grid_interval(
    *,
    category,
    bot_id,
    max_price,
    min_price,
    grid_num,
    grid_type="",
)

trade.grid.add_investment(
    *,
    category,
    bot_id,
    size,
    coin="USDT",
    funds_source=("funding",),
    adjust_type="",
    reinvest_profit=None,
)

trade.grid.close_bot(*, bot_id)
```

The directional/Spot `modify_bot` fields are `take_profit`, `stop_loss`,
`termination_condition`, `termination_params`, `auto_reserve_margin`,
`reserved_margin`, `hodl_mode`, `loss_reserve`, and
`auto_transfer_profits`. `bot_id`, `take_profit`, and `stop_loss` are required.
`termination_sell` is platform-owned and ignored on `modify_bot`.
Leverage cannot be modified and is not accepted. The additional category,
symbol, investment, trigger, slippage, and trailing fields remain available for
compatibility with existing Grid bots. When changing investment through this
compatibility surface, pass `category` and `investment_amount`, plus
`investment_coin` for scalar amounts; `funds_source` remains `["funding"]`.
For neutral Grid, pass `category`, `grid_type="neutral"`, `bot_id`,
`take_profit`, and `stop_loss`; only `auto_transfer_profits` is additionally
accepted. `termination_sell` remains ignored, and the other compatibility
fields are rejected.

Use `modify_grid_interval` for range/count changes and pass
`grid_type="neutral"` for a neutral bot. `add_investment` requires
`adjust_type="increase"` or `"decrease"` for contracts. Spot may omit
`reinvest_profit` to use the default (`yes`) or pass an explicit toggle.
`coin` defaults to `USDT`, and `funds_source` is fixed to `["funding"]`. The
orchestration action `shutdown` maps to `close_bot`; no category is passed to
`close_bot`.

## Read methods

```python
trade.grid.bot_detail(*, bot_id, grid_type="")

trade.grid.list_details(
    *,
    bot_id,
    category="",
    grid_type="",
)
```

`bot_detail` returns bot configuration, lifecycle status, balances, and profit
fields. Pass `grid_type="neutral"` to select the neutral detail route.
`list_details` returns working buy and sell Grid order lists. Neutral calls
require both `grid_type="neutral"` and `category`; non-neutral calls do not
normally require `category`. Resolve any category from the bot's creation-time
snapshot `params.trade_type`, not the instance's current configuration.

## Snapshot and envelope rules

Every existing Grid snapshot must carry its creation-time `trade_type` and
`grid_type`. Spot bots use `trade_type: spot` with `grid_type: spot`; contract
bots use `trade_type: contract` with `grid_type: long`, `short`, or `neutral`.
Missing or unknown values must fail the cycle before any mutation. For contract
bots, a `gridType` / `grid_type` returned by bot detail must match the snapshot
Grid type. Do not compare a Spot snapshot's synthetic `grid_type: spot` with
bot-detail `gridType`; Spot detail may report `long` even though the bot is
unambiguously Spot.

All methods return standard Trade SDK envelopes with `code`, `message`, and
optional `data`. Relevant successful data fields include:

- create/modify results: `botId`
- bot detail identity/status: `botId`, `symbol`, `status` (`init`, `waiting`,
  `running`, `terminating`, `terminated`), `createdTime`, `runningTime`
- bot detail profit: `totalProfit`, `roi`, `gridProfit`, `gridProfitRate`,
  `unpairedProfit`, `unpairedProfitRate`, `margin`, `arbitrageAPR`, `totalAPR`
- bot detail configuration: `gridType`, `maxPrice`, `minPrice`, `gridNum`,
  `gridOrderMode`, `slippage`, `triggerCondition`, `triggerParams`,
  `triggerPrice`, `terminationCondition`, `terminationParams`,
  `terminationSell`, `stopLoss`, `takeProfit`, `hodlMode`,
  `autoTransferProfits`
- bot detail balances/investment: `currentBaseBalance`,
  `currentQuoteBalance`, `initialBaseHoldings`, `initialQuoteHoldings`,
  `reservedBaseTradingFee`, `reservedQuoteTradingFee`, `gridStartPrice`,
  `baseInvestmentCoin`, `baseInvestmentAmount`, `quoteInvestmentCoin`,
  `quoteInvestmentAmount`
- list details: `botId`, `symbol`, `buyOrderList`, `sellOrderList`; each order
  includes `orderId`, `delegateCount`, `delegatePrice`, and
  `changeRequired` (percentage value without `%`, so `1` means 1%)

Do not guess additional methods or keyword arguments.
