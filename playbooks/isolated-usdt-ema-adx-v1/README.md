# BTC/ETH/SOL Isolated EMA-ADX v1

## 策略 / Strategy

This is one deterministic, long-only EMA-ADX trend-following Playbook for
Bitget USDT perpetual contracts. The universe is frozen to `BTCUSDT`,
`ETHUSDT`, and `SOLUSDT`. Each was resolved through Bitget's official
`USDT-FUTURES` contract configuration on 2026-10-09 and returned
`symbolStatus=normal`. The exact exchange-native symbols are used everywhere.

EMA-ADX trend following was chosen over mean reversion because the required
one-sided exposure cannot hedge persistent bear trends, while the ADX and
volatility gates provide an explicit way to avoid weak, range-bound conditions.
The strategy seeks occasional larger winners and caps each initial loss rather
than repeatedly fading a move that may continue.

Only closed 1-hour bars are decision inputs. A long setup requires all of:

1. EMA(20) above EMA(50);
2. price freshly crossing above EMA(20) and closing above it;
3. ADX(14) at least 25;
4. ATR(14)/price percentile between the 20th and 80th percentile of its last
   252 closed hourly observations; and
5. current volume at least 1.5 times the prior 20-bar average.

The traded regime is a confirmed upward trend with moderate-to-high, but not
extreme, normalized volatility. The Playbook sits out ADX below 25, volatility
below the 20th percentile, volatility above the 80th percentile, bearish EMA
alignment, absent volume confirmation, stale or incomplete data, and every
invalid or ambiguous signal. There is no default direction: invalid input means
`NO TRADE`.

Shorts are disabled. They may only be introduced in a separate later version
after an independent test has at least 30 closed short trades and positive net
expectancy after fees, one-tick slippage, and funding.

## 开仓 / Entry

The intended entry is an isolated-margin long limit order, one adverse tick
from the signal close, canceled if unfilled after four hours. Position quantity
is `15 USDT / (1.5 × ATR(14) stop distance)`, rounded down to the exchange size
step. Leverage defaults to 3x and cannot exceed 5x. One position per symbol and
three positions total are allowed.

The documented Trade SDK supports `margin_mode="isolated"` and atomic
`tp_trigger_price` / `sl_trigger_price` on `trade.contract.place_order`.
However, this frozen v1 deliberately sets `live_execution_gate: false`.
Authoritative realized-PnL/loss-streak accounting, a documented 60-second data
timestamp, durable pending-order age across runs, and a reliable distinction
between flat and unknown subaccount position state are not all exposed by the
installed public SDK contract. Live runs therefore emit `NO TRADE`; they do not
claim controls that cannot be verified.

## 平仓 / Exit

The initial stop is 1.5 times ATR(14) on the entry timeframe. The selected
take-profit option is a fixed 2R target. The trend time stop is eight hours.
EMA trend failure also exits. Backtest exits are conservative: if stop and
target are both touched in one hourly bar, the stop has priority.

The fixed initial risk is 15 USDT per trade. New entries pause when daily
realized PnL reaches -30 USDT. The Playbook stops for the day at -40 USDT and
halts after five consecutive realized losses. Data older than 60 seconds and an
unknown subaccount position must halt and alert without touching that position.
These live account controls remain fail-closed and `PENDING` for the reasons
above.

## 风险 / Risk

Three crypto contracts are strongly correlated and can stop together. Limit
orders may not fill; stops can gap; funding can overwhelm a modest edge; and
exchange fee tiers can differ by account. Isolated margin reduces cross-position
contagion but does not prevent liquidation. Backtest fill models cannot prove
live order behavior.

No positive-expectancy claim is made. Net expectancy, profit factor, Sharpe,
drawdown, win rate, and trade count are `PENDING` until a real managed run
completes with funding debits included. Displayed ROI is not an optimization
target or acceptance metric.

## Frozen parameter table

| Name | Value | Rationale | Source |
|---|---:|---|---|
| Symbols | BTCUSDT, ETHUSDT, SOLUSDT | Limited liquid universe | User requirement; Bitget public contract config verified |
| Side | Long only | Prevent untested direction changes | User requirement |
| Entry timeframe | 1h | Required validation timeframe | Design choice, frozen ex ante |
| Fast / slow EMA | 20 / 50 | Medium-speed trend alignment | Design choice, frozen ex ante |
| ADX | 14; minimum 25 | Exclude weak trends | User-required indicator; threshold is a frozen design choice |
| ATR/price percentile | 14; 252-bar rank; 20–80 | Exclude dormant and extreme volatility | Frozen design choice |
| Volume gate | 1.5 × prior 20-bar average | Require participation | User requirement |
| Entry | Long limit, +1 tick | Conservative adverse tick assumption | Frozen execution assumption |
| Cancel | 4h | Bound stale intent | User requirement |
| Initial stop | 1.5 × ATR(14) | Volatility-scaled stop | User requirement |
| Quantity | 15 / stop distance | Fixed 15 USDT initial risk | User requirement |
| Take profit | 2R | Chosen fixed-R option | Frozen design choice |
| Time stop | 8h | Required trend timeout | User requirement |
| Leverage | 3x default; 5x maximum | Keep leverage bounded | Default is design choice; maximum is user requirement |
| Margin mode | Isolated | Contain collateral exposure | User requirement; live verification PENDING |
| Concurrency | 3 total; 1 per symbol | Bound correlated exposure | User requirement |
| Daily entry pause / stop | -30 / -40 USDT realized | Session circuit breakers | User requirement; live enforcement PENDING |
| Loss-streak halt | 5 | Stop adverse sequence | User requirement; live enforcement PENDING |
| Freshness halt | >60 seconds | Reject stale decisions | User requirement; source timestamp support PENDING |
| Maker / taker fee | 0.02% / 0.06% | Conservative requested schedule | PENDING account-tier verification |
| Slippage | 1 tick | Explicit execution cost | User requirement |
| Funding | Actual historical debit/credit | Required net accounting | PENDING managed-engine attribution support |

## Flow

`scan → filter → trigger → order → manage → exit → log`

1. Scan only the three frozen symbols on closed 1-hour bars.
2. Filter ADX and ATR/price percentile into traded or sat-out regimes.
3. Require EMA alignment, a fresh price trigger, and volume confirmation.
4. If any input or safety state is unknown, log `NO TRADE`.
5. Otherwise risk-size one isolated long limit with atomic exchange-side stop
   and take-profit intent; cancel after four hours.
6. Enforce symbol, portfolio, daily-loss, streak, and stale-data gates.
7. Exit at stop, 2R target, trend failure, or eight-hour time stop.
8. Log timestamp, symbol, side, intended price versus fill price, fees, funding,
   and reason for every action.

## Validation protocol

The historical window is 2024-09-01 through 2026-09-30 on real Bitget 1-hour
bars, fetched in pages below the endpoint row cap. A run fails if any symbol has
less than 95% of expected coverage.

Walk-forward is frozen as 12 months train / 3 months test, rolling every three
months. Parameters may be diagnosed on each train segment but not changed
inside v1; each following test segment is out of sample. Fold orchestration is
not exposed by the installed managed runner, so walk-forward results are
`PENDING` and no verdict is allowed.

Required metrics are trade count, win rate, average R, net expectancy in R,
profit factor, maximum drawdown, and Sharpe. There is no verdict below 30
closed trades. Fee sensitivity runs at 0x, 1x, and 2x the assumed maker/taker
schedule. A negative 2x-cost expectancy rejects the strategy. Funding must also
be included before any net-positive verdict.

For later live evidence, `PASS` requires at least 30 closed trades, profit
factor at least 1.3, Sharpe at least 0.5, and positive net expectancy after all
costs. Profit factor at or below 1.1 is `FAIL` and requires stopping the
Playbook through the user-controlled GetAgent page. The Playbook itself never
starts, stops, activates, or flattens an instance.

## Assumptions and falsifiers

- Assumption: filtered upward trends persist long enough to pay more than all
  losses and costs. Falsifier: 2x-cost net expectancy is non-positive.
- Assumption: the volume gate identifies genuine participation. Falsifier:
  walk-forward test folds show no positive net expectancy.
- Assumption: three symbols provide enough opportunities without unbounded
  concentration. Falsifier: correlated loss clusters breach the declared
  drawdown tolerance, which is `PENDING` until evidence exists.
- Assumption: limit entries and attached protection behave as modeled.
  Falsifier: paper/live intended-versus-fill logs show persistent adverse gaps
  or missing protection.
- Assumption: funding is not large enough to reverse the edge. Falsifier:
  funding-inclusive net expectancy is non-positive.

## Versioning

Activation, publishing, and subscription are not authorized. When eventually
published, v1 is frozen at activation. Each later version may change exactly
one parameter and must record an ex ante directional prediction before testing,
for example: “raising the ADX threshold should reduce trade count and improve
net expectancy after costs.” No parameter is changed in response to the same
test used to judge it.
