"""Structured logging configuration for OpenWatt API.

Uses structlog for structured JSON logging with request-id correlation.
Designed for production observability (ELK stack, CloudWatch, etc.).
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from api.app.core.config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to all log entries."""
    event_dict["service"] = settings.project_name
    event_dict["environment"] = "production"  # TODO: Add to settings
    return event_dict


def configure_logging() -> None:
    """Configure structured logging with JSON output for production.

    Logs are formatted as JSON with:
    - timestamp (ISO 8601)
    - level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - event (log message)
    - request_id (correlation ID for distributed tracing)
    - service (project name)
    - logger (module name)
    - Additional context fields
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Structlog processors chain
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_created", user_id=123, email="test@example.com")
        # Output: {"event": "user_created", "user_id": 123, "email": "test@example.com", ...}
    """
    return structlog.get_logger(name)
