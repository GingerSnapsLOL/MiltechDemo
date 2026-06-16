# LLM Provider

A pluggable, local-first LLM abstraction. Agents depend only on the
`LLMProvider` interface and receive a concrete implementation via dependency
injection — exactly mirroring the `ToolGateway` pattern (see `docs/mcp.md`).

## Architecture

```
LangGraph agents (analyst synthesis, reporter writing)
        │  depend only on the ABC, injected via the run config
        ▼
   LLMProvider (abc.ABC)   generate(LLMRequest) -> LLMResponse   (sync)
        ├── FakeLLMProvider   (deterministic, no I/O; default)
        └── OllamaProvider    (ollama.Client -> local Ollama server)
                                   └── (future) VLLMProvider (OpenAI-compatible)
```

- **`LLMProvider`** (`services/llm.py`) — `abc.ABC` with one method,
  `generate(LLMRequest) -> LLMResponse`. Typed Pydantic I/O (`schemas/llm.py`).
- **`FakeLLMProvider`** — deterministic, offline; echoes a trimmed prompt. The
  default, so the whole demo runs locally with no model server and tests stay
  stable.
- **`OllamaProvider`** (`services/ollama_provider.py`) — wraps `ollama.Client`,
  sends a system+user chat to a local Ollama server, and returns the content.
  Raises a typed `LLMError` on failure. The client is injectable for testing.

## Configuration (`pydantic-settings`)

`core/config.Settings` (env prefix `MILTECH_`):

- `llm_provider: "fake" | "ollama"` (default `"fake"`).
- `model_name` (default `qwen2.5:7b-instruct`) and `ollama_base_url`
  (default `http://localhost:11434`) — used by `OllamaProvider`.
- `llm_temperature` (default `0.0`).

`build_llm_provider(settings)` selects the implementation; `get_llm_provider()`
is the cached process-wide default. To use a real model:

```bash
export MILTECH_LLM_PROVIDER=ollama
ollama serve && ollama pull qwen2.5:7b-instruct
```

## Dependency injection

Agents never import a model client. The analyst and reporter obtain the provider
from the LangGraph run config via `agents/_deps.llm_from_config`, and
`run_workflow(query, gateway=..., llm=...)` injects it
(`config["configurable"]["llm"]`). A guard test
(`tests/agents/test_no_direct_tool_access.py`) asserts agent modules don't import
`ollama`.

## API probe

`POST /api/v1/llm/test` runs the configured provider against a prompt — a quick
connectivity/sanity check.

```bash
curl -s localhost:8000/api/v1/llm/test \
  -H 'content-type: application/json' \
  -d '{"prompt": "Say hello in one word."}' | jq
# -> {"text": "...", "model": "..."}
```

## Future: vLLM

vLLM serves an OpenAI-compatible HTTP API. Adding it needs only a new
`VLLMProvider(LLMProvider)` (httpx/`openai` client against the vLLM `/v1`
endpoint), a `"vllm"` option in `llm_provider`, and a `build_llm_provider`
branch. Because agents depend only on the `LLMProvider` ABC, **no agent or graph
changes are required**.

## Testing

- `tests/services/test_llm.py` — `FakeLLMProvider` determinism; `OllamaProvider`
  request-building/parsing and error wrapping with a stub client; a conformance
  suite over both providers; an opt-in real-server test
  (`MILTECH_OLLAMA_TEST=1`, skipped otherwise).
- `tests/api/test_llm.py` — the `/api/v1/llm/test` endpoint (fake provider).
