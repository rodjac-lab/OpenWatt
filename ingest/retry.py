"""Retry logic with exponential backoff for ingestion pipeline.

Uses tenacity for robust retry behavior with configurable backoff.
"""

from __future__ import annotations

import logging
from typing import TypeVar, Callable

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_network_error(
    max_attempts: int = 3,
    min_wait_seconds: int = 1,
    max_wait_seconds: int = 10,
) -> Callable:
    """Decorator for retrying operations that may fail due to network issues.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait_seconds: Minimum wait time between retries
        max_wait_seconds: Maximum wait time between retries

    Returns:
        Decorator function

    Example:
        >>> @retry_on_network_error(max_attempts=5)
        >>> def fetch_tariff_pdf(url: str) -> bytes:
        >>>     return requests.get(url).content
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=1,
            min=min_wait_seconds,
            max=max_wait_seconds,
        ),
        retry=retry_if_exception_type(
            (
                ConnectionError,
                TimeoutError,
                OSError,
            )
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        reraise=True,
    )


def retry_on_parse_error(
    max_attempts: int = 2,
) -> Callable:
    """Decorator for retrying parse operations.

    Retries fewer times than network operations since parsing errors
    are usually deterministic.

    Args:
        max_attempts: Maximum number of retry attempts (default: 2)

    Returns:
        Decorator function

    Example:
        >>> @retry_on_parse_error(max_attempts=2)
        >>> def parse_pdf_table(pdf_path: str) -> list[dict]:
        >>>     return pdfplumber.extract_table(pdf_path)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((ValueError, KeyError, IndexError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
