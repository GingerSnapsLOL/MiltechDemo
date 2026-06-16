"""OllamaProvider: an LLMProvider backed by a local Ollama server.

Isolates the ``ollama`` client so the rest of the codebase depends only on the
:class:`LLMProvider` interface. The client is injectable for testing.
"""

from typing import Any, Protocol, cast

import structlog
from ollama import Client

from miltech_demo.schemas import LLMRequest, LLMResponse
from miltech_demo.services.llm import LLMError, LLMProvider

logger = structlog.get_logger(__name__)


class _ChatClient(Protocol):
    """Minimal structural type for the Ollama client (eases testing)."""

    def chat(self, model: str, messages: Any, **kwargs: Any) -> Any: ...


class OllamaProvider(LLMProvider):
    """Generates text via a local Ollama server."""

    def __init__(self, model: str, base_url: str, client: _ChatClient | None = None) -> None:
        self._model = model
        self._client: _ChatClient = (
            client if client is not None else cast(_ChatClient, Client(host=base_url))
        )

    def generate(self, request: LLMRequest) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                options={"temperature": request.temperature},
            )
        except Exception as exc:  # noqa: BLE001 - re-raised as a typed error below
            logger.error("ollama_error", model=self._model, error=str(exc))
            raise LLMError(f"Ollama generation failed: {exc}") from exc

        text = response.message.content or ""
        return LLMResponse(text=text, model=self._model)
