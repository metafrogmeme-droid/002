# News Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`news.company`](#newscompany)
- [`news.label_search`](#newslabel-search)
- [`news.world`](#newsworld)

## Endpoint reference

### `news.company`

```python
data.news.company(start_time=None, end_time=None, symbol=None, limit=50, date=None, display='full', updated_since=None, published_since=None, sort='created', order='desc', isin=None, cusip=None, channels=None, topics=None, authors=None, content_types=None, page=0, press_release=None, source=None, sentiment=None, language=None, topic=None, word_count_greater_than=None, word_count_less_than=None, is_spam=None, business_relevance_greater_than=None, business_relevance_less_than=None, offset=0)
```

Summary: Company

| Field | Value |
|---|---|
| Endpoint ID | `news.company` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/news/company` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `symbol` | `no` | `string | null` | `-` | Symbol to get data for. Multiple comma separated items allowed |
| `limit` | `no` | `integer | null` | `50` | The number of data entries to return. Max 500. |
| `date` | `no` | `string | null` | `-` | A specific date to get data for. |
| `display` | `no` | `string` | `full` | enum: headline, abstract, full Specify headline only (headline), headline + teaser (abstract), or headline + full body (full). |
| `updated_since` | `no` | `integer | null` | `-` | Number of seconds since the news was updated. |
| `published_since` | `no` | `integer | null` | `-` | Number of seconds since the news was published. |
| `sort` | `no` | `string` | `created` | enum: id, created, updated Key to sort the news by. |
| `order` | `no` | `string` | `desc` | enum: asc, desc Order to sort the news by. |
| `isin` | `no` | `string | null` | `-` | The company's ISIN. |
| `cusip` | `no` | `string | null` | `-` | The company's CUSIP. |
| `channels` | `no` | `string | null` | `-` | Channels of the news to retrieve. |
| `topics` | `no` | `string | null` | `-` | Topics of the news to retrieve. |
| `authors` | `no` | `string | null` | `-` | Authors of the news to retrieve. |
| `content_types` | `no` | `string | null` | `-` | Content types of the news to retrieve. |
| `page` | `no` | `integer | null` | `0` | Page number of the results. Use in combination with limit.; The page number to start from. Use with limit. |
| `press_release` | `no` | `boolean | null` | `-` | When true, will return only press releases for the given symbol(s). |
| `source` | `no` | `string | null` | `-` | The source of the news article.; A comma-separated list of the domains requested. Multiple comma separated items allowed. |
| `sentiment` | `no` | `string | null` | `-` | Return news only from this source. |
| `language` | `no` | `string | null` | `-` | Filter by language. Unsupported for yahoo source. |
| `topic` | `no` | `string | null` | `-` | Filter by topic. Unsupported for yahoo source. |
| `word_count_greater_than` | `no` | `integer | null` | `-` | News stories will have a word count greater than this value. Unsupported for yahoo source. |
| `word_count_less_than` | `no` | `integer | null` | `-` | News stories will have a word count less than this value. Unsupported for yahoo source. |
| `is_spam` | `no` | `boolean | null` | `-` | Filter whether it is marked as spam or not. Unsupported for yahoo source. |
| `business_relevance_greater_than` | `no` | `number | null` | `-` | News stories will have a business relevance score more than this value. Unsupported for yahoo source. Value is a decimal between 0 and 1. |
| `business_relevance_less_than` | `no` | `number | null` | `-` | News stories will have a business relevance score less than this value. Unsupported for yahoo source. Value is a decimal between 0 and 1. |
| `offset` | `no` | `integer | null` | `0` | Page offset, used in conjunction with limit. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. The date of publication. |
| `title` | `string` | Title of the article. |
| `author` | `string` | Author of the article. |
| `excerpt` | `string` | Excerpt of the article text. |
| `body` | `string` | Body of the article text. |
| `images` | `object` | Images associated with the article. |
| `url` | `string` | URL to the article. |
| `symbols` | `string` | Symbols associated with the article. |
| `source` | `string` | Name of the news site. |
| `summary` | `string` | The summary of the news article. |
| `topics` | `string` | The topics related to the news article. |
| `word_count` | `integer` | The word count of the news article. |
| `business_relevance` | `number` | How strongly correlated the news article is to the business. |
| `sentiment` | `string` | The sentiment of the news article - i.e, negative, positive. |
| `sentiment_confidence` | `number` | The confidence score of the sentiment rating. |
| `language` | `string` | The language of the news article. |
| `spam` | `boolean` | Whether the news article is spam. |
| `copyright` | `string` | The copyright notice of the news article. |
| `id` | `string` | Article ID. |
| `security` | `object` | The Intrinio Security object. Contains the security details related to the news article. |
| `channels` | `string` | Channels associated with the news. |
| `tags` | `string` | Tags associated with the news. |
| `updated` | `string` | Updated date of the news. |
| `original_id` | `string` | Original ID of the news article. |
| `article_id` | `integer` | Unique ID of the news article. |
| `crawl_date` | `string` | Date the news article was crawled. |

---

### `news.label_search`

```python
data.news.label_search(label=..., language_id=0, start_time=None, end_time=None, page=1, page_size=10)
```

Summary: Label Search

| Field | Value |
|---|---|
| Endpoint ID | `news.label_search` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/news/label_search` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `label` | `yes` | `integer | string` | `-` | News label type to search for. Accepts either the integer type code or the human-readable name: 1=Crypto, 2=Stocks, 6=Commodities & Forex, 7=Macro. |
| `language_id` | `no` | `integer | string | null` | `0` | Language filter. Accepts either the integer language code or a locale string (e.g. 'en', 'zh-CN', 'ja'). Defaults to 0 (English). |
| `start_time` | `no` | `string | integer | number | null` | `-` | Start of the time range. Accepts a datetime object, an ISO-8601 string, or a Unix timestamp (seconds or milliseconds). Converted to millisecond epoch before sending to the API. |
| `end_time` | `no` | `string | integer | number | null` | `-` | End of the time range. Accepts a datetime object, an ISO-8601 string, or a Unix timestamp (seconds or milliseconds). Converted to millisecond epoch before sending to the API. |
| `page` | `no` | `integer | null` | `1` | Page number for pagination (1-based). Defaults to 1. |
| `page_size` | `no` | `integer | null` | `10` | Number of news items per page. Defaults to 10. Max 1000. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `title` | `string` | News article title. |
| `content` | `string` | Full HTML/text content of the news article. |
| `labels` | `array` | Human-readable label names associated with the article (e.g. ['Crypto', 'Stocks']). |
| `language` | `string` | Locale string of the article language (e.g. 'en', 'zh-CN'). |
| `published_at` | `string` | Publication timestamp of the article. |

---

### `news.world`

```python
data.news.world(start_time=None, end_time=None, limit=20, date=None, display='full', updated_since=None, published_since=None, sort='created', order='desc', isin=None, cusip=None, channels=None, topics=None, authors=None, content_types=None, term=None, source=None, topic='general', page=None, sentiment=None, language=None, word_count_greater_than=None, word_count_less_than=None, is_spam=None, business_relevance_greater_than=None, business_relevance_less_than=None, offset=0)
```

Summary: World

| Field | Value |
|---|---|
| Endpoint ID | `news.world` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/news/world` |
| SDK | `supported` |
| Host | `supported` |
| Notes | Global news feed endpoint for macro/news-aware strategies. |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `start_time` | `no` | `integer | null` | `-` | Start time of the data as a Unix timestamp in milliseconds. Takes priority over start_date when both are provided. |
| `end_time` | `no` | `integer | null` | `-` | End time of the data as a Unix timestamp in milliseconds. Takes priority over end_date when both are provided. |
| `limit` | `no` | `integer | null` | `20` | The number of articles to return. Max 500. |
| `date` | `no` | `string | null` | `-` | A specific date to get data for. |
| `display` | `no` | `string` | `full` | enum: headline, abstract, full Specify headline only (headline), headline + teaser (abstract), or headline + full body (full). |
| `updated_since` | `no` | `integer | null` | `-` | Number of seconds since the news was updated. |
| `published_since` | `no` | `integer | null` | `-` | Number of seconds since the news was published. |
| `sort` | `no` | `string` | `created` | enum: id, created, updated Key to sort the news by. |
| `order` | `no` | `string` | `desc` | enum: asc, desc Order to sort the news by. |
| `isin` | `no` | `string | null` | `-` | The ISIN of the news to retrieve. |
| `cusip` | `no` | `string | null` | `-` | The CUSIP of the news to retrieve. |
| `channels` | `no` | `string | null` | `-` | Channels of the news to retrieve. |
| `topics` | `no` | `string | null` | `-` | Topics of the news to retrieve. |
| `authors` | `no` | `string | null` | `-` | Authors of the news to retrieve. |
| `content_types` | `no` | `string | null` | `-` | Content types of the news to retrieve. |
| `term` | `no` | `string | null` | `-` | Search term to filter articles by. This overrides all other filters. |
| `source` | `no` | `string | null` | `-` | Filter by a specific publisher. Only valid when filter is set to source.; The source of the news article.; A comma-separated list of the domains requested. Multiple comma separated items allowed. |
| `topic` | `no` | `string | null` | `general` | The topic of the news to be fetched.; Filter by topic. Unsupported for yahoo source. |
| `page` | `no` | `integer | null` | `-` | Page number of the results. Use in combination with limit. |
| `sentiment` | `no` | `string | null` | `-` | Return news only from this source. |
| `language` | `no` | `string | null` | `-` | Filter by language. Unsupported for yahoo source. |
| `word_count_greater_than` | `no` | `integer | null` | `-` | News stories will have a word count greater than this value. Unsupported for yahoo source. |
| `word_count_less_than` | `no` | `integer | null` | `-` | News stories will have a word count less than this value. Unsupported for yahoo source. |
| `is_spam` | `no` | `boolean | null` | `-` | Filter whether it is marked as spam or not. Unsupported for yahoo source. |
| `business_relevance_greater_than` | `no` | `number | null` | `-` | News stories will have a business relevance score more than this value. Unsupported for yahoo source. Value is a decimal between 0 and 1. |
| `business_relevance_less_than` | `no` | `number | null` | `-` | News stories will have a business relevance score less than this value. Unsupported for yahoo source. Value is a decimal between 0 and 1. |
| `offset` | `no` | `integer | null` | `0` | Page offset, used in conjunction with limit. |

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `date` | `string` | The date of the data. The date of publication. |
| `title` | `string` | Title of the article. |
| `author` | `string` | Author of the article. |
| `excerpt` | `string` | Excerpt of the article text. |
| `body` | `string` | Body of the article text. |
| `images` | `object` | Images associated with the article. |
| `url` | `string` | URL to the article. |
| `source` | `string` | News source. |
| `tags` | `array` | Tags for the article. |
| `score` | `number` | Search relevance score for the article. |
| `symbols` | `string` | Ticker tagged in the fetched news. |
| `article_id` | `integer` | Unique ID of the news article. |
| `site` | `string` | News source. |
| `crawl_date` | `string` | Date the news article was crawled. |
| `channels` | `string` | Channels associated with the news. |
| `stocks` | `string` | Stocks associated with the news. |
| `updated` | `string` | Updated date of the news. |
| `id` | `string` | Article ID. |
| `updated_id` | `string` | Updated article ID if the article was updated. |
| `summary` | `string` | The summary of the news article. |
| `topics` | `string` | The topics related to the news article. |
| `word_count` | `integer` | The word count of the news article. |
| `business_relevance` | `number` | How strongly correlated the news article is to the business. |
| `sentiment` | `string` | The sentiment of the news article - i.e, negative, positive. |
| `sentiment_confidence` | `number` | The confidence score of the sentiment rating. |
| `language` | `string` | The language of the news article. |
| `spam` | `boolean` | Whether the news article is spam. |
| `copyright` | `string` | The copyright notice of the news article. |
| `company` | `object` | The Intrinio Company object. Contains details company reference data. |
| `security` | `object` | The Intrinio Security object. Contains the security details related to the news article. |
