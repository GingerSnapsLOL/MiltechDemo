import pytest
from pydantic import ValidationError

from miltech_demo.schemas import (
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


def test_agent_card_with_capabilities_round_trips() -> None:
    card = AgentCard(
        name="analyst",
        description="Analyzes documents.",
        capabilities=[AgentCapability(name="summarize", description="Summarize docs.")],
    )

    restored = AgentCard.model_validate_json(card.model_dump_json())

    assert restored == card
    assert restored.version == "0.1.0"
    assert isinstance(restored.capabilities[0], AgentCapability)


def test_agent_task_defaults() -> None:
    task = AgentTask(objective="do the thing")

    assert task.task_id
    assert task.trace_id
    assert task.status is TaskStatus.PENDING
    assert task.messages == []
    assert task.artifacts == []
    assert task.created_at.tzinfo is not None


def test_agent_message_requires_task_id() -> None:
    with pytest.raises(ValidationError):
        AgentMessage(role=MessageRole.AGENT, content="hi")  # type: ignore[call-arg]


def test_agent_message_requires_trace_id() -> None:
    with pytest.raises(ValidationError):
        AgentMessage(task_id="task-1", role=MessageRole.AGENT, content="hi")  # type: ignore[call-arg]


def test_agent_message_has_unique_id_and_round_trips() -> None:
    msg = AgentMessage(
        trace_id="trace-1", task_id="task-1", role=MessageRole.AGENT, content="hi"
    )

    assert msg.id
    assert msg.trace_id == "trace-1"
    assert AgentMessage.model_validate_json(msg.model_dump_json()) == msg


def test_task_owns_single_trace_id_propagated_to_message_and_artifact() -> None:
    task = AgentTask(objective="do the thing", source_agent="router", target_agent="analyst")

    message = AgentMessage(
        trace_id=task.trace_id,
        task_id=task.task_id,
        sender_agent="router",
        target_agent="analyst",
        role=MessageRole.AGENT,
        content="starting",
    )
    artifact = AgentArtifact(
        trace_id=task.trace_id,
        task_id=task.task_id,
        name="report",
        kind="report",
        content="{...}",
    )

    # One correlation id flows through the whole workflow.
    assert message.trace_id == task.trace_id
    assert artifact.trace_id == task.trace_id
    assert message.task_id == artifact.task_id == task.task_id


def test_sender_and_target_agent_serialize() -> None:
    msg = AgentMessage(
        trace_id="trace-1",
        task_id="task-1",
        sender_agent="retriever",
        target_agent="analyst",
        role=MessageRole.AGENT,
        content="hi",
    )

    dumped = msg.model_dump()
    assert dumped["sender_agent"] == "retriever"
    assert dumped["target_agent"] == "analyst"
    assert AgentMessage.model_validate_json(msg.model_dump_json()) == msg


def test_task_source_and_target_agent_serialize() -> None:
    task = AgentTask(objective="x", source_agent="router", target_agent="analyst")

    dumped = task.model_dump()
    assert dumped["source_agent"] == "router"
    assert dumped["target_agent"] == "analyst"
    assert AgentTask.model_validate_json(task.model_dump_json()) == task


def test_artifact_metadata_accepts_json_scalars() -> None:
    artifact = AgentArtifact(
        trace_id="trace-1",
        task_id="task-1",
        name="report",
        kind="report",
        content="{...}",
        metadata={"pages": 3, "verified": True, "score": 0.9, "note": "ok", "ref": None},
    )

    assert AgentArtifact.model_validate_json(artifact.model_dump_json()) == artifact


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(objective="x", unexpected="y")  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("status", "terminal"),
    [
        (TaskStatus.PENDING, False),
        (TaskStatus.RUNNING, False),
        (TaskStatus.COMPLETED, True),
        (TaskStatus.FAILED, True),
        (TaskStatus.CANCELLED, True),
    ],
)
def test_status_is_terminal(status: TaskStatus, terminal: bool) -> None:
    assert status.is_terminal is terminal


@pytest.mark.parametrize(
    ("current", "target", "allowed"),
    [
        (TaskStatus.PENDING, TaskStatus.RUNNING, True),
        (TaskStatus.PENDING, TaskStatus.COMPLETED, False),
        (TaskStatus.RUNNING, TaskStatus.COMPLETED, True),
        (TaskStatus.RUNNING, TaskStatus.PENDING, False),
        (TaskStatus.COMPLETED, TaskStatus.RUNNING, False),
    ],
)
def test_can_transition(current: TaskStatus, target: TaskStatus, allowed: bool) -> None:
    assert can_transition(current, target) is allowed


def test_agent_response_nests_message_and_artifacts() -> None:
    response = AgentResponse(
        trace_id="trace-1",
        task_id="task-1",
        status=TaskStatus.COMPLETED,
        message=AgentMessage(
            trace_id="trace-1", task_id="task-1", role=MessageRole.AGENT, content="done"
        ),
        artifacts=[
            AgentArtifact(
                trace_id="trace-1",
                task_id="task-1",
                name="report",
                kind="report",
                content="{...}",
            )
        ],
    )

    restored = AgentResponse.model_validate_json(response.model_dump_json())

    assert restored == response
    assert restored.message is not None
    assert isinstance(restored.artifacts[0], AgentArtifact)


def test_agent_response_routing_fields_serialize() -> None:
    response = AgentResponse(
        trace_id="trace-1",
        task_id="task-1",
        status=TaskStatus.COMPLETED,
        sender_agent="analyst",
        target_agent="router",
    )

    dumped = response.model_dump()
    assert dumped["sender_agent"] == "analyst"
    assert dumped["target_agent"] == "router"
    assert AgentResponse.model_validate_json(response.model_dump_json()) == response


def test_agent_response_routing_defaults_to_none() -> None:
    response = AgentResponse(trace_id="trace-1", task_id="task-1", status=TaskStatus.PENDING)
    assert response.sender_agent is None
    assert response.target_agent is None


def test_schemas_contain_examples() -> None:
    for model in (AgentCard, AgentCapability, AgentMessage, AgentArtifact, AgentTask):
        assert "examples" in model.model_json_schema()
