from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import delete

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.app.db import models  # noqa: E402
from api.app.db.session import get_session_factory  # noqa: E402
from api.app.models.enums import TariffOption  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import TRVE reference data into the database")
    parser.add_argument("json", help="Path to the JSON file containing TRVE rows")
    parser.add_argument(
        "--valid-from", dest="valid_from", required=True, help="ISO date YYYY-MM-DD"
    )
    parser.add_argument("--valid-to", dest="valid_to", help="Optional ISO date YYYY-MM-DD")
    parser.add_argument(
        "--truncate", action="store_true", help="Delete existing TRVE rows before import"
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    valid_from = date.fromisoformat(args.valid_from)
    valid_to = date.fromisoformat(args.valid_to) if args.valid_to else None

    session_factory = get_session_factory()
    async with session_factory() as session:
        if args.truncate:
            await session.execute(delete(models.TrveReference))
        for row in data:
            option = TariffOption(row["option"])
            reference = models.TrveReference(
                option=option,
                puissance_kva=row["puissance_kva"],
                price_kwh_ttc=row.get("price_kwh_ttc"),
                price_kwh_hp_ttc=row.get("price_kwh_hp_ttc"),
                price_kwh_hc_ttc=row.get("price_kwh_hc_ttc"),
                abo_month_ttc=row["abo_month_ttc"],
                valid_from=valid_from,
                valid_to=valid_to,
            )
            session.add(reference)
        await session.commit()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
