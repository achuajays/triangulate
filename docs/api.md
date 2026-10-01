# API reference

The public surface is deliberately small: one facade, one result type, four backends.

## `Triangulate`

```python
from triangulate import Triangulate
```

The only class most users ever need.

### `Triangulate(backend="local", **backend_kwargs)`

| Arg | Type | Notes |
|---|---|---|
| `backend` | `str` or backend object | `"local"`, `"anthropic"`, `"openai"`, `"gemini"` (aliases: `claude`, `gpt`, `google`), or any object with an `extract(text, dimensions)` method |
| `model` | `str` | optional model override, passed to the named backend |
| other kwargs | — | forwarded to the backend constructor (e.g. `max_tokens` for Anthropic, `store` for Gemini) |

### `.compare(sources, dimensions=None) -> Result`

| Arg | Type | Notes |
|---|---|---|
| `sources` | `list[(source_id, text)]` | one pair per account of the same subject; ids must be unique and non-empty |
| `dimensions` | `list[str]` | topics to structure around; inferred from the text when omitted |

## `Result`

Everything the pipeline found, in raw, table, and report form.

| Member | Returns | Description |
|---|---|---|
| `conflicts` | `list[Conflict]` | dimensions where sources meaningfully disagree; each has `dimension`, `reason`, `sources`, `points` |
| `gaps` | `list[Gap]` | dimensions some sources addressed and others completely ignored; each has `dimension`, `mentioned_by`, `missing_from` |
| `low_confidence_points` | `list[Point]` | extractions below 0.5 confidence, surfaced for human review |
| `extra_points` | `list[Point]` | points that fit no requested dimension — nothing silently vanishes |
| `conflict_dimensions` | `list[str]` | just the names, for quick checks |
| `gap_dimensions` | `list[str]` | just the names |
| `to_dict()` | `dict` | raw structured data for building your own UI |
| `table(width=None)` | `str` | per-dimension × per-source grid for the terminal |
| `to_markdown()` | `str` | rendered report, ready to paste into a debrief doc |

## `Point`

One structured point extracted from one source, about one dimension.

| Field | Type | Notes |
|---|---|---|
| `source_id` | `str` | stamped by the pipeline |
| `dimension` | `str` | lowercase topic |
| `claim` | `str` | short standalone claim, faithful to the source's stance |
| `confidence` | `float` | 0.0–1.0; below 0.5 is surfaced for review |
| `keywords` | `list[str]` | salient terms, used for alignment |

## Backends

All four implement the same one-method interface:
`extract(text, dimensions=None) -> list[Point]`.

| Name | Extra install | Env var | Default model |
|---|---|---|---|
| `local` | — | — | — |
| `anthropic` | `triangulate[anthropic]` | `ANTHROPIC_API_KEY` | `claude-sonnet-5-5` |
| `openai` | `triangulate[openai]` | `OPENAI_API_KEY` | `gpt-5-mini` |
| `gemini` | `triangulate[gemini]` | `GEMINI_API_KEY` | `gemini-3.8-flash` |

Custom backend: any object with `extract(text, dimensions=None) -> list[Point]`.

## CLI

```
triangulate compare SOURCES_FILE [-b BACKEND] [-m MODEL] [-d "dim1, dim2"] [-o OUT.md]
```

`SOURCES_FILE` uses `=== source_id` section headers.
