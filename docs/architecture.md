# Architecture

How a query flows end to end, and why the pieces are arranged the way they are.

## Layers and dependency direction

```
api  ─┐
       ├─► graph ─► agents ─► services ─► schemas
mcp_server ──────────────────┘            ▲
core (config, logging) ────────────────────┘
```

- **schemas/** — Pydantic v2 contracts only (no logic): domain models
  (`Document`, `Evidence`, `IntelligenceReport`), the A2A protocol (`a2a.py`), MCP
  tool I/O (`mcp.py`), LLM I/O (`llm.py`), chat API models (`chat.py`).
- **services/** — all business logic: `protocol.py` (correlation + lifecycle),
  `documents.py`, `intel_db.py`, `tool_gateway.py` (+ `mcp_gateway.py`), `llm.py`
  (+ `ollama_provider.py`).
- **agents/** — LangGraph node functions (`router`, `analyst`, `validator`,
  `reporter`); `_deps.py` extracts injected dependencies from the run config.
- **graph/** — state (`state.py`) and wiring (`workflow.py`).
- **mcp_server/** — the MCP server; thin handlers delegate to the gateway.
- **api/** — FastAPI endpoints; thin, delegate to `run_workflow`.

Business logic never lives in endpoints, Pydantic models, or MCP handlers.

## End-to-end request flow

```
POST /api/v1/chat {query}
  → run_workflow(query, gateway, llm)        # deps injected via run config
  → router    : root AgentTask (mints trace_id) → analyst
  → analyst   : ToolGateway.search_documents + query_intel_db (MCP tools)
                → Evidence; LLMProvider synthesizes the analysis
                → AgentMessage + AgentArtifact + AgentResponse; next task → validator
  → validator : consumes analyst artifact; ToolGateway.query_intel_db corroboration
                → AgentMessage + AgentArtifact + AgentResponse; next task → reporter
  → reporter  : LLMProvider writes summary; IntelligenceReport(evidence=state.evidence)
                → report AgentArtifact + AgentResponse
  ← ChatResponse { answer, evidence, agent_trace }
```

`answer = report.summary`, `evidence = report.evidence`, `agent_trace` is the
ordered per-node log.

## A2A communication (never bypassed)

Every agent-to-agent interaction is an A2A model — `AgentTask`, `AgentMessage`,
`AgentArtifact`, `AgentResponse`. Nodes never pass plain dicts between each other;
the `TypedDict` graph state is only the LangGraph envelope. `Evidence` is domain
content carried in state (it goes into the report), not an agent transport.

## Single trace_id

The router mints one `trace_id` on the root task. Every later task, message,
artifact, and response is constructed with that same `trace_id`, and the final
`IntelligenceReport.trace_id` matches it. When an object is attached to a task,
`services.attach_message` / `attach_artifact` run `validate_*_belongs_to_task`,
which raises `ProtocolViolationError` on a `task_id`/`trace_id` mismatch — so a
broken correlation fails loudly.

## Task status lifecycle

`TaskStatus`: `PENDING → RUNNING → {COMPLETED | FAILED | CANCELLED}`. Allowed moves
are declared in `ALLOWED_TRANSITIONS`; `advance_task_status` enforces them via
`can_transition`. Each node owns the lifecycle of the task it executes and creates
the next subtask (same `trace_id`) routed to the next agent.

## Dependency injection

Agents depend only on interfaces, never concrete tools or model clients:

- **ToolGateway** (`InMemoryToolGateway` | `MCPToolGateway`) — selected by
  `settings.tool_gateway`.
- **LLMProvider** (`FakeLLMProvider` | `OllamaProvider`) — selected by
  `settings.llm_provider`.

Both are injected into the LangGraph run config by `run_workflow(query, gateway=,
llm=)` and read via `agents/_deps`. The FastAPI endpoint provides them through
overridable dependencies (`get_gateway`, `get_llm`), which tests replace with a
temp-DB gateway and the deterministic fake LLM.

## Design notes / trade-offs

- **Local-first & deterministic by default.** Retrieval is real (MCP tools), but
  the default `FakeLLMProvider` keeps the demo offline and tests stable. Set
  `MILTECH_LLM_PROVIDER=ollama` for a real model.
- **A2A-style, not Google A2A.** Internal, typed, observable protocol — no A2A SDK
  or JSON-RPC transport.
- **Sync gateway/LLM interfaces.** Keeps nodes simple; `MCPToolGateway` confines
  async to an `anyio` portal bridge.
