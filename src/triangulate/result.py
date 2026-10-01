"""Result: the structured, inspectable, renderable output of a comparison."""

from __future__ import annotations

import shutil
import textwrap
from dataclasses import dataclass, field

from .aligner import Aligned
from .base import Point
from .conflict import Conflict, Gap, ScanReport

_NOT_MENTIONED = "—"


@dataclass
class DimensionView:
    """One dimension with what each source said about it (or not)."""

    dimension: str
    # source_id -> points; empty list means "not mentioned by this source".
    by_source: dict[str, list[Point]] = field(default_factory=dict)

    def mentions(self) -> list[str]:
        """Source ids that addressed this dimension."""
        return [sid for sid, pts in self.by_source.items() if pts]

    def claims_for(self, source_id: str) -> list[str]:
        """That source's claims on this dimension; empty when not mentioned."""
        return [pt.claim for pt in self.by_source.get(source_id, [])]

    def all_points(self) -> list[Point]:
        return [pt for pts in self.by_source.values() for pt in pts]


@dataclass
class Result:
    """Everything the pipeline found, in raw, table, and report form."""

    dimensions: list[str]
    source_ids: list[str]
    rows: list[DimensionView]
    conflicts: list[Conflict]
    gaps: list[Gap]
    low_confidence_points: list[Point]
    extra_points: list[Point] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Programmatic access
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        """Raw structured data, for anyone building their own UI on top."""
        return {
            "dimensions": self.dimensions,
            "sources": self.source_ids,
            "rows": [
                {
                    "dimension": row.dimension,
                    "by_source": {
                        sid: [
                            {
                                "claim": pt.claim,
                                "confidence": pt.confidence,
                                "source_id": pt.source_id,
                            }
                            for pt in pts
                        ]
                        for sid, pts in row.by_source.items()
                    },
                }
                for row in self.rows
            ],
            "conflicts": [
                {
                    "dimension": c.dimension,
                    "reason": c.reason,
                    "sources": c.sources,
                    "claims": [pt.claim for pt in c.points],
                }
                for c in self.conflicts
            ],
            "gaps": [
                {
                    "dimension": g.dimension,
                    "mentioned_by": g.mentioned_by,
                    "missing_from": g.missing_from,
                }
                for g in self.gaps
            ],
            "low_confidence_points": [
                {"source_id": pt.source_id, "dimension": pt.dimension,
                 "claim": pt.claim, "confidence": pt.confidence}
                for pt in self.low_confidence_points
            ],
            "extra_points": [
                {"source_id": pt.source_id, "dimension": pt.dimension,
                 "claim": pt.claim, "confidence": pt.confidence}
                for pt in self.extra_points
            ],
        }

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #

    def table(self, width: int | None = None) -> str:
        """A per-dimension x per-source grid, for printing or export.

        Args:
            width: total width of the grid; defaults to terminal width (min 100).
        """
        if not self.rows:
            return "(no dimensions)"
        term_width = width or max(shutil.get_terminal_size((100, 24)).columns, 100)
        n_sources = max(len(self.source_ids), 1)
        dim_w = min(24, max(12, term_width // 6))
        cell_w = max(10, (term_width - dim_w - n_sources * 3) // n_sources)

        def fit(text: str) -> str:
            lines = textwrap.wrap(
                text, width=cell_w, max_lines=3,
                placeholder=" …",
            ) or [""]
            return "\n".join(lines)

        header = (
            "dimension".ljust(dim_w) + " | "
            + " | ".join(sid[:cell_w].ljust(cell_w) for sid in self.source_ids)
        )
        lines = [header, "-" * len(header)]
        for row in self.rows:
            cells = []
            for sid in self.source_ids:
                claims = row.claims_for(sid)
                cell = "; ".join(claims) if claims else _NOT_MENTIONED
                cells.append(fit(cell).replace("\n", " "))
            lines.append(
                row.dimension[:dim_w].ljust(dim_w) + " | " + " | ".join(c.ljust(cell_w) for c in cells)
            )
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """A rendered report, ready to paste into a debrief doc."""
        parts: list[str] = ["# Triangulation report", ""]

        parts.append(f"**Sources:** {', '.join(f'`{s}`' for s in self.source_ids)}")
        parts.append("")

        parts.append("## Dimension matrix")
        parts.append("")
        parts.append("| dimension | " + " | ".join(self.source_ids) + " |")
        parts.append("|---" * (len(self.source_ids) + 1) + "|")
        for row in self.rows:
            cells = []
            for sid in self.source_ids:
                claims = row.claims_for(sid)
                text = " · ".join(claims) if claims else _NOT_MENTIONED
                cells.append(text.replace("|", "\\|").replace("\n", " "))
            parts.append(
                f"| {row.dimension} | " + " | ".join(cells) + " |"
            )
        parts.append("")

        if self.conflicts:
            parts.append("## Conflicts")
            parts.append("")
            for c in self.conflicts:
                parts.append(f"- **{c.dimension}** — {c.reason}")
                for pt in c.points:
                    parts.append(f"  - `{pt.source_id}`: {pt.claim} (confidence {pt.confidence:.2f})")
            parts.append("")

        if self.gaps:
            parts.append("## Gaps")
            parts.append("")
            for g in self.gaps:
                parts.append(
                    f"- **{g.dimension}** — mentioned by {', '.join(f'`{s}`' for s in g.mentioned_by)}; "
                    f"absent from {', '.join(f'`{s}`' for s in g.missing_from)}"
                )
            parts.append("")

        if self.low_confidence_points:
            parts.append("## Low-confidence extractions (review)")
            parts.append("")
            for pt in self.low_confidence_points:
                parts.append(
                    f"- `{pt.source_id}` **{pt.dimension}**: {pt.claim} ({pt.confidence:.2f})"
                )
            parts.append("")

        if self.extra_points:
            parts.append("## Unassigned points")
            parts.append("")
            for pt in self.extra_points:
                parts.append(f"- `{pt.source_id}`: {pt.claim}")
            parts.append("")

        parts.append(
            "_triangulate does not make the decision for you — it shows where "
            "your sources do not line up. Go look._"
        )
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    # Conveniences
    # ------------------------------------------------------------------ #

    @property
    def conflict_dimensions(self) -> list[str]:
        """Dimensions where sources disagree."""
        return [c.dimension for c in self.conflicts]

    @property
    def gap_dimensions(self) -> list[str]:
        """Dimensions only some sources addressed."""
        return [g.dimension for g in self.gaps]

def build_result(aligned: Aligned, scan: ScanReport) -> Result:
    """Assemble the final Result from alignment + scan output (pipeline-internal)."""
    rows = [
        DimensionView(dimension=dim, by_source=dict(aligned.by_source[dim]))
        for dim in aligned.dimensions
    ]
    return Result(
        dimensions=list(aligned.dimensions),
        source_ids=aligned.sources(),
        rows=rows,
        conflicts=scan.conflicts,
        gaps=scan.gaps,
        low_confidence_points=scan.low_confidence_points,
        extra_points=list(aligned.extra_points),
    )
