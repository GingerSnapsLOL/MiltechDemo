# 5-Minute Technical Demo — Runbook

A tight, rehearsed script for demoing MilTech Demo live. Everything runs locally
and deterministically (default **fake LLM** + in-process tools), so nothing depends
on a network or a model server during the demo.

> One-liner to open with:
> *"This is a local-first multi-agent intelligence platform. A query flows through
> a LangGraph workflow of four agents that talk to each other using an A2A-style
> protocol and pull real evidence through MCP tools — and every step shares one
> trace_id so the whole run is auditable."*

---

## Before you start (do this off-camera)

```bash
make install            # uv sync
make test               # confirm green: ~98 passed, 1 skipped
make run                # FastAPI on http://localhost:8000
```

Open three things:
1. A terminal (for `curl`).
2. Browser tab → `http://localhost:8000/docs` (Swagger UI).
3. Editor with these files ready: `graph/workflow.py`, `schemas/a2a.py`,
   `services/protocol.py`, `services/tool_gateway.py`.

Keep `jq` installed for readable JSON.

---

## Demo scenario

A user asks an intelligence question — *"Summarize recent activity in the eastern
corridor."* The platform runs `router → analyst → (MCP tools) → validator →
reporter` and returns an **answer**, the **evidence** behind it, and the **agent
trace**. Goal: show clean architecture, A2A correlation, MCP integration, and
test-backed determinism in five minutes.

---

## Minute-by-minute

### 0:00–0:45 — Frame it (talk + one file)
- **Say:** the one-liner above; "built for architecture quality and
  explainability, not feature count — Python 3.12, FastAPI, LangGraph, MCP,
  Pydantic v2, fully typed (mypy strict), tested."
- **Show:** `graph/workflow.py` — point at the four `add_node`/`add_edge` lines.
  *"The whole pipeline is declared here in ~15 lines."*

### 0:45–2:00 — Run the end-to-end query (the money shot)
- **Click/Run** in the terminal:
  ```bash
  curl -s localhost:8000/api/v1/chat \
    -H 'content-type: application/json' \
    -d '{"query": "Summarize recent activity in the eastern corridor."}' | jq
  ```
- **Show:** the response has three keys — `answer`, `evidence` (cited snippets with
  `document_id` + `relevance_score`), and `agent_trace` (4 ordered steps).
- **Say:** *"One HTTP call ran the whole agent graph. The evidence came from real
  MCP tool calls; the agent_trace is the audit log of which agent did what."*
- **Show (server logs):** point at the structlog JSON lines — *"notice the **same
  `trace_id`** on router → analyst → validator → reporter."*

### 2:00–3:00 — Show the A2A protocol & enforcement
- **Show:** `schemas/a2a.py` — `AgentTask / AgentMessage / AgentArtifact /
  AgentResponse`, each carrying `trace_id` + `task_id`.
- **Show:** `services/protocol.py` — `attach_message` / `attach_artifact` call
  `validate_*_belongs_to_task`. **Say:** *"Agents can't bypass correlation — attach
  a mismatched message and it raises `ProtocolViolationError`. There's a test for
  exactly that."*

### 3:00–4:00 — Show MCP + the ToolGateway abstraction
- **Show:** `services/tool_gateway.py` — the `ToolGateway` ABC with
  `InMemoryToolGateway` and `MCPToolGateway`.
- **Say:** *"Agents depend on this interface, injected via the LangGraph run config
  — they never import a tool client. The MCP server exposes the same three tools
  over the protocol; the in-graph gateway shares the service layer, so there's one
  implementation. A guard test enforces that agents don't import tools directly."*
- **Optional click:** in Swagger (`/docs`) expand **POST /api/v1/llm/test**, "Try it
  out", send `{"prompt":"hello"}` → returns `fake-llm`. **Say:** *"The LLM is
  pluggable too — fake by default for determinism; flip one env var to use a local
  Ollama model."*

### 4:00–4:45 — Prove it's real engineering
- **Run:**
  ```bash
  make check        # ruff + mypy --strict + pytest
  ```
- **Say:** *"Strict typing, lint, and ~100 tests — schema validation, service
  logic, a ToolGateway conformance suite over both implementations, and full
  workflow + API integration tests. Deterministic and offline, so it's
  reproducible."*

### 4:45–5:00 — Close
- **Say:** *"To summarize: a small, clean, fully-typed multi-agent system —
  LangGraph for orchestration, an A2A-style protocol for observable agent
  communication, MCP for real tool integration, and a pluggable local LLM. Honest
  scope: it's A2A-**style**, not Google A2A, and the default LLM is a deterministic
  fake — both swappable."*

---

## What to show (cheat sheet)

| Beat | Artifact | The point |
|------|----------|-----------|
| Pipeline | `graph/workflow.py` | declarative 4-node graph |
| Result | `POST /api/v1/chat` output | answer + evidence + agent_trace |
| Observability | server structlog output | one `trace_id` across all agents |
| Protocol | `schemas/a2a.py` + `services/protocol.py` | typed, enforced correlation |
| Tools | `services/tool_gateway.py` + `/docs` | MCP + DI + pluggable |
| Rigor | `make check` | strict types, lint, ~100 tests |

---

## Expected interviewer questions & suggested answers

**Q: Is this real Google A2A?**
A: No — and I'm explicit about that everywhere. It's an *A2A-style* protocol
inspired by agent-to-agent concepts: typed `AgentTask/Message/Artifact/Response`,
one `trace_id`, enforced correlation and a status lifecycle. No A2A SDK or JSON-RPC
transport. I'd adopt the real spec if interop with external A2A agents were a goal.

**Q: The LLM output looks templated — is the model actually running?**
A: By default no — the default provider is a deterministic `FakeLLMProvider` so the
demo and tests are offline and reproducible. `LLMProvider` is an ABC; set
`MILTECH_LLM_PROVIDER=ollama` and it calls a local Ollama model. The agents only
depend on the interface, so nothing else changes.

**Q: Why LangGraph instead of plain functions or an autonomous agent framework?**
A: The task is an explicit, auditable pipeline with shared evolving state. LangGraph
gives typed reducer-based state, single-responsibility nodes, and clean dependency
injection via run config — without emergent looping I'd have to debug. It's also
easy to explain, which matters here.

**Q: How does MCP add value over just calling a function?**
A: MCP is a standard, typed, discoverable tool boundary. The same three tools are
callable by the in-graph agents *and* by any external MCP client (e.g. Claude
Desktop) over the protocol — one implementation, two transports. Handlers are thin
and delegate to services.

**Q: How do you guarantee agents don't bypass the protocol / tools?**
A: Correlation is enforced in `services/protocol.py` (`attach_*` validate
`task_id`+`trace_id` and raise on mismatch), and a guard test asserts agent modules
never import the concrete services or tool/model clients — they only use the
injected interfaces.

**Q: How is the `trace_id` guaranteed to be consistent?**
A: The router mints it once on the root task; every child task, message, artifact,
and response is constructed with that same id, and the final report carries it.
`attach_*` rejects anything whose `trace_id`/`task_id` doesn't match the task. Tests
assert all four collections share one id.

**Q: Is `query_intel_db` an SQL-injection risk?**
A: No — it's a parameterized `LIKE` keyword search, never arbitrary SQL execution.
There's a test that feeds a `DROP TABLE` payload and confirms it's treated as a
literal term and the table survives.

**Q: How would you scale / productionize this?**
A: Stream the chat endpoint (SSE) and Ollama tokens; add a LangGraph checkpointer +
OpenTelemetry keyed on the existing `trace_id`; real RAG (embeddings + vector store)
behind `search_documents`; a FastAPI lifespan to manage the MCP gateway connection;
and a coverage threshold in CI. I keep these in the README's "Future improvements".

**Q: What's the weakest part / what would you change first?**
A: Two things from my own review: the cached `MCPToolGateway` isn't closed on
shutdown (fine for the default in-memory path, but I'd add a lifespan hook), and
nodes mutate the prior task object in place — safe now, but I'd return mutated tasks
before adding a checkpointer. Both are tracked in TASK.md.

**Q: Why synthetic data and a fake model — is anything actually working?**
A: The *plumbing* is fully real: FastAPI, the LangGraph graph, the A2A protocol with
enforcement, a real MCP server, and the provider abstractions. I substituted
deterministic data/LLM so the demo is reproducible and the focus stays on
architecture. Swapping in real data/model is a config change, not a rewrite.

---

## If something breaks (recovery)

- API won't start → `make install` then `make run`; check port 8000 is free.
- Empty `evidence` → use a query that matches the synthetic reports (e.g. contains
  "corridor", "border", "supply", or "air").
- Fall back to `make test` to show everything passes even if the live server misbehaves.
