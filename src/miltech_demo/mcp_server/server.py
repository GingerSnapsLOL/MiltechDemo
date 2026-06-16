"""MCP server exposing the intelligence tools via the official MCP SDK (FastMCP).

Handlers are thin: each validates its typed input, delegates to the shared
:class:`ToolGateway`, and returns a typed Pydantic result. All business logic
lives in the services layer.

Run as a stdio MCP server with::

    uv run python -m miltech_demo.mcp_server.server
"""

import structlog
from mcp.server.fastmcp import FastMCP

from miltech_demo.core.config import get_settings
from miltech_demo.schemas import (
    GetDocumentInput,
    GetDocumentResult,
    QueryIntelInput,
    QueryIntelResult,
    SearchDocumentsInput,
    SearchDocumentsResult,
)
from miltech_demo.services import ToolGateway, build_in_memory_gateway

logger = structlog.get_logger(__name__)


def build_mcp_server(gateway: ToolGateway | None = None) -> FastMCP:
    """Build a FastMCP server whose tools delegate to ``gateway``.

    The server is the tool *provider*, so it always uses an in-process gateway by
    default (never the configurable, possibly-MCP agent gateway, which would
    recurse back into this server).
    """
    tools = gateway if gateway is not None else build_in_memory_gateway(get_settings())
    mcp = FastMCP("miltech-intel")

    @mcp.tool()
    def search_documents(query: str, limit: int = 5) -> SearchDocumentsResult:
        """Search synthetic markdown reports for the given query."""
        return tools.search_documents(SearchDocumentsInput(query=query, limit=limit))

    @mcp.tool()
    def get_document(document_id: str) -> GetDocumentResult:
        """Fetch a single document by its identifier."""
        return tools.get_document(GetDocumentInput(document_id=document_id))

    @mcp.tool()
    def query_intel_db(query: str, limit: int = 20) -> QueryIntelResult:
        """Keyword-search the synthetic intelligence database."""
        return tools.query_intel_db(QueryIntelInput(query=query, limit=limit))

    return mcp


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    server = build_mcp_server()
    logger.info("mcp_server_starting", transport="stdio")
    server.run()


if __name__ == "__main__":
    main()
