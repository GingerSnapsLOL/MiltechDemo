"""Validator node: consumes the analyst artifact and produces a validation artifact.

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
    AgentTask,
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


def validator_node(state: GraphState) -> StateUpdate:
    """Validate the analyst artifact, emit message + artifact + response, route on."""
    task = find_task_targeting(state["tasks"], "validator")
    advance_task_status(task, TaskStatus.RUNNING)
    task.assigned_agent = "validator"

    # Consume the analyst artifact and confirm it belongs to its originating task.
    analysis = find_artifact_by_kind(state["artifacts"], "analysis")
    source_task = find_task_by_id(state["tasks"], analysis.task_id)
    validate_artifact_belongs_to_task(source_task, analysis)

    message = AgentMessage(
        trace_id=task.trace_id,
        task_id=task.task_id,
        sender_agent="validator",
        target_agent="reporter",
        role=MessageRole.AGENT,
        content=f"Validated analysis artifact {analysis.id}.",
    )
    attach_message(task, message)

    validation = AgentArtifact(
        trace_id=task.trace_id,
        task_id=task.task_id,
        name="validation",
        kind="validation",
        content=f"Validation passed for analysis artifact {analysis.id}.",
        metadata={"validated_artifact_id": analysis.id, "valid": True},
    )
    attach_artifact(task, validation)

    advance_task_status(task, TaskStatus.COMPLETED)
    response = AgentResponse(
        trace_id=task.trace_id,
        task_id=task.task_id,
        status=task.status,
        sender_agent="validator",
        target_agent="reporter",
        message=message,
        artifacts=[validation],
    )

    reporter_task = AgentTask(
        trace_id=task.trace_id,
        objective="Compile the final intelligence report.",
        source_agent="validator",
        target_agent="reporter",
    )

    logger.info("validator_completed", trace_id=task.trace_id, task_id=task.task_id)
    return StateUpdate(
        tasks=[reporter_task],
        messages=[message],
        artifacts=[validation],
        responses=[response],
        agent_trace=["validator: validated analysis -> reporter"],
    )
