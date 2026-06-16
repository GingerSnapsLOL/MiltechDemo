"""Document and DocumentChunk domain models."""

from datetime import datetime

from pydantic import ConfigDict, Field

from miltech_demo.schemas.base import IdentifiedModel
from miltech_demo.schemas.enums import Classification


class Document(IdentifiedModel):
    """A source intelligence document ingested into the platform."""

    title: str = Field(min_length=1, description="Human-readable document title.")
    source: str = Field(min_length=1, description="Origin of the document.")
    content: str = Field(min_length=1, description="Full document text.")
    classification: Classification = Field(
        default=Classification.UNCLASSIFIED,
        description="Security classification level.",
    )
    published_at: datetime | None = Field(
        default=None, description="When the source published the document, if known."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Arbitrary source-specific metadata."
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "title": "Border Activity Summary",
                    "source": "field-report-7",
                    "content": "Increased vehicle movement observed along the eastern corridor.",
                    "classification": "CONFIDENTIAL",
                    "metadata": {"region": "east", "analyst": "j.doe"},
                }
            ]
        },
    )


class DocumentChunk(IdentifiedModel):
    """A retrievable slice of a :class:`Document`."""

    document_id: str = Field(description="Identifier of the parent document.")
    index: int = Field(ge=0, description="Zero-based position of the chunk in the document.")
    content: str = Field(min_length=1, description="Chunk text.")
    token_count: int | None = Field(
        default=None, ge=0, description="Approximate token count of the chunk."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Arbitrary chunk-specific metadata."
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "document_id": "doc-123",
                    "index": 0,
                    "content": "Increased vehicle movement observed along the eastern corridor.",
                    "token_count": 11,
                }
            ]
        },
    )
