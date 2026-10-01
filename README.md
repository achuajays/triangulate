# triangulate

*Find out where your sources disagree — before someone has to find out the hard way.*

`triangulate` takes several people's free-text accounts of the same thing and tells
you where they **agree**, where they **genuinely disagree**, and what's **missing
entirely** — instead of just summarizing each one separately.

- Multiple interviewers' notes on one candidate
- Multiple doctors' notes on one patient
- Multiple reviewers' comments on one PR
- Multiple support tickets about one feature
- Multiple witness statements about one incident

**What it deliberately does not do:** make the underlying decision. There is no
`recommend()` function, on purpose. It only ever says *"here's where your sources
don't line up — go look."*

## Quickstart (zero API keys, zero cost)

```bash
pip install triangulate
```

```python
from triangulate import Triangulate

tri = Triangulate(backend="local")  # no API key needed

result = tri.compare(
    sources=[
        ("interviewer_1", "Strong on system design, a bit quiet in the room..."),
        ("interviewer_2", "Struggled when asked to design the cache layer..."),
        ("interviewer_3", "Good communicator, very structured answers..."),
    ],
    dimensions=["system design", "communication", "culture fit"],  # optional
)

print(result.to_markdown())
```

The `local` backend is a deterministic keyword fallback — good enough to try the
whole pipeline in the next five minutes. For real extraction quality, plug in an LLM.

## Pluggable backends

```python
tri = Triangulate(backend="anthropic")  # Claude  — pip install triangulate[anthropic]
tri = Triangulate(backend="openai")     # GPT     — pip install triangulate[openai]
tri = Triangulate(backend="gemini")     # Gemini  — pip install triangulate[gemini]
tri = Triangulate(backend="local")      # fallback — always available
```

| Backend | Package | Env var | Default model |
|---|---|---|---|
| `anthropic` | `triangulate[anthropic]` | `ANTHROPIC_API_KEY` | `claude-sonnet-5-5` |
| `openai` | `triangulate[openai]` | `OPENAI_API_KEY` | `gpt-5-mini` |
| `gemini` | `triangulate[gemini]` | `GEMINI_API_KEY` | `gemini-3.8-flash` |
| `local` | — (nothing) | — | — |

Swap providers without touching anything else — or pass any object implementing
`extract(text, dimensions) -> list[Point]`:

```python
tri = Triangulate(backend="gemini", model="gemini-3.1-pro-preview")
tri = Triangulate(backend=MyCustomBackend())  # duck-typed Backend
```

## The result object

```python
result.conflicts        # dimensions where sources meaningfully disagree
result.gaps             # dimensions only some sources addressed
result.table()          # per-dimension x per-source grid, for printing
result.to_markdown()    # rendered report, ready to paste into a debrief doc
result.to_dict()        # raw structured data, for building your own UI
result.low_confidence_points  # extractions to surface for human review
```

## CLI

```bash
triangulate compare notes.txt --backend gemini -d "system design, communication"
```

Sources file format (`=== source_id` sections):

```
=== interviewer_1
Strong on system design, a bit quiet in the room...

=== interviewer_2
Struggled when asked to design the cache layer...
```

## Examples

Runnable walkthroughs live in [`docs/examples/`](docs/examples/):

1. [Hiring debrief](docs/examples/hiring.md) — interviewer notes in, conflict table out
2. [Medical second opinion](docs/examples/medical.md) — specialists' notes on one case
3. [Code review consolidation](docs/examples/code_review.md) — comments grouped by concern
4. [Customer feedback rollup](docs/examples/feedback.md) — where complaints agree and contradict

Or run the end-to-end demo: `python examples/run_hiring_demo.py`

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests never call a real LLM. The full pipeline is covered end-to-end by the
deterministic `local` backend; provider adapters share one prompt and one parser.

## License

MIT
