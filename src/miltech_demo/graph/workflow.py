"""LangGraph workflow wiring the A2A-style agent nodes.

This is an *A2A-style* workflow, NOT official Google A2A compliance. Nodes
communicate exclusively through the internal A2A protocol models
(``AgentTask`` / ``AgentMessage`` / ``AgentArtifact`` / ``AgentResponse``) and a
single ``trace_id`` minted by the router on the root task is propagated through
the whole run.

Flow: ``router -> analyst -> validator -> reporter``.
"""

from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from miltech_demo.agents.analyst import analyst_node
from miltech_demo.agents.reporter import reporter_node
from miltech_demo.agents.router import router_node
from miltech_demo.agents.validator import validator_node
from miltech_demo.graph.state import GraphState, initial_state
from miltech_demo.services.tool_gateway import ToolGateway, get_tool_gateway

CompiledWorkflow = CompiledStateGraph[GraphState, Any, GraphState, GraphState]


def build_graph() -> CompiledWorkflow:
    """Build and compile the router -> analyst -> validator -> reporter graph."""
    builder: StateGraph[GraphState, Any, GraphState, GraphState] = StateGraph(GraphState)
    builder.add_node("router", router_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("validator", validator_node)
    builder.add_node("reporter", reporter_node)

    builder.add_edge(START, "router")
    builder.add_edge("router", "analyst")
    builder.add_edge("analyst", "validator")
    builder.add_edge("validator", "reporter")
    builder.add_edge("reporter", END)

    return builder.compile()


def run_workflow(query: str, gateway: ToolGateway | None = None) -> GraphState:
    """Run the workflow for ``query`` and return the final graph state.

    The ``ToolGateway`` is injected into the run config so the analyst and
    validator can access tools. When omitted, the process-wide gateway is used.
    """
    tool_gateway = gateway if gateway is not None else get_tool_gateway()
    graph = build_graph()
    config: RunnableConfig = {"configurable": {"tool_gateway": tool_gateway}}
    result = graph.invoke(initial_state(query), config=config)
    return cast(GraphState, result)
