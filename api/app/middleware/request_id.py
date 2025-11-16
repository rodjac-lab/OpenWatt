"""Request ID middleware for distributed tracing.

Adds unique request_id to every HTTP request for correlation across logs.
"""
from __future__ import annotations

import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request_id to each request.

    The request_id is:
    - Generated as UUID4
    - Added to response headers (X-Request-ID)
    - Bound to structlog context for all logs in this request
    - Accessible via request.state.request_id
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with request_id injection."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store in request state
        request.state.request_id = request_id

        # Bind to structlog context for this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        # Process request
        response = await call_next(request)

        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id

        return response
