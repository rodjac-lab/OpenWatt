from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.app.core.config import settings
from api.app.models.admin import (
    AdminRunsResponse,
    OverrideCreatePayload,
    OverrideEntry,
    OverrideHistoryResponse,
)
from api.app.services import admin_service

router = APIRouter(prefix=f"{settings.api_v1_prefix}/admin", tags=["admin"])


@router.get("/runs", response_model=AdminRunsResponse, summary="Etat des jobs ingest")
async def get_admin_runs() -> AdminRunsResponse:
    return await admin_service.fetch_runs()


@router.get("/overrides", response_model=OverrideHistoryResponse, summary="Historique des overrides")
async def get_overrides() -> OverrideHistoryResponse:
    return await admin_service.list_overrides()


@router.post(
    "/overrides",
    response_model=OverrideEntry,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Déclarer une source manuelle",
)
async def create_override(payload: OverrideCreatePayload) -> OverrideEntry:
    if not settings.enable_db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not enabled")
    try:
        return await admin_service.create_override(payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
