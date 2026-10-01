# Quickstart

## 1. Install

```bash
pip install triangulate          # core + local backend, no API keys
pip install "triangulate[all]"   # + anthropic, openai, gemini SDKs
```

## 2. Run the pipeline with zero keys

```python
from triangulate import Triangulate

tri = Triangulate(backend="local")

result = tri.compare(
    sources=[
        ("interviewer_1", "Strong on system design, walked through a scalable cache layer. A bit quiet in the room."),
        ("interviewer_2", "Struggled when asked to design the cache layer. Excellent communicator, structured answers."),
        ("interviewer_3", "Good communicator. System design was shallow, no mention of tradeoffs."),
    ],
    dimensions=["system design", "communication"],
)

print(result.table())
print(result.to_markdown())
```

A longer, runnable version lives in `examples/run_hiring_demo.py` in the repo.

## 3. Switch to a real model (one argument)

```python
| Backend | Package | Env var | Default model |
|---|---|---|---|
| `anthropic` | `triangulate[anthropic]` | `ANTHROPIC_API_KEY` | `claude-sonnet-5-5` |
| `openai` | `triangulate[openai]` | `OPENAI_API_KEY` | `gpt-5-mini` |
| `gemini` | `triangulate[gemini]` | `GEMINI_API_KEY` | `gemini-3.8-flash` |
| `local` | — (nothing) | — | — |
```

Everything downstream of extraction — alignment, conflict scanning, rendering —
is identical for every backend, so switching providers changes nothing else. Any
current model string works via `model=...`.

## 4. From the terminal

```bash
triangulate compare sources.txt --backend local
triangulate compare sources.txt --backend gemini -d "design, communication" -o report.md
```

`sources.txt` uses `=== source_id` headers:

```
=== interviewer_1
Strong on system design...

=== interviewer_2
Struggled with the cache layer...
```

## What you get

- **`result.conflicts`** — dimensions where sources meaningfully disagree, with a
  plain-language reason.
- **`result.gaps`** — dimensions mentioned by some sources but completely absent
  from others.
- **`result.low_confidence_points`** — extractions below 0.5 confidence, surfaced
  for human review instead of trusted blindly.
- **`result.to_dict()`** — everything above as plain data.

It never tells you what to decide. It tells you where to look.
