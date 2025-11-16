from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.app.db.base import Base  # noqa: E402
from api.app.db import models  # noqa: F401,E402  # ensures metadata is populated


async def _bootstrap(database_url: str, *, drop: bool) -> None:
    engine = create_async_engine(database_url, future=True)
    async with engine.begin() as conn:
        if drop:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create the OpenWatt schema on the configured database "
            "(works with Postgres or SQLite)."
        )
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("OPENWATT_DATABASE_URL"),
        help="SQLAlchemy database URL. Defaults to env OPENWATT_DATABASE_URL.",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop the existing schema before recreating it (useful for local resets).",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("Set --database-url or OPENWATT_DATABASE_URL before running bootstrap_db")

    asyncio.run(_bootstrap(args.database_url, drop=args.drop))
    print(f"Schema bootstrapped on {args.database_url}")


if __name__ == "__main__":
    main()
