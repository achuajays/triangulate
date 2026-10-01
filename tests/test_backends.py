"""Backend registry and shared prompt/parsing tests (no network calls)."""

import pytest

from triangulate.backends import available_backends, create_backend
from triangulate.backends.shared import parse_extraction


class TestRegistry:
    def test_all_four_backends_registered(self):
        assert available_backends() == ["anthropic", "gemini", "local", "openai"]

    def test_local_backend_is_dependency_free(self):
        assert create_backend("local").name == "local"

    def test_aliases_resolve(self):
        assert create_backend("claude").name == "anthropic"
        assert create_backend("gpt").name == "openai"
        assert create_backend("google").name == "gemini"

    def test_unknown_backend_raises_helpfully(self):
        with pytest.raises(ValueError, match="Available"):
            create_backend("wizard")


class TestParseExtraction:
    def test_plain_json(self):
        pts = parse_extraction(
            '{"dimensions": [{"name": "system design", '
            '"points": [{"claim": "Strong", "confidence": 0.9}]}]}',
            ["system design"],
        )
        assert len(pts) == 1
        assert pts[0].dimension == "system design"
        assert pts[0].claim == "Strong"
        assert pts[0].confidence == 0.9

    def test_fenced_json_with_prose(self):
        raw = 'Sure! Here is the extraction:\n```json\n{"dimensions": [{"name": "communication", "points": [{"claim": "Clear", "confidence": 0.7}]}]}\n```\nHope that helps.'
        pts = parse_extraction(raw, ["communication"])
        assert len(pts) == 1
        assert pts[0].claim == "Clear"

    def test_near_miss_dimension_name_snaps(self):
        pts = parse_extraction(
            '{"dimensions": [{"name": "design of systems", '
            '"points": [{"claim": "X", "confidence": 0.5}]}]}',
            ["system design"],
        )
        assert pts[0].dimension == "system design"

    def test_unknown_dimension_is_dropped_when_dimensions_requested(self):
        pts = parse_extraction(
            '{"dimensions": [{"name": "weather", "points": [{"claim": "Sunny", "confidence": 0.5}]}]}',
            ["system design"],
        )
        assert pts == []

    def test_free_form_dimensions_are_kept_when_not_requested(self):
        pts = parse_extraction(
            '{"dimensions": [{"name": "Weather Patterns", "points": [{"claim": "Sunny", "confidence": 0.5}]}]}',
            None,
        )
        assert pts[0].dimension == "weather patterns"

    def test_bare_string_points_are_coerced(self):
        pts = parse_extraction(
            '{"dimensions": [{"name": "coding", "points": "Clean code"}]}',
            ["coding"],
        )
        assert len(pts) == 1
        assert pts[0].claim == "Clean code"
        assert pts[0].confidence == 0.5

    def test_garbage_returns_empty_not_crash(self):
        assert parse_extraction("The model declined to answer.", ["x"]) == []
        assert parse_extraction("", ["x"]) == []

    def test_confidence_out_of_range_is_clamped(self):
        pts = parse_extraction(
            '{"dimensions": [{"name": "x", "points": [{"claim": "c", "confidence": 7}]}]}',
            ["x"],
        )
        assert pts[0].confidence == 1.0
