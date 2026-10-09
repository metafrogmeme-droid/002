# USDT-M Trend v1 — EMA-ADX Long Only

Long-only hourly trend Playbook for BTCUSDT, ETHUSDT and SOLUSDT
USDT-M perpetuals, run in an isolated sub-account. It optimises for
verifiable positive **net** expectancy, not displayed ROI. Any value
that cannot be derived from data is marked PENDING — no performance
figures are invented anywhere in this package.

## 策略 / Strategy

The Playbook bets that confirmed hourly trends on three major USDT-M
perpetuals continue long enough to pay a fixed risk multiple. A
regime filter (ADX(14) trend strength plus an ATR(14)/price
percentile rank) decides whether the market is tradable at all:
strong-trend regimes are traded, weak or dormant regimes are sat out.
Mean reversion was rejected because it conflicts with the ADX-high
regime filter and with the trend-length time stop. An optional AI
overlay hook exists in the design but is NOT wired: any invalid or
missing model output resolves to NO TRADE, and direction is never
defaulted.

Traded regimes: ADX(14) above threshold with ATR percentile rank in a
normal-to-elevated band (trend present, market alive). Sat-out
regimes: ADX below threshold (chop), ATR percentile rank in the
bottom decile (dormant), funding blackout windows, and funding firmly
against longs.

## 开仓 / Entry

One trigger only, evaluated on closed 1H bars per symbol:

1. Regime gate passes (ADX(14) > 20, ATR% rank >= 10th percentile).
2. Fresh EMA(20) cross above EMA(50) on the 1H timeframe.
3. Bar volume >= 1.5x the prior 20-bar average.
4. No funding blackout (±15 min around 00:00/08:00/16:00 UTC) and
   latest funding rate <= 0.03%/8h (longs pay positive funding).
5. Portfolio gates pass (see Risk). Shorts are disabled: there is no
   short trigger unless a separate short-side test later shows >= 30
   trades with positive net expectancy.

Orders are limit entries at the signal close with the stop attached
as an exchange-side TPSL pair. Unfilled entries are cancelled after
4 hours. AI layer invalid or missing -> NO TRADE, logged.

## 平仓 / Exit

- Stop: 1.5x ATR(14) below entry, attached to the entry order.
- Take profit: fixed 2R (twice the stop distance), full close.
  Chosen over partial-plus-trail for simplicity and auditability:
  one exit price per trade keeps fills, fees and expectancy math
  exactly reconcilable.
- Time stop: flat after 8 hourly bars without touching stop or target.
- Opposite crosses never reverse; they are ignored while flat and
  the time stop handles stale longs.

## 风险 / Risk

- Fixed loss per trade: 15 USDT. Size = 15 / stop distance, floored
  to the instrument size increment, minimum 5 USDT notional.
- Isolated margin; leverage hard cap 5x (deployment prerequisite:
  sub-account set to isolated mode before activation).
- Max 3 concurrent positions, max 1 per symbol.
- Daily realised guard: pause new entries at -30 USDT, stop the
  Playbook at -40 USDT (live: equity-snapshot proxy, see Assumptions).
- Halt on 5 consecutive losses; halt when market data is stale
  (>60 s beyond the expected bar close); halt with alert-only when
  any position exists that the Playbook did not open (never touched).
- Costs: taker 0.06% / maker 0.02% (matches current Bitget
  USDT-FUTURES tier for these symbols — re-verify at activation),
  1-tick slippage assumed live, funding charged on held positions.
  All reported results are net of modelled costs.

## Parameters

| name | value | rationale | source |
|---|---|---|---|
| trading_symbols | BTCUSDT, ETHUSDT, SOLUSDT | majors only; liquid USDT-M perps | data (Bitget contracts API: symbolStatus normal) |
| entry_timeframe | 1H | trend signal vs noise trade-off; matches ADX/ATR(14) calibration | default |
| ema_fast / ema_slow | 20 / 50 | responsive cross without minute-noise whipsaw | default |
| adx_period / adx_threshold | 14 / 20 | standard trend-strength read; trade only confirmed trends | default |
| atr_period / atr_stop_mult | 14 / 1.5 | volatility-scaled stop; 15 USDT risk maps to sane size on majors | default |
| atr_min_rank | 0.10 | sit out dormant bottom-decile markets | default |
| volume_lookback / volume_mult | 20 / 1.5 | confirm participation; refuse thin crosses | default |
| tp_r_mult | 2.0 (fixed 2R, full close) | auditability over trail optimisation | default |
| risk_per_trade_usdt | 15 | fixed-loss sizing; daily stops are 2-2.7x one loss | default |
| leverage | 5 (hard cap) | venue-compatible sizing headroom | default |
| margin_budget | 300 USDT | per-strategy return denominator; covers 3 concurrent margins | default |
| max_positions / max_per_symbol | 3 / 1 | concentration limit; one idea per symbol | default |
| daily_pause_usdt / daily_stop_usdt | -30 / -40 | pause at 2R day, stop at ~2.7R day | default |
| consec_loss_halt | 5 | halt on regime-break streak | default |
| entry_ttl_hours | 4 | stale limit entries cancelled | default |
| time_stop_hours | 8 (trend) | free margin from drifters | default |
| funding_guard_pct | 0.03 | skip longs paying adverse funding | default |
| funding_blackout_min | 15 | no entries ±15 min around 00/08/16 UTC funding | default |
| taker_fee / maker_fee | 0.0006 / 0.0002 | matches Bitget USDT-FUTURES schedule seen 2026-10-09 | data (re-verify tier at activation) |
| slippage_ticks | 1 | conservative live fill assumption | default |
| exchange symbols | BTCUSDT/ETHUSDT/SOLUSDT, USDT-FUTURES, symbolStatus normal, minTrade 5 USDT | exact native symbols confirmed | data (public contracts API) |
| backtest window | 2023-10-01 → 2025-10-01, 1H | >= 2y hourly with 2024-10-01 train/test split | default |
| forward PASS | PF >= 1.3 AND Sharpe >= 0.5 after >= 30 live trades | fixed activation gate | default |
| forward FAIL | PF <= 1.1 | stop the Playbook | default |
| win rate / avg R / expectancy / PF / max DD / Sharpe | PENDING | computed by sandbox run; never pre-filled | PENDING |
| 0x/1x/2x cost sensitivity | PENDING (code wired; run in sandbox) | reject on negative expectancy at 2x | PENDING |
| short-side test | PENDING (long-only until >= 30 short trades show positive net expectancy) | no shorts without evidence | PENDING |
| AI overlay output | PENDING (hook specified, fail-closed, unwired) | no direction defaulting | PENDING |
| isolated-margin venue proof | PENDING (verified at deployment) | account-level setting | PENDING |

## Flow

scan (fetch 1H bars per symbol, freshness check) -> filter (stale /
foreign-position / portfolio / funding-blackout / funding-guard /
regime ADX+ATR / volume gates) -> trigger (fresh EMA cross, long
only; AI invalid -> NO TRADE) -> order (limit + attached TPSL,
quantized to tick, 4h TTL) -> manage (exchange-side stop/target,
time stop, 1-per-symbol cap) -> exit (stop / 2R target / time stop /
halt) -> log (per-action row, see below).

## Backtest & validation (run in sandbox)

`src/main.py` historical path fetches >= 2y of 1H bars per symbol in
paged chunks, replays the full window plus a walk-forward
train (up to 2024-10-01) / test (from 2024-10-01) split, and repeats
the full window at 0x and 2x fees. It reports trades, win rate,
avg R (recomputed from closed positions against entry-bar ATR risk;
PENDING if position rows lack entry fields), net expectancy (R),
profit factor, max drawdown and Sharpe, all net. No verdict is taken
under 30 trades. Negative expectancy at 2x fees rejects the version.
v1 parameters are frozen at activation; each later version changes
ONE parameter with a written prediction recorded before running.

## Assumptions + falsification

- Replay uses market fills; live uses limit entries that may miss.
  Falsified if live fill rate diverges so far that live expectancy
  trails replay expectancy beyond fees + 1-tick slippage.
- Replay assumes funding gates pass; live enforces them, so live
  trades a subset of replay trades. Falsified if gate-skipped trades
  were the profit source (test slice degrades after enforcement).
- Backtest venue is the managed replay venue; live venue is Bitget
  USDT-FUTURES. Fee schedule equality is assumed, re-verified at
  activation.
- Live daily guard uses a day-open equity snapshot proxy (includes
  unrealized), which pauses earlier, never later, than realised-only
  accounting. Exchange-verified realised-PnL wiring is PENDING.
- Consecutive-loss halt is fully enforced in replay; live
  fill-attribution wiring is PENDING, so the live counter starts
  unconfirmed and must be verified in forward review.
- AI overlay is specified fail-closed and unwired; any future
  wiring needs `backtest_support: none` for that path or isolation
  as a non-replayable veto, plus `runtime_profile: llm_bounded`.

## Per-action log schema

Every live decision prints one JSON row:

```json
{"playbook_action_log": {"timestamp": "ISO-8601 UTC", "symbol": "BTCUSDT",
"side": "long|flat", "intended_price": "limit or -",
"filled_price": "fill, PENDING_FILL or -", "fees_usdt": "0 or PENDING",
"funding_usdt": "0", "reason_code": "ENTER_LONG_LIMIT | NO_TRADE_* | HALT_*"}}
```

Reason codes: ENTER_LONG_LIMIT, NO_TRADE_STALE_DATA,
NO_TRADE_FUNDING_BLACKOUT, NO_TRADE_FUNDING_GUARD,
NO_TRADE_FUNDING_UNKNOWN, NO_TRADE_REGIME_ADX,
NO_TRADE_REGIME_ATR_DEAD, NO_TRADE_NO_CROSS, NO_TRADE_VOLUME,
NO_TRADE_SIZING, NO_TRADE_MIN_NOTIONAL, NO_TRADE_SYMBOL_OCCUPIED,
NO_TRADE_INDICATOR_WARMUP, NO_TRADE_INSUFFICIENT_BARS,
NO_TRADE_AI_INVALID, NO_TRADE_DAILY_PAUSE, NO_TRADE_POSITION_QUERY_FAIL,
HALT_DAILY_STOP, HALT_CONSEC_LOSS, HALT_FOREIGN_POSITION.

## How to read backtest metrics

`total_return_pct` is the strategy-budget return
(`net_pnl / margin_budget`); `account_total_return_pct` is the raw
engine number. Judge win rate only beside trade count (>= 30 before
any verdict), expectancy in R beside profit factor, and Sharpe
beside max drawdown. A high return on few trades, or a passing
backtest that fails at 2x fees, is a rejection, not a tune-up.
