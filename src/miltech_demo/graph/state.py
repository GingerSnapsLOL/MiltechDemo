"""Graph state for the LangGraph workflow.

The state is a ``TypedDict`` (LangGraph plumbing, not a domain contract). The
accumulating channels use ``operator.add`` reducers so each node returns only the
items it produced. All values are A2A-style protocol models, never plain dicts.
"""

import operator
from typing import Annotated, TypedDict

from miltech_demo.schemas import (
    AgentArtifact,
    AgentMessage,
    AgentResponse,
    AgentTask,
    IntelligenceReport,
)


class GraphState(TypedDict):
    """Full workflow state threaded through the graph."""

    query: str
    root_task: AgentTask | None
    tasks: Annotated[list[AgentTask], operator.add]
    messages: Annotated[list[AgentMessage], operator.add]
    artifacts: Annotated[list[AgentArtifact], operator.add]
    responses: Annotated[list[AgentResponse], operator.add]
    final_report: IntelligenceReport | None
    agent_trace: Annotated[list[str], operator.add]


class StateUpdate(TypedDict, total=False):
    """Partial state update returned by a node (subset of GraphState keys)."""

    root_task: AgentTask | None
    tasks: list[AgentTask]
    messages: list[AgentMessage]
    artifacts: list[AgentArtifact]
    responses: list[AgentResponse]
    final_report: IntelligenceReport | None
    agent_trace: list[str]


def initial_state(query: str) -> GraphState:
    """Build the starting state for a workflow run."""
    return GraphState(
        query=query,
        root_task=None,
        tasks=[],
        messages=[],
        artifacts=[],
        responses=[],
        final_report=None,
        agent_trace=[],
    )


def find_task_targeting(tasks: list[AgentTask], agent: str) -> AgentTask:
    """Return the task routed to ``agent`` (raises if none)."""
    for task in tasks:
        if task.target_agent == agent:
            return task
    raise LookupError(f"no task targeting {agent!r}")


def find_task_by_id(tasks: list[AgentTask], task_id: str) -> AgentTask:
    """Return the task with ``task_id`` (raises if none)."""
    for task in tasks:
        if task.task_id == task_id:
            return task
    raise LookupError(f"no task with task_id {task_id!r}")


def find_artifact_by_kind(artifacts: list[AgentArtifact], kind: str) -> AgentArtifact:
    """Return the most recent artifact of ``kind`` (raises if none)."""
    for artifact in reversed(artifacts):
        if artifact.kind == kind:
            return artifact
    raise LookupError(f"no artifact of kind {kind!r}")
