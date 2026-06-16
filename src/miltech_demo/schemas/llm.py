"""Typed request/response models for the LLM provider abstraction."""

from pydantic import ConfigDict, Field

from miltech_demo.schemas.base import DomainModel


class LLMRequest(DomainModel):
    """A single generation request to an LLM provider."""

    prompt: str = Field(min_length=1, description="The user prompt.")
    system: str | None = Field(default=None, description="Optional system instruction.")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature.")
    max_tokens: int | None = Field(default=None, ge=1, description="Optional output cap.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "prompt": "Summarize recent activity in the eastern corridor.",
                    "system": "You are an intelligence analyst.",
                    "temperature": 0.0,
                }
            ]
        }
    )


class LLMResponse(DomainModel):
    """The result of an LLM generation."""

    text: str = Field(description="Generated text.")
    model: str = Field(description="Model/provider identifier that produced the text.")
