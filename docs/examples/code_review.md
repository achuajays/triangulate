# Example: code review consolidation

Multiple reviewers' comments on one PR, grouped by **concern** (performance,
security, readability) instead of by reviewer — so "nobody flagged security"
is visible at a glance, and "two reviewers contradict each other on caching"
doesn't hide inside three comment threads.

```python
from triangulate import Triangulate

tri = Triangulate(backend="openai")  # or any backend

result = tri.compare(
    sources=[
        ("reviewer_1", """
            The retry loop in sync.py will hammer the API under load — add
            exponential backoff. The new cache layer is a nice improvement.
            Error handling around the network calls is thorough.
        """),
        ("reviewer_2", """
            Security: the token refresh flow logs credentials at debug level.
            Needs fixing before merge. Performance looks fine to me, the
            retry logic is already generous. Readability is good overall,
            though sync.py is getting long.
        """),
        ("reviewer_3", """
            LGTM on the feature side. Haven't looked at security. The cache
            layer adds complexity without measurements justifying it —
            I'd drop it. Tests cover the happy path only.
        """),
    ],
    dimensions=["performance", "security", "readability", "testing", "architecture"],
)

for c in result.conflicts:
    print(f"CONFLICT — {c.dimension}: {c.reason}")

print(result.to_markdown())
```

Why this beats reading three threads:

- **performance → conflict**: reviewer_1 wants backoff, reviewer_2 says retries
  are already generous. Two different beliefs about the same code.
- **architecture → conflict**: reviewer_2 praises the cache layer, reviewer_3
  wants it dropped.
- **security → gap**: reviewer_3 explicitly skipped it — the gap column makes
  "nobody looked" impossible to miss.
- **testing → gap**: only one reviewer covered it.

Point the same code at your actual PR comments (any text source works) and the
shape is identical.
