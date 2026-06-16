# MilTech Demo — Local-First Multi-Agent Intelligence Platform

A production-style prototype demonstrating FastAPI + LangGraph + MCP + an
A2A-style agent protocol, running locally with deterministic logic (Ollama
integration is planned). The emphasis is architecture quality, type safety,
testing, and explainability — not feature count.

## Layout

- `schemas/` — Pydantic v2 data contracts (domain models, A2A protocol, MCP tool
  I/O). No business logic.
- `services/` — business logic: correlation/lifecycle helpers, the document and
  intel services, and the `ToolGateway`.
- `agents/` + `graph/` — the LangGraph workflow nodes (`router → analyst →
  validator → reporter`) and wiring.
- `mcp_server/` — the MCP server (thin handlers delegating to the `ToolGateway`).
- `api/` — FastAPI app (currently a `/health` endpoint).
- `core/` — config (`pydantic-settings`) and structlog setup.

## Local setup

```bash
make install              # uv sync
make run                  # FastAPI on http://localhost:8000
make mcp-server           # run the MCP server over stdio
make lint type test       # quality gates
```

Configuration comes from environment variables (prefix `MILTECH_`, see
`.env.example`) via `core/config.py`.

## MCP server

A real MCP server (`mcp_server/server.py`, built on the official `mcp` SDK's
`FastMCP`) exposes three tools backed by synthetic data:

- `search_documents(query, limit)` — ranked hits over synthetic markdown reports.
- `get_document(document_id)` — a single `Document`.
- `query_intel_db(query, limit)` — rows from a synthetic SQLite intel database
  (parameterized keyword search — **no arbitrary SQL**).

Handlers are thin: they validate typed input, delegate to a `ToolGateway`, and
return typed Pydantic results.

`ToolGateway` is an abstract interface (`services/tool_gateway.py`) with two
implementations — `InMemoryToolGateway` (in-process, default) and
`MCPToolGateway` (real MCP client). Agents depend only on the interface and
receive a concrete instance via dependency injection, so tool logic lives in
`services/` exactly once.

See **[docs/mcp.md](docs/mcp.md)** for the MCP architecture, the ToolGateway
abstraction + DI, tool contracts, and expected responses.

## A2A design

An **A2A-style** protocol (`schemas/a2a.py`) — NOT official Google A2A compliance.
Interactions are modelled as `AgentTask`, `AgentMessage`, `AgentArtifact`,
`AgentResponse`, all carrying one `trace_id` minted by the router.
`services/protocol.py` enforces correlation (`attach_message`/`attach_artifact`
validate `task_id` + `trace_id`) and lifecycle (`advance_task_status`).

## LangGraph workflow

`router → analyst → validator → reporter` (`graph/workflow.py`). Nodes communicate
only through A2A models. State (`graph/state.py`) is a `TypedDict` with
`operator.add` reducers. The analyst and validator retrieve real data through the
injected `ToolGateway` (analyst: `search_documents` + `query_intel_db`; validator:
`query_intel_db` corroboration) — they never call tools directly. The narrative
synthesis is currently deterministic (no LLM yet).

## Testing

`make test` runs unit tests (schemas, services, MCP tools) and integration tests
(the A2A protocol and the LangGraph workflow). Logic is deterministic, so
assertions are stable and offline.
