from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from api.app.db import models
from api.app.models.enums import FreshnessStatus, TariffOption
from api.app.models.tariffs import TariffObservation


class TariffRepository:
    """Read-only helpers mapping ORM rows to API payloads."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch_latest(
        self,
        *,
        option: TariffOption | None = None,
        puissance: int | None = None,
        include_stale: bool = False,
    ) -> list[TariffObservation]:
        stmt = (
            select(models.Tariff)
            .join(models.Supplier)
            .options(selectinload(models.Tariff.supplier))
        )
        if option:
            stmt = stmt.where(models.Tariff.option == option)
        if puissance:
            stmt = stmt.where(models.Tariff.puissance_kva == puissance)
        stmt = stmt.order_by(models.Tariff.observed_at.desc()).limit(512)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        observations: list[TariffObservation] = []
        for row in rows:
            obs = self._to_observation(row)
            if include_stale or obs.data_status not in {FreshnessStatus.STALE, FreshnessStatus.BROKEN}:
                observations.append(obs)
        return observations

    async def fetch_history(self, filters: dict) -> list[TariffObservation]:
        stmt = (
            select(models.Tariff)
            .join(models.Supplier)
            .options(selectinload(models.Tariff.supplier))
        )
        if supplier := filters.get("supplier"):
            stmt = stmt.where(models.Supplier.name == supplier)
        if option := filters.get("option"):
            stmt = stmt.where(models.Tariff.option == option)
        if puissance := filters.get("puissance_kva"):
            stmt = stmt.where(models.Tariff.puissance_kva == puissance)
        if since := filters.get("since"):
            stmt = stmt.where(models.Tariff.observed_at >= datetime.combine(since, datetime.min.time(), tzinfo=timezone.utc))
        if until := filters.get("until"):
            stmt = stmt.where(models.Tariff.observed_at <= datetime.combine(until, datetime.max.time(), tzinfo=timezone.utc))
        stmt = stmt.order_by(models.Tariff.observed_at.desc()).limit(1024)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_observation(row) for row in rows]

    def _to_observation(self, row: models.Tariff) -> TariffObservation:
        observed_at = row.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        return TariffObservation(
            supplier=row.supplier.name if row.supplier else "unknown",
            option=row.option,
            puissance_kva=row.puissance_kva,
            price_kwh_ttc=float(row.price_kwh_ttc) if row.price_kwh_ttc is not None else None,
            price_kwh_hp_ttc=float(row.price_kwh_hp_ttc) if row.price_kwh_hp_ttc is not None else None,
            price_kwh_hc_ttc=float(row.price_kwh_hc_ttc) if row.price_kwh_hc_ttc is not None else None,
            abo_month_ttc=float(row.abo_month_ttc),
            observed_at=observed_at,
            parser_version=row.parser_version,
            source_url=row.source_url,
            source_checksum=row.source_checksum,
            data_status=self._derive_status(row),
            last_verified=None,
        )

    def _derive_status(self, row: models.Tariff) -> FreshnessStatus:
        now = datetime.now(timezone.utc)
        observed_at = row.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if row.notes and "broken" in row.notes.lower():
            return FreshnessStatus.BROKEN
        if row.notes and "validation" in row.notes.lower() and (now - observed_at) <= timedelta(hours=48):
            return FreshnessStatus.VERIFYING
        if now - observed_at > timedelta(days=14):
            return FreshnessStatus.STALE
        return FreshnessStatus.FRESH
