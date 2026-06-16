from typing import Annotated

import structlog
from fastapi import Depends, FastAPI, HTTPException

from miltech_demo.core.config import get_settings
from miltech_demo.core.logging import configure_logging
from miltech_demo.graph.workflow import run_workflow
from miltech_demo.schemas import ChatRequest, ChatResponse, LLMRequest, LLMResponse
from miltech_demo.services import (
    LLMError,
    LLMProvider,
    ToolGateway,
    get_llm_provider,
    get_tool_gateway,
)

settings = get_settings()
configure_logging(settings)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


def get_llm() -> LLMProvider:
    """Provide the configured LLM provider (overridable in tests)."""
    return get_llm_provider()


def get_gateway() -> ToolGateway:
    """Provide the configured ToolGateway (overridable in tests)."""
    return get_tool_gateway()


@app.get("/health")
async def health() -> dict[str, str]:
    logger.info(
        "health_check",
        environment=settings.environment,
        model=settings.model_name,
    )
    return {
        "status": "ok",
        "environment": settings.environment,
        "model": settings.model_name,
    }


@app.post("/api/v1/llm/test")
def llm_test(
    request: LLMRequest,
    llm: Annotated[LLMProvider, Depends(get_llm)],
) -> LLMResponse:
    """Generate a response from the configured LLM provider (a connectivity probe)."""
    logger.info("llm_test", provider=settings.llm_provider)
    try:
        return llm.generate(request)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/v1/chat")
def chat(
    request: ChatRequest,
    gateway: Annotated[ToolGateway, Depends(get_gateway)],
    llm: Annotated[LLMProvider, Depends(get_llm)],
) -> ChatResponse:
    """Run the multi-agent workflow for a query and return the final report."""
    logger.info("chat_request", query=request.query)
    state = run_workflow(request.query, gateway=gateway, llm=llm)
    report = state["final_report"]
    if report is None:  # pragma: no cover - the reporter always produces a report
        raise HTTPException(status_code=500, detail="workflow produced no report")
    return ChatResponse(
        answer=report.summary,
        evidence=report.evidence,
        agent_trace=state["agent_trace"],
    )
