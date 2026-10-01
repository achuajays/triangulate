# triangulate

*Find out where your sources disagree — before someone has to find out the hard way.*

Multiple free-text sources about the same subject, structured by topic, checked
for disagreement and gaps. Start with the [Quickstart](quickstart.md).

## The shape of the problem

The same pipeline applies wherever several accounts of one thing need comparing:

- Hiring debriefs — [example](examples/hiring.md)
- Medical second opinions — [example](examples/medical.md)
- Code review consolidation — [example](examples/code_review.md)
- Customer feedback rollups — [example](examples/feedback.md)

## Design

- **Pluggable backends** — `anthropic`, `openai`, `gemini`, or the zero-key
  `local` fallback, all behind one `extract(text, dimensions) -> list[Point]`
  interface. Custom backends are one method.
- **Restraint by design** — there is no `recommend()` function. The package
  surfaces conflicts, gaps, and low-confidence extractions; the decision stays
  with you.
- **Nothing silently vanishes** — points that fit no requested dimension land
  in `result.extra_points`; sources that never mention a dimension show as an
  explicit empty cell, not a blank.

## API surface

| Class | Role |
|---|---|
| `Triangulate` | facade: `compare(sources, dimensions) -> Result` |
| `Extractor` | runs a backend's extraction over every source |
| `Aligner` | matches points across sources to dimensions |
| `ConflictScan` | flags disagreements, gaps, low-confidence points |
| `Result` | `to_dict()`, `table()`, `to_markdown()` |

| Backend | Extra | Env var |
|---|---|---|
| `local` | — | — |
| `anthropic` | `triangulate[anthropic]` | `ANTHROPIC_API_KEY` |
| `openai` | `triangulate[openai]` | `OPENAI_API_KEY` |
| `gemini` | `triangulate[gemini]` | `GEMINI_API_KEY` |
