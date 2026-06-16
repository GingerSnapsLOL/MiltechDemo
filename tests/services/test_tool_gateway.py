"""Conformance tests: InMemoryToolGateway and MCPToolGateway must behave identically.

The MCP gateway is exercised over the in-memory transport (no subprocess), so it
runs offline while still going through the real MCP protocol.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from miltech_demo.core.config import Settings
from miltech_demo.mcp_server.server import build_mcp_server
from miltech_demo.schemas import GetDocumentInput, QueryIntelInput, SearchDocumentsInput
from miltech_demo.services import build_in_memory_gateway
from miltech_demo.services.mcp_gateway import MCPToolGateway
from miltech_demo.services.tool_gateway import ToolGateway


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(intel_db_path=tmp_path / "intel.db")


@pytest.fixture
def gateway(request: pytest.FixtureRequest, settings: Settings) -> Iterator[ToolGateway]:
    if request.param == "memory":
        yield build_in_memory_gateway(settings)
        return
    # MCP gateway over an in-memory connection to our FastMCP server.
    server = build_mcp_server(build_in_memory_gateway(settings))
    mcp_gateway = MCPToolGateway(
        lambda: create_connected_server_and_client_session(server._mcp_server)
    )
    yield mcp_gateway
    mcp_gateway.close()


pytestmark = pytest.mark.parametrize("gateway", ["memory", "mcp"], indirect=True)


def test_search_documents(gateway: ToolGateway) -> None:
    result = gateway.search_documents(SearchDocumentsInput(query="corridor"))
    assert result.count >= 1
    assert all(0.0 <= hit.score <= 1.0 for hit in result.hits)


def test_get_document_found(gateway: ToolGateway) -> None:
    result = gateway.get_document(GetDocumentInput(document_id="eastern-corridor"))
    assert result.found is True
    assert result.document is not None
    assert result.document.id == "eastern-corridor"


def test_get_document_missing(gateway: ToolGateway) -> None:
    result = gateway.get_document(GetDocumentInput(document_id="nope"))
    assert result.found is False
    assert result.document is None


def test_query_intel_db(gateway: ToolGateway) -> None:
    result = gateway.query_intel_db(QueryIntelInput(query="corridor"))
    assert result.count >= 1
    assert all(row.region for row in result.rows)
