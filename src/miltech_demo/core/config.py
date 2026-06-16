from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Default packaged synthetic markdown reports directory (src/miltech_demo/data/reports).
_DEFAULT_REPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"


class Settings(BaseSettings):
    app_name: str = "MilTech Demo"
    environment: str = "local"
    log_level: str = "INFO"

    model_provider: str = "ollama"
    model_name: str = "qwen2.5:7b-instruct"
    ollama_base_url: str = "http://localhost:11434"

    # MCP data sources.
    reports_dir: Path = _DEFAULT_REPORTS_DIR
    intel_db_path: Path = Path("intel.db")

    # Which ToolGateway implementation agents use: in-process or real MCP client.
    tool_gateway: Literal["memory", "mcp"] = "memory"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MILTECH_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()