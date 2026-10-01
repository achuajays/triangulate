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

## 3. Switch to a real model (one argument)

```python
tri = Triangulate(backend="gemini")   # GEMINI_API_KEY
tri = Triangulate(backend="anthropic")  # ANTHROPIC_API_KEY
tri = Triangulate(backend="openai")   # OPENAI_API_KEY

# Any other current model:
tri = Triangulate(backend="gemini", model="gemini-3.1-pro-preview")
tri = Triangulate(backend="anthropic", model="claude-haiku-4-5")
tri = Triangulate(backend="openai", model="gpt-5-mini")
```

Everything downstream of extraction — alignment, conflict scanning, rendering —
is identical for every backend, so switching providers changes nothing else.

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
