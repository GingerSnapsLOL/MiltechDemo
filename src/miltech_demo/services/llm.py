"""LLMProvider abstraction: the pluggable LLM surface agents depend on.

Agents never import a concrete model client; they depend only on the
:class:`LLMProvider` interface, which is injected at runtime. Implementations:

- :class:`FakeLLMProvider` — deterministic, no I/O (default; keeps the demo
  local-first and tests offline).
- :class:`OllamaProvider` (in ``services.ollama_provider``) — calls a local
  Ollama server.

Selection is driven by ``settings.llm_provider``.
"""

import abc
from functools import lru_cache

from miltech_demo.core.config import Settings, get_settings
from miltech_demo.schemas import LLMRequest, LLMResponse


class LLMError(Exception):
    """Raised when an LLM provider fails to generate a response."""


class LLMProvider(abc.ABC):
    """The interface agents use for text generation."""

    @abc.abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response for ``request``."""


class FakeLLMProvider(LLMProvider):
    """Deterministic provider that echoes a trimmed prompt. No network I/O."""

    model_name = "fake-llm"

    def generate(self, request: LLMRequest) -> LLMResponse:
        prefix = f"{request.system.strip()} " if request.system else ""
        text = f"[fake-llm] {prefix}{request.prompt.strip()}"
        return LLMResponse(text=text, model=self.model_name)


def build_llm_provider(settings: Settings) -> LLMProvider:
    """Build the LLM provider selected by ``settings.llm_provider``."""
    if settings.llm_provider == "ollama":
        from miltech_demo.services.ollama_provider import OllamaProvider

        return OllamaProvider(
            model=settings.model_name,
            base_url=settings.ollama_base_url,
        )
    return FakeLLMProvider()


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the process-wide LLM provider built from settings."""
    return build_llm_provider(get_settings())
