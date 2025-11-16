from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, HttpUrl, constr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.app.db.models import Supplier, Tariff
from api.app.db.session import get_session_factory
from api.app.models.enums import Puissance, TariffOption
from parsers.core.config import SupplierConfig


class IngestRow(BaseModel):
    supplier: str
    option: TariffOption
    puissance_kva: Puissance
    price_kwh_ttc: float | None = None
    price_kwh_hp_ttc: float | None = None
    price_kwh_hc_ttc: float | None = None
    abo_month_ttc: float
    observed_at: datetime
    parser_version: str
    source_url: HttpUrl
    source_checksum: constr(min_length=64, max_length=64)


class TariffPersister:
    """Insert parsed rows into the insert-only database."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None):
        self.session_factory = session_factory or get_session_factory()

    async def persist(self, config: SupplierConfig, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        async with self.session_factory() as session:
            supplier_id = await self._ensure_supplier(session, config)
            inserted = 0
            for row in rows:
                data = IngestRow(**row)
                if await self._row_exists(session, supplier_id, data):
                    continue
                session.add(
                    Tariff(
                        supplier_id=supplier_id,
                        option=data.option,
                        puissance_kva=data.puissance_kva,
                        price_kwh_ttc=data.price_kwh_ttc,
                        price_kwh_hp_ttc=data.price_kwh_hp_ttc,
                        price_kwh_hc_ttc=data.price_kwh_hc_ttc,
                        abo_month_ttc=data.abo_month_ttc,
                        observed_at=data.observed_at,
                        parser_version=data.parser_version,
                        source_url=str(data.source_url),
                        source_checksum=data.source_checksum,
                    )
                )
                inserted += 1
            await session.commit()
            return inserted

    async def _ensure_supplier(self, session: AsyncSession, config: SupplierConfig) -> int:
        result = await session.execute(select(Supplier).where(Supplier.name == config.supplier))
        supplier = result.scalar_one_or_none()
        if supplier:
            return supplier.id
        supplier = Supplier(
            name=config.supplier,
            website=str(config.source.url.host or config.source.url),
        )
        session.add(supplier)
        await session.flush()
        return supplier.id

    async def _row_exists(self, session: AsyncSession, supplier_id: int, data: IngestRow) -> bool:
        stmt = select(Tariff.id).where(
            Tariff.supplier_id == supplier_id,
            Tariff.option == data.option,
            Tariff.puissance_kva == data.puissance_kva,
            Tariff.observed_at == data.observed_at,
            Tariff.parser_version == data.parser_version,
            Tariff.source_checksum == data.source_checksum,
        )
        result = await session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None
