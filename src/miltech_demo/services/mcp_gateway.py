"""MCPToolGateway: a ToolGateway backed by a real MCP client session.

The MCP client is asynchronous, but the :class:`ToolGateway` interface is
synchronous (so agent nodes stay simple). This gateway bridges the two with an
``anyio`` blocking portal that runs a persistent :class:`ClientSession` on a
background event-loop thread. Each sync method dispatches the corresponding MCP
tool call through the portal and parses the structured output back into the
typed Pydantic result.
"""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, AbstractContextManager, asynccontextmanager
from typing import Any

import anyio.from_thread
import structlog
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult

from miltech_demo.core.config import Settings
from miltech_demo.schemas import (
    GetDocumentInput,
    GetDocumentResult,
    QueryIntelInput,
    QueryIntelResult,
    SearchDocumentsInput,
    SearchDocumentsResult,
)
from miltech_demo.services.tool_gateway import ToolGateway

logger = structlog.get_logger(__name__)

# A factory returning an async context manager that yields a ready ClientSession.
SessionFactory = Callable[[], AbstractAsyncContextManager[ClientSession]]


@asynccontextmanager
async def _stdio_session(params: StdioServerParameters) -> Any:
    """Open an initialized client session against a stdio MCP server."""
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        yield session


class MCPToolGateway(ToolGateway):
    """A ToolGateway that calls tools over the MCP protocol."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._portal_cm = anyio.from_thread.start_blocking_portal()
        self._portal = self._portal_cm.__enter__()
        self._session_cm: AbstractContextManager[ClientSession] = (
            self._portal.wrap_async_context_manager(session_factory())
        )
        self._session = self._session_cm.__enter__()

    def _call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result: CallToolResult = self._portal.call(self._session.call_tool, name, arguments)
        if result.structuredContent is None:
            raise RuntimeError(f"MCP tool {name!r} returned no structured content")
        return result.structuredContent

    def search_documents(self, params: SearchDocumentsInput) -> SearchDocumentsResult:
        data = self._call("search_documents", params.model_dump())
        return SearchDocumentsResult.model_validate(data)

    def get_document(self, params: GetDocumentInput) -> GetDocumentResult:
        data = self._call("get_document", params.model_dump())
        return GetDocumentResult.model_validate(data)

    def query_intel_db(self, params: QueryIntelInput) -> QueryIntelResult:
        data = self._call("query_intel_db", params.model_dump())
        return QueryIntelResult.model_validate(data)

    def close(self) -> None:
        """Tear down the session and the portal."""
        self._session_cm.__exit__(None, None, None)
        self._portal_cm.__exit__(None, None, None)

    def __enter__(self) -> "MCPToolGateway":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def build_mcp_gateway(settings: Settings) -> MCPToolGateway:
    """Build an MCPToolGateway that spawns the project's MCP server over stdio."""
    params = StdioServerParameters(
        command="python", args=["-m", "miltech_demo.mcp_server.server"]
    )
    logger.info("mcp_gateway_connecting", transport="stdio")
    return MCPToolGateway(lambda: _stdio_session(params))
