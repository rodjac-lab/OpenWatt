from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.app.core import config as config_module
from api.app.db import models
from api.app.db.base import Base
from api.app.db import session as session_module
from api.app.models.enums import FreshnessStatus, TariffOption


@pytest.fixture
def seeded_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Seed a lightweight SQLite DB so the API exercises the persistence path."""

    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'openwatt_api.db').as_posix()}"
    engine = create_async_engine(database_url, future=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def _prepare():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            supplier = models.Supplier(name="Engie", website="https://particuliers.engie.fr")
            session.add(supplier)
            await session.flush()

            now = datetime.now(timezone.utc)
            fresh_row = models.Tariff(
                supplier_id=supplier.id,
                option=TariffOption.HPHC,
                puissance_kva=9,
                price_kwh_hp_ttc=0.15097,
                price_kwh_hc_ttc=0.13183,
                abo_month_ttc=38.95,
                observed_at=now - timedelta(days=2),
                parser_version="engie_pdf_v1",
                source_url="https://particuliers.engie.fr/content/dam/pdf/fiches-descriptives/fiche-descriptive-elec-reference-3-ans.pdf",
                source_checksum="f2f9d6fca563bf9a94f4e5a3c30c35b6aecb5ba8cb4d9138313ecc48f2e19a09",
            )
            stale_row = models.Tariff(
                supplier_id=supplier.id,
                option=TariffOption.HPHC,
                puissance_kva=9,
                price_kwh_hp_ttc=0.17097,
                price_kwh_hc_ttc=0.15183,
                abo_month_ttc=40.12,
                observed_at=now - timedelta(days=40),
                parser_version="engie_pdf_v0",
                source_url="https://legacy.engie.fr/tarifs",
                source_checksum="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            )
            session.add_all([fresh_row, stale_row])
            await session.commit()

    asyncio.run(_prepare())

    monkeypatch.setattr(session_module, "_engine", engine, raising=False)
    monkeypatch.setattr(session_module, "_session_factory", session_factory, raising=False)
    monkeypatch.setattr(config_module.settings, "enable_db", True)
    monkeypatch.setattr(config_module.settings, "database_url", database_url)

    yield

    asyncio.run(engine.dispose())
    monkeypatch.setattr(session_module, "_engine", None, raising=False)
    monkeypatch.setattr(session_module, "_session_factory", None, raising=False)


def test_latest_tariffs_reads_from_db(seeded_db, client):
    response = client.get("/v1/tariffs")
    assert response.status_code == 200
    items = response.json()["items"]
    # The stale observation should be hidden when include_stale=False.
    assert len(items) == 1
    assert items[0]["supplier"] == "Engie"
    assert items[0]["data_status"] == FreshnessStatus.FRESH.value


def test_latest_tariffs_include_stale_flag(seeded_db, client):
    response = client.get("/v1/tariffs", params={"include_stale": True})
    assert response.status_code == 200
    statuses = {item["data_status"] for item in response.json()["items"]}
    assert {FreshnessStatus.FRESH.value, FreshnessStatus.STALE.value}.issubset(statuses)


def test_tariff_history_returns_db_rows(seeded_db, client):
    response = client.get("/v1/tariffs/history", params={"supplier": "Engie", "option": "HPHC"})
    assert response.status_code == 200
    body = response.json()
    assert body["filters"]["supplier"] == "Engie"
    assert len(body["items"]) == 2
    observed_at_values = {item["observed_at"] for item in body["items"]}
    assert len(observed_at_values) == 2  # two distinct observations from the DB
