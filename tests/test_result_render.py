"""Golden-file tests for Result rendering + to_dict shape.

Renders the same fixture through the deterministic local backend and compares
`to_markdown()` against a committed golden file. If you intentionally change
the rendering, regenerate the golden file:

    pytest tests/test_result_render.py --update-golden
"""

import json
from pathlib import Path

import pytest

from triangulate import Triangulate

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN = FIXTURES / "golden_report.md"
DIMENSIONS = ["system design", "communication", "culture fit", "coding"]


def _sources():
    data = json.loads((FIXTURES / "sample_sources.json").read_text())
    return [(d["source_id"], d["text"]) for d in data]


@pytest.fixture
def report():
    return Triangulate(backend="local").compare(_sources(), DIMENSIONS).to_markdown()


def test_markdown_matches_golden(report, pytestconfig):
    if not GOLDEN.exists() or pytestconfig.getoption("--update-golden"):
        GOLDEN.write_text(report)
        pytest.skip("golden file written; re-run to compare")
    assert report == GOLDEN.read_text()


def test_to_dict_shape():
    data = Triangulate(backend="local").compare(_sources(), DIMENSIONS).to_dict()
    assert set(data) == {
        "dimensions", "sources", "rows", "conflicts", "gaps",
        "low_confidence_points", "extra_points",
    }
    assert data["sources"] == ["interviewer_1", "interviewer_2", "interviewer_3"]
    for row in data["rows"]:
        assert set(row) == {"dimension", "by_source"}
        assert set(row["by_source"]) == set(data["sources"])
        for points in row["by_source"].values():
            for pt in points:
                assert set(pt) == {"claim", "confidence", "source_id"}


def test_table_contains_all_sources_and_dimensions():
    result = Triangulate(backend="local").compare(_sources(), DIMENSIONS)
    grid = result.table(width=120)
    for sid in result.source_ids:
        assert sid in grid
    for dim in DIMENSIONS:
        assert dim in grid
