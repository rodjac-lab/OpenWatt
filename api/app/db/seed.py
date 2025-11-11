from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import text

from api.app.core.config import settings
from api.app.db.models import Supplier, Tariff
from api.app.db.session import get_engine, get_session_factory
from api.app.models.enums import TariffOption

SUPPLIERS = [
    {"name": "EDF", "website": "https://www.edf.fr"},
    {"name": "Engie", "website": "https://particuliers.engie.fr"},
    {"name": "TotalEnergies", "website": "https://www.totalenergies.fr"},
]

TARIFFS = [
    {
        "supplier": "EDF",
        "option": TariffOption.BASE,
        "puissance_kva": 6,
        "abo_month_ttc": 12.5,
        "price_kwh_ttc": 0.251,
    },
    {
        "supplier": "EDF",
        "option": TariffOption.HPHC,
        "puissance_kva": 9,
        "abo_month_ttc": 15.2,
        "price_kwh_hp_ttc": 0.269,
        "price_kwh_hc_ttc": 0.19,
    },
    {
        "supplier": "Engie",
        "option": TariffOption.HPHC,
        "puissance_kva": 6,
        "abo_month_ttc": 13.8,
        "price_kwh_hp_ttc": 0.278,
        "price_kwh_hc_ttc": 0.189,
    },
    {
        "supplier": "TotalEnergies",
        "option": TariffOption.BASE,
        "puissance_kva": 9,
        "abo_month_ttc": 16.4,
        "price_kwh_ttc": 0.259,
    },
]


async def seed() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE tariffs RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE suppliers RESTART IDENTITY CASCADE"))

    session_factory = get_session_factory()
    async with session_factory() as session:
        suppliers = {}
        for supplier in SUPPLIERS:
            db_supplier = Supplier(name=supplier["name"], website=supplier["website"])
            session.add(db_supplier)
            await session.flush()
            suppliers[supplier["name"]] = db_supplier.id

        now = datetime.now(timezone.utc)
        for row in TARIFFS:
            session.add(
                Tariff(
                    supplier_id=suppliers[row["supplier"]],
                    option=row["option"],
                    puissance_kva=row["puissance_kva"],
                    abo_month_ttc=row["abo_month_ttc"],
                    price_kwh_ttc=row.get("price_kwh_ttc"),
                    price_kwh_hp_ttc=row.get("price_kwh_hp_ttc"),
                    price_kwh_hc_ttc=row.get("price_kwh_hc_ttc"),
                    observed_at=now,
                    parser_version=f"{row['supplier'].lower()}_seed",
                    source_url=f"https://{row['supplier'].lower()}.example/tarifs",
                    source_checksum="seed".ljust(64, "0"),
                )
            )
        await session.commit()
    print("Seeded suppliers and tariffs into", settings.database_url)


if __name__ == "__main__":
    asyncio.run(seed())
