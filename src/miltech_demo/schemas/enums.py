"""Enumerations shared across domain models."""

from enum import StrEnum


class Classification(StrEnum):
    """Security classification level of a document or report."""

    UNCLASSIFIED = "UNCLASSIFIED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"
