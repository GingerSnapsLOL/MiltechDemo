"""Reporter node: consumes validated artifacts and produces the final report.

Uses the injected LLMProvider to write the summary; structure is deterministic.
"""

import structlog
from langchain_core.runnables import RunnableConfig

from miltech_demo.agents._deps import llm_from_config
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
    LLMRequest,
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


def reporter_node(state: GraphState, config: RunnableConfig) -> StateUpdate:
    """Compile the final IntelligenceReport from the validated analysis."""
    task = find_task_targeting(state["tasks"], "reporter")
    llm = llm_from_config(config)
    advance_task_status(task, TaskStatus.RUNNING)
    task.assigned_agent = "reporter"

    # Consume the validated artifact and confirm its correlation.
    validation = find_artifact_by_kind(state["artifacts"], "validation")
    source_task = find_task_by_id(state["tasks"], validation.task_id)
    validate_artifact_belongs_to_task(source_task, validation)
    analysis = find_artifact_by_kind(state["artifacts"], "analysis")

    query = state["query"]
    evidence = state["evidence"]
    summary = llm.generate(
        LLMRequest(
            system="You are an intelligence report writer. Be concise.",
            prompt=f"Query: {query}\nValidated analysis: {analysis.content}\nWrite a summary.",
        )
    )
    report = IntelligenceReport(
        query=query,
        summary=summary.text,
        findings=[
            f"Analysis for '{query}' was produced and validated.",
            f"{len(evidence)} supporting evidence item(s) were gathered.",
        ],
        evidence=evidence,
        confidence=round(min(0.9, 0.4 + 0.1 * len(evidence)), 3),
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
