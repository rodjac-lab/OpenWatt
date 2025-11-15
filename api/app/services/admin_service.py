from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from api.app.core.config import settings
from api.app.db.repositories.admin import AdminRepository
from api.app.db.repositories.tariffs import TariffRepository
from api.app.db.session import get_session
from api.app.models.admin import (
    AdminRunItem,
    AdminRunsResponse,
    OverrideCreatePayload,
    OverrideEntry,
    OverrideHistoryResponse,
)
from api.app.models.enums import FreshnessStatus
from api.app.services.tariff_service import _seed_observations

logger = logging.getLogger(__name__)


async def fetch_runs() -> AdminRunsResponse:
    observations = await _latest_observations()
    items: list[AdminRunItem] = []
    for obs in observations:
        status = "ok"
        message = "Dernier run OK"
        if obs.data_status == FreshnessStatus.BROKEN:
            status = "nok"
            message = "Parser en erreur"
        elif obs.data_status == FreshnessStatus.VERIFYING:
            message = "Validation en attente"
        elif obs.data_status == FreshnessStatus.STALE:
            message = "Observation > 14j"
        items.append(
            AdminRunItem(
                supplier=obs.supplier,
                status=status,
                message=message,
                observed_at=obs.observed_at,
            )
        )
    items.sort(key=lambda item: (item.observed_at or datetime.fromtimestamp(0)), reverse=True)
    return AdminRunsResponse(generated_at=datetime.now(timezone.utc), items=items)


async def list_overrides() -> OverrideHistoryResponse:
    if not settings.enable_db:
        return OverrideHistoryResponse(items=[])
    try:
        async with get_session() as session:
            repo = AdminRepository(session)
            rows = await repo.list_overrides()
    except SQLAlchemyError as exc:
        logger.warning("DB list_overrides failed: %s", exc)
        return OverrideHistoryResponse(items=[])
    return OverrideHistoryResponse(items=[OverrideEntry.model_validate(row) for row in rows])


async def create_override(payload: OverrideCreatePayload) -> OverrideEntry:
    if not settings.enable_db:
        raise RuntimeError("Database disabled")
    async with get_session() as session:
        repo = AdminRepository(session)
        try:
            entry = await repo.insert_override(
                supplier=payload.supplier,
                url=str(payload.url),
                observed_at=payload.observed_at,
            )
            await session.commit()
            return OverrideEntry.model_validate(entry)
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("Failed to insert override: %s", exc)
            raise


async def _latest_observations():
    observations = []
    if settings.enable_db:
        try:
            async with get_session() as session:
                repo = TariffRepository(session)
                observations = await repo.fetch_latest(include_stale=True)
        except SQLAlchemyError as exc:
            logger.warning("DB fetch_latest for admin runs failed: %s", exc)
            observations = []
    if not observations:
        observations = _seed_observations()
    return observations
