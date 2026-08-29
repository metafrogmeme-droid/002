# Wikipedia Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`wikipedia.content`](#wikipediacontent)
- [`wikipedia.search`](#wikipediasearch)
- [`wikipedia.summary`](#wikipediasummary)

## Endpoint reference

### `wikipedia.content`

```python
data.wikipedia.content(title=None, lang='en', intro_only=False)
```

Summary: Content

| Field | Value |
|---|---|
| Endpoint ID | `wikipedia.content` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/wikipedia/content` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `title` | `no` | `string | null` | `-` | Wikipedia article title to retrieve. |
| `lang` | `no` | `string` | `en` | Wikipedia language edition. |
| `intro_only` | `no` | `boolean` | `false` | Return only the introductory section instead of the full article. |

---

### `wikipedia.search`

```python
data.wikipedia.search(query=None, max_results=10, page=1, lang='en')
```

Summary: Search

| Field | Value |
|---|---|
| Endpoint ID | `wikipedia.search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/wikipedia/search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string | null` | `-` | Search query string. |
| `max_results` | `no` | `integer` | `10` | Maximum number of results. |
| `page` | `no` | `integer` | `1` | Page number, starting at 1. |
| `lang` | `no` | `string` | `en` | Wikipedia language edition. |

---

### `wikipedia.summary`

```python
data.wikipedia.summary(title=None, lang='en')
```

Summary: Summary

| Field | Value |
|---|---|
| Endpoint ID | `wikipedia.summary` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/wikipedia/summary` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `title` | `no` | `string | null` | `-` | Wikipedia article title to retrieve. |
| `lang` | `no` | `string` | `en` | Wikipedia language edition. |
