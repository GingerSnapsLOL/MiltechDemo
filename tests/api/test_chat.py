from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from miltech_demo.api.main import app, get_gateway, get_llm
from miltech_demo.core.config import Settings
from miltech_demo.services import FakeLLMProvider, build_in_memory_gateway
from miltech_demo.services.tool_gateway import ToolGateway


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    gateway: ToolGateway = build_in_memory_gateway(Settings(intel_db_path=tmp_path / "intel.db"))
    app.dependency_overrides[get_gateway] = lambda: gateway
    app.dependency_overrides[get_llm] = FakeLLMProvider
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_chat_returns_answer_evidence_and_trace(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"query": "eastern corridor activity"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert isinstance(body["evidence"], list)
    assert body["evidence"]  # eastern-corridor matches, so evidence is present
    assert len(body["agent_trace"]) == 4


def test_chat_evidence_items_are_well_formed(client: TestClient) -> None:
    body = client.post("/api/v1/chat", json={"query": "corridor"}).json()
    first = body["evidence"][0]
    assert first["document_id"]
    assert 0.0 <= first["relevance_score"] <= 1.0


def test_chat_rejects_empty_query(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"query": ""})
    assert response.status_code == 422
