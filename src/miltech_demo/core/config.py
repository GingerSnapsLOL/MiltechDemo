from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MilTech Demo"
    environment: str = "local"
    log_level: str = "INFO"

    model_provider: str = "ollama"
    model_name: str = "qwen2.5:7b-instruct"
    ollama_base_url: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MILTECH_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()