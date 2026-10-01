"""Gemini backend: Gemini 3.8 Flash via the Interactions API (google-genai >= 2).

Requires: pip install triangulate[gemini]  (env var: GEMINI_API_KEY)
"""

from __future__ import annotations

from typing import Sequence

from ..base import Backend, Point
from .shared import EXTRACTION_SCHEMA, build_prompt, parse_extraction

DEFAULT_MODEL = "gemini-3.8-flash"


class GeminiBackend(Backend):
    """Gemini-backed extraction. Adjust `model` to any current Gemini model."""

    name = "gemini"

    def __init__(self, model: str = DEFAULT_MODEL, store: bool = False):
        self.model = model
        self.store = store

    def extract(self, text: str, dimensions: Sequence[str] | None = None) -> list[Point]:
        try:
            from google import genai
        except ImportError as exc:
            raise ImportError(
                "The gemini backend needs the 'google-genai' package (>= 2.0). "
                "Install it with: pip install triangulate[gemini]"
            ) from exc

        client = genai.Client()  # reads GEMINI_API_KEY / GOOGLE_API_KEY
        interaction = client.interactions.create(
            model=self.model,
            input=build_prompt(text, dimensions),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": EXTRACTION_SCHEMA,
            },
            store=self.store,
        )
        return parse_extraction(interaction.output_text or "", dimensions)
