"""Middleware modules for OpenWatt API."""

from __future__ import annotations

from api.app.middleware.request_id import RequestIDMiddleware

__all__ = ["RequestIDMiddleware"]
