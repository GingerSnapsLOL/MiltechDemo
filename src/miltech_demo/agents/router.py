"""Router node: entry point that creates the root A2A task and routes to analyst."""

import structlog

from miltech_demo.graph.state import GraphState, StateUpdate
from miltech_demo.schemas import AgentMessage, AgentTask, MessageRole
from miltech_demo.services import attach_message

logger = structlog.get_logger(__name__)


def router_node(state: GraphState) -> StateUpdate:
    """Create the root task (owning the workflow trace_id) and a routing message."""
    query = state["query"]
    root_task = AgentTask(
        objective=query,
        source_agent="router",
        target_agent="analyst",
    )
    message = AgentMessage(
        trace_id=root_task.trace_id,
        task_id=root_task.task_id,
        sender_agent="router",
        target_agent="analyst",
        role=MessageRole.SYSTEM,
        content=f"Routing query to analyst: {query}",
    )
    attach_message(root_task, message)

    logger.info(
        "router_created_task",
        trace_id=root_task.trace_id,
        task_id=root_task.task_id,
        target_agent=root_task.target_agent,
    )
    return StateUpdate(
        root_task=root_task,
        tasks=[root_task],
        messages=[message],
        agent_trace=["router: created root task -> analyst"],
    )
