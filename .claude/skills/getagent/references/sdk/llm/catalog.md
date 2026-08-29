# `getagent.llm`

Author-facing bounded LLM surface for live-only Playbooks.

## When to use

Use `getagent.llm` when the strategy depends on runner-managed model reasoning
that cannot be fairly replayed from historical market data alone.

Typical fit:

- `runtime_profile: llm_bounded`
- `backtest_support: none`
- `output_kind: trade_strategy` with `execution_mode: follow_trade` when the
  strategy must trade live via managed follow trading
- live/paper evidence instead of historical backtest claims

Do **not** use `getagent.llm` for replayable logic that should stay in
`getagent.backtest`.

## Public API

### Availability

- `llm.is_available() -> bool`
  - Returns whether the current sandbox run injected bounded LLM access
  - `False` in deterministic runs

### Calls

- `llm.complete(prompt, *, system=None, max_tokens=None, temperature=None) -> LLMResult`
- `llm.chat(messages, *, system=None, max_tokens=None, temperature=None) -> LLMResult`

`messages` accepts either:

- `llm.LLMMessage(role="user", content="...")`
- plain dicts like `{"role": "user", "content": "..."}`

### Result shape

`LLMResult` exposes:

- `content`
- `model`
- `request_id`
- `finish_reason`
- `usage`
- `raw`

`raw` currently carries lightweight provider metadata such as reasoning text or
estimated cost when available.

## Runtime boundaries

The bounded runtime is intentionally narrow:

- one runner-managed model only
- no free model switching from Playbook code
- no tool calls
- no built-in web/search access; fetch facts first through `getagent.data`
- no direct `httpx` / `requests` / `litellm` usage from Playbook source
- fixed limits for:
  - calls per run
  - prompt characters
  - output tokens
  - timeout

If a request exceeds those limits, `getagent.llm` raises a typed runtime error
instead of silently falling back.

## Errors

The module raises explicit `RuntimeError` subclasses:

- `LLMRuntimeUnavailableError` — this run is not `llm_bounded`
- `LLMConfigurationError` — runner-side LLM config is missing or invalid
- `LLMInputError` — caller input is malformed
- `LLMBudgetExceededError` — bounded runtime budget exceeded
- `LLMError` — upstream/provider call failed

## Example

```python
from getagent import llm, runtime

if not llm.is_available():
    raise RuntimeError("This playbook requires runtime_profile=llm_bounded")

summary = llm.complete(
    "Summarize today's macro risk for BTC in 3 sentences.",
    system="You are a cautious crypto macro analyst.",
    max_tokens=300,
)

runtime.emit_signal(
    action="watch",
    symbol="BTCUSDT",
    confidence=0.55,
    meta={
        "llm_summary": summary.content,
        "llm_model": summary.model,
    },
)
```

## Hard rules

- Keep LLM outputs as bounded inputs into trading logic, not as an open-ended
  agent loop
- Do not claim historical replayability for `llm_bounded` strategies
- Do not read `GETAGENT_LLM_*` env vars directly unless debugging a runtime issue
- Do not import internal implementation modules such as `getall`, `litellm`, or
  `httpx`

## Related docs

- [`../../package-schema.md`](../../package-schema.md)
- [`../../sandbox-runtime.md`](../../sandbox-runtime.md)
- [`../../api/publish.md`](../../api/publish.md)
- [`../../api/subscription-links.md`](../../api/subscription-links.md)
