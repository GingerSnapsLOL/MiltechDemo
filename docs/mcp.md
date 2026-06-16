# MCP Server

A real Model Context Protocol server, built on the official `mcp` Python SDK
(`FastMCP`), exposing three intelligence tools over synthetic demo data.

## Architecture

```
MCP client (stdio)                 LangGraph agents (analyst, validator)
      │                                   │  depend only on the ABC
      ▼                                   ▼
FastMCP server (mcp_server/server.py)   ToolGateway (abc.ABC)
      │   thin handlers                   ├── InMemoryToolGateway ─┐
      ▼                                   └── MCPToolGateway ──────┤ (MCP client)
InMemoryToolGateway ───────────────────────────────────────────── ┘
      │
      ├─► DocumentService (services/documents.py) ─► synthetic markdown reports
      └─► IntelDatabase   (services/intel_db.py)  ─► synthetic SQLite database
```

Design rules (per CLAUDE.md):

- **Thin handlers.** Each `@mcp.tool()` handler validates typed input, delegates
  to a gateway, and returns a typed Pydantic result. No logic in handlers.
- **Logic in services.** `DocumentService` and `IntelDatabase` hold all behavior.
- **Typed I/O.** Tool inputs/outputs are Pydantic v2 models (`schemas/mcp.py`),
  so the MCP tool schemas and structured outputs are generated from the contracts.

## ToolGateway abstraction & dependency injection

`ToolGateway` (`services/tool_gateway.py`) is an `abc.ABC` with three typed
methods (`search_documents`, `get_document`, `query_intel_db`). It has two
implementations:

- **`InMemoryToolGateway`** — calls the services in-process (default; deterministic,
  offline). The MCP server itself always uses this (it *is* the tool provider).
- **`MCPToolGateway`** (`services/mcp_gateway.py`) — calls the real MCP server over
  the protocol via an `mcp.ClientSession`. Because the client is async and the
  interface is sync, it bridges through an `anyio` blocking portal running a
  persistent session on a background thread, and parses the structured tool output
  back into the Pydantic result models.

**Agents never call tools directly.** The analyst and validator depend only on the
`ToolGateway` ABC, obtained from the LangGraph run config
(`config["configurable"]["tool_gateway"]`) via `agents/_deps.gateway_from_config`.
`run_workflow(query, gateway=...)` injects the instance; `build_tool_gateway`
selects the implementation from `settings.tool_gateway` (`"memory"` | `"mcp"`). A
guard test (`tests/agents/test_no_direct_tool_access.py`) asserts agent modules do
not import the services or the MCP client.

## Data sources (synthetic, deterministic)

- **Markdown reports**: `src/miltech_demo/data/reports/*.md` (packaged with the
  wheel), parsed into `Document` models.
- **SQLite intel DB**: created and seeded idempotently on first use at
  `MILTECH_INTEL_DB_PATH` (default `intel.db`). Six synthetic rows.

## Tools

### `search_documents(query: str, limit: int = 5) -> SearchDocumentsResult`

Ranked keyword search over the markdown reports (match ratio of query terms).

Expected response:

```json
{
  "query": "eastern corridor",
  "hits": [
    {
      "id": "eastern-corridor",
      "title": "Eastern Corridor Activity",
      "source": "field-report-7",
      "snippet": "Increased vehicle movement has been observed along the eastern corridor...",
      "score": 1.0
    }
  ],
  "count": 1
}
```

### `get_document(document_id: str) -> GetDocumentResult`

Fetch a single document by id.

```json
{
  "found": true,
  "document": {
    "id": "eastern-corridor",
    "title": "Eastern Corridor Activity",
    "source": "field-report-7",
    "content": "# Eastern Corridor Activity\n\n...",
    "classification": "UNCLASSIFIED"
  }
}
```

A missing id returns `{"found": false, "document": null}`.

### `query_intel_db(query: str, limit: int = 20) -> QueryIntelResult`

Keyword search over the SQLite intel database. The query is bound as a **literal
LIKE parameter** — there is no arbitrary SQL execution and no injection surface.

```json
{
  "query": "corridor",
  "rows": [
    {
      "id": 6,
      "title": "Night corridor traffic",
      "region": "east",
      "category": "movement",
      "severity": "medium",
      "summary": "Increased nighttime traffic observed along the eastern corridor.",
      "reported_at": "2026-06-15"
    }
  ],
  "count": 2
}
```

## Running

```bash
make mcp-server     # runs the server over stdio for any MCP client
```

This registers `search_documents`, `get_document`, and `query_intel_db`. Point an
MCP client (e.g. Claude Desktop) at the command to call them.

## Testing

- `tests/mcp_server/test_tools.py` — exercises the tools through `FastMCP.call_tool`
  (real MCP dispatch), asserting registration and structured outputs.
- `tests/services/test_tool_gateway.py` — a conformance suite parametrized over
  `InMemoryToolGateway` and `MCPToolGateway` (the latter over an in-memory MCP
  transport), proving the two implementations behave identically.
- `tests/services/test_documents.py` / `test_intel_db.py` — service logic
  (including the no-SQL-execution guarantee).
- `tests/agents/test_no_direct_tool_access.py` — guard ensuring agents only use
  the gateway.

## Note

The LangGraph analyst and validator consume these tools through the `ToolGateway`
(injected via the run config). The MCP server itself is real and
protocol-accessible (`make mcp-server`).
