"""triangulate CLI: `triangulate compare sources.txt --backend gemini`"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .backends import available_backends
from .version import __version__


def _read_sources(path: str) -> list[tuple[str, str]]:
    """Read sources from a plain-text file.

    Format: lines of `=== source_id` headers, with the free text after each.
    """
    text = Path(path).read_text(encoding="utf-8")
    sources: list[tuple[str, str]] = []
    current_id: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("==="):
            if current_id is not None:
                sources.append((current_id, "\n".join(current_lines).strip()))
            current_id = line[3:].strip()
            current_lines = []
        elif current_id is not None:
            current_lines.append(line)
    if current_id is not None:
        sources.append((current_id, "\n".join(current_lines).strip()))
    if not sources:
        raise SystemExit(
            f"{path}: no `=== source_id` sections found. "
            "See docs/quickstart.md for the file format."
        )
    return sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="triangulate",
        description=(
            "Compare multiple free-text accounts of the same subject: find "
            "where they agree, disagree, and what's missing."
        ),
    )
    parser.add_argument("--version", action="version", version=f"triangulate {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    cmp_cmd = sub.add_parser("compare", help="Compare sources from a text file")
    cmp_cmd.add_argument("sources", help="Path to a sources file (=== source_id sections)")
    cmp_cmd.add_argument(
        "-b", "--backend", default="local", choices=available_backends(),
        help="Extraction backend (default: local, no API key needed)",
    )
    cmp_cmd.add_argument("-m", "--model", default=None, help="Override the backend's model")
    cmp_cmd.add_argument(
        "-d", "--dimensions", default=None,
        help="Comma-separated dimensions (inferred from the text if omitted)",
    )
    cmp_cmd.add_argument(
        "-o", "--output", default=None,
        help="Write the markdown report to a file instead of stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Import here so --version works with zero dependencies installed.
    from .api import Triangulate

    kwargs = {"model": args.model} if args.model else {}
    tri = Triangulate(backend=args.backend, **kwargs)
    result = tri.compare(
        sources=_read_sources(args.sources),
        dimensions=args.dimensions.split(",") if args.dimensions else None,
    )
    report = result.to_markdown()
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Wrote report to {args.output}", file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
