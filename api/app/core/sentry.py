"""Sentry configuration for error tracking and performance monitoring."""

from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from api.app.core.config import settings
from api.app.core.logging import get_logger

logger = get_logger(__name__)


def configure_sentry() -> None:
    """Configure Sentry SDK for error tracking.

    Only initializes if OPENWATT_SENTRY_DSN is set.

    Features:
    - Automatic error capture
    - Performance monitoring (transactions)
    - Request context (headers, user, etc.)
    - SQLAlchemy query tracking
    - Release tracking
    """
    if not settings.sentry_dsn:
        logger.info("sentry_disabled", reason="no_dsn_configured")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=f"openwatt@0.1.0",  # TODO: Get from git tag
        # Performance monitoring
        traces_sample_rate=1.0 if settings.environment == "development" else 0.1,
        # Profiles (CPU/memory)
        profiles_sample_rate=1.0 if settings.environment == "development" else 0.1,
        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=None,  # Don't capture logs (we use structlog)
                event_level=None,  # Don't capture events
            ),
        ],
        # Send default PII (emails, usernames, IPs)
        send_default_pii=False,  # Disable for GDPR compliance
        # Attach stack locals to errors (useful for debugging)
        attach_stacktrace=True,
        # Max breadcrumbs to capture
        max_breadcrumbs=50,
        # Before send hook for filtering
        before_send=_before_send,
    )

    logger.info(
        "sentry_initialized",
        environment=settings.environment,
        traces_sample_rate=1.0 if settings.environment == "development" else 0.1,
    )


def _before_send(event: dict, hint: dict) -> dict | None:
    """Filter events before sending to Sentry.

    Args:
        event: Sentry event dict
        hint: Additional context

    Returns:
        Modified event or None to drop it
    """
    # Drop health check errors (they're expected)
    if "request" in event:
        url = event["request"].get("url", "")
        if "/health" in url:
            return None

    # Drop specific exceptions
    if "exception" in event:
        for exception in event["exception"].get("values", []):
            exception_type = exception.get("type", "")

            # Drop expected exceptions
            if exception_type in ["HTTPException", "ValidationError"]:
                return None

    return event


def capture_exception(error: Exception, **context: any) -> None:
    """Manually capture an exception to Sentry with context.

    Args:
        error: Exception to capture
        **context: Additional context (user_id, tariff_id, etc.)

    Example:
        >>> try:
        >>>     parse_pdf(file)
        >>> except Exception as exc:
        >>>     capture_exception(exc, supplier="EDF", file_size=1024)
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **context: any) -> None:
    """Manually capture a message to Sentry.

    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **context: Additional context

    Example:
        >>> capture_message(
        >>>     "Unusual tariff spike detected",
        >>>     level="warning",
        >>>     supplier="EDF",
        >>>     increase_percent=150
        >>> )
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)
