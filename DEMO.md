# Demo Walkthrough

A short, runnable demo of the end-to-end multi-agent workflow. Everything runs
locally and deterministically (default fake LLM + in-process tools).

## 1. Setup

```bash
make install
```

## 2. Run the API

```bash
make run        # http://localhost:8000
```

## 3. Ask a question

```bash
curl -s localhost:8000/api/v1/chat \
  -H 'content-type: application/json' \
  -d '{"query": "Summarize recent activity in the eastern corridor."}' | jq
```

Expected response shape (ids/text vary; default LLM is the deterministic fake):

```json
{
  "answer": "[fake-llm] ... Query: Summarize recent activity in the eastern corridor ...",
  "evidence": [
    {
      "document_id": "eastern-corridor",
      "snippet": "Increased vehicle movement has been observed along the eastern corridor...",
      "relevance_score": 1.0,
      "rationale": "Document matched query '...'."
    }
  ],
  "agent_trace": [
    "router: created root task -> analyst",
    "analyst: retrieved evidence via tools -> validator",
    "validator: validated + corroborated analysis -> reporter",
    "reporter: compiled final report"
  ]
}
```

## What just happened

1. **router** created the root `AgentTask` and minted the workflow `trace_id`.
2. **analyst** called the MCP tools through the `ToolGateway`
   (`search_documents` + `query_intel_db`), turned the hits into `Evidence`, and
   used the `LLMProvider` to synthesize the analysis — emitting an `AgentMessage`,
   `AgentArtifact`, and `AgentResponse`.
3. **validator** consumed the analyst artifact, corroborated it via
   `query_intel_db`, and produced its own message/artifact/response.
4. **reporter** wrote the summary via the LLM and assembled the final
   `IntelligenceReport` (carrying the evidence).

The structlog JSON logs show one `trace_id` across every step.

## 4. Use a real local model (optional)

```bash
ollama serve && ollama pull qwen2.5:7b-instruct
export MILTECH_LLM_PROVIDER=ollama
make run
# probe the provider:
curl -s localhost:8000/api/v1/llm/test -H 'content-type: application/json' \
  -d '{"prompt": "Say hello in one word."}' | jq
```

## 5. Explore the MCP server directly

```bash
make mcp-server     # stdio MCP server exposing the three tools
```

The analyst uses these same tools in-process; an external MCP client (e.g. Claude
Desktop) can call them over the protocol.

## 6. Quality gates

```bash
make lint
make type
make test
```

## Talking points (interview)

- Every agent interaction is a typed A2A object; one `trace_id` makes the whole
  run traceable, and correlation is enforced (fails loudly on mismatch).
- Tools and the LLM are behind injected interfaces (`ToolGateway`, `LLMProvider`)
  with in-memory/MCP and fake/Ollama implementations — swappable via config, no
  agent changes.
- The MCP server is real; the in-graph gateway shares its service layer.
- Deterministic and offline by default, so the workflow is fully testable.
