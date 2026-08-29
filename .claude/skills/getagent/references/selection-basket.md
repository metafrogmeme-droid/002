# Selection Basket Playbooks

Use this reference when authoring callout Playbooks that select a basket of
assets instead of emitting tradeable strategy signals.

## Contents

- [When To Use](#when-to-use)
- [Manifest Contract](#manifest-contract)
- [Output Contract](#output-contract)
- [LLM And Data Usage](#llm-and-data-usage)
- [Product Surface](#product-surface)
- [Authoring Checklist](#authoring-checklist)
- [Minimal Example](#minimal-example)

## When To Use

Use `output_kind: selection_basket` for Playbooks whose product outcome is
"these assets are worth watching today" rather than "open, close, or follow this
trade." Typical examples include callout baskets, watchlists, thematic picks, or
candidate lists that intentionally stop at ranking and commentary.

Do not choose this output kind merely because the assets are non-crypto. Bitget
RWA stock tokens and RWA metals can be normal `trade_strategy` packages when the
target spot/contract market is tradable and the strategy satisfies the normal
replay or follow-trade rules. Do not use this output kind for strategies that
place or follow orders. If the package can trade, it is a normal
`trade_strategy`.

## Manifest Contract

Selection baskets must lock the runtime contract to non-trading live/paper
output and must not declare an execution mode:

```yaml
output_kind: selection_basket
decision_mode: deterministic        # or llm_assisted
backtest_support: none
runtime_profile: deterministic      # or llm_bounded when getagent.llm is used
follow_trade_supported: false
official_evidence_kind: paper
display_name_i18n:                  # required for newly authored packages
  en: "Selection Basket"
  zh: "选篮子"
  zh-tw: "選籃子"
  es: "Cesta de selección"
  ja: "選択バスケット"
  vi: "Rổ lựa chọn"
description_i18n:
  en: "Non-trading basket that selects assets to watch."
  zh: "仅发信号的资产观察篮子。"
  zh-tw: "僅發出訊號的資產觀察籃子。"
  es: "Cesta solo de señales que selecciona activos para vigilar."
  ja: "注目資産を選ぶシグナル専用バスケット。"
  vi: "Rổ chỉ phát tín hiệu để chọn tài sản cần theo dõi."
```

Rules:

- `output_kind` defaults to `trade_strategy` when omitted. Always set
  `selection_basket` explicitly for callout packages.
- `backtest_support` must be `none`. A basket has no historical trade replay
  semantics.
- `execution_mode` must be omitted.
- `follow_trade_supported` must be `false`.
- `official_evidence_kind`, when present, must be `paper`.
- Do not include `backtest.yaml`.
- `schedule.cron` must not run more often than every 15 minutes, and
  `schedule.tz` is required when `schedule.cron` is present.
- New packages must include `display_name_i18n` and `description_i18n` with
  exactly these product locales: `en`, `zh`, `zh-tw`, `es`, `ja`, and `vi`.
  The base platform projects these into its translation table and still returns
  plain `display_name` / `description` selected by `X-Language-Id`.

## Output Contract

Emit the basket through the normal managed signal channel. The platform persists
the last signal's `meta.basket` after every completed `selection_basket` run.

```python
from getagent import runtime

runtime.emit_signal(
    action="watch",
    symbol="BTCUSDT",
    confidence=0.72,
    metrics={"basket_size": 2},
    meta={
        "basket": [
            {
                "asset": "BTC",
                "symbol": "BTCUSDT",
                "market": "spot",
                "name": "Bitcoin",
                "asset_class": "crypto",
                "reference_price": "100000",
                "target_price": "120000",
                "stop_loss": "90000",
                "thesis": "Core liquidity anchor for today's basket.",
                "risk": "High beta to broad crypto risk-off moves.",
                "thesis_i18n": {
                    "en": "Core liquidity anchor for today's basket.",
                    "zh": "今日篮子的核心流动性锚。",
                    "zh-tw": "今日籃子的核心流動性錨。",
                    "es": "Ancla de liquidez principal de la cesta de hoy.",
                    "ja": "本日のバスケットの中核となる流動性アンカー。",
                    "vi": "Neo thanh khoản cốt lõi của rổ hôm nay.",
                },
                "risk_i18n": {
                    "en": "High beta to broad crypto risk-off moves.",
                    "zh": "对加密市场整体避险行情的 beta 较高。",
                    "zh-tw": "對加密市場整體避險行情的 beta 較高。",
                    "es": "Beta alta frente a movimientos risk-off amplios en cripto.",
                    "ja": "暗号資産市場全体のリスクオフに対するベータが高い。",
                    "vi": "Beta cao với các đợt risk-off rộng của thị trường crypto.",
                },
            }
        ]
    },
)
```

Basket payload shape:

- `meta.basket` may be a list of picks, or an object with `picks` or `holdings`.
- Maximum persisted picks: 100. Keep product baskets concise.
- Every pick should include `asset` or `symbol`; include both when possible.
- Recommended fields are `asset`, `symbol`, `market`, `name`, `asset_class`,
  `reference_price`, `target_price`, `stop_loss`, `thesis`, and `risk`.
- `name` is the stable canonical asset/company name for product display. Do not
  localize or translate it into the user's language; use the exchange/data
  provider's English/common name when available, or fall back to the ticker/base
  asset code. For example, use `Visa Inc.`, `MSCI Inc.`, and `Moody's
  Corporation`, not `维萨公司`, `明晟公司`, or `穆迪公司`.
- Do not emit `name_i18n`. Required localized text maps for new packages are
  `thesis_i18n` and `risk_i18n`. Each map must include `en`, `zh`, `zh-tw`,
  `es`, `ja`, and `vi`. Keep the plain `thesis` and `risk` fields as English
  fallback text for old clients and old snapshots.
- Supported `asset_class` values are `crypto`, `stock`, `rwa`, `commodity`,
  `metal`, and `other`.
- Supported `market` values are `spot`, `futures`, `perpetual`, `contract`,
  and `other`. Use `spot` for spot symbols such as `BTCUSDT` or `RAAPLUSDT`.
- Prices may be strings or numbers. Prefer decimal strings to avoid float
  formatting artifacts.
- The platform resolves row icons by coin/base asset after the run; do not
  fetch icon URLs from Playbook code.

## LLM And Data Usage

Selection baskets may be deterministic or LLM-assisted:

- Use `runtime_profile: deterministic` when ranking can be computed from
  `getagent.data` responses and static rules.
- Use `runtime_profile: llm_bounded` only when `getagent.llm` is needed to
  summarize or score candidates. Keep `backtest_support: none`.
- `getagent.llm` is not a searchable agent. It has no tool calls and no web
  search. Fetch structured data first through `getagent.data`, then pass the
  compact facts into `llm.complete()` or `llm.chat()`.
- Never import `requests`, `httpx`, exchange clients, or browser/search clients.

Good pattern:

1. Discover candidates with documented `getagent.data` endpoints.
2. For picks that claim a tradable Bitget market, run the same authoring-time
   Bitget public config lookup used by trade strategies and store the confirmed
   exchange-native symbol in `meta.basket[].symbol`.
3. Normalize symbols and asset classes.
4. Rank or summarize with deterministic logic, optionally using one bounded LLM
   call.
5. Emit one `watch` signal whose `meta.basket` contains the final picks.

## Product Surface

The product APIs treat callout baskets differently from trade strategies:

- List surfaces return `output_kind: "selection_basket"` so clients can switch
  card/detail layouts.
- Detail embeds `basket_stats` with 3/7/14-day win-rate windows and today's top
  mover fields.
- The holdings table is read from the separate product basket endpoint and is
  paginated.
- Holdings display the latest snapshot, not historical holdings.
- Trade performance blocks are intentionally empty/unavailable for callout
  Playbooks.

## Authoring Checklist

- Manifest contains `output_kind: selection_basket`.
- Manifest locks `backtest_support: none`, omits `execution_mode`, and sets
  `follow_trade_supported: false`.
- No `backtest.yaml` is included.
- Code emits `runtime.emit_signal(..., meta={"basket": [...]})`.
- Basket fields are explicit and stable; no frontend-only fields are hidden in
  prose.
- Basket `name` values are canonical/non-localized asset names, never translated
  UI copy.
- Data/search calls go through `getagent.data`.
- LLM calls, if any, use `getagent.llm` only under `runtime_profile:
  llm_bounded`.
- README explains this is a watchlist/callout product, not auto-trading.

## Minimal Example

Use `examples/selection-basket-demo/` for a runnable minimal package. Read its
`README.md`, then run:

```bash
python3 scripts/validate.py skills/getagent/examples/selection-basket-demo
```
