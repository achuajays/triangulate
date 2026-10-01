"""Anthropic backend: Claude via the Messages API.

Requires: pip install triangulate[anthropic]  (env var: ANTHROPIC_API_KEY)
"""

from __future__ import annotations

from typing import Sequence

from ..base import Backend, Point
from .shared import build_prompt, parse_extraction

DEFAULT_MODEL = "claude-sonnet-5-5"


class AnthropicBackend(Backend):
    """Claude-backed extraction. Adjust `model` to any current Claude model."""

    name = "anthropic"

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = 2000):
        self.model = model
        self.max_tokens = max_tokens

    def extract(self, text: str, dimensions: Sequence[str] | None = None) -> list[Point]:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "The anthropic backend needs the 'anthropic' package. "
                "Install it with: pip install triangulate[anthropic]"
            ) from exc

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=(
                "You extract structured data from text. You always reply with a "
                "single JSON object and nothing else."
            ),
            messages=[{"role": "user", "content": build_prompt(text, dimensions)}],
        )
        return parse_extraction(response.content[0].text, dimensions)
