"""End-to-end triangulate demo: three interviewers, one candidate.

Runs the full pipeline (extract -> align -> scan -> render) on the hiring
fixture with the zero-key local backend, then prints what each pluggable
backend would need so you can switch with one argument:

    python examples/run_hiring_demo.py            # local, no API keys
    python examples/run_hiring_demo.py --backend gemini
    python examples/run_hiring_demo.py --backend anthropic
    python examples/run_hiring_demo.py --backend openai
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from triangulate import Triangulate
from triangulate.backends import available_backends

FIXTURE = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_sources.json"
DIMENSIONS = ["system design", "communication", "culture fit", "coding"]

ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def load_sources():
    data = json.loads(FIXTURE.read_text())
    return [(d["source_id"], d["text"]) for d in data]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-b", "--backend", default="local",
        choices=available_backends(),
        help="extraction backend (default: local — no API key needed)",
    )
    parser.add_argument("-m", "--model", default=None, help="override the backend's model")
    args = parser.parse_args()

    env_var = ENV_VARS.get(args.backend)
    if env_var and not os.environ.get(env_var):
        print(f"note: {env_var} is not set; the {args.backend} backend will fail.",
              file=__import__("sys").stderr)

    kwargs = {"model": args.model} if args.model else {}
    tri = Triangulate(backend=args.backend, **kwargs)
    result = tri.compare(load_sources(), DIMENSIONS)

    print(f"backend: {args.backend}")
    print("=" * 72)
    print(result.table(width=120))
    print("=" * 72)
    print(result.to_markdown())

    print("\nsummary")
    print(f"  conflicts: {result.conflict_dimensions or 'none'}")
    print(f"  gaps:      {result.gap_dimensions or 'none'}")
    print(f"  low-confidence points needing review: {len(result.low_confidence_points)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
