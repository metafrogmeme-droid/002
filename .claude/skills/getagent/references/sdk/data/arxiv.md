# Arxiv Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`arxiv.search`](#arxivsearch)

## Endpoint reference

### `arxiv.search`

```python
data.arxiv.search(query=None, max_results=10, page=1, sort_by='relevance', sort_order='descending', search_field='all', category=None)
```

Summary: Search

| Field | Value |
|---|---|
| Endpoint ID | `arxiv.search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/arxiv/search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `query` | `no` | `string | null` | `-` | Search query string. |
| `max_results` | `no` | `integer` | `10` | Maximum number of results. |
| `page` | `no` | `integer` | `1` | Page number, starting at 1. |
| `sort_by` | `no` | `string` | `relevance` | Sort by relevance, last updated date, or submitted date. |
| `sort_order` | `no` | `string` | `descending` | Sort direction. |
| `search_field` | `no` | `string` | `all` | Field to search: all, ti (title), au (author), abs (abstract), cat (category). |
| `category` | `no` | `string | null` | `-` | Filter by arXiv subject category, e.g. 'cs.AI', 'q-fin.TR'. |
