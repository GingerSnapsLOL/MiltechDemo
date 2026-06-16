from pathlib import Path

import pytest

from miltech_demo.core.config import Settings
from miltech_demo.mcp_server.server import build_mcp_server
from miltech_demo.services import build_tool_gateway
from miltech_demo.services.tool_gateway import ToolGateway


@pytest.fixture
def gateway(tmp_path: Path) -> ToolGateway:
    return build_tool_gateway(Settings(intel_db_path=tmp_path / "intel.db"))


async def test_tools_are_registered(gateway: ToolGateway) -> None:
    server = build_mcp_server(gateway)
    tools = await server.list_tools()
    names = {tool.name for tool in tools}
    assert {"search_documents", "get_document", "query_intel_db"} <= names


async def test_search_documents_tool_returns_structured_output(gateway: ToolGateway) -> None:
    server = build_mcp_server(gateway)
    _content, structured = await server.call_tool("search_documents", {"query": "corridor"})

    assert structured["query"] == "corridor"
    assert structured["count"] >= 1
    assert all(0.0 <= hit["score"] <= 1.0 for hit in structured["hits"])


async def test_query_intel_db_tool(gateway: ToolGateway) -> None:
    server = build_mcp_server(gateway)
    _content, structured = await server.call_tool("query_intel_db", {"query": "corridor"})

    assert structured["count"] >= 1
    assert all("region" in row for row in structured["rows"])


async def test_get_document_tool_found_and_missing(gateway: ToolGateway) -> None:
    server = build_mcp_server(gateway)

    _c, found = await server.call_tool("get_document", {"document_id": "eastern-corridor"})
    assert found["found"] is True

    _c2, missing = await server.call_tool("get_document", {"document_id": "nope"})
    assert missing["found"] is False
