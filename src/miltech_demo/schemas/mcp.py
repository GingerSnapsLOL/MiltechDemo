"""Typed input/output models for the MCP tools.

MCP handlers stay thin; these models define the tool contracts and the service
layer consumes/produces them.
"""

from pydantic import ConfigDict, Field

from miltech_demo.schemas.base import DomainModel
from miltech_demo.schemas.documents import Document


class SearchDocumentsInput(DomainModel):
    """Input for the ``search_documents`` tool."""

    query: str = Field(min_length=1, description="Search terms.")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum hits to return.")


class DocumentHit(DomainModel):
    """A single search result."""

    id: str = Field(description="Document identifier.")
    title: str = Field(description="Document title.")
    source: str = Field(description="Document source.")
    snippet: str = Field(description="Matching excerpt.")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score in [0, 1].")


class SearchDocumentsResult(DomainModel):
    """Output for the ``search_documents`` tool."""

    query: str = Field(description="The query that was run.")
    hits: list[DocumentHit] = Field(default_factory=list, description="Ranked hits.")
    count: int = Field(ge=0, description="Number of hits returned.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "eastern corridor",
                    "hits": [
                        {
                            "id": "eastern-corridor",
                            "title": "Eastern Corridor Activity",
                            "source": "markdown",
                            "snippet": "Increased vehicle movement...",
                            "score": 0.8,
                        }
                    ],
                    "count": 1,
                }
            ]
        }
    )


class GetDocumentInput(DomainModel):
    """Input for the ``get_document`` tool."""

    document_id: str = Field(min_length=1, description="Document identifier.")


class GetDocumentResult(DomainModel):
    """Output for the ``get_document`` tool."""

    found: bool = Field(description="Whether the document exists.")
    document: Document | None = Field(default=None, description="The document, if found.")


class QueryIntelInput(DomainModel):
    """Input for the ``query_intel_db`` tool."""

    query: str = Field(min_length=1, description="Keyword to match across intel fields.")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum rows to return.")


class IntelRecord(DomainModel):
    """A row from the synthetic intelligence database."""

    id: int = Field(description="Record id.")
    title: str = Field(description="Short headline.")
    region: str = Field(description="Region the record concerns.")
    category: str = Field(description="Record category.")
    severity: str = Field(description="Severity level.")
    summary: str = Field(description="One-line summary.")
    reported_at: str = Field(description="ISO date the record was reported.")


class QueryIntelResult(DomainModel):
    """Output for the ``query_intel_db`` tool."""

    query: str = Field(description="The query that was run.")
    rows: list[IntelRecord] = Field(default_factory=list, description="Matching rows.")
    count: int = Field(ge=0, description="Number of rows returned.")
