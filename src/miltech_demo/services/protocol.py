"""Protocol validation helpers (A2A-style).

Schemas (:mod:`miltech_demo.schemas`) define the data contracts. This module
enforces correlation rules across those contracts — keeping such logic out of
the Pydantic models, per the project's architecture rules (business logic lives
in services/agents/graph, not in schemas).
"""

import structlog

from miltech_demo.schemas.a2a import (
    AgentArtifact,
    AgentMessage,
    AgentTask,
    TaskStatus,
    can_transition,
)
from miltech_demo.schemas.base import now_utc

logger = structlog.get_logger(__name__)


class ProtocolViolationError(Exception):
    """Raised when a message or artifact does not belong to its task."""


def validate_message_belongs_to_task(task: AgentTask, message: AgentMessage) -> None:
    """Ensure ``message`` shares the task's ``task_id`` and ``trace_id``.

    Raises:
        ProtocolViolationError: if either correlation id does not match.
    """
    if message.task_id != task.task_id:
        logger.warning(
            "protocol_violation",
            kind="message",
            field="task_id",
            expected=task.task_id,
            actual=message.task_id,
        )
        raise ProtocolViolationError(
            f"AgentMessage task_id {message.task_id!r} does not match "
            f"task task_id {task.task_id!r}"
        )
    if message.trace_id != task.trace_id:
        logger.warning(
            "protocol_violation",
            kind="message",
            field="trace_id",
            expected=task.trace_id,
            actual=message.trace_id,
        )
        raise ProtocolViolationError(
            f"AgentMessage trace_id {message.trace_id!r} does not match "
            f"task trace_id {task.trace_id!r}"
        )


def validate_artifact_belongs_to_task(task: AgentTask, artifact: AgentArtifact) -> None:
    """Ensure ``artifact`` shares the task's ``task_id`` and ``trace_id``.

    Raises:
        ProtocolViolationError: if either correlation id does not match.
    """
    if artifact.task_id != task.task_id:
        logger.warning(
            "protocol_violation",
            kind="artifact",
            field="task_id",
            expected=task.task_id,
            actual=artifact.task_id,
        )
        raise ProtocolViolationError(
            f"AgentArtifact task_id {artifact.task_id!r} does not match "
            f"task task_id {task.task_id!r}"
        )
    if artifact.trace_id != task.trace_id:
        logger.warning(
            "protocol_violation",
            kind="artifact",
            field="trace_id",
            expected=task.trace_id,
            actual=artifact.trace_id,
        )
        raise ProtocolViolationError(
            f"AgentArtifact trace_id {artifact.trace_id!r} does not match "
            f"task trace_id {task.trace_id!r}"
        )


def attach_message(task: AgentTask, message: AgentMessage) -> None:
    """Validate correlation, then record ``message`` on ``task``."""
    validate_message_belongs_to_task(task, message)
    task.messages.append(message)


def attach_artifact(task: AgentTask, artifact: AgentArtifact) -> None:
    """Validate correlation, then record ``artifact`` on ``task``."""
    validate_artifact_belongs_to_task(task, artifact)
    task.artifacts.append(artifact)


def advance_task_status(task: AgentTask, target: TaskStatus) -> None:
    """Move ``task`` to ``target`` status if the transition is allowed.

    Raises:
        ProtocolViolationError: if the transition is not permitted.
    """
    if not can_transition(task.status, target):
        logger.warning(
            "invalid_transition",
            task_id=task.task_id,
            current=task.status,
            target=target,
        )
        raise ProtocolViolationError(
            f"illegal task status transition {task.status} -> {target}"
        )
    task.status = target
    task.updated_at = now_utc()
