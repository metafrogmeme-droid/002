# Data Reference Catalog

This catalog is the self-contained runtime reference for `getagent.data`.
All links in this directory stay inside the packaged runtime skill so an
agent can inspect DataSDK endpoint contracts without depending on the
Playbook creator source tree.

## Read order

1. Use the domain files below for exact signatures, defaults, enums,
   and parameter details.

## Domain index

| Domain | File | Endpoints |
|---|---|---:|
| `Coverage` | [coverage.md](coverage.md) | 3 |
| `arxiv` | [arxiv.md](arxiv.md) | 1 |
| `commodity` | [commodity.md](commodity.md) | 7 |
| `crypto` | [crypto.md](crypto.md) | 111 |
| `currency` | [currency.md](currency.md) | 4 |
| `derivatives` | [derivatives.md](derivatives.md) | 8 |
| `economy` | [economy.md](economy.md) | 42 |
| `equity` | [equity.md](equity.md) | 74 |
| `etf` | [etf.md](etf.md) | 12 |
| `famafrench` | [famafrench.md](famafrench.md) | 6 |
| `fixedincome` | [fixedincome.md](fixedincome.md) | 25 |
| `imf_utils` | [imf_utils.md](imf_utils.md) | 8 |
| `index` | [index.md](index.md) | 7 |
| `news` | [news.md](news.md) | 3 |
| `regulators` | [regulators.md](regulators.md) | 10 |
| `sentiment` | [sentiment.md](sentiment.md) | 11 |
| `uscongress` | [uscongress.md](uscongress.md) | 4 |
| `web_search` | [web_search.md](web_search.md) | 2 |
| `wikipedia` | [wikipedia.md](wikipedia.md) | 3 |

## Notes

- **Coin/stock screening, selection, or cross-sectional scan tasks** ("选币",
  "选股", "which symbols satisfy...", building a `selection_basket` that
  ranks/filters a universe) → read
  [`crypto-screener.md`](crypto-screener.md) directly instead of `crypto.md`.
  It documents `crypto.market.screener.scan` end-to-end: the field-naming
  convention (`technical_{interval}.` prefix rules), the full filter
  operation table, and the complete factor catalogue (technical indicators,
  composite tag arrays, funding/derivatives, Crypto metrics).
- Status rows are generated from the same availability registry used by
  the SDK tests and runtime metadata.
- Playbook sandboxes are expected to support the complete generated
  `getagent.data` namespace. Do not treat data endpoints as having a
  separate sandbox allowlist.
- Data domains are not the same as tradable-symbol namespaces. `equity.*`,
  `commodity.*`, and `economy.*` endpoints may use tickers, FIGIs, ISINs, or
  series IDs for research. A Playbook can trade only after mapping the idea to a
  supported Bitget exchange-native pair such as `RAAPLUSDT`, `AAPLUSDT`, or
  `XAUUSDT`.
- The mandatory tradable-symbol discovery path is Bitget's official public
  config APIs during authoring: `/api/v2/spot/public/symbols` for spot and
  `/api/v2/mix/market/contracts?productType=USDT-FUTURES` for USDT contracts.
  `crypto.market` is runtime market metadata, not a substitute for that
  authoring gate. Use CCXT-style symbols only when an endpoint explicitly
  documents that namespace; use confirmed exchange-native IDs everywhere else.
- For backtests, verify the endpoint returns the fields and time axis your
  strategy needs before declaring those fields in `backtest.yaml`.
- For credit-spread and macro-risk strategies, start with
  `fixedincome.bond_indices(index_type="oas", ...)`. The supported IG OAS proxy
  is `category="us", index="corporate"`; the supported HY OAS proxy is
  `category="high_yield", index="us"`. Use `economy.fred_series` only
  when you already have a documented FRED series ID, and do not present these
  OAS proxies as exact CDX IG/HY data.
- Time ranges use millisecond Unix-epoch `start_time` / `end_time` and the
  canonical datetime column is `time`. The SDK still accepts the legacy
  `start_date` / `end_date` parameters (and exposes a derived `date` field)
  with a `DeprecationWarning` until upstream removes the legacy surface.
  Call `data.to_dataframe(bars)` without `datetime_index` to let the SDK
  pick the canonical column.
