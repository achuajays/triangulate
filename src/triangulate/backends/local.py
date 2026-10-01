"""Local backend: keyword-based extraction, zero API keys, zero cost, deterministic."""

from __future__ import annotations

import re
from typing import Sequence

from ..base import Backend, Point, fuzzy_tokens, keywords

# Cues that suggest the writer is characterizing rather than reporting.
_CLUE_PREFIXES = (
    "struggled", "excellent", "strong", "good", "great", "poor", "weak",
    "outstanding", "impressive", "lacked", "lacks", "failed", "fails",
    "effective", "ineffective", "skilled", "unskilled", "quiet", "confident",
    "communicat", "clear", "unclear", "helpful", "unhelpful", "thorough",
)


class LocalBackend(Backend):
    """A dependency-free fallback so the quickstart runs with no API key at all.

    Heuristic, not smart: it splits text into sentences, assigns each sentence
    to the provided dimension it overlaps most (or a keyword-cluster when no
    dimensions are given), and keeps sentences that look like characterizations.
    Good enough to prove the end-to-end loop deterministically; swap in an LLM
    backend for real extraction quality.
    """

    name = "local"

    def extract(self, text: str, dimensions: Sequence[str] | None = None) -> list[Point]:
        sentences = _sentences(text)
        if not sentences:
            return []

        if dimensions:
            dim_list = [d.strip().lower() for d in dimensions if d.strip()]
        else:
            dim_list = self._infer_dimensions(sentences)

        points: list[Point] = []
        for sentence in sentences:
            s_kws = keywords(sentence)
            if not s_kws:
                continue
            best_dim, best_score = None, 0
            for dim in dim_list:
                score = len(fuzzy_tokens(sentence) & fuzzy_tokens(dim))
                if score > best_score:
                    best_dim, best_score = dim, score
            # No overlap with any requested dimension: label it "general" so
            # the Aligner can set it aside into extra_points instead of
            # guessing a dimension it does not belong to.
            if best_dim is None:
                best_dim = "general"
            points.append(
                Point(
                    source_id="",
                    dimension=best_dim,
                    claim=sentence,
                    confidence=0.5,
                    keywords=s_kws,
                )
            )
        return points

    def _infer_dimensions(self, sentences: list[str]) -> list[str]:
        """Cluster sentence keywords into topic buckets when no dimensions are given."""
        counts: dict[str, int] = {}
        for sentence in sentences:
            for kw in keywords(sentence):
                counts[kw] = counts.get(kw, 0) + 1
        # Prefer multiword phrases from the text, then fall back to frequent terms.
        phrases = re.findall(
            r"\b([a-z]+(?:\s+[a-z]+){1,2})\b", " ".join(sentences).lower()
        )
        phrase_counts: dict[str, int] = {}
        for p in phrases:
            phrase_counts[p] = phrase_counts.get(p, 0) + 1
        ranked = sorted(phrase_counts.items(), key=lambda kv: (-kv[1], -len(kv[0])))
        dims = [p for p, c in ranked if c >= 2 and len(p) > 8][:4]
        if not dims:
            freq = sorted(counts.items(), key=lambda kv: -kv[1])
            dims = [w for w, c in freq if c >= 2][:4] or ["general"]
        return dims


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]
