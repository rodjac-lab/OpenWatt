from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from api.app.core.config import settings
from api.app.models.tariffs import (
    TariffCollection,
    TariffHistoryFilters,
    TariffHistoryResponse,
    TariffOption,
)
from api.app.services import tariff_service

PUISSANCE_VALUES = [3, 6, 9, 12, 15, 18, 24, 30, 36]

router = APIRouter(prefix=settings.api_v1_prefix, tags=["tariffs"])


@router.get("/tariffs", response_model=TariffCollection, summary="Derniers tarifs frais")
async def get_latest_tariffs(
    option: TariffOption | None = Query(default=None, description="Filtrer par option tarifaire"),
    puissance: int | None = Query(
        default=None,
        description="Limiter a une puissance specifique (kVA)",
        ge=min(PUISSANCE_VALUES),
        le=max(PUISSANCE_VALUES),
    ),
    include_stale: bool = Query(
        default=False,
        description="Inclure les observations marquees stale/broken pour audit",
    ),
) -> TariffCollection:
    """Expose `/v1/tariffs` tel que decrit dans `specs/api.md`."""
    return await tariff_service.fetch_latest_tariffs(option=option, puissance=puissance, include_stale=include_stale)


@router.get(
    "/tariffs/history",
    response_model=TariffHistoryResponse,
    summary="Historique insert-only",
)
async def get_tariff_history(
    supplier: str | None = Query(default=None, description="Filtrer par fournisseur"),
    option: TariffOption | None = Query(default=None),
    puissance: int | None = Query(default=None, ge=min(PUISSANCE_VALUES), le=max(PUISSANCE_VALUES)),
    since: date | None = Query(default=None, description="Inclure les observations a partir de cette date"),
    until: date | None = Query(default=None, description="Inclure les observations jusqu'a cette date"),
) -> TariffHistoryResponse:
    filters = TariffHistoryFilters(
        supplier=supplier,
        option=option,
        puissance_kva=puissance,
        since=since,
        until=until,
    )
    return await tariff_service.fetch_history(filters)
