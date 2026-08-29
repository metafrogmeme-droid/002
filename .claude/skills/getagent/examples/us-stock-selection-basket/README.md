# US Stock Selection Basket

This package is a test Playbook for the `selection_basket` output path. It emits
a structured RWA US stock watchlist and never places orders.

## What It Does

- Uses `output_kind: selection_basket`
- Declares no trading execution mode
- Emits one `watch` signal
- Places selected US stock RWA rows in `meta.basket`
- Never calls trade mutation APIs
- Does not include `backtest.yaml`

## 策略 / Strategy

The demo ranks a fixed universe of Bitget RWA US stock spot markets and emits a
compact basket for product QA. It is intentionally deterministic so upload,
validation, snapshot persistence, and basket rendering can be tested without
depending on live data availability.

## 开仓 / Entry

There is no trade entry. A run only publishes the current watchlist candidates
through `runtime.emit_signal(action="watch", meta={"basket": ...})`.

## 平仓 / Exit

There is no trade exit. The next completed scheduled run replaces the displayed
basket snapshot.

## 风险 / Risk

This is a platform test artifact, not an investment recommendation. The embedded
prices are illustrative fixtures, and real trading decisions require separate
market checks.

## Run Local Validation

From the repository root:

```bash
python3 skills/getagent/scripts/validate.py skills/getagent/examples/us-stock-selection-basket
```

## Output Shape

Each basket row includes `asset`, `symbol`, `market`, `name`, `asset_class`,
`reference_price`, `target_price`, `stop_loss`, `thesis`, `risk`, and localized
`thesis_i18n` and `risk_i18n` maps for `en`, `zh`, `zh-tw`, `es`, `ja`, and
`vi`. Asset names remain canonical and non-localized.
