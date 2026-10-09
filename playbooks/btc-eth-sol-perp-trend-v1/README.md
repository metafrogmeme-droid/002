# BTC/ETH/SOL Perp Trend Pullback v1

Long-only, regime-filtered trend pullback Playbook for the `BTCUSDT`, `ETHUSDT`
and `SOLUSDT` USDT-M perpetual contracts on Bitget, built to run in an isolated
sub-account with a fixed USDT loss per trade. All reported figures are **net**
of exchange fees, modelled slippage and funding. Anything that could not be
derived from data is marked `PENDING`. Full design notes, the parameter table,
assumptions/falsifiers and the log schema are in `DESIGN.md`; version history
is in `CHANGELOG.md`.

## 策略 / Strategy

The strategy bets that in an established uptrend with normal (not extreme)
volatility, a shallow pullback to the fast moving average that is bought back
on elevated volume tends to continue in the trend direction. It is a
rule-based **EMA + ADX trend-following** system (not mean reversion) because
the mandated regime filter — ADX(14) on 1H above a strength threshold — by
construction selects trending bars, and fading moves inside such a regime
would fight the filter. Mean reversion would need the opposite regime
(low ADX), which this Playbook deliberately sits out.

Regimes (1H bars):

| Regime | Definition | Traded? |
| --- | --- | --- |
| `range` | ADX(14) < 25 | No |
| `trend_lowvol` | ADX ≥ 25 and ATR(14)/close percentile over the last 720 bars (30 days) < 20 | No |
| `trend_blowoff` | ADX ≥ 25 and ATR percentile > 90 | No |
| `trend_tradable` | ADX ≥ 25 and 20 ≤ ATR percentile ≤ 90 | Yes |

There is no AI/LLM layer in v1: the sandbox forbids `getagent.llm` in
replayable logic, so the rule set is authoritative and `backtest_support: full`
is honest. A future LLM veto (live-only, defaulting to NO TRADE on invalid
output) would be a separate version with its own evidence.

## 开仓 / Entry

At each 1H close, for each symbol, a **long** entry is triggered when all of
the following hold:

1. Regime is `trend_tradable` and `+DI > -DI`.
2. `EMA(20) > EMA(50)`.
3. Pullback-resume: previous close ≤ previous EMA(20) and current close > EMA(20).
4. Volume ≥ 1.5× the average of the previous 20 bars.
5. The bar close is not within ±15 minutes of a funding settlement (00:00 / 08:00 / 16:00 UTC).
6. The latest funding rate is not above +0.03% per 8h (longs would pay).
7. No open or pending position on the symbol, fewer than 3 positions open, no
   daily pause/stop or halt active.

The order is a **limit at the signal close** (at or better than signal price)
with an exchange-side stop loss and take profit attached to the order itself,
and it is cancelled if unfilled after 4 hours. Shorts are **disabled** in v1
(see `DESIGN.md` for the short-side research run and its outcome).

Position size: `qty = 15 USDT / (1.5 × ATR(14))`, floored to the contract size
step; the required isolated margin (`notional / 5`) is capped at
`margin_budget / 3` per position and the size is reduced if the cap binds, so
leverage never exceeds 5×.

## 平仓 / Exit

* **Stop loss**: `entry − 1.5 × ATR(14)` (stop-market, attached to the entry).
* **Take profit**: fixed `2R` = `entry + 3 × ATR(14)` (limit, attached to the
  entry). Fixed 2R was chosen over "50% at 1.5R + ATR trail" because it is the
  only variant that can be fully preset exchange-side on the entry order
  (no post-fill gap), it is exactly replayable on 1H bars, and the 8h time
  stop leaves little room for a trailing leg to add value.
* **Time stop**: 8 hours after the fill (market order).
* **Daily rules** (UTC, realised PnL): pause new entries at −30 USDT; at −40
  USDT cancel pending entries, flatten Playbook-opened positions and block
  entries for the rest of the day. In live mode the Playbook alerts and asks
  you to stop it in the GetAgent page — code is not allowed to stop itself.
* **Halt**: 5 consecutive losses → entries blocked for 24h (replay) / alert
  and block (live). Stale data (newest closed bar older than 2 intervals, or
  fetch slower than 60s) → no decision for that symbol. Any position in the
  sub-account the Playbook did not open → alert only, never touched.

## 参数 / Parameters

User-tunable (also in `user_config_schema`):

| Parameter | Default | Effect of raising it |
| --- | --- | --- |
| `trading_symbols` | BTCUSDT, ETHUSDT, SOLUSDT | More symbols = more, more diversified setups |
| `margin_budget` | 1500 USDT | Larger isolated-margin cap; return % denominator |
| `leverage` | 5 (hard max 5) | Less margin per position; **does not** change USDT risk |
| `risk_per_trade_usdt` | 15 | Larger positions, larger daily swings |

Fixed internal parameters (ADX/ATR periods, thresholds, EMA lengths, TTL, time
stop, daily limits, halt rules, funding gates) are listed with rationale and
source in `DESIGN.md`. v1 is frozen; later versions change one parameter at a
time with a written prediction (see `CHANGELOG.md`).

## 回测 / Backtest and validation

The historical run fetches ~2 years of 1H Bitget bars plus funding history,
replays them through the managed Nautilus engine with maker 0.02% / taker
0.06% fees, and then computes from the real fills:

* net expectancy (R), win rate, profit factor, max drawdown, Sharpe
  (daily PnL on the margin budget, annualised);
* anchored walk-forward folds (12 months train / 3 months test, parameters
  frozen — no per-fold fitting), per fold and out-of-sample aggregate;
* cost sensitivity at 0×/1×/2× of all modelled costs; negative expectancy at
  2× costs → configuration **REJECTED**;
* no verdict is issued on fewer than 30 trades.

Return % is reported on a strategy basis (`net PnL / margin_budget`); the
engine's account-basis numbers (100 000 USDT replay balance) are kept
separately as `account_*`. Latest sandbox results: see `DESIGN.md` →
"Backtest results".

Forward (live) criteria, fixed in advance: **PASS** = profit factor ≥ 1.3 and
Sharpe ≥ 0.5 after ≥ 30 live trades; **FAIL** = profit factor ≤ 1.1 → stop.

## 风险 / Risk

* Trend filters lag; a range that briefly looks like a trend produces a run of
  stops. The daily and consecutive-loss limits bound, but do not remove, this.
* Limit entries assume a fill when price trades through the limit; live fill
  rates can be lower and adverse selection higher (filled only when price keeps
  falling).
* Stop-market exits can slip beyond 1 tick in fast markets or gaps; the model
  charges only 1 tick of slippage on taker fills.
* Funding is modelled from historical 8h rates; live funding can spike.
* Long-only: in prolonged bear markets the Playbook will mostly sit out.
* Fee tier: public contract config shows maker 0.02% / taker 0.06%. Your
  account-specific tier is `PENDING (verify in account)`.
* Historical results are not a guarantee; do not fund this with capital you
  cannot afford to lose.
