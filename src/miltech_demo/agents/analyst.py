"""Analyst node: consumes the analyst task and produces the analysis artifact.

Deterministic placeholder logic (no LLM yet); a model-backed service can be
injected here in a later phase.
"""

import structlog

from miltech_demo.graph.state import GraphState, StateUpdate
from miltech_demo.schemas import (
    AgentArtifact,
    AgentMessage,
    AgentResponse,
    AgentTask,
    MessageRole,
    TaskStatus,
)
from miltech_demo.services import advance_task_status, attach_artifact, attach_message

logger = structlog.get_logger(__name__)


def analyst_node(state: GraphState) -> StateUpdate:
    """Analyze the query, emit message + artifact + response, route to validator."""
    task = state["root_task"]
    if task is None:
        raise RuntimeError("analyst_node requires a root_task created by the router")

    query = state["query"]
    advance_task_status(task, TaskStatus.RUNNING)
    task.assigned_agent = "analyst"

    message = AgentMessage(
        trace_id=task.trace_id,
        task_id=task.task_id,
        sender_agent="analyst",
        target_agent="validator",
        role=MessageRole.AGENT,
        content=f"Analyzed query: {query}",
    )
    attach_message(task, message)

    artifact = AgentArtifact(
        trace_id=task.trace_id,
        task_id=task.task_id,
        name="analysis",
        kind="analysis",
        content=f"Analysis of '{query}': identified key entities and notable activity.",
        metadata={"query": query, "agent": "analyst"},
    )
    attach_artifact(task, artifact)

    advance_task_status(task, TaskStatus.COMPLETED)
    response = AgentResponse(
        trace_id=task.trace_id,
        task_id=task.task_id,
        status=task.status,
        sender_agent="analyst",
        target_agent="validator",
        message=message,
        artifacts=[artifact],
    )

    validator_task = AgentTask(
        trace_id=task.trace_id,
        objective=f"Validate analysis for: {query}",
        source_agent="analyst",
        target_agent="validator",
    )

    logger.info("analyst_completed", trace_id=task.trace_id, task_id=task.task_id)
    return StateUpdate(
        tasks=[validator_task],
        messages=[message],
        artifacts=[artifact],
        responses=[response],
        agent_trace=["analyst: produced analysis -> validator"],
    )
