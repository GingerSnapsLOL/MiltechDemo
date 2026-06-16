"""Services: lifecycle/correlation rules and tool logic over the schema contracts."""

from miltech_demo.services.documents import DocumentService
from miltech_demo.services.intel_db import IntelDatabase
from miltech_demo.services.llm import (
    FakeLLMProvider,
    LLMError,
    LLMProvider,
    build_llm_provider,
    get_llm_provider,
)
from miltech_demo.services.mcp_gateway import MCPToolGateway
from miltech_demo.services.ollama_provider import OllamaProvider
from miltech_demo.services.protocol import (
    ProtocolViolationError,
    advance_task_status,
    attach_artifact,
    attach_message,
    validate_artifact_belongs_to_task,
    validate_message_belongs_to_task,
)
from miltech_demo.services.tool_gateway import (
    InMemoryToolGateway,
    ToolGateway,
    build_in_memory_gateway,
    build_tool_gateway,
    get_tool_gateway,
)

__all__ = [
    "DocumentService",
    "FakeLLMProvider",
    "InMemoryToolGateway",
    "IntelDatabase",
    "LLMError",
    "LLMProvider",
    "MCPToolGateway",
    "OllamaProvider",
    "ProtocolViolationError",
    "ToolGateway",
    "advance_task_status",
    "attach_artifact",
    "attach_message",
    "build_in_memory_gateway",
    "build_llm_provider",
    "build_tool_gateway",
    "get_llm_provider",
    "get_tool_gateway",
    "validate_artifact_belongs_to_task",
    "validate_message_belongs_to_task",
]
