"""LangGraph workflow package.

Import the runnable workflow from :mod:`miltech_demo.graph.workflow`
(``build_graph`` / ``run_workflow``). Keeping those out of this package
``__init__`` avoids a circular import, since the workflow imports the agent
nodes and the agent nodes import :mod:`miltech_demo.graph.state`.
"""

from miltech_demo.graph.state import GraphState, initial_state

__all__ = ["GraphState", "initial_state"]
