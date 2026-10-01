"""Aligner: matches extracted points across sources to the same dimension."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Sequence

from .base import Point, fuzzy_tokens, keywords
from .extractor import SourceInput, validate_sources


@dataclass
class Aligned:
    """The aligned result: per dimension, what each source said.

    Attributes:
        dimensions: dimension names in order.
        by_source: dimension -> source_id -> that source's points on it
            (an empty list means the source did not mention the dimension).
        extra_points: points that could not confidently be assigned to any
            requested dimension — never dropped, so nothing silently vanishes.
    """

    dimensions: list[str]
    by_source: dict[str, dict[str, list[Point]]]
    extra_points: list[Point] = field(default_factory=list)

    def sources(self) -> list[str]:
        """Source ids, in the order they were given."""
        if not self.by_source:
            return []
        first = next(iter(self.by_source.values()))
        return list(first.keys())


class Aligner:
    """Assigns every extracted point to exactly one dimension.

    Invariant (this is what the tests pin down): a source's points are never
    split across two dimensions. Each point is assigned once, to the single
    best-matching dimension, or set aside into `extra_points`.
    """

    # A point must share at least this fraction of its keywords with the best
    # dimension's keywords to be assigned on keyword overlap alone.
    MIN_OVERLAP = 0.3

    def align(
        self,
        sources: Sequence[SourceInput],
        extracted: Sequence[Sequence[Point]],
        dimensions: Sequence[str] | None = None,
    ) -> Aligned:
        valid = validate_sources(sources)
        if len(extracted) != len(valid):
            raise ValueError(
                f"Got {len(extracted)} extraction results for "
                f"{len(valid)} sources; they must be parallel."
            )
        source_ids = [sid for sid, _ in valid]

        if dimensions:
            dim_list = self._dedupe([d.strip().lower() for d in dimensions if d.strip()])
        else:
            dim_list = self._infer_dimensions(
                [pt for pts in extracted for pt in pts]
            )

        # Empty bucket per (dimension, source) — "not mentioned" is explicit.
        by_source: dict[str, dict[str, list[Point]]] = {
            dim: {sid: [] for sid in source_ids} for dim in dim_list
        }
        dim_keywords = {dim: fuzzy_tokens(dim) for dim in dim_list}

        extra: list[Point] = []
        for sid, points in zip(source_ids, extracted):
            for point in points:
                target = self._match(point, dim_list, dim_keywords)
                if target is None:
                    extra.append(replace(point, source_id=sid))
                else:
                    by_source[target][sid].append(replace(point, source_id=sid))

        return Aligned(dimensions=dim_list, by_source=by_source, extra_points=extra)

    def _match(
        self,
        point: Point,
        dim_list: list[str],
        dim_keywords: dict[str, set[str]],
    ) -> str | None:
        """Return the one dimension this point belongs to, or None to set it aside."""
        # Fast path: the extractor echoed a requested dimension name.
        if point.dimension in dim_keywords:
            return point.dimension

        kw = fuzzy_tokens(point.claim)
        scores = {dim: len(kw & dim_keywords[dim]) for dim in dim_list}
        best = max(scores, key=lambda d: scores[d]) if scores else None
        if best is None or scores[best] == 0:
            return None

        total = sum(scores.values())
        if scores[best] >= 2 and scores[best] / total >= self.MIN_OVERLAP:
            return best

        # Weak signal (a single shared keyword): accept only when unambiguous
        # or when the extractor's own dimension label agrees.
        if total == 1:
            return best
        label = point.dimension
        if best in label or label in best:
            return best
        return None

    def _dedupe(self, dims: list[str]) -> list[str]:
        seen: set[str] = set()
        out = []
        for d in dims:
            if d not in seen:
                seen.add(d)
                out.append(d)
        return out or ["general"]

    def _infer_dimensions(self, points: list[Point]) -> list[str]:
        """Infer a dimension set from extracted points when none were given.

        Prefers the extractor's own per-point dimension labels (LLM backends
        return meaningful ones); falls back to frequent-phrase extraction.
        """
        import re

        labels: list[str] = []
        seen: set[str] = set()
        for pt in points:
            label = pt.dimension.strip().lower()
            if label and label not in seen:
                seen.add(label)
                labels.append(label)
        if len(labels) >= 2:
            return labels[:8]

        counts: dict[str, int] = {}
        for pt in points:
            for kw in pt.keywords:
                counts[kw] = counts.get(kw, 0) + 1
        text = " ".join(pt.claim for pt in points).lower()
        phrase_counts: dict[str, int] = {}
        for phrase in re.findall(r"\b([a-z]+(?:\s+[a-z]+){1,2})\b", text):
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        ranked = sorted(phrase_counts.items(), key=lambda kv: (-kv[1], -len(kv[0])))
        dims = [p for p, c in ranked if c >= 2][:5]
        if not dims:
            freq = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
            dims = [w for w, c in freq if c >= 2][:5]
        return self._dedupe(dims or labels or ["general"])
