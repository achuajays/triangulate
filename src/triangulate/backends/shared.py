"""Shared system prompt + tolerant JSON parsing for all LLM backends.

The three provider adapters (anthropic, openai, gemini) use the exact same
extraction prompt and the same parsing, so results are comparable across
backends and a provider swap changes nothing downstream.
"""

from __future__ import annotations

import json
import re
from typing import Any, Sequence

from ..base import Point

MAX_POINTS_PER_DIMENSION = 5

# Plain-dict JSON schema. Provider-native schema objects differ per SDK, but all
# three APIs accept a plain JSON-Schema dict, and this keeps the three adapters
# byte-identical where it matters.
EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "points": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "claim": {"type": "string"},
                                "confidence": {"type": "number"},
                            },
                            "required": ["claim", "confidence"],
                        },
                    },
                },
                "required": ["name", "points"],
            },
        }
    },
    "required": ["dimensions"],
}


def build_prompt(text: str, dimensions: Sequence[str] | None) -> str:
    """Build the shared extraction prompt. Identical for every provider."""
    if dimensions:
        dims = "".join(f"- {d}\n" for d in dimensions)
        task = (
            "Extract what this account says about each dimension listed below. "
            "Include a dimension only if the text actually addresses it; omit "
            "dimensions the text does not mention."
        )
    else:
        dims = ""
        task = (
            "First identify the 3-8 most salient dimensions (topics) this account "
            "addresses, then extract what it says about each."
        )

    return f"""You are a precise extraction engine. {task}

For each point you extract:
- "claim": one short, self-contained sentence stating what this source says. Be
  faithful to the source's wording and stance; do not soften or normalize
  disagreements away.
- "confidence": 0.0-1.0, how sure you are that the text actually says this.

Return ONLY a JSON object matching this schema:
{{"dimensions": [{{"name": "<dimension>", "points": [{{"claim": "...", "confidence": 0.0}}]}}]}}

Dimensions:
{dims}
Text:
\"\"\"{text}\"\"\""""


def parse_extraction(raw: str, dimensions: Sequence[str] | None) -> list[Point]:
    """Parse an LLM's JSON reply into Points, tolerating the usual LLM messiness.

    Handles code fences, leading prose, single points per dimension, and
    dimensions that are near-misses of the requested names.
    """
    payload = _load_json(raw)
    if not isinstance(payload, dict):
        return []

    requested = [d.strip().lower() for d in dimensions] if dimensions else None

    points: list[Point] = []
    for entry in payload.get("dimensions") or []:
        if not isinstance(entry, dict):
            continue
        dim = _match_dimension(entry.get("name") or "", requested)
        if dim is None:
            continue
        raw_points = entry.get("points") or []
        # Backends sometimes return a bare string instead of a points list.
        if isinstance(raw_points, str):
            raw_points = [{"claim": raw_points, "confidence": 0.5}]
        for rp in raw_points:
            if not isinstance(rp, dict):
                continue
            claim = str(rp.get("claim") or "").strip()
            if not claim:
                continue
            try:
                confidence = float(rp.get("confidence", 0.8))
            except (TypeError, ValueError):
                confidence = 0.8
            points.append(Point(source_id="", dimension=dim, claim=claim, confidence=confidence))
    return points


def _load_json(raw: str) -> Any:
    """Extract a JSON object from a reply that may be fenced or wrapped in prose."""
    text = raw.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def _match_dimension(name: str, requested: Sequence[str] | None) -> str | None:
    """Return the requested dimension this entry matches, or its own name if free-form."""
    name_l = name.strip().lower()
    if not name_l:
        return None
    if requested is None:
        return name_l
    if name_l in requested:
        return name_l
    # Near-miss matching on prefix stems: "design of systems" ~ "system design".
    name_kws = {t[:5] for t in re.findall(r"[a-z0-9]+", name_l)}
    for req in requested:
        req_kws = {t[:5] for t in re.findall(r"[a-z0-9]+", req)}
        if name_kws and req_kws and (name_kws & req_kws):
            return req
    return None
