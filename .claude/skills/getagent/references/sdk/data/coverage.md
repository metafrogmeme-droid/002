# Coverage Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`coverage.command_model`](#coveragecommand-model)
- [`coverage.commands`](#coveragecommands)
- [`coverage.providers`](#coverageproviders)

## Endpoint reference

### `coverage.command_model`

```python
data.coverage.command_model()
```

Summary: Get Commands Model Map

| Field | Value |
|---|---|
| Endpoint ID | `coverage.command_model` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/coverage/command_model` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

No query parameters.

---

### `coverage.commands`

```python
data.coverage.commands()
```

Summary: Get Command Coverage

| Field | Value |
|---|---|
| Endpoint ID | `coverage.commands` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/coverage/commands` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

No query parameters.

---

### `coverage.providers`

```python
data.coverage.providers()
```

Summary: Get Provider Coverage

| Field | Value |
|---|---|
| Endpoint ID | `coverage.providers` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/coverage/providers` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

No query parameters.
