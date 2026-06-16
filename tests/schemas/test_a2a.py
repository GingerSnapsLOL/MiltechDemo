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


def test_agent_message_has_unique_id_and_round_trips() -> None:
    msg = AgentMessage(task_id="task-1", role=MessageRole.AGENT, content="hi")

    assert msg.id
    assert msg.trace_id
    assert AgentMessage.model_validate_json(msg.model_dump_json()) == msg


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


def test_schemas_contain_examples() -> None:
    for model in (AgentCard, AgentCapability, AgentMessage, AgentArtifact, AgentTask):
        assert "examples" in model.model_json_schema()
