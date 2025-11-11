"""Liveness endpoint keeping parity with Spec-Kit availability requirements."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from api.app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health probe", description="Basic uptime signal for monitoring.")
async def health_probe() -> dict[str, str]:
    """Return minimal metadata so GitHub Actions and monitors can confirm uptime."""
    return {
        "status": "ok",
        "service": settings.project_name,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
