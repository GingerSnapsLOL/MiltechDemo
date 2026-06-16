"""Analyst node: retrieves supporting data via the injected ToolGateway.

The analyst depends only on the ``ToolGateway`` interface (provided through the
run config); it never imports the document/intel services or the MCP client.
Retrieval is real; the narrative synthesis is deterministic (no LLM yet).
"""

import structlog
from langchain_core.runnables import RunnableConfig

from miltech_demo.agents._deps import gateway_from_config
from miltech_demo.graph.state import GraphState, StateUpdate
from miltech_demo.schemas import (
    AgentArtifact,
    AgentMessage,
    AgentResponse,
    AgentTask,
    MessageRole,
    QueryIntelInput,
    SearchDocumentsInput,
    TaskStatus,
)
from miltech_demo.services import advance_task_status, attach_artifact, attach_message

logger = structlog.get_logger(__name__)


def analyst_node(state: GraphState, config: RunnableConfig) -> StateUpdate:
    """Retrieve documents + intel via the gateway, then emit message/artifact/response."""
    task = state["root_task"]
    if task is None:
        raise RuntimeError("analyst_node requires a root_task created by the router")

    gateway = gateway_from_config(config)
    query = state["query"]
    advance_task_status(task, TaskStatus.RUNNING)
    task.assigned_agent = "analyst"

    docs = gateway.search_documents(SearchDocumentsInput(query=query, limit=3))
    intel = gateway.query_intel_db(QueryIntelInput(query=query, limit=5))

    message = AgentMessage(
        trace_id=task.trace_id,
        task_id=task.task_id,
        sender_agent="analyst",
        target_agent="validator",
        role=MessageRole.AGENT,
        content=f"Analyzed '{query}': {docs.count} document hit(s), {intel.count} intel record(s).",
    )
    attach_message(task, message)

    artifact = AgentArtifact(
        trace_id=task.trace_id,
        task_id=task.task_id,
        name="analysis",
        kind="analysis",
        content=(
            f"Analysis of '{query}': {docs.count} matching document(s) and "
            f"{intel.count} intel record(s)."
        ),
        metadata={"document_hits": docs.count, "intel_rows": intel.count},
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

    logger.info(
        "analyst_completed",
        trace_id=task.trace_id,
        task_id=task.task_id,
        document_hits=docs.count,
        intel_rows=intel.count,
    )
    return StateUpdate(
        tasks=[validator_task],
        messages=[message],
        artifacts=[artifact],
        responses=[response],
        agent_trace=["analyst: retrieved evidence via tools -> validator"],
    )
