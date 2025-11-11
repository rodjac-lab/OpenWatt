from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.app.db.base import Base
from ingest.persist import TariffPersister
from parsers.core.config import SelectorConfig, SourceConfig, SupplierConfig


def test_tariff_persister_inserts_and_skips_duplicates():
    import asyncio

    asyncio.run(_run_persist_test())


async def _run_persist_test():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    config = SupplierConfig(
        supplier="TestCo",
        parser_version="test_v1",
        source=SourceConfig(url="https://example.com", format="html"),
        selectors=SelectorConfig(rows="article"),
    )

    rows = [
        {
            "supplier": "TestCo",
            "option": "BASE",
            "puissance_kva": 6,
            "abo_month_ttc": 12.5,
            "price_kwh_ttc": 0.251,
            "price_kwh_hp_ttc": None,
            "price_kwh_hc_ttc": None,
            "observed_at": "2025-02-12T08:00:00Z",
            "parser_version": "test_v1",
            "source_url": "https://example.com/tarifs",
            "source_checksum": "f" * 64,
        }
    ]

    persister = TariffPersister(session_factory=session_factory)

    first_run = await persister.persist(config, rows)
    assert first_run == 1

    second_run = await persister.persist(config, rows)
    assert second_run == 0
