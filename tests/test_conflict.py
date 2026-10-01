"""Tests for ConflictScan: no LLM, pre-aligned structures only."""

from triangulate.aligner import Aligned
from triangulate.base import Point
from triangulate.conflict import ConflictScan

SID = "interviewer_1"
OTHER = "interviewer_2"


def make_aligned(dim, a_points, b_points, sources=(SID, OTHER)):
    return Aligned(
        dimensions=[dim],
        by_source={dim: {sid: list(pts) for sid, pts in zip(sources, (a_points, b_points))}},
    )


def pt(claim, conf=0.9):
    return Point(source_id="", dimension="d", claim=claim, confidence=conf)


def test_positive_vs_negative_is_a_conflict():
    aligned = make_aligned(
        "system design",
        [pt("Strong on system design, scalable cache layer")],
        [pt("Struggled to design the cache layer, failed on invalidation")],
    )
    report = ConflictScan().scan(aligned)

    assert [c.dimension for c in report.conflicts] == ["system design"]
    assert "positive" in report.conflicts[0].reason
    assert set(report.conflicts[0].sources) == {SID, OTHER}


def test_agreement_is_not_a_conflict():
    aligned = make_aligned(
        "system design",
        [pt("Strong system design, solid cache layer")],
        [pt("Strong system design, solid cache approach")],
    )
    report = ConflictScan().scan(aligned)

    assert report.conflicts == []


def test_gap_when_one_source_is_silent():
    aligned = make_aligned(
        "culture fit",
        [pt("Great culture fit, collaborative")],
        [],
    )
    report = ConflictScan().scan(aligned)

    assert len(report.gaps) == 1
    assert report.gaps[0].mentioned_by == [SID]
    assert report.gaps[0].missing_from == [OTHER]


def test_no_gap_when_everyone_mentioned_it():
    aligned = make_aligned(
        "culture fit",
        [pt("Great culture fit")],
        [pt("Good culture fit, collaborative")],
    )
    report = ConflictScan().scan(aligned)

    assert report.gaps == []


def test_numeric_claims_that_disagree_are_conflicts():
    aligned = make_aligned(
        "ticket volume",
        [pt("Around 3 issues reported this week")],
        [pt("Around 30 issues reported this week")],
    )
    report = ConflictScan().scan(aligned)

    assert report.conflicts, "3 vs 30 should be flagged"


def test_low_confidence_points_are_surfaced_for_review():
    aligned = make_aligned(
        "system design",
        [pt("Maybe strong on design?", conf=0.3)],
        [pt("Struggled with design", conf=0.9)],
    )
    report = ConflictScan().scan(aligned)

    assert len(report.low_confidence_points) == 1
    assert report.low_confidence_points[0].confidence == 0.3


def test_silent_sources_are_not_conflicts():
    # Only one source mentioned it: nothing to disagree with, just a gap.
    aligned = make_aligned("communication", [pt("Very structured communicator")], [])
    report = ConflictScan().scan(aligned)

    assert report.conflicts == []
    assert report.gaps != []
