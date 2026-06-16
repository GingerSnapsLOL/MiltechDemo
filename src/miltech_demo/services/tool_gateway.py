"""ToolGateway abstraction: the single tool surface agents depend on.

Agents never call tools directly; they depend only on the :class:`ToolGateway`
interface, which is injected at runtime. Two implementations exist:

- :class:`InMemoryToolGateway` — calls the services in-process (default).
- :class:`MCPToolGateway` (in ``services.mcp_gateway``) — calls the real MCP
  server over the protocol.

The MCP server itself always uses an in-process gateway (it *is* the tool
provider); only the choice for the *agents* is configurable.
"""

import abc
from functools import lru_cache

from miltech_demo.core.config import Settings, get_settings
from miltech_demo.schemas import (
    GetDocumentInput,
    GetDocumentResult,
    QueryIntelInput,
    QueryIntelResult,
    SearchDocumentsInput,
    SearchDocumentsResult,
)
from miltech_demo.services.documents import DocumentService
from miltech_demo.services.intel_db import IntelDatabase


class ToolGateway(abc.ABC):
    """The typed tool interface agents use. Implementations decide the transport."""

    @abc.abstractmethod
    def search_documents(self, params: SearchDocumentsInput) -> SearchDocumentsResult:
        """Search documents."""

    @abc.abstractmethod
    def get_document(self, params: GetDocumentInput) -> GetDocumentResult:
        """Fetch a single document by id."""

    @abc.abstractmethod
    def query_intel_db(self, params: QueryIntelInput) -> QueryIntelResult:
        """Keyword-search the intel database."""


class InMemoryToolGateway(ToolGateway):
    """In-process gateway delegating to the document and intel services."""

    def __init__(self, documents: DocumentService, intel_db: IntelDatabase) -> None:
        self._documents = documents
        self._intel_db = intel_db

    def search_documents(self, params: SearchDocumentsInput) -> SearchDocumentsResult:
        return self._documents.search_documents(params)

    def get_document(self, params: GetDocumentInput) -> GetDocumentResult:
        return self._documents.get_document(params)

    def query_intel_db(self, params: QueryIntelInput) -> QueryIntelResult:
        return self._intel_db.query(params)


def build_in_memory_gateway(settings: Settings) -> InMemoryToolGateway:
    """Construct an in-process gateway and initialize the intel database."""
    intel_db = IntelDatabase(settings.intel_db_path)
    intel_db.initialize()
    return InMemoryToolGateway(DocumentService(settings.reports_dir), intel_db)


def build_tool_gateway(settings: Settings) -> ToolGateway:
    """Build the agent-facing gateway selected by ``settings.tool_gateway``."""
    if settings.tool_gateway == "mcp":
        from miltech_demo.services.mcp_gateway import build_mcp_gateway

        return build_mcp_gateway(settings)
    return build_in_memory_gateway(settings)


@lru_cache
def get_tool_gateway() -> ToolGateway:
    """Return the process-wide agent-facing gateway built from settings."""
    return build_tool_gateway(get_settings())
