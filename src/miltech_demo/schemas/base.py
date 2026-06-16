"""Shared base classes for domain models.

All domain models inherit from :class:`DomainModel` so they share strict,
explicit validation behaviour. Models that represent persisted entities inherit
from :class:`IdentifiedModel`, which supplies a generated id and creation
timestamp.
"""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def now_utc() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def new_id() -> str:
    """Return a new random identifier."""
    return str(uuid4())


class DomainModel(BaseModel):
    """Base for all domain models: reject unknown fields, validate on assignment."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class IdentifiedModel(DomainModel):
    """A domain model with a generated identifier and creation timestamp."""

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=now_utc)
