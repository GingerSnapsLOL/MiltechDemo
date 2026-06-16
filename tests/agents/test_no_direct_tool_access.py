"""Guard test: agent nodes must access tools only via the injected ToolGateway.

They must not import the concrete services or the MCP client directly.
"""

from pathlib import Path

import miltech_demo.agents as agents_pkg

_FORBIDDEN = (
    "DocumentService",
    "IntelDatabase",
    "mcp_gateway",
    "import mcp",
    "from mcp",
    "ollama",
    "OllamaProvider",
)
_AGENT_FILES = ("router.py", "analyst.py", "validator.py", "reporter.py")


def test_agents_do_not_access_tools_directly() -> None:
    agents_dir = Path(agents_pkg.__file__).parent
    for filename in _AGENT_FILES:
        source = (agents_dir / filename).read_text(encoding="utf-8")
        for token in _FORBIDDEN:
            assert token not in source, f"{filename} must not reference {token!r}"
