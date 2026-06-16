"""Shared dependency access for agent nodes.

Agents obtain their tools exclusively through the injected ``ToolGateway`` — they
never construct services or call tools directly. The gateway is passed via the
LangGraph run config (``configurable``).
"""

from langchain_core.runnables import RunnableConfig

from miltech_demo.services.tool_gateway import ToolGateway


def gateway_from_config(config: RunnableConfig) -> ToolGateway:
    """Extract the injected ToolGateway from the run config (raises if absent)."""
    configurable = config.get("configurable") or {}
    gateway = configurable.get("tool_gateway")
    if not isinstance(gateway, ToolGateway):
        raise RuntimeError("agent node requires a 'tool_gateway' in the run config")
    return gateway
