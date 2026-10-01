"""End-to-end pipeline tests on the hiring fixture — local backend only.

Fast, free, deterministic: this is the "at least one full pipeline test with
zero API keys" requirement from the testing strategy.
"""

import json
from pathlib import Path

from triangulate import Aligner, ConflictScan, Extractor, Result, Triangulate
from triangulate.backends import LocalBackend

FIXTURES = Path(__file__).parent / "fixtures"
DIMENSIONS = ["system design", "communication", "culture fit", "coding"]


def _sources():
    data = json.loads((FIXTURES / "sample_sources.json").read_text())
    return [(d["source_id"], d["text"]) for d in data]


def test_full_pipeline_via_facade():
    result = Triangulate(backend="local").compare(_sources(), DIMENSIONS)

    assert isinstance(result, Result)
    assert result.dimensions == DIMENSIONS
    assert result.source_ids == ["interviewer_1", "interviewer_2", "interviewer_3"]
    assert len(result.rows) == len(DIMENSIONS)
    # Deterministic backend => identical output on a second run.
    again = Triangulate(backend="local").compare(_sources(), DIMENSIONS)
    assert again.to_markdown() == result.to_markdown()


def test_piecewise_pipeline_matches_facade():
    sources = _sources()
    backend = LocalBackend()
    extracted = Extractor(backend).extract_all(sources, DIMENSIONS)
    aligned = Aligner().align(sources, extracted, DIMENSIONS)
    scan = ConflictScan().scan(aligned)
    from triangulate.result import build_result

    piecewise = build_result(aligned, scan)
    facade = Triangulate(backend).compare(sources, DIMENSIONS)

    assert piecewise.to_dict() == facade.to_dict()


def test_inferred_dimensions_pipeline():
    result = Triangulate(backend="local").compare(_sources(), dimensions=None)

    assert result.dimensions
    assert result.rows


def test_extra_points_are_preserved_not_dropped():
    sources = _sources() + [("interviewer_4", "The office plants were green and the coffee was cold.")]
    result = Triangulate(backend="local").compare(sources, DIMENSIONS)

    # Off-topic content must not silently vanish.
    flat = [p["claim"] for row in result.to_dict()["rows"] for pts in row["by_source"].values() for p in pts]
    all_claims = flat + [p["claim"] for p in result.extra_points]
    assert any("coffee" in c for c in all_claims)
