"""Liveness endpoint keeping parity with Spec-Kit availability requirements."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from api.app.core.config import settings
from api.app.core.logging import get_logger
from api.app.services.health_service import HealthService

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", summary="Health probe", description="Basic uptime signal for monitoring.")
async def health_probe() -> dict[str, str]:
    """Return minimal metadata so GitHub Actions and monitors can confirm uptime."""
    logger.debug("health_check_requested")
    return {
        "status": "ok",
        "service": settings.project_name,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/v1/health/ingest",
    summary="Ingest pipeline health",
    description="Get health status of ingest pipeline for all suppliers.",
)
async def ingest_health() -> dict[str, Any]:
    """Return health status of ingest pipeline."""
    logger.debug("ingest_health_check_requested")
    service = HealthService()
    return await service.get_ingest_health()
