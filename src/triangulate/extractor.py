"""Extractor: runs a backend's extraction over every source."""

from __future__ import annotations

from typing import Sequence

from .base import Backend, Point

# A source input is (source_id, raw_text).
SourceInput = tuple[str, str]


def validate_sources(sources: Sequence[SourceInput]) -> list[SourceInput]:
    """Validate the (source_id, text) pairs, normalizing ids."""
    if not sources:
        raise ValueError("Need at least one source to compare.")
    normalized: list[SourceInput] = []
    seen: set[str] = set()
    for item in sources:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError(
                "Each source must be a (source_id, raw_text) pair, got: "
                f"{item!r}"
            )
        source_id, text = item
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"Invalid source_id: {source_id!r}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Source {source_id!r} has empty text.")
        source_id = source_id.strip()
        if source_id in seen:
            raise ValueError(f"Duplicate source_id: {source_id!r}")
        seen.add(source_id)
        normalized.append((source_id, text))
    return normalized


class Extractor:
    """Turns each source's raw text into structured points via a backend."""

    def __init__(self, backend: Backend):
        self.backend = backend

    def extract_all(
        self,
        sources: Sequence[SourceInput],
        dimensions: Sequence[str] | None = None,
    ) -> list[list[Point]]:
        """Extract points for each source, in input order.

        A backend failure on one source aborts the comparison: silently
        dropping a source would look exactly like a "gap", and gaps are
        supposed to mean something.
        """
        valid = validate_sources(sources)
        return [
            self.backend.extract(text, dimensions)
            for _, text in valid
        ]
