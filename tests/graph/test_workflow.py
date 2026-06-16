from pathlib import Path

import pytest

from miltech_demo.agents.analyst import analyst_node
from miltech_demo.agents.router import router_node
from miltech_demo.core.config import Settings
from miltech_demo.graph.state import initial_state
from miltech_demo.graph.workflow import run_workflow
from miltech_demo.schemas import (
    AgentMessage,
    IntelligenceReport,
    MessageRole,
    TaskStatus,
)
from miltech_demo.services import ProtocolViolationError, attach_message, build_in_memory_gateway
from miltech_demo.services.tool_gateway import ToolGateway


@pytest.fixture
def gateway(tmp_path: Path) -> ToolGateway:
    return build_in_memory_gateway(Settings(intel_db_path=tmp_path / "intel.db"))


def test_workflow_runs_end_to_end(gateway: ToolGateway) -> None:
    state = run_workflow("eastern corridor activity", gateway=gateway)

    assert state["root_task"] is not None
    assert isinstance(state["final_report"], IntelligenceReport)
    assert len(state["agent_trace"]) == 4
    assert len(state["tasks"]) == 3  # root + validator + reporter


def test_all_messages_share_one_trace_id(gateway: ToolGateway) -> None:
    state = run_workflow("corridor", gateway=gateway)
    trace_id = state["root_task"].trace_id  # type: ignore[union-attr]
    assert state["messages"]
    assert all(message.trace_id == trace_id for message in state["messages"])


def test_all_artifacts_share_one_trace_id(gateway: ToolGateway) -> None:
    state = run_workflow("corridor", gateway=gateway)
    trace_id = state["root_task"].trace_id  # type: ignore[union-attr]
    assert state["artifacts"]
    assert all(artifact.trace_id == trace_id for artifact in state["artifacts"])


def test_all_responses_share_one_trace_id(gateway: ToolGateway) -> None:
    state = run_workflow("corridor", gateway=gateway)
    trace_id = state["root_task"].trace_id  # type: ignore[union-attr]
    assert state["responses"]
    assert all(response.trace_id == trace_id for response in state["responses"])


def test_all_tasks_share_one_trace_id(gateway: ToolGateway) -> None:
    state = run_workflow("corridor", gateway=gateway)
    trace_id = state["root_task"].trace_id  # type: ignore[union-attr]
    assert all(task.trace_id == trace_id for task in state["tasks"])


def test_analyst_artifact_reflects_tool_results(gateway: ToolGateway) -> None:
    state = run_workflow("corridor", gateway=gateway)
    analysis = next(a for a in state["artifacts"] if a.kind == "analysis")
    # The analyst used the tools: at least one document hit for "corridor".
    assert analysis.metadata["document_hits"] >= 1


def test_validator_corroborates_via_tools(gateway: ToolGateway) -> None:
    state = run_workflow("corridor", gateway=gateway)
    validation = next(a for a in state["artifacts"] if a.kind == "validation")
    assert validation.metadata["corroborating_records"] >= 1
    assert validation.metadata["valid"] is True


def test_reporter_produces_final_report(gateway: ToolGateway) -> None:
    state = run_workflow("eastern corridor", gateway=gateway)
    report = state["final_report"]
    assert isinstance(report, IntelligenceReport)
    assert report.query == "eastern corridor"
    assert any(artifact.kind == "report" for artifact in state["artifacts"])


def test_evidence_is_gathered_and_carried_into_report(gateway: ToolGateway) -> None:
    state = run_workflow("eastern corridor", gateway=gateway)
    assert state["evidence"]
    report = state["final_report"]
    assert report is not None
    assert report.evidence == state["evidence"]


def test_all_evidence_traces_to_workflow(gateway: ToolGateway) -> None:
    state = run_workflow("corridor", gateway=gateway)
    report = state["final_report"]
    assert report is not None
    # The report's trace_id matches the single workflow trace_id.
    assert report.trace_id == state["root_task"].trace_id  # type: ignore[union-attr]


def test_all_responses_completed(gateway: ToolGateway) -> None:
    state = run_workflow("corridor", gateway=gateway)
    assert all(response.status is TaskStatus.COMPLETED for response in state["responses"])


def test_trace_mismatch_raises() -> None:
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
    with pytest.raises(RuntimeError):
        analyst_node(initial_state("q"), {"configurable": {}})


def test_analyst_node_requires_gateway() -> None:
    state = initial_state("q")
    update = router_node(state)
    state["root_task"] = update["root_task"]
    state["tasks"] = update["tasks"]
    with pytest.raises(RuntimeError, match="tool_gateway"):
        analyst_node(state, {"configurable": {}})
