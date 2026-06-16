import pytest

from miltech_demo.agents.analyst import analyst_node
from miltech_demo.agents.router import router_node
from miltech_demo.graph.state import initial_state
from miltech_demo.graph.workflow import run_workflow
from miltech_demo.schemas import (
    AgentMessage,
    IntelligenceReport,
    MessageRole,
    TaskStatus,
)
from miltech_demo.services import ProtocolViolationError, attach_message


def test_workflow_runs_end_to_end() -> None:
    state = run_workflow("Summarize eastern corridor activity")

    assert state["root_task"] is not None
    assert isinstance(state["final_report"], IntelligenceReport)
    # router + analyst + validator + reporter each leave a trace entry.
    assert len(state["agent_trace"]) == 4
    # root task + validator task + reporter task.
    assert len(state["tasks"]) == 3


def test_all_messages_share_one_trace_id() -> None:
    state = run_workflow("q")
    trace_id = state["root_task"].trace_id  # type: ignore[union-attr]

    assert state["messages"]
    assert all(message.trace_id == trace_id for message in state["messages"])


def test_all_artifacts_share_one_trace_id() -> None:
    state = run_workflow("q")
    trace_id = state["root_task"].trace_id  # type: ignore[union-attr]

    assert state["artifacts"]
    assert all(artifact.trace_id == trace_id for artifact in state["artifacts"])


def test_all_responses_share_one_trace_id() -> None:
    state = run_workflow("q")
    trace_id = state["root_task"].trace_id  # type: ignore[union-attr]

    assert state["responses"]
    assert all(response.trace_id == trace_id for response in state["responses"])


def test_all_tasks_share_one_trace_id() -> None:
    state = run_workflow("q")
    trace_id = state["root_task"].trace_id  # type: ignore[union-attr]

    assert all(task.trace_id == trace_id for task in state["tasks"])


def test_analyst_produces_artifact() -> None:
    state = run_workflow("q")
    kinds = {artifact.kind for artifact in state["artifacts"]}

    assert "analysis" in kinds


def test_validator_consumes_analyst_artifact() -> None:
    state = run_workflow("q")
    validation = next(a for a in state["artifacts"] if a.kind == "validation")
    analysis = next(a for a in state["artifacts"] if a.kind == "analysis")

    # The validation artifact references the analysis artifact it consumed.
    assert validation.metadata["validated_artifact_id"] == analysis.id


def test_reporter_produces_final_report() -> None:
    state = run_workflow("eastern corridor")
    report = state["final_report"]

    assert isinstance(report, IntelligenceReport)
    assert report.query == "eastern corridor"
    assert any(artifact.kind == "report" for artifact in state["artifacts"])


def test_all_responses_completed() -> None:
    state = run_workflow("q")
    assert all(response.status is TaskStatus.COMPLETED for response in state["responses"])


def test_trace_mismatch_raises() -> None:
    # Build a router root task, then a message with a tampered trace_id.
    update = router_node(initial_state("q"))
    root_task = update["root_task"]
    assert root_task is not None

    bad_message = AgentMessage(
        trace_id="not-the-trace",
        task_id=root_task.task_id,
        role=MessageRole.AGENT,
        content="tampered",
    )
    with pytest.raises(ProtocolViolationError, match="trace_id"):
        attach_message(root_task, bad_message)


def test_task_id_mismatch_raises() -> None:
    update = router_node(initial_state("q"))
    root_task = update["root_task"]
    assert root_task is not None

    bad_message = AgentMessage(
        trace_id=root_task.trace_id,
        task_id="not-the-task",
        role=MessageRole.AGENT,
        content="tampered",
    )
    with pytest.raises(ProtocolViolationError, match="task_id"):
        attach_message(root_task, bad_message)


def test_analyst_node_requires_root_task() -> None:
    state = initial_state("q")
    with pytest.raises(RuntimeError):
        analyst_node(state)
