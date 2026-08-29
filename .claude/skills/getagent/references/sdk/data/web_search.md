# Web_Search Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`web_search.news`](#web-searchnews)
- [`web_search.web`](#web-searchweb)

## Endpoint reference

### `web_search.news`

```python
data.web_search.news(query=..., max_results=10, page=1)
```

Summary: News

| Field | Value |
|---|---|
| Endpoint ID | `web_search.news` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/web_search/news` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `yes` | `string` | `-` | Search query string. |
| `max_results` | `no` | `integer` | `10` | Maximum number of news results to return. |
| `page` | `no` | `integer` | `1` | Page number for pagination, starting at 1. |

---

### `web_search.web`

```python
data.web_search.web(query=..., max_results=10, page=1, backend='auto')
```

Summary: Web

| Field | Value |
|---|---|
| Endpoint ID | `web_search.web` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/web_search/web` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `yes` | `string` | `-` | Search query string. |
| `max_results` | `no` | `integer` | `10` | Maximum number of results to return. |
| `page` | `no` | `integer` | `1` | Page number for pagination, starting at 1. |
| `backend` | `no` | `string` | `auto` | enum: auto, duckduckgo, google, bing, brave, yandex, yahoo, wikipedia, grokipedia, mojeek Search engine backend. 'auto' queries multiple engines with automatic fallback for resilience. |
