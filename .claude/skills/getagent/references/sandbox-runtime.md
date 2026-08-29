# Sandbox Runtime

## Contents

- [Execution Model](#execution-model)
- [State and Persistence](#state-and-persistence)
- [Runtime Profiles](#runtime-profiles)
- [Pre-installed Dependencies](#pre-installed-dependencies)
- [Allowed Standard Library Modules](#allowed-standard-library-modules)
- [Blocked Modules](#blocked-modules)
- [Network Restrictions](#network-restrictions)
- [Output Conventions](#output-conventions)
- [Environment Variables](#environment-variables)

## Execution Model

- **Engine:** Python 3.12
- **Entry point:** package executes as `python -m src.main`
- **Working directory:** `/workspace/`
- **Timeout:** 180 seconds
- **Memory:** 2GB
- **Fresh workspace:** Each run starts in a fresh workspace snapshot.
- **Executable runtime profiles:** `deterministic`, plus deployment-enabled `llm_bounded`
- **No built-in agent loop:** Do not assume planner / reflection / tool-orchestration loops are provided by the platform.

## State and Persistence

The workspace is ephemeral by default, but the runner may optionally hydrate and
sync `.state/` on behalf of the Playbook.

- Treat `.state/` as the only supported persisted path across runs.
- Do not rely on files outside `.state/` surviving between runs.
- If `.state/` hydrate fails, the runner may abort instead of silently running
with missing state.
- Agent memory is **not** part of the default sandbox contract. If a future
runtime introduces agent memory, it should live behind an explicit runtime
profile and policy.

## Runtime Profiles

The product direction is to separate package shape from runtime capability.

- `deterministic`
  - Current default executable profile
  - No built-in general-purpose agent loop
  - Best fit for `backtest_support: full`
- `llm_bounded`
  - Executable only when the deployment enables managed Playbook LLM access
  - Use through `getagent.llm`, not direct HTTP clients
  - Fixed call-count, prompt-size, output-token, and timeout budgets
  - Best fit for `backtest_support: none`
- `agentic`
  - Declared contract only for now; current sandbox rejects it at runtime
  - Should not be assumed in the default Playbook sandbox

### Agent loop guidance

Do **not** assume a full general-purpose agent runtime is available in the
default Playbook sandbox.

`llm_bounded` is intentionally narrower than a general-purpose agent loop. If
the platform later introduces `agentic`, it should still require:

- an explicit runtime profile or separate image
- fixed tool allowlists
- `max_steps`
- `max_runtime_ms`
- `max_model_tokens`
- trace persistence
- an explicit memory policy

## Pre-installed Dependencies

These are the public packages available to Playbook source code.


| Package           | Version             | Purpose                                                                       |
| ----------------- | ------------------- | ----------------------------------------------------------------------------- |
| `getagent`         | 0.5.1               | SDK (data, trade, backtest, runtime, llm)                                     |
| `getall`          | repo source         | Internal managed runtime used by `getagent.llm`                                |
| `litellm`         | 1.83.7              | Internal provider bridge behind `getagent.llm`                                 |
| `trade-sdk`       | vendored source     | Internal implementation behind `getagent.trade` (not a public Playbook import) |
| `pandas`          | ≥2.0                | Data manipulation                                                             |
| `numpy`           | ≥1.24               | Numerical computation                                                         |
| `nautilus_trader` | current image build | Backtest engine (used by SDK and author strategy classes)                     |
| `pydantic`        | 2.13.2              | Internal config/runtime models                                                |
| `pyyaml`          | ≥6.0                | YAML parsing                                                                  |
| `matplotlib`      | ≥3.7                | Chart rendering (used by SDK internally)                                      |


**No pip install.** PyPI is network-blocked. Only pre-installed packages are available.

### Public author imports

Playbook source code should import from the public surface only:

- `getagent`
- `nautilus_trader`
- `pandas`
- `numpy`
- safe standard-library modules listed below

Do not import undocumented implementation packages even when Python can resolve
them. Only the public imports above are part of the Playbook contract.

## Allowed Standard Library Modules

`json`, `math`, `datetime`, `pathlib`, `asyncio`, `typing`, `dataclasses`,
`collections`, `functools`, `re`, `decimal`, `statistics`, `itertools`,
`operator`, `copy`, `enum`, `abc`, `numbers`, `fractions`

## Blocked Author Imports

Local and upload validation reject blocked imports, dynamic imports,
`eval`/`exec`, and unsafe built-in access. Playbook code must fetch data through
`getagent.data`, trade through `getagent.trade`, and use bounded model access
through `getagent.llm`. Direct network, process, and database clients are not
part of the public contract.

### Blocked categories

**Network:** `requests`, `httpx`, `trade_sdk`, `urllib`, `aiohttp`, `socket`, `http`, `ftplib`, `smtplib`

**System:** `subprocess`, `os`, `shutil`, `importlib`, `ctypes`, `multiprocessing`

**Database:** `sqlalchemy`, `redis`, `pymongo`

**Frameworks:** `fastapi`, `flask`, `django`

**Messaging:** `telegram`, `slack_sdk`, `discord`

## Network Restrictions


| Allowed                                                                             | Blocked                                                                            |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Managed SDK data access via `getagent.data`                                          | PyPI (`pypi.org`, `files.pythonhosted.org`)                                        |
| Managed trading via `getagent.trade`                                                  | Direct `requests` / `httpx` / `urllib` calls from Playbook code                    |
| Managed LLM calls via `getagent.llm` when `runtime_profile: llm_bounded` is injected |                                                                                    |
|                                                                                     | All private networks, localhost, and arbitrary public addresses from Playbook code |


**All data fetching must go through `getagent.data`, all trade-proxy access must go through `getagent.trade`, and bounded model calls must go through `getagent.llm`.** Do not make direct HTTP requests.

## Output Conventions


| Output Type     | Mechanism                                                               | Available |
| --------------- | ----------------------------------------------------------------------- | --------- |
| Trading signals | `runtime.emit_signal()` → stdout JSON + `/workspace/output/signal.json` | Yes       |
| Selection baskets | `runtime.emit_signal(..., meta={"basket": [...]})` for `output_kind: selection_basket` | Yes |
| Scheduling progress (Grid only) | `runtime.emit_progress(blocks)` | Yes |
| Strategy Bot lifecycle | `runtime.execute_strategy_bot_action(...)` for `create`/`modify`/`shutdown`/`watch` | Yes for matching bot packages |
| Strategy Bot inventory | `runtime.list_strategy_bots(status=...)` | Yes for matching bot packages |
| Backtest charts | `backtest.generate_chart()` → `/workspace/output/*.png` (matplotlib)    | Yes       |
| Debug output    | `print()` → stdout (Runner collects first 5000 chars)                   | Yes       |
| Errors          | `print(..., file=sys.stderr)` → stderr                                  | Yes       |


The Runner collects all `.png`, `.json`, `.csv` files from `/workspace/output/`
as artifacts after execution completes.

For callout / selection basket Playbooks, the platform persists `meta.basket`
from completed runs for product display. Do not write basket snapshots yourself
and do not fetch icon URLs from Playbook code.

## Environment Variables

These public runtime variables are injected inside the sandbox. Prefer the
corresponding `getagent.runtime` attributes and helpers when available.

| Variable                       | Description                                                                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| `GETAGENT_WORKSPACE`            | Working directory path (default `/workspace`)                                                                                        |
| `GETAGENT_RUN_ID`               | Unique run identifier                                                                                                                |
| `GETAGENT_PLAYBOOK_ID`          | Playbook ID                                                                                                                          |
| `GETAGENT_CHAT_ID`              | Delivery target for manual or scheduled results                                                                                      |
| `GETAGENT_EVALUATION_MODE`      | `historical` or `live`; prefer `runtime.evaluation_mode`                                                                              |
| `GETAGENT_PLAYBOOK_EXECUTION_MODE` | `follow_trade` or `grid`; omitted for non-trading packages; prefer `runtime.execution_mode()`                                     |
| `GETAGENT_RUNTIME_PROFILE`      | Runner-selected runtime profile for the current execution                                                                            |
