# Selection Basket Demo

This package demonstrates a callout Playbook that emits a current watchlist
basket instead of a trade strategy.

This is not an auto-trading strategy. It emits only a basket signal, never
opens positions, never exits positions, and never calls trade APIs. The main
risk is that a user may misread a watchlist as a deterministic buy or sell
recommendation.

## What It Does

- Uses `output_kind: selection_basket`
- Declares no trading execution mode
- Emits one `watch` signal
- Places the basket in `meta.basket`
- Never calls trade mutation APIs
- Does not include `backtest.yaml`

## 策略 / Strategy

The demo strategy is a structured watchlist. It selects a small fixed basket
and emits it through managed Playbook output.

## 开仓 / Entry

There is no trade entry. The run only publishes current basket candidates.

## 平仓 / Exit

There is no trade exit. The next completed scheduled run replaces the displayed
basket snapshot.

## 风险 / Risk

The basket is research context, not a performance promise or auto-trading
instruction.

## Run Local Validation

From the skill root:

```bash
python3 scripts/validate.py examples/selection-basket-demo
```

From the repository root:

```bash
python3 skills/getagent/scripts/validate.py skills/getagent/examples/selection-basket-demo
```

## Output Shape

The platform persists the list under `meta.basket` after each completed run.
Each item includes asset identity, market, prices, thesis, risk text, and
localized `thesis_i18n` / `risk_i18n` maps for `en`, `zh`, `zh-tw`, `es`,
`ja`, and `vi`. Asset names remain canonical and non-localized.

This demo uses fixed illustrative prices. Production callout Playbooks should
fetch current context through documented `getagent.data` endpoints before
ranking and emitting their basket.
