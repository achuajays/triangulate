"""Tests for the Aligner: no LLM, pre-extracted points only."""

import pytest

from triangulate.aligner import Aligner
from triangulate.base import Point

SOURCES = [("a", "text a"), ("b", "text b"), ("c", "text c")]


def pts(*triples):
    """Build points quickly: (source_hint, dimension, claim)."""
    return [Point(source_id=s, dimension=d, claim=c) for s, d, c in triples]


class TestAlignsWithDimensions:
    def test_every_point_lands_in_exactly_one_dimension(self):
        extracted = [
            pts(("", "system design", "designed a cache layer"),
                ("", "communication", "clear structured answers")),
            pts(("", "system design", "struggled with cache invalidation")),
            pts(("", "communication", "good communicator")),
        ]
        aligned = Aligner().align(SOURCES, extracted, dimensions=["system design", "communication"])

        assert aligned.dimensions == ["system design", "communication"]
        total = sum(len(p) for buckets in aligned.by_source.values() for p in buckets.values())
        assert total == 4
        assert len(aligned.extra_points) == 0

    def test_unmentioned_dimension_is_explicit_empty_bucket(self):
        extracted = [pts(("", "system design", "solid design")), [], []]
        aligned = Aligner().align(SOURCES, extracted, dimensions=["system design", "culture fit"])

        assert aligned.by_source["culture fit"] == {"a": [], "b": [], "c": []}

    def test_source_ids_are_stamped(self):
        extracted = [pts(("", "system design", "solid design")), [], []]
        aligned = Aligner().align(SOURCES, extracted, dimensions=["system design"])

        assert aligned.by_source["system design"]["a"][0].source_id == "a"

    def test_near_miss_dimension_label_snaps_to_requested(self):
        extracted = [pts(("", "designing of systems", "designed a cache layer")), [], []]
        aligned = Aligner().align(SOURCES, extracted, dimensions=["system design"])

        assert aligned.dimensions == ["system design"]
        assert len(aligned.by_source["system design"]["a"]) == 1


class TestNeverSplits:
    def test_a_source_point_is_never_assigned_to_two_dimensions(self):
        # "cache layer" overlaps both dimensions; it must land in exactly one.
        extracted = [
            pts(("", "system design", "cache layer design strong")),
        ]
        aligned = Aligner().align(
            SOURCES[:1],
            extracted,
            dimensions=["system design", "cache layer performance"],
        )
        assignments = sum(
            1 for buckets in aligned.by_source.values() for p in buckets.values() if p
        )
        assert assignments == 1

    def test_weak_overlap_goes_to_extra_points_not_a_guess(self):
        extracted = [pts(("", "weather", "sunny and warm outside")), [], []]
        aligned = Aligner().align(SOURCES, extracted, dimensions=["system design", "communication"])

        assert aligned.extra_points and aligned.extra_points[0].source_id == "a"
        assert all(
            not any(p for p in buckets.values())
            for buckets in aligned.by_source.values()
        )


class TestDimensionInference:
    def test_infers_dimensions_from_points_when_none_given(self):
        extracted = [
            pts(("", "cache layer", "cache layer design was strong"),
                ("", "cache layer", "cache layer invalidation strategy")),
            pts(("", "cache layer", "cache layer was shaky")),
            pts(("", "communication", "communication clear and structured")),
        ]
        aligned = Aligner().align(SOURCES, extracted, dimensions=None)

        assert aligned.dimensions
        assert all(p.dimension in aligned.dimensions for p in (
            pt for buckets in aligned.by_source.values() for b in buckets.values() for pt in b
        ))


class TestValidation:
    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            Aligner().align(SOURCES, [pts(("", "x", "y"))], ["x"])

    def test_duplicate_dimensions_are_deduped(self):
        aligned = Aligner().align(
            SOURCES[:1], [pts(("", "x", "y"))], dimensions=["System Design", "system design"]
        )
        assert aligned.dimensions == ["system design"]
