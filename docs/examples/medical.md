# Example: medical second opinion

Multiple specialists' notes on one patient. The value is structural: each
specialist saw the case through their own lens, and triangulate shows exactly
where the lenses disagree — which is precisely where a case conference should
start.

```python
from triangulate import Triangulate

tri = Triangulate(backend="gemini")  # or any backend

result = tri.compare(
    sources=[
        ("cardiologist", """
            58-year-old with exertional chest tightness, relieved by rest.
            ECG shows nonspecific ST changes. Ejection fraction preserved.
            Suspicious for stable angina; recommend stress testing.
            No arrhythmia observed on telemetry.
        """),
        ("pulmonologist", """
            Exertional dyspnea more prominent than chest pain. Spirometry
            suggests mild restriction. Given the dyspnea-predominant
            presentation, consider pulmonary causes before cardiac workup.
            No arrhythmia noted.
        """),
        ("internist", """
            presentation is atypical. Patient reports palpitations at night,
            which neither specialist note addresses. Exercise tolerance
            declining over three months. Family history of early cardiac
            disease.
        """),
    ],
    dimensions=[
        "primary symptom", "cardiac findings", "pulmonary findings",
        "recommended next step",
    ],
)

print(result.to_markdown())
```

What to look for in the output:

- **gaps** are the safety net: the internist noted nighttime palpitations that
  neither specialist addressed — that shows up as a dimension absent from two
  of three sources.
- **conflicts** like "dyspnea-predominant" vs "chest-tightness-predominant"
  come with a plain-language reason and the exact claims, ready for the
  case-conference doc.
- **low-confidence points** from any note get surfaced for human review rather
  than silently blended in.

As everywhere in triangulate: no diagnosis, no recommendation — only
*"here is where your sources don't line up."*
