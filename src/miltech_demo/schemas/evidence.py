"""Evidence domain model."""

from pydantic import ConfigDict, Field

from miltech_demo.schemas.base import IdentifiedModel


class Evidence(IdentifiedModel):
    """A cited snippet from a document supporting a finding."""

    document_id: str = Field(description="Identifier of the source document.")
    chunk_id: str | None = Field(
        default=None, description="Identifier of the source chunk, if applicable."
    )
    snippet: str = Field(min_length=1, description="The cited text.")
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="How relevant this evidence is, in [0, 1]."
    )
    rationale: str | None = Field(
        default=None, description="Why this snippet supports the finding."
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "document_id": "doc-123",
                    "chunk_id": "chunk-0",
                    "snippet": "Increased vehicle movement observed along the eastern corridor.",
                    "relevance_score": 0.92,
                    "rationale": "Directly describes the activity in question.",
                }
            ]
        },
    )
