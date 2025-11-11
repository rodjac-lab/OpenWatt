from __future__ import annotations

from fastapi import APIRouter

from api.app.core.config import settings
from api.app.models.tariffs import TrveDiffResponse
from api.app.services import tariff_service

router = APIRouter(prefix=f"{settings.api_v1_prefix}/guards", tags=["guards"])


@router.get("/trve-diff", response_model=TrveDiffResponse, summary="Ecart vs TRVE")
async def get_trve_diff() -> TrveDiffResponse:
    """Return last validation snapshot between observed tariffs and TRVE reference."""
    return tariff_service.compute_trve_diff()
