"""OpenAI backend: GPT via Chat Completions.

Requires: pip install triangulate[openai]  (env var: OPENAI_API_KEY)
"""

from __future__ import annotations

from typing import Sequence

from ..base import Backend, Point
from .shared import build_prompt, parse_extraction

DEFAULT_MODEL = "gpt-5-mini"


class OpenAIBackend(Backend):
    """GPT-backed extraction. Adjust `model` to any current OpenAI model."""

    name = "openai"

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def extract(self, text: str, dimensions: Sequence[str] | None = None) -> list[Point]:
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "The openai backend needs the 'openai' package. "
                "Install it with: pip install triangulate[openai]"
            ) from exc

        client = openai.OpenAI()  # reads OPENAI_API_KEY
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured data from text. You always reply "
                        "with a single JSON object and nothing else."
                    ),
                },
                {"role": "user", "content": build_prompt(text, dimensions)},
            ],
            response_format={"type": "json_object"},
        )
        return parse_extraction(response.choices[0].message.content or "", dimensions)
