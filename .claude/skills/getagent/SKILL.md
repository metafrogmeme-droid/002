---
name: getagent
description: >-
  Authors, validates, uploads, backtests, and publishes GetAgent quantitative
  trading Playbooks, and provides GetAgent page links for user-controlled
  subscription management. Use when the user asks to create, review, fix,
  validate, upload, run, publish, subscribe to, or stop a trading strategy or
  selection basket/callout Playbook; mentions strategy backtesting, publishing,
  uploading, callout, selection basket, BTC EMA, or GetAgent; or provides
  existing Playbook package code for review.
compatibility: >-
  Designed for Claude Code, Codex, Cursor, and other agents that support
  Agent Skills. Requires Python 3.11+ for local static validation and network
  access to the GetAgent Playbook control-plane API for upload/run/publish.
metadata:
  author: getagent
  version: v0.6.2
---

# GetAgent Playbook Creator

This skill helps an agent turn a strategy idea into a GetAgent Playbook package,
validate it locally, upload it to GetAgent Cloud, run sandbox backtests or
evaluations, publish accepted versions, and direct users to GetAgent for any
subscription start or stop action.

Local authoring is **not** local SDK execution. User machines can only run
static package checks and call the Playbook control-plane APIs. `getagent.data`,
`getagent.trade`, `getagent.llm`, `getagent.backtest`, and `getagent.runtime`
are sandbox-preinstalled SDK modules. Use the bundled references to write code
against their public shape, but do not try to execute data, trade, or LLM SDK
calls on the user's machine.

## First Use

On first use each session:

1. If available, run `scripts/version_check.sh`. Show update instructions only
   when it prints a message.
2. Read `references/package-schema.md` before creating or modifying a package.
3. Read `references/sdk.md` before writing `src/**` strategy code.
4. Read the exact API reference under `references/api/` before upload, run,
   publish, subscription-link, or list operations.

## User Opening

When the user asks generally how to start, use this stable opening. Do not ask
for credentials in the opening.

```text
The GetAgent Playbook assistant is ready.

I can help you take a strategy idea through the full Playbook workflow:

- Describe a strategy in natural language, and I can generate runnable code
- Provide existing code, and I can review, fix, and improve it
- I will validate the package locally before upload
- After validation, I can upload it and start a sandbox run when appropriate
- After the run, I can explain return, drawdown, win rate, trade count, and risk
- Then we can iterate on the next version

How would you like to start?

A. Run a demo to see the workflow first (BTC EMA follow-trade strategy)
B. I have a rough direction; help me build a minimal skeleton
C. I will describe my strategy idea directly
D. I already have strategy code; review and fix it before running validation
```

For option A, do not author from scratch: use the bundled runnable demo at
`examples/btc-ema-cross-demo/` (read its `README.md` first), validate it
locally, then walk the user through upload and a sandbox run.

## Default Workflow

1. Clarify only missing strategy requirements that block authoring. Ask one
   concrete question at a time.
2. Before writing any strategy package, resolve each user-requested tradable
   asset through Bitget's official public symbol/contract config APIs. Confirm
   whether it is tradable and record the exact exchange-native symbol that must
   be used in `manifest.yaml`, `backtest.yaml`, data calls, trade calls, and
   emitted signals.
3. Scaffold the package shape from `references/package-schema.md`.
   If the user asks for a callout / selection basket, read
   `references/selection-basket.md` before writing `manifest.yaml` or
   `src/main.py`.
4. Write strategy code against `getagent.*` imports only, plus allowed
   scientific/runtime packages documented in the schema.
5. Validate locally (requires Python 3.11+; install PyYAML once with
   `pip install pyyaml` if missing — without it the validator falls back to a
   weaker parser):

   ```bash
   python3 scripts/validate.py ./my-strategy/
   ```

   If validation fails, fix every reported issue and re-run until it prints
   `Validation PASSED`. Never upload a package that fails local validation.
6. Ask for the user's Bitget OpenAPI `ACCESS-KEY` only before the first
   authenticated upload/run/publish/subscription-link call. Never write credentials to disk.
   Read the anonymous install id with `python3 scripts/telemetry.py install-id`
   and include it as `X-GetAgent-Install-Id` on those calls when non-empty.
7. Upload the package through the documented control-plane API; uploads are
   temporary iteration artifacts until confirmed.
8. Run a sandbox evaluation before publish when the package supports backtests.
9. Read results back in plain language before proposing publish or iteration.
10. When the user accepts the final package, confirm the latest temporary as a
   draft. Publish only after explicit user intent.

## Reference Map

- Package contract: `references/package-schema.md`
- SDK overview: `references/sdk.md`
- Sandbox runtime and blocked imports: `references/sandbox-runtime.md`
- Selection basket / callout Playbooks: `references/selection-basket.md`
- Strategy Bot orchestration lifecycle:
  `references/strategy-bot-orchestration.md`
- Grid-specific parameters and Trade API mapping:
  `references/grid-playbook.md`
- Backtest engine behavior: `references/backtest-engine.md`
- Control-plane APIs: `references/api/index.md`
- Data SDK domain index: `references/sdk/data/catalog.md`; high-frequency
  domain files: `references/sdk/data/crypto.md`,
  `references/sdk/data/equity.md`, `references/sdk/data/economy.md`,
  `references/sdk/data/derivatives.md` (other domains via the catalog)
- Trade SDK: `references/sdk/trade/patterns.md`
- Grid Trade SDK: `references/sdk/trade/grid.md`
- Backtest SDK: `references/sdk/backtest/catalog.md`
- Runtime SDK: `references/sdk/runtime/catalog.md`
- LLM SDK: `references/sdk/llm/catalog.md`
- Runnable demo package: `examples/btc-ema-cross-demo/` (BTC EMA follow-trade;
  used by option A of the opening)
- Selection basket demo package: `examples/selection-basket-demo/`

## Backtest Output Pitfalls

Before writing `main_backtest.py`, read `references/backtest-engine.md` §Backtest
Output Contract. The three most common publish failures are:

1. **Missing publishable real equity curve** — no `output/equity_curve.csv`, and the
   JSON report is too large for the Runner to read.
2. **Missing real evidence** — the run did not produce a real
   `output/equity_curve.csv` or platform-readable historical evidence. Do not
   fabricate dense points or hand-written summaries.
3. **Incorrect `total_return_pct` display** — `result.raw` has engine-level
   summary fields flattened to the top level. The backend merge uses the report
   as BASE (`setdefault` from signal cannot override). You must overwrite
   `raw["net_pnl"]` and `raw["total_return_pct"]` with correct absolute values
   before writing `backtest_report.json`.

## Data SDK Constraints

Rules that apply every time `getagent.data` is used in Playbook code.

### Before writing any data call

1. Read `references/sdk.md` §`getagent.data` read order. Follow its links to
   `references/sdk/data/catalog.md` (domain table), then open the matching
   domain file (e.g. `references/sdk/data/crypto.md`).
2. Locate the exact endpoint section. If it has a **bitget_data provider**
   table, use that for parameters and response fields. Only use tables
   titled **Query parameters (other providers)** when not calling
   `bitget_data`. Never mix the two.
3. Never invent endpoint names, namespaces, or keyword arguments by guessing
   from plausible names. If the needed capability is absent, report missing
   coverage instead of falling back to a direct HTTP client.

### Provider selection

- **Always prefer `provider="bitget_data"`** when the endpoint supports a
  `provider` parameter. Bitget-native data has the best coverage for the
  tradable symbols used in Playbooks and is the canonical source for
  backtesting on Bitget markets.
- Fall back to another documented provider (e.g. `"binance"`, `"coingecko"`)
  only when `bitget_data` does not cover the requested symbol or data type.
  State the fallback reason clearly in a code comment.
- For THS-backed US-equity fundamentals, ownership, analyst estimates, ETF
  data, and ETF fund flows, use the existing `equity.*` and `etf.*` endpoints
  with `provider="bitget_data"`. Read the **bitget_data provider** query and
  response tables in `references/sdk/data/equity.md` or `etf.md`. Do not copy
  `period`, `fiscal_year`, `ttm`, `start_time`, `date`, or other-provider
  field names. Public `symbol`/`limit`/`page` are correct; the platform maps
  `symbol` to upstream `sec_code` and `limit` to `size`.
- Never pass a `provider` value that is not listed in the endpoint's
  documented enum. If no provider is documented for an endpoint, omit the
  parameter entirely.

### Credit spread and macro risk data

For credit-spread-driven strategies, use the SDK's supported fixed-income
surface before declaring missing data coverage:

- Use `data.fixedincome.bond_indices(index_type="oas", category="us",
  index="corporate")` as the Investment Grade OAS proxy.
- Use `data.fixedincome.bond_indices(index_type="oas", category="high_yield",
  index="us")` as the High Yield OAS proxy.
- Response rows expose `date`, `symbol`, `value`, and `title`; treat `value` as
  the spread level for the requested OAS index and compute weekly bp changes in
  strategy code from real returned rows.
- Do not claim this is exact CDX IG/HY data. The current SDK has no exact
  `CDX` endpoint name. If the user explicitly requires CDX rather than OAS
  proxy data, state that gap clearly.
- If a strategy needs a specific known FRED macro/credit series ID, use
  `data.economy.fred_series(symbol="...")`. Do not guess FRED symbols; use
  `data.economy.fred_search(...)` or documented series IDs first.

### Tradable assets and symbol format

Do not infer product type from asset class. Crypto, RWA stock tokens, and RWA
metals can all be normal `trade_strategy` packages when the target Bitget spot
or contract market is tradable, the data path returns replayable bars, and the
strategy satisfies the normal follow-trade/backtest rules. Use
`selection_basket` only when the product outcome is a watchlist/callout basket.
For newly authored packages, include product copy in `display_name_i18n` and
`description_i18n` for `en`, `zh`, `zh-tw`, `es`, `ja`, and `vi`. For
selection baskets, keep asset `name` values canonical and non-localized; do not
emit `name_i18n`. Basket rows must include `thesis_i18n` and `risk_i18n` for
the same locales; the platform selects thesis/risk language from
`X-Language-Id` and still returns plain text fields.

There are **three separate symbol namespaces**:

**Exchange-native tradable pair** — e.g. `"BTCUSDT"`, `"RAAPLUSDT"`,
`"AAPLUSDT"`, `"XAUUSDT"` (no slash, no colon). Use this format everywhere the
package refers to a tradable instrument:

- `manifest.trading_symbols`
- `strategy_config.trading_symbols`
- `backtest.yaml` instrument `raw_symbol` / `symbol`
- emitted signal `symbol`
- Trade SDK calls
- price / OHLCV / derivatives data calls such as `crypto.futures.kline`,
  `crypto.spot.kline`, funding, taker volume, open interest, tickers, and trades

> **Exception — `equity.price.historical` and `equity.price.quote` with
> `provider="bitget_data"`**: pass a bare uppercase US ticker (`"AAPL"`, not
> `"AAPLUSDT"`).

For Bitget RWA markets, spot symbols use an `R` prefix before the asset code
(for example `RAAPLUSDT`, `RTSLAUSDT`). RWA perpetual/contract symbols use the
base asset code without the `R` prefix (for example `AAPLUSDT`, `TSLAUSDT`,
`XAUUSDT`).

Before writing any strategy, check every user-requested tradable asset against
Bitget's official public market configuration during authoring. This lookup
decides whether the asset is tradable and what exact exchange-native symbol the
package must use. It is performed by the agent/Cursor environment, not by
Playbook runtime source code:

```bash
# Spot symbols; omit symbol to list all spot pairs.
curl "https://api.bitget.com/api/v2/spot/public/symbols?symbol=RAAPLUSDT"

# USDT futures/contracts; omit symbol to list all USDT-FUTURES contracts.
curl "https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES&symbol=AAPLUSDT"
```

- Spot response rows are market-level tradable when `code == "00000"` and
  `data[].status == "online"`.
- Contract response rows are market-level tradable when `code == "00000"` and
  `data[].symbolStatus == "normal"`.
- RWA contract rows may include `isRwa: "YES"`; for example Bitget's public
  contract config exposes `AAPLUSDT` and `XAUUSDT` as RWA USDT futures.
- The public Bitget endpoint proves exchange support. Use
  `trade.market.check_symbol_support([...])` separately when code needs to
  verify the current bound account/subaccount can trade that exact symbol.
- Exchange support does not prove historical replay support. Before setting
  `backtest_support: full`, probe the managed kline path for each declared
  symbol with `exchange="bitget"`, the intended interval, and the intended
  backtest lookback/window. Require HTTP 200, valid JSON, and non-empty rows.
  Treat 204/empty body and 4xx as not replayable for official backtest.
- Never import `requests`, `httpx`, `urllib`, or exchange clients in Playbook
  `src/**` to do this lookup. Resolve symbols while authoring, then write the
  confirmed exchange-native symbol into the package.

**CCXT unified market symbol** — e.g. `"BTC/USDT"` (spot),
`"BTC/USDT:USDT"` or `"AAPL/USDT:USDT"` (linear perpetual). Use this only when
filtering `crypto.market` metadata. If the response contains `exchange_id`, use
that exchange-native value for the package contract and all tradable calls. Do
not put unified symbols in `manifest.trading_symbols` or `backtest.yaml`.

**Non-trading research identifiers** — e.g. equity tickers, FIGIs, ISINs,
CoinGecko IDs, or macro series IDs. Use these only with their documented
research endpoints (`equity.*`, `commodity.*`, `economy.*`, CoinGecko-style
crypto endpoints). They are not tradable symbols until mapped to a supported
Bitget exchange-native pair.

**Runtime market metadata is not the authoring gate.** After the official
Bitget public config lookup has confirmed the exchange-native symbol,
`data.crypto.market(...)` may be used as documented market metadata in strategy
logic. Do not use it as a substitute for the mandatory authoring-time Bitget
symbol/contract config lookup, and do not put its CCXT unified `symbol` output
into the package contract.

- Do not mix namespaces. Do not pass `"BTC/USDT:USDT"` to `kline`, Trade SDK,
  `manifest.trading_symbols`, or `backtest.yaml`.
- Do not pass `"BTCUSDT"` to `crypto.market(symbol=...)`; use the endpoint's
  documented market metadata format there.
- When a parameter note is ambiguous (just says "Symbol to get data for"),
  default to exchange-native format for `crypto.futures.*`, `crypto.spot.*`, and
  all trade/backtest package contracts.

### Kline exchange resolution

`crypto.futures.kline` and `crypto.spot.kline` both accept an `exchange`
parameter that defaults to `"binance"`. Not every symbol is listed on every
exchange — passing an unsupported exchange returns an empty or failed response.
Before writing any kline call, use `data.crypto.market` to confirm which
exchanges carry the target symbol:

1. Call `data.crypto.market` with symbol and `market_type`
   to retrieve exchange availability:

   ```python
   # For a futures/perpetual kline probe
   markets = data.crypto.market(
       symbol="BTC/USDT",        # CCXT unified format — NOT exchange-native
       market_type="perpetual",  # or "spot" for crypto.spot.kline
       exchange="binance",       # optional: narrow to one exchange
   )
   df = data.to_dataframe(markets)
   # df columns: exchange, symbol, active, exchange_id, market_type, …
   ```

2. Select an exchange where `active` is `True` (ccxt provider) or `status`
   is `"online"` (bitget_data provider). Record `exchange_id` as the
   exchange-native symbol for the kline call and `exchange` as the exchange
   identifier.

3. Pass the confirmed values to the kline call:

   ```python
   bars = data.crypto.futures.kline(
       symbol="BTCUSDT",    # exchange_id from market response
       interval="1h",
       exchange="binance",  # exchange from market response
   )
   ```

4. If no active row exists for the intended exchange, fall back to the next
   available exchange returned by `crypto.market`, or report that the symbol
   is not supported on any exchange rather than guessing a default.

- `crypto.market` uses CCXT unified symbol format (`"BTC/USDT"`,
  `"BTC/USDT:USDT"`); kline endpoints use exchange-native format
  (`"BTCUSDT"`). Never mix these two namespaces.
- For multi-symbol strategies, build a lookup from the `crypto.market`
  response — mapping each symbol to its confirmed exchange and
  exchange-native ID — before entering the kline loop.
- This probe applies both at authoring time (agent confirming parameters
  before writing code) and as a runtime pattern when symbol availability
  must be resolved dynamically.

### Parameter compliance

- Pass only parameters that appear in the endpoint's documented signature.
  Never add undocumented kwargs.
- Required parameters (marked `yes` in the table) must always be supplied.
  Optional parameters with a documented default may be omitted.
- Respect documented enum values exactly (e.g. `interval` must be one of
  `5m`, `15m`, `1h`, `4h`, `1d` for kline endpoints; `market_type` must be
  one of `spot`, `perpetual`, `future`, `option`).
- For paginated endpoints, respect the documented maximum `size`/`limit`
  (e.g. `size ≤ 200` for `crypto.market`, `limit ≤ 1000` for klines).
  Loop over pages when more data is needed rather than requesting beyond
  the cap.

### Time ranges

- Use `start_time` / `end_time` (millisecond Unix-epoch integers) in
  preference to the deprecated `start_date` / `end_date` string params.
- `crypto.futures.kline` and `crypto.spot.kline` cap **each request** at
  **90 days** of data. This is a per-fetch API limit, not a backtest window
  restriction — when the replay window is longer, fetch multiple 90-day
  chunks and concatenate them.
- The raw kline feed includes the **currently-forming candle**; the SDK
  drops it by default (`closed_only=True`) so the last returned bar is
  stable. Pass `closed_only=False` only when a live partial bar is
  explicitly wanted — never trade on its close. Live paths must also assert
  freshness before emitting: refuse to act when
  `now - (last_bar_open + interval) > 2 x interval`.
- The canonical datetime column in SDK responses is `time`. Call
  `data.to_dataframe(bars)` without `datetime_index` to let the SDK pick it;
  only override when the endpoint's response fields table names a different
  time column (e.g. `date`).

### Response handling

- Always convert `OBBject` responses with `data.to_dataframe()`,
  `data.to_dict()`, or `data.to_records()` before accessing individual fields.
- Reference only field names that appear in the endpoint's **Response fields**
  table. Never guess a field name from context.
- Fields documented as `string` from market info endpoints (e.g.
  `min_order_qty`, `price_precision`) are decimal strings, not floats.
  Cast explicitly when arithmetic is needed.
- Endpoints that return a context-only snapshot (no `time` column) cannot
  be aligned into a replay feature frame. Use them as decision context only
  and do not declare their fields in `backtest.yaml.data_requirements`.

### Endpoint discovery

- When in doubt which endpoint to use, read `catalog.md` for the domain
  table, then read the domain file. Do not rely on memory or path guessing.
- Domain files are large (crypto.md ≈ 4000 lines). Jump to an endpoint
  section with grep instead of reading the whole file, e.g.
  `grep -n "crypto.futures.funding_rate" references/sdk/data/crypto.md`,
  then read that section's parameter and response tables.
- `data.coverage.commands()` lists every available endpoint at runtime.
  Use it programmatically if the domain file and catalog are insufficient.
- CoinGecko-based endpoints (`crypto.coin_info`, `crypto.coin_history`, etc.)
  accept a **CoinGecko coin ID** (e.g. `"bitcoin"`), not a trading-pair symbol.
  Futures/spot kline endpoints accept trading-pair symbols. These are
  different namespaces — do not mix them.

## Hard Boundaries

- Do not tell users to install or execute the private GetAgent SDK locally.
- Do not import or recommend direct clients such as `requests`, `httpx`,
  `ccxt`, `trade_sdk`, `yfinance`, `akshare`, or exchange clients in Playbook
  source code.
- Do not use `getagent.llm` for replayable historical logic. LLM-backed
  strategies are live/evaluation-only and require `runtime_profile:
  llm_bounded` with `backtest_support: none`.
- Asset class alone never decides `output_kind`. For callout / selection basket
  Playbooks, set `output_kind: selection_basket` and follow
  `references/selection-basket.md`; never add follow-trade or historical
  backtest claims to that package. For grid trading Playbooks, set
  `output_kind: grid` with `execution_mode: grid` and follow
  `references/grid-playbook.md`. For tradable RWA/equity/metal markets, use a
  normal `trade_strategy` contract instead.
- Do not call trade mutation APIs outside the callback passed to
  `runtime.emit_signal_or_follow(...)`. The runtime's live trade-permission
  gate is authoritative. Grid Playbooks must route every `trade.grid` mutation through the
  `execute=` callback of `runtime.execute_strategy_bot_action(...)` and must
  never call `trade.contract`, `trade.spot`, or `trade.account` mutations.
  The same public methods support Spot plus `long`, `short`, and `neutral`
  contract Grid; pass `grid_type="neutral"` to select neutral routing. Do not
  invent separate neutral or Martingale methods.
  Direct `emit_decision(create/modify/shutdown)` does not execute a bot action.
  Every Grid cycle must restore running bots through
  `runtime.list_strategy_bots(status="running")`; query or occupied-funds
  failures must stop creation rather than fall back to local state.
- For `backtest_support: full`, never pass `provider=...`, and ensure any
  `data_requirements.required_bar_fields` are actually built and referenced in
  `src/**`. The `execution.start` / `execution.end` replay window is entirely
  the author's choice — the platform never polices window presence, length,
  or recency; the only hard rule is that evidence must be real, never
  fabricated.
- Keep symbols consistent across `manifest.trading_symbols`, display text,
  README, `backtest.yaml` instruments, data calls, and emitted signals. If the
  submitted symbol is a typo or unavailable and you replace it with a supported
  symbol, rename the package/title and explain the correction in README and the
  final summary.
- In Nautilus strategy code, call `self.cancel_all_orders(instrument_id)` and
  `self.close_all_positions(instrument_id)` with an explicit instrument id.
- Never call an API or tool that enables, disables, starts, stops, subscribes,
  unsubscribes, terminates, or flattens a Playbook instance. These operations
  can affect real funds and require the user to act in the GetAgent page.
- When the user asks for one of those operations, read
  `references/api/subscription-links.md`, generate the appropriate short-lived
  link, and return it as a clickable link. Do not open the link, follow the
  redirect, or claim the requested operation completed.
- Do not publish without showing the endpoint and masked `ACCESS-KEY` prefix
  and getting the user's intent for that operation.

## Post-Backtest Response

After every successful sandbox run, summarize the result before any next action:

- strategy-basis `total_return_pct`
- `max_drawdown_pct`
- `win_rate` paired with `total_trades`
- finite `sharpe_ratio` only when trades exist
- the main risk revealed by the run

Then offer 2-3 concrete next moves: tune a declared parameter, change symbol or
timeframe within schema, revise entry/exit logic in a new version, or publish
only if evidence is acceptable.
