from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from miltech_demo.api.main import app, get_llm
from miltech_demo.services.llm import FakeLLMProvider


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_llm] = FakeLLMProvider
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_llm_test_endpoint_returns_response(client: TestClient) -> None:
    response = client.post("/api/v1/llm/test", json={"prompt": "hello"})

    assert response.status_code == 200
    body = response.json()
    assert "hello" in body["text"]
    assert body["model"] == "fake-llm"


def test_llm_test_rejects_empty_prompt(client: TestClient) -> None:
    response = client.post("/api/v1/llm/test", json={"prompt": ""})
    assert response.status_code == 422
