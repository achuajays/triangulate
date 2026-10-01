# Example: customer feedback rollup

Many support tickets about one feature: where do complaints **agree**, where do
they **contradict** each other, and what is nobody talking about?

```python
from triangulate import Triangulate

tickets = [
    ("ticket_101", """
        The mobile app crashes when I upload photos larger than 10MB.
        Otherwise the upload flow is smooth. Support was responsive.
    """),
    ("ticket_102", """
        Uploads fail constantly on mobile, even for small files.
        Been like this for two weeks. Haven't heard back from support.
    """),
    ("ticket_103", """
        Love the new sharing feature. Desktop uploads work great.
        No complaints except the mobile app feels slow.
    """),
    ("ticket_104", """
        Mobile upload of photos works fine for me after the last update.
        The confusing part is the share dialog — too many steps.
    """),
]

tri = Triangulate(backend="local")  # zero API keys; swap in any LLM backend
result = tri.compare(
    sources=tickets,
    dimensions=["mobile uploads", "sharing", "support", "performance"],
)

print(result.table(width=140))
print(result.to_markdown())
```

Reading the output:

- **mobile uploads → conflict**: "crashes over 10MB" and "fails constantly"
  vs "works fine after the last update." That's not noise — it's probably a
  version or size-band-specific bug, and the conflicting claims are the clue.
- **support → conflict + gap**: "responsive" vs "haven't heard back," with one
  ticket silent on it.
- **sharing → mostly agreement**, with one ticket flagging dialog UX nobody
  else mentioned.

For a rollup over dozens of tickets, keep the local backend for a free first
pass, then re-run the conflicted dimensions through an LLM backend for
higher-fidelity extraction.
