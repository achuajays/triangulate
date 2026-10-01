"""Shared data model and the backend interface every provider implements."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "if", "then", "so", "because", "as", "of", "at",
    "by", "for", "with", "about", "into", "to", "from", "in", "on", "off",
    "over", "under", "it", "its", "this", "that", "these", "those", "their",
    "his", "her", "they", "he", "she", "we", "you", "i", "not", "no", "very",
    "when", "while", "than", "has", "have", "had", "do", "does", "did", "just",
}


@dataclass
class Point:
    """One structured point extracted from one source, about one dimension.

    Attributes:
        source_id: which source this point came from ("" until stamped by the pipeline).
        dimension: the topic/dimension this point is about, lowercase.
        claim: what the source said, as a short standalone claim.
        confidence: extraction confidence in [0.0, 1.0]; low values should be
            surfaced for human review rather than trusted blindly.
        keywords: salient terms used for matching/alignment and the local backend.
    """

    source_id: str
    dimension: str
    claim: str
    confidence: float = 0.8
    keywords: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.dimension = self.dimension.strip().lower()
        self.claim = self.claim.strip()
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        if not self.keywords:
            self.keywords = keywords(self.claim)


def keywords(text: str) -> list[str]:
    """Lowercase alphanumeric tokens with stopwords removed, deduplicated in order."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    seen: set[str] = set()
    out: list[str] = []
    for w in words:
        if len(w) > 2 and w not in _STOPWORDS and w not in seen:
            seen.add(w)
            out.append(w)
    return out


def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    """Jaccard similarity between two token sets (0.0 when both are empty)."""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def fuzzy_tokens(text: str) -> set[str]:
    """Prefix-stemmed keyword tokens (first 5 chars) for tolerant matching.

    Crude but effective: 'designed' and 'design', 'communicator' and
    'communication' collapse to the same prefix, so dimension matching does
    not hinge on exact inflections.
    """
    return {w[:5] for w in keywords(text)}


class Backend(ABC):
    """The small interface every model backend implements.

    A backend's only job is `extract(text, dimensions) -> list[Point]`: turn one
    source's raw text into structured points per dimension. Everything else —
    aligning points across sources, scanning for conflicts and gaps — is
    backend-independent, so swapping providers never touches the rest of the
    pipeline.
    """

    name: str = "backend"

    @abstractmethod
    def extract(self, text: str, dimensions: Sequence[str] | None = None) -> list[Point]:
        """Extract structured points from one source's raw text.

        Args:
            text: one source's free-text account.
            dimensions: topics to structure around. Backends must return a point
                for every dimension actually addressed; when None, infer a
                reasonable set from the text itself.
        Returns:
            Points with source_id set to "" (the pipeline stamps the real id).
        """
        raise NotImplementedError
