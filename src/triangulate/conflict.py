"""ConflictScan: flags disagreements and gaps across the aligned result.

Deliberately produces no recommendation — the whole trust story of this
package is "here is where your sources don't line up, go look."
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .aligner import Aligned
from .base import Point, fuzzy_tokens

# Negation / antonym cues that suggest two claims about the same dimension
# take opposite stances.
_NEGATION_CUES = (
    "not ", "no ", "never", "without", "lacked", "lacks", "lack of",
    "failed", "fails", "unable", "struggled", "struggles", "weak", "poor",
    "missing", "absent", "avoided", "avoids", "declined", "refused",
    "insufficient", "inadequate", "couldn't", "could not", "did not",
    "didn't", "doesn't", "does not", "isn't", "is not", "won't", "would not",
    "unsure", "unclear", "doubt", "concern", "hesitant", "worried",
    "ran out",
)
_POSITIVE_CUES = (
    "strong", "excellent", "good", "great", "outstanding", "effective",
    "skilled", "solid", "capable", "clear", "thorough", "consistent",
    "impressive", "well", "helpful", "confident", "improved", "works",
    "clean", "fast", "smooth",
)
_LOW_CONFIDENCE = 0.5


@dataclass
class Conflict:
    """A dimension where sources meaningfully disagree."""

    dimension: str
    reason: str
    sources: list[str] = field(default_factory=list)
    points: list[Point] = field(default_factory=list)


@dataclass
class Gap:
    """A dimension some sources addressed but others completely ignored."""

    dimension: str
    mentioned_by: list[str] = field(default_factory=list)
    missing_from: list[str] = field(default_factory=list)


@dataclass
class ScanReport:
    """The scan outcome, kept inspectable rather than collapsed into a boolean."""

    conflicts: list[Conflict] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)
    low_confidence_points: list[Point] = field(default_factory=list)


class ConflictScan:
    """Scans an Aligned result for disagreements, gaps, and shaky extractions."""

    def scan(self, aligned: Aligned) -> ScanReport:
        report = ScanReport()
        for dim in aligned.dimensions:
            buckets = aligned.by_source[dim]
            mentioned = {
                sid: pts for sid, pts in buckets.items() if pts
            }
            all_dim_points = [pt for pts in mentioned.values() for pt in pts]

            report.low_confidence_points.extend(
                pt for pt in all_dim_points if pt.confidence < _LOW_CONFIDENCE
            )

            if len(mentioned) >= 2:
                self._detect_conflict(dim, mentioned, report)

            if 0 < len(mentioned) < len(buckets):
                report.gaps.append(
                    Gap(
                        dimension=dim,
                        mentioned_by=sorted(mentioned),
                        missing_from=sorted(sid for sid in buckets if not buckets[sid]),
                    )
                )
        return report

    def _detect_conflict(
        self,
        dim: str,
        mentioned: dict[str, list[Point]],
        report: ScanReport,
    ) -> None:
        positives = [sid for sid, pts in mentioned.items() if _any(pts, "pos")]
        negatives = [
            sid for sid, pts in mentioned.items()
            if _any(pts, "neg") and sid not in positives
        ]

        if positives and negatives:
            involved = sorted(set(positives) | set(negatives))
            report.conflicts.append(
                Conflict(
                    dimension=dim,
                    reason=(
                        f"Some sources report a positive assessment ({', '.join(positives)}) "
                        f"while others report a negative one ({', '.join(negatives)})."
                    ),
                    sources=involved,
                    points=[pt for sid in involved for pt in mentioned[sid]],
                )
            )
            return

        # No stance flip: still flag *meaningfully different* claims about the
        # same dimension — different points from different sources that barely
        # overlap in content are worth a human look.
        sids = sorted(mentioned)
        for i in range(len(sids)):
            for j in range(i + 1, len(sids)):
                if not _claims_diverge(mentioned[sids[i]], mentioned[sids[j]]):
                    continue
                report.conflicts.append(
                    Conflict(
                        dimension=dim,
                        reason=(
                            f"{sids[i]} and {sids[j]} made materially different "
                            f"claims about '{dim}'."
                        ),
                        sources=[sids[i], sids[j]],
                        points=mentioned[sids[i]] + mentioned[sids[j]],
                    )
                )
                return  # one flag per dimension


def _any(points: list[Point], stance: str) -> bool:
    return any(_stance(pt.claim) == stance for pt in points)


def _stance(text: str) -> str | None:
    """The stance this claim takes: 'pos', 'neg', or None (neutral/informational).

    First-cue-wins: whichever stance cue appears earliest in the claim decides.
    'Strong on system design, walked through a scalable cache layer without
    prompting' is positive despite the trailing 'without' — the earliest cue
    ('strong') is the writer's actual stance.
    """
    lowered = text.lower()
    best: tuple[int, str] | None = None
    for cue in _NEGATION_CUES:
        idx = lowered.find(cue)
        if idx != -1 and (best is None or idx < best[0]):
            best = (idx, "neg")
    for cue in _POSITIVE_CUES:
        idx = lowered.find(cue)
        if idx != -1 and (best is None or idx < best[0]):
            best = (idx, "pos")
    return best[1] if best else None


def _claims_diverge(a: list[Point], b: list[Point]) -> bool:
    """True when two sources' claims about a dimension share too little content.

    Uses numbers as a hard signal (3 issues vs 10 issues is a real conflict
    even when wording is identical) and keyword overlap otherwise.
    """
    a_nums = _numbers(a)
    b_nums = _numbers(b)
    if a_nums and b_nums:
        if all(abs(x - y) > max(0.1 * max(abs(x), abs(y)), 1e-9)
               for x in a_nums for y in b_nums):
            return True
    tokens_a = {t for pt in a for t in fuzzy_tokens(pt.claim)}
    tokens_b = {t for pt in b for t in fuzzy_tokens(pt.claim)}
    if not tokens_a or not tokens_b:
        return False
    overlap = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    return overlap < 0.2


def _numbers(points: list[Point]) -> list[float]:
    out: list[float] = []
    for pt in points:
        for match in re.findall(r"\d+(?:\.\d+)?", pt.claim):
            out.append(float(match))
    return out
