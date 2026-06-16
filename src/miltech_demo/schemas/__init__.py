"""Domain models (pure data contracts) for the platform."""

from miltech_demo.schemas.a2a import (
    ALLOWED_TRANSITIONS,
    AgentArtifact,
    AgentCapability,
    AgentCard,
    AgentMessage,
    AgentResponse,
    AgentTask,
    MessageRole,
    TaskStatus,
    can_transition,
)
from miltech_demo.schemas.base import DomainModel, IdentifiedModel
from miltech_demo.schemas.documents import Document, DocumentChunk
from miltech_demo.schemas.enums import Classification
from miltech_demo.schemas.evidence import Evidence
from miltech_demo.schemas.report import IntelligenceReport

__all__ = [
    "ALLOWED_TRANSITIONS",
    "AgentArtifact",
    "AgentCapability",
    "AgentCard",
    "AgentMessage",
    "AgentResponse",
    "AgentTask",
    "Classification",
    "Document",
    "DocumentChunk",
    "DomainModel",
    "Evidence",
    "IdentifiedModel",
    "IntelligenceReport",
    "MessageRole",
    "TaskStatus",
    "can_transition",
]
