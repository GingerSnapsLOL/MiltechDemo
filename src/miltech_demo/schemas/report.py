"""IntelligenceReport domain model."""

from pydantic import ConfigDict, Field

from miltech_demo.schemas.base import IdentifiedModel
from miltech_demo.schemas.enums import Classification
from miltech_demo.schemas.evidence import Evidence


class IntelligenceReport(IdentifiedModel):
    """The final report produced for an intelligence query."""

    query: str = Field(min_length=1, description="The original analyst query.")
    summary: str = Field(description="Narrative summary of the findings.")
    findings: list[str] = Field(
        default_factory=list, description="Discrete findings derived from the evidence."
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="Evidence cited in support of the findings."
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Overall confidence in the report, in [0, 1]."
    )
    classification: Classification = Field(
        default=Classification.UNCLASSIFIED,
        description="Security classification level of the report.",
    )
    trace_id: str | None = Field(
        default=None, description="Trace identifier linking the report to its agent run."
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "query": "Summarize recent activity in the eastern corridor.",
                    "summary": "Vehicle movement has increased over the past week.",
                    "findings": ["Increased vehicle movement along the eastern corridor."],
                    "evidence": [
                        {
                            "document_id": "doc-123",
                            "snippet": "Increased vehicle movement observed.",
                            "relevance_score": 0.92,
                        }
                    ],
                    "confidence": 0.8,
                    "classification": "CONFIDENTIAL",
                    "trace_id": "trace-abc",
                }
            ]
        },
    )
