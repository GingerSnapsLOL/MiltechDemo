import structlog
from fastapi import FastAPI

from miltech_demo.core.config import get_settings
from miltech_demo.core.logging import configure_logging

settings = get_settings()
configure_logging(settings)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


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
