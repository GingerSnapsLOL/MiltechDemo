import pytest

from miltech_demo.schemas import AgentArtifact, AgentMessage, AgentTask, MessageRole
from miltech_demo.services import (
    ProtocolViolationError,
    validate_artifact_belongs_to_task,
    validate_message_belongs_to_task,
)


def _message_for(task: AgentTask, **overrides: str) -> AgentMessage:
    fields = {
        "trace_id": task.trace_id,
        "task_id": task.task_id,
        "role": MessageRole.AGENT,
        "content": "hi",
    }
    fields.update(overrides)
    return AgentMessage(**fields)  # type: ignore[arg-type]


def _artifact_for(task: AgentTask, **overrides: str) -> AgentArtifact:
    fields = {
        "trace_id": task.trace_id,
        "task_id": task.task_id,
        "name": "report",
        "kind": "report",
        "content": "{...}",
    }
    fields.update(overrides)
    return AgentArtifact(**fields)  # type: ignore[arg-type]


def test_message_matching_ids_succeeds() -> None:
    task = AgentTask(objective="x")
    # Should not raise.
    validate_message_belongs_to_task(task, _message_for(task))


def test_message_mismatched_task_id_fails() -> None:
    task = AgentTask(objective="x")
    message = _message_for(task, task_id="other-task")
    with pytest.raises(ProtocolViolationError, match="task_id"):
        validate_message_belongs_to_task(task, message)


def test_message_mismatched_trace_id_fails() -> None:
    task = AgentTask(objective="x")
    message = _message_for(task, trace_id="other-trace")
    with pytest.raises(ProtocolViolationError, match="trace_id"):
        validate_message_belongs_to_task(task, message)


def test_artifact_matching_ids_succeeds() -> None:
    task = AgentTask(objective="x")
    # Should not raise.
    validate_artifact_belongs_to_task(task, _artifact_for(task))


def test_artifact_mismatched_task_id_fails() -> None:
    task = AgentTask(objective="x")
    artifact = _artifact_for(task, task_id="other-task")
    with pytest.raises(ProtocolViolationError, match="task_id"):
        validate_artifact_belongs_to_task(task, artifact)


def test_artifact_mismatched_trace_id_fails() -> None:
    task = AgentTask(objective="x")
    artifact = _artifact_for(task, trace_id="other-trace")
    with pytest.raises(ProtocolViolationError, match="trace_id"):
        validate_artifact_belongs_to_task(task, artifact)
