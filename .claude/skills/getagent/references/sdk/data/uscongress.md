# Uscongress Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`uscongress.bill_info`](#uscongressbill-info)
- [`uscongress.bill_text`](#uscongressbill-text)
- [`uscongress.bill_text_urls`](#uscongressbill-text-urls)
- [`uscongress.bills`](#uscongressbills)

## Endpoint reference

### `uscongress.bill_info`

```python
data.uscongress.bill_info(bill_url=None)
```

Summary: Bill Info

| Field | Value |
|---|---|
| Endpoint ID | `uscongress.bill_info` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/uscongress/bill_info` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `bill_url` | `no` | `string | null` | `-` | Enter a base URL of a bill (e.g., 'https://api.congress.gov/v3/bill/119/s/1947?format=json'). Alternatively, you can enter a bill number (e.g., '119/s/1947'). |

---

### `uscongress.bill_text`

```python
data.uscongress.bill_text(, body=...)
```

Summary: Bill Text

| Field | Value |
|---|---|
| Endpoint ID | `uscongress.bill_text` |
| HTTP | `POST` |
| Path | `/inner/v1/agent-data/uscongress/bill_text` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `body` | `no` | `string | array | object | null` | `-` | List of direct bill URLs to download. Multiple comma separated items allowed. |

---

### `uscongress.bill_text_urls`

```python
data.uscongress.bill_text_urls(bill_url=..., is_workspace=False)
```

Summary: Bill Text Urls

| Field | Value |
|---|---|
| Endpoint ID | `uscongress.bill_text_urls` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/uscongress/bill_text_urls` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `bill_url` | `yes` | `string` | `-` | - |
| `is_workspace` | `no` | `boolean` | `false` | - |

---

### `uscongress.bills`

```python
data.uscongress.bills(congress=None, bill_type=None, start_date=None, end_date=None, limit=None, offset=None, sort_by='desc')
```

Summary: Bills

| Field | Value |
|---|---|
| Endpoint ID | `uscongress.bills` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/uscongress/bills` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `congress` | `no` | `integer | null` | `-` | Congress number (e.g., 118 for the 118th Congress). The 103rd Congress started in 1993, which is the earliest date supporting full text versions. Each Congress spans two years, starting in odd-numbered years. |
| `bill_type` | `no` | `string | null` | `-` | Bill type (e.g., "hr" for House bills). Must be one of: hr, s, hjres, sjres, hconres, sconres, hres, sres. Bills ----- A bill is the form used for most legislation, whether permanent or temporary, general or special, public or private. A bill originating in the House of Representatives is designated by the letters “H.R.”, signifying “House of Representatives”, followed by a number that it retains throughout all its parliamentary stages. Bills are presented to the President for action when approved in identical form by both the House of Representatives and the Senate. Joint Resolutions ----------------- Joint resolutions may originate either in the House of Representatives or in the Senate. There is little practical difference between a bill and a joint resolution. Both are subject to the same procedure, except for a joint resolution proposing an amendment to the Constitution. On approval of such a resolution by two-thirds of both the House and Senate, it is sent directly to the Administrator of General Services for submission to the individual states for ratification. It is not presented to the President for approval. A joint resolution originating in the House of Representatives is designated “H.J.Res.” followed by its individual number. Joint resolutions become law in the same manner as bills. Concurrent Resolutions ---------------------- Matters affecting the operations of both the House of Representatives and Senate are usually initiated by means of concurrent resolutions. A concurrent resolution originating in the House of Representatives is designated “H.Con.Res.” followed by its individual number. On approval by both the House of Representatives and Senate, they are signed by the Clerk of the House and the Secretary of the Senate. They are not presented to the President for action. Simple Resolutions ------------------ A matter concerning the operation of either the House of Representatives or Senate alone is initiated by a simple resolution. A resolution affecting the House of Representatives is designated “H.Res.” followed by its number. They are not presented to the President for action. |
| `start_date` | `no` | `string | null` | `-` | Start date of the data, in YYYY-MM-DD format. Filters bills by the last updated date. |
| `end_date` | `no` | `string | null` | `-` | End date of the data, in YYYY-MM-DD format. Filters bills by the last updated date. |
| `limit` | `no` | `integer | null` | `-` | The number of data entries to return. When None, default sets to 100. Max 250. |
| `offset` | `no` | `integer | null` | `-` | The starting record returned. 0 is the first record. |
| `sort_by` | `no` | `string` | `desc` | Sort by update date. Default is latest first. |
