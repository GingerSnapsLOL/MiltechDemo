import os
from types import SimpleNamespace
from typing import Any

import pytest

from miltech_demo.schemas import LLMRequest
from miltech_demo.services.llm import FakeLLMProvider, LLMError, LLMProvider
from miltech_demo.services.ollama_provider import OllamaProvider


class _StubClient:
    """Minimal stand-in for ollama.Client used in tests."""

    def __init__(self, content: str = "stub-answer") -> None:
        self.content = content
        self.calls: list[dict[str, Any]] = []

    def chat(self, model: str, messages: Any, **kwargs: Any) -> Any:
        self.calls.append({"model": model, "messages": messages, "kwargs": kwargs})
        return SimpleNamespace(message=SimpleNamespace(content=self.content))


def test_fake_provider_is_deterministic() -> None:
    provider = FakeLLMProvider()
    first = provider.generate(LLMRequest(prompt="hello"))
    second = provider.generate(LLMRequest(prompt="hello"))

    assert first == second
    assert "hello" in first.text
    assert first.model == "fake-llm"


def test_ollama_provider_builds_request_and_parses() -> None:
    stub = _StubClient("the answer")
    provider = OllamaProvider(model="m1", base_url="http://x", client=stub)

    response = provider.generate(LLMRequest(prompt="hi", system="sys", temperature=0.3))

    assert response.text == "the answer"
    assert response.model == "m1"
    call = stub.calls[0]
    assert call["model"] == "m1"
    assert [m["role"] for m in call["messages"]] == ["system", "user"]
    assert call["kwargs"]["options"]["temperature"] == 0.3


def test_ollama_provider_wraps_errors() -> None:
    class _Boom:
        def chat(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("connection refused")

    provider = OllamaProvider(model="m", base_url="x", client=_Boom())
    with pytest.raises(LLMError):
        provider.generate(LLMRequest(prompt="hi"))


@pytest.fixture(params=["fake", "ollama"])
def provider(request: pytest.FixtureRequest) -> LLMProvider:
    if request.param == "fake":
        return FakeLLMProvider()
    return OllamaProvider(model="m", base_url="x", client=_StubClient("ok"))


def test_provider_conformance(provider: LLMProvider) -> None:
    response = provider.generate(LLMRequest(prompt="anything"))
    assert response.text
    assert response.model


@pytest.mark.skipif(
    not os.getenv("MILTECH_OLLAMA_TEST"),
    reason="requires a running Ollama server (set MILTECH_OLLAMA_TEST=1)",
)
def test_ollama_real_server() -> None:  # pragma: no cover - opt-in integration
    from miltech_demo.core.config import get_settings

    settings = get_settings()
    provider = OllamaProvider(model=settings.model_name, base_url=settings.ollama_base_url)
    response = provider.generate(LLMRequest(prompt="Say hello in one word."))
    assert response.text
