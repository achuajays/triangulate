# Example: hiring debrief

Interviewer notes in, conflict table out. The classic use case.

```python
from triangulate import Triangulate

tri = Triangulate(backend="anthropic")  # or "gemini", "openai", "local"

result = tri.compare(
    sources=[
        ("interviewer_1", """
            Strong on system design, walked through a scalable cache layer
            without prompting. A bit quiet in the room, answers needed
            follow-up questions to open up. Good culture fit — collaborative
            and curious. Not much hands-on coding evidence, only whiteboard talk.
        """),
        ("interviewer_2", """
            Struggled when asked to design the cache layer, could not explain
            invalidation strategy. Excellent communicator though, very
            structured answers. Unsure about culture fit — seemed more focused
            on individual output than team work. Coding exercise was clean.
        """),
        ("interviewer_3", """
            Good communicator, very structured answers. System design was
            shallow, no mention of tradeoffs. Great culture fit, asked
            thoughtful questions about how the team works. Ran out of time
            for the coding exercise.
        """),
    ],
    dimensions=["system design", "communication", "culture fit", "coding"],
)

print(result.table())
print(result.to_markdown())
```

What comes out:

- **system design → conflict**: interviewer_1 says strong, interviewer_2 and
  interviewer_3 say weak. That disagreement is the debrief.
- **culture fit → conflict**: positive from 1 and 3, hesitant from 2.
- **coding → gap**: nobody fully covered it (one didn't probe, one saw it go
  well, one ran out of time) — the gap says "go look before deciding."

The package does not say hire or no-hire. It says: *these two dimensions are
where your interviewers did not see the same thing.*
