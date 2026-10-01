"""The Triangulate facade: the only class most users ever need."""

from __future__ import annotations

from typing import Sequence

from .aligner import Aligner
from .backends import create_backend
from .base import Backend, Point
from .conflict import ConflictScan
from .extractor import Extractor, SourceInput, validate_sources
from .result import Result, build_result


class Triangulate:
    """Compare multiple free-text accounts of the same subject.

    Example:
        tri = Triangulate(backend="gemini")   # or anthropic / openai / local
        result = tri.compare(
            sources=[("alice", "..."), ("bob", "...")],
            dimensions=["system design", "communication"],
        )
        print(result.to_markdown())

    `backend` accepts either a backend name string ("local", "anthropic",
    "openai", "gemini") or any Backend instance, so custom backends drop in
    without touching this class.
    """

    def __init__(self, backend: str | Backend, **backend_kwargs):
        if isinstance(backend, str):
            self.backend: Backend = create_backend(backend, **backend_kwargs)
        elif callable(getattr(backend, "extract", None)):
            self.backend = backend  # any duck-typed Backend drops in
        else:
            raise TypeError(
                "backend must be a name ('local', 'anthropic', 'openai', 'gemini') "
                "or an object with an extract(text, dimensions) method"
            )
        self._extractor = Extractor(self.backend)
        self._aligner = Aligner()
        self._scan = ConflictScan()

    def compare(
        self,
        sources: Sequence[SourceInput],
        dimensions: Sequence[str] | None = None,
    ) -> Result:
        """Run the full pipeline: extract -> align -> scan -> Result."""
        valid = validate_sources(sources)
        extracted = self._extractor.extract_all(valid, dimensions)
        aligned = self._aligner.align(valid, extracted, dimensions)
        scan = self._scan.scan(aligned)
        return build_result(aligned, scan)
