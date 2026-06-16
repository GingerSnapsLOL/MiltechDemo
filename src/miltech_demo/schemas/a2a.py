"""A2A-style protocol models.

This is an *A2A-style* implementation. It is NOT official Google A2A compliance;
it is a small, typed, observable protocol for agent-to-agent communication
inspired by A2A concepts.

Every interaction carries a ``trace_id`` (correlates a whole exchange) and a
``task_id`` (the unit of work it belongs to), so flows are debuggable end to end.
The ``trace_id`` originates on the :class:`AgentTask` and must be propagated
explicitly to the messages and artifacts of that task — they never mint their own
``trace_id`` — so a single workflow keeps one correlation id throughout.

The task status lifecycle is expressed declaratively via :data:`ALLOWED_TRANSITIONS`
and the pure helper :func:`can_transition`. Enforcement of transitions is the
responsibility of the services/agents layer, not these data contracts.

Separation of concerns:
    Schemas (this module) define the contracts.
    Services (:mod:`miltech_demo.services.protocol`) enforce lifecycle and
    correlation rules over those contracts.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from miltech_demo.schemas.base import (
    DomainModel,
    IdentifiedModel,
    JsonMetadata,
    new_id,
    now_utc,
)


class TaskStatus(StrEnum):
    """Lifecycle states of an :class:`AgentTask`."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        """Whether no further transition is possible from this state."""
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)


ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset(
        {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
    ),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}


def can_transition(current: TaskStatus, target: TaskStatus) -> bool:
    """Return whether moving from ``current`` to ``target`` is allowed."""
    return target in ALLOWED_TRANSITIONS[current]


class MessageRole(StrEnum):
    """Originator of an :class:`AgentMessage`."""

    USER = "USER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class AgentCapability(DomainModel):
    """A single capability advertised by an agent."""

    name: str = Field(min_length=1, description="Capability identifier.")
    description: str = Field(min_length=1, description="What the capability does.")
    tags: list[str] = Field(default_factory=list, description="Searchable tags.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "summarize",
                    "description": "Summarize a set of documents.",
                    "tags": ["nlp", "analysis"],
                }
            ]
        }
    )


class AgentCard(DomainModel):
    """Discovery metadata advertising an agent and its capabilities."""

    name: str = Field(min_length=1, description="Agent name.")
    description: str = Field(min_length=1, description="What the agent is for.")
    version: str = Field(default="0.1.0", description="Agent version.")
    capabilities: list[AgentCapability] = Field(
        default_factory=list, description="Capabilities the agent offers."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "analyst",
                    "description": "Analyzes retrieved documents into findings.",
                    "version": "0.1.0",
                    "capabilities": [
                        {"name": "summarize", "description": "Summarize documents."}
                    ],
                }
            ]
        }
    )


class AgentMessage(IdentifiedModel):
    """A message exchanged within a task (A2A-style, not official Google A2A)."""

    trace_id: str = Field(
        description="Correlation id propagated from the owning task; never generated here."
    )
    task_id: str = Field(description="Identifier of the owning task.")
    sender_agent: str | None = Field(default=None, description="Agent that sent the message.")
    target_agent: str | None = Field(
        default=None, description="Agent the message is addressed to."
    )
    role: MessageRole = Field(description="Who produced the message.")
    content: str = Field(min_length=1, description="Message body.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "trace_id": "trace-abc",
                    "task_id": "task-123",
                    "sender_agent": "retriever",
                    "target_agent": "analyst",
                    "role": "AGENT",
                    "content": "Retrieved 3 relevant documents.",
                }
            ]
        }
    )


class AgentArtifact(IdentifiedModel):
    """A concrete output produced while working a task (A2A-style, not official Google A2A)."""

    trace_id: str = Field(
        description="Correlation id propagated from the owning task; never generated here."
    )
    task_id: str = Field(description="Identifier of the owning task.")
    name: str = Field(min_length=1, description="Artifact name.")
    kind: str = Field(min_length=1, description="Artifact type, e.g. 'report' or 'text'.")
    content: str = Field(description="Artifact payload.")
    metadata: JsonMetadata = Field(default_factory=dict, description="Extra metadata.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "trace_id": "trace-abc",
                    "task_id": "task-123",
                    "name": "intel-report",
                    "kind": "report",
                    "content": "{...}",
                }
            ]
        }
    )


class AgentTask(DomainModel):
    """A unit of work routed between agents (A2A-style, not official Google A2A).

    Owns the ``trace_id`` for the whole exchange; messages and artifacts created
    while working the task must reuse this ``trace_id``.
    """

    task_id: str = Field(default_factory=new_id, description="Unique task identifier.")
    trace_id: str = Field(
        default_factory=new_id,
        description="Correlation id for the whole exchange; propagated to messages/artifacts.",
    )
    objective: str = Field(min_length=1, description="What the task should accomplish.")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Lifecycle state.")
    source_agent: str | None = Field(
        default=None, description="Agent that created the task."
    )
    target_agent: str | None = Field(
        default=None, description="Intended recipient agent for the task."
    )
    assigned_agent: str | None = Field(
        default=None, description="Agent currently executing the task."
    )
    created_at: datetime = Field(default_factory=now_utc, description="Creation time.")
    updated_at: datetime = Field(default_factory=now_utc, description="Last update time.")
    messages: list[AgentMessage] = Field(default_factory=list, description="Exchange log.")
    artifacts: list[AgentArtifact] = Field(
        default_factory=list, description="Produced artifacts."
    )
    error: str | None = Field(default=None, description="Failure detail, if any.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_id": "task-123",
                    "trace_id": "trace-abc",
                    "objective": "Summarize recent activity in the eastern corridor.",
                    "status": "PENDING",
                    "source_agent": "router",
                    "target_agent": "analyst",
                    "assigned_agent": "analyst",
                }
            ]
        }
    )


class AgentResponse(DomainModel):
    """The result returned for a task, carrying correlation ids and final status."""

    trace_id: str = Field(description="Correlates the exchange.")
    task_id: str = Field(description="Identifier of the task this responds to.")
    status: TaskStatus = Field(description="Status reported by the responder.")
    sender_agent: str | None = Field(default=None, description="Agent that produced the response.")
    target_agent: str | None = Field(
        default=None, description="Agent the response is addressed to."
    )
    message: AgentMessage | None = Field(default=None, description="Optional reply message.")
    artifacts: list[AgentArtifact] = Field(
        default_factory=list, description="Artifacts produced."
    )
    error: str | None = Field(default=None, description="Failure detail, if any.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "trace_id": "trace-abc",
                    "task_id": "task-123",
                    "status": "COMPLETED",
                    "sender_agent": "analyst",
                    "target_agent": "router",
                    "artifacts": [],
                }
            ]
        }
    )
