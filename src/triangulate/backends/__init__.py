"""Backend registry.

Backends are looked up by name: "local", "anthropic", "openai", or "gemini".
Provider adapters import their SDK lazily, so the core package stays
dependency-free and a missing SDK fails with a clear "install the extra"
message instead of an ImportError at import time.
"""

from __future__ import annotations

from typing import Callable

from ..base import Backend
from .local import LocalBackend

_BACKEND_FACTORIES: dict[str, Callable[[], Backend]] = {
    "local": LocalBackend,
    "anthropic": lambda: _load("AnthropicBackend", ".anthropic"),
    "openai": lambda: _load("OpenAIBackend", ".openai"),
    "gemini": lambda: _load("GeminiBackend", ".gemini"),
}

_ALIASES = {"claude": "anthropic", "gpt": "openai", "google": "gemini"}


def _load(class_name: str, module: str) -> Backend:
    import importlib

    mod = importlib.import_module(module, __package__)
    return getattr(mod, class_name)()


def create_backend(name: str, **kwargs) -> Backend:
    """Create a backend by name. Names: local, anthropic, openai, gemini."""
    key = name.strip().lower()
    key = _ALIASES.get(key, key)
    if key not in _BACKEND_FACTORIES:
        valid = ", ".join(sorted(_BACKEND_FACTORIES))
        raise ValueError(f"Unknown backend {name!r}. Available: {valid}")
    return _BACKEND_FACTORIES[key](**kwargs)


def available_backends() -> list[str]:
    """Names of all built-in backends, sorted."""
    return sorted(_BACKEND_FACTORIES)
