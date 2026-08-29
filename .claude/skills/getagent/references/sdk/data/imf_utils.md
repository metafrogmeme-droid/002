# Imf_Utils Data Reference

Use this file when an agent needs detailed signatures and parameter
rules for one DataSDK domain. All generated `getagent.data` endpoints
are callable through the DataSDK wrapper.

## Contents
- [`imf_utils.get_dataflow_dimensions`](#imf-utilsget-dataflow-dimensions)
- [`imf_utils.list_dataflow_choices`](#imf-utilslist-dataflow-choices)
- [`imf_utils.list_dataflows`](#imf-utilslist-dataflows)
- [`imf_utils.list_port_id_choices`](#imf-utilslist-port-id-choices)
- [`imf_utils.list_table_choices`](#imf-utilslist-table-choices)
- [`imf_utils.list_tables`](#imf-utilslist-tables)
- [`imf_utils.presentation_table`](#imf-utilspresentation-table)
- [`imf_utils.presentation_table_choices`](#imf-utilspresentation-table-choices)

## Endpoint reference

### `imf_utils.get_dataflow_dimensions`

```python
data.imf_utils.get_dataflow_dimensions(dataflow_id=..., output_format='json')
```

Summary: Get Dataflow Dimensions

| Field | Value |
|---|---|
| Endpoint ID | `imf_utils.get_dataflow_dimensions` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/imf_utils/get_dataflow_dimensions` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `dataflow_id` | `yes` | `string` | `-` | The IMF dataflow ID. Use `list_dataflows()` to see available dataflows. |
| `output_format` | `no` | `string` | `json` | - |

---

### `imf_utils.list_dataflow_choices`

```python
data.imf_utils.list_dataflow_choices()
```

Summary: List Dataflow Choices

| Field | Value |
|---|---|
| Endpoint ID | `imf_utils.list_dataflow_choices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/imf_utils/list_dataflow_choices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

No query parameters.

---

### `imf_utils.list_dataflows`

```python
data.imf_utils.list_dataflows(output_format='json')
```

Summary: List Dataflows

| Field | Value |
|---|---|
| Endpoint ID | `imf_utils.list_dataflows` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/imf_utils/list_dataflows` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `output_format` | `no` | `string` | `json` | - |

---

### `imf_utils.list_port_id_choices`

```python
data.imf_utils.list_port_id_choices()
```

Summary: List Port Id Choices

| Field | Value |
|---|---|
| Endpoint ID | `imf_utils.list_port_id_choices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/imf_utils/list_port_id_choices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

No query parameters.

---

### `imf_utils.list_table_choices`

```python
data.imf_utils.list_table_choices()
```

Summary: List Table Choices

| Field | Value |
|---|---|
| Endpoint ID | `imf_utils.list_table_choices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/imf_utils/list_table_choices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

No query parameters.

---

### `imf_utils.list_tables`

```python
data.imf_utils.list_tables()
```

Summary: List Tables

| Field | Value |
|---|---|
| Endpoint ID | `imf_utils.list_tables` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/imf_utils/list_tables` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

No query parameters.

---

### `imf_utils.presentation_table`

```python
data.imf_utils.presentation_table(dataflow_group=None, table=None, country=None, frequency=None, dimension_values=None, limit=1, raw=False)
```

Summary: Presentation Table

| Field | Value |
|---|---|
| Endpoint ID | `imf_utils.presentation_table` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/imf_utils/presentation_table` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `dataflow_group` | `no` | `string | null` | `-` | The IMF dataflow group. See presentation_table_choices() for options. |
| `table` | `no` | `string | null` | `-` | The IMF presentation table ID. See presentation_table_choices() for options. |
| `country` | `no` | `string | null` | `-` | Country code to filter the data. Enter multiple codes by joining on '+'. See presentation_table_choices() for options. Typical values are ISO3 country codes. |
| `frequency` | `no` | `string | null` | `-` | The data frequency. See presentation_table_choices() for options. Typical values are 'A' (annual), 'Q' (quarter), 'M' (month), or 'D' (day). |
| `dimension_values` | `no` | `array | string | null` | `-` | accepts array values Dimension selection for filtering. Format: 'DIM_ID1:VAL1+VAL2.' See presentation_table_choices() and list_dataflow_choices() for available dimensions and values. |
| `limit` | `no` | `integer` | `1` | Maximum number of records to retrieve per series. |
| `raw` | `no` | `boolean` | `false` | Return presentation table as raw JSON data if True. |

---

### `imf_utils.presentation_table_choices`

```python
data.imf_utils.presentation_table_choices(dataflow_group=None, table=None, country=None, frequency=None)
```

Summary: Presentation Table Choices

| Field | Value |
|---|---|
| Endpoint ID | `imf_utils.presentation_table_choices` |
| HTTP | `GET` |
| Path | `/inner/v1/agent-data/imf_utils/presentation_table_choices` |
| SDK | `supported` |
| Host | `supported` |
| Notes | - |

#### Query parameters

| Param | Required | Type | Default | Notes |
|---|---|---|---|---|
| `dataflow_group` | `no` | `string | null` | `-` | - |
| `table` | `no` | `string | null` | `-` | - |
| `country` | `no` | `string | null` | `-` | - |
| `frequency` | `no` | `string | null` | `-` | - |
