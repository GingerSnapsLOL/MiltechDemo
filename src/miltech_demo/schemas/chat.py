"""Request/response models for the chat API."""

from pydantic import ConfigDict, Field

from miltech_demo.schemas.base import DomainModel
from miltech_demo.schemas.evidence import Evidence


class ChatRequest(DomainModel):
    """A user query submitted to the workflow."""

    query: str = Field(min_length=1, description="The user's intelligence question.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"query": "Summarize recent activity in the eastern corridor."}]
        }
    )


class ChatResponse(DomainModel):
    """The workflow result returned to the user."""

    answer: str = Field(description="Final report summary.")
    evidence: list[Evidence] = Field(
        default_factory=list, description="Evidence supporting the answer."
    )
    agent_trace: list[str] = Field(
        default_factory=list, description="Ordered log of agent steps."
    )
