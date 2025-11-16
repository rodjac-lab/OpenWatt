from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db import models


class AdminRepository:
    """Persistence helpers for the admin console (overrides, runs)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_override(
        self,
        *,
        supplier: str,
        url: str,
        observed_at: datetime | None = None,
    ) -> models.AdminOverride:
        entry = models.AdminOverride(supplier=supplier, url=url, observed_at=observed_at)
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def list_overrides(self, limit: int = 50) -> list[models.AdminOverride]:
        stmt = (
            select(models.AdminOverride)
            .order_by(models.AdminOverride.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
