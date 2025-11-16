from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from api.app.core.config import settings
from api.app.models.admin import (
    AdminRunsResponse,
    InspectResponse,
    OverrideCreatePayload,
    OverrideEntry,
    OverrideHistoryResponse,
)
from api.app.services import admin_service

router = APIRouter(prefix=f"{settings.api_v1_prefix}/admin", tags=["admin"])


@router.get("/runs", response_model=AdminRunsResponse, summary="Etat des jobs ingest")
async def get_admin_runs() -> AdminRunsResponse:
    return await admin_service.fetch_runs()


@router.get(
    "/overrides", response_model=OverrideHistoryResponse, summary="Historique des overrides"
)
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not enabled"
        )
    try:
        return await admin_service.create_override(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post(
    "/inspect",
    response_model=InspectResponse,
    summary="Inspecter un PDF via config YAML",
)
async def inspect_pdf(
    supplier: str = Form(...), file: UploadFile = File(...), limit: int = Form(50)
) -> InspectResponse:
    temp_path: Path | None = None
    try:
        suffix = Path(file.filename or "upload.pdf").suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Empty file")
            tmp.write(content)
            temp_path = Path(tmp.name)
        return await admin_service.inspect_upload(
            supplier=supplier, file_path=temp_path, limit=limit
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)
