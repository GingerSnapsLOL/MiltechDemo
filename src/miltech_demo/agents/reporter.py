"""Reporter node: consumes validated artifacts and produces the final report.

Deterministic placeholder logic (no LLM yet).
"""

import structlog

from miltech_demo.graph.state import (
    GraphState,
    StateUpdate,
    find_artifact_by_kind,
    find_task_by_id,
    find_task_targeting,
)
from miltech_demo.schemas import (
    AgentArtifact,
    AgentMessage,
    AgentResponse,
    IntelligenceReport,
    MessageRole,
    TaskStatus,
)
from miltech_demo.services import (
    advance_task_status,
    attach_artifact,
    attach_message,
    validate_artifact_belongs_to_task,
)

logger = structlog.get_logger(__name__)


def reporter_node(state: GraphState) -> StateUpdate:
    """Compile the final IntelligenceReport from the validated analysis."""
    task = find_task_targeting(state["tasks"], "reporter")
    advance_task_status(task, TaskStatus.RUNNING)
    task.assigned_agent = "reporter"

    # Consume the validated artifact and confirm its correlation.
    validation = find_artifact_by_kind(state["artifacts"], "validation")
    source_task = find_task_by_id(state["tasks"], validation.task_id)
    validate_artifact_belongs_to_task(source_task, validation)

    query = state["query"]
    report = IntelligenceReport(
        query=query,
        summary=f"Validated findings for: {query}",
        findings=[f"Analysis for '{query}' was produced and validated."],
        evidence=[],
        confidence=0.7,
        trace_id=task.trace_id,
    )
    report_artifact = AgentArtifact(
        trace_id=task.trace_id,
        task_id=task.task_id,
        name="intelligence-report",
        kind="report",
        content=report.model_dump_json(),
        metadata={"confidence": report.confidence},
    )
    attach_artifact(task, report_artifact)

    message = AgentMessage(
        trace_id=task.trace_id,
        task_id=task.task_id,
        sender_agent="reporter",
        target_agent="router",
        role=MessageRole.AGENT,
        content="Final intelligence report compiled.",
    )
    attach_message(task, message)

    advance_task_status(task, TaskStatus.COMPLETED)
    response = AgentResponse(
        trace_id=task.trace_id,
        task_id=task.task_id,
        status=task.status,
        sender_agent="reporter",
        target_agent="router",
        message=message,
        artifacts=[report_artifact],
    )

    logger.info("reporter_completed", trace_id=task.trace_id, task_id=task.task_id)
    return StateUpdate(
        final_report=report,
        messages=[message],
        artifacts=[report_artifact],
        responses=[response],
        agent_trace=["reporter: compiled final report"],
    )
