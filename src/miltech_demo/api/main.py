from fastapi import FastAPI

from miltech_demo.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "model": settings.model_name,
    }