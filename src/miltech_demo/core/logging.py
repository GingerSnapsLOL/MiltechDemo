"""Structured logging setup using structlog.

Call :func:`configure_logging` once at application startup. Modules then obtain
a logger via ``structlog.get_logger(__name__)``.
"""

import logging

import structlog

from miltech_demo.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure structlog to emit JSON logs at the configured level."""
    level = logging.getLevelNamesMapping().get(settings.log_level.upper(), logging.INFO)

    logging.basicConfig(format="%(message)s", level=level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
