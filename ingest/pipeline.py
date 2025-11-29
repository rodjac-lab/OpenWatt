from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ingest.fetch import fetch_supplier_artifact
from ingest.persist import TariffPersister
from parsers.core import parser as yaml_parser
from parsers.core.config import SupplierConfig, load_supplier_config
from api.app.core.logging import configure_logging, get_logger
from api.app.core.sentry import configure_sentry
from api.app.db.models import IngestRun
from api.app.db.session import get_session_factory

logger = get_logger(__name__)

DEFAULT_PARSED_DIR = Path("artifacts/parsed")


class IngestRunLogger:
    """Log ingest runs to database."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None):
        self.session_factory = session_factory or get_session_factory()

    async def start_run(
        self, supplier: str, source_url: str | None = None
    ) -> int:
        """Create a new ingest run record with status 'running'."""
        async with self.session_factory() as session:
            run = IngestRun(
                supplier=supplier,
                status="running",
                source_url=source_url,
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            return run.id

    async def complete_run(
        self,
        run_id: int,
        status: str,
        rows_inserted: int = 0,
        error_message: str | None = None,
        source_checksum: str | None = None,
    ) -> None:
        """Update run record with completion status."""
        async with self.session_factory() as session:
            run = await session.get(IngestRun, run_id)
            if run:
                run.finished_at = datetime.now(timezone.utc)
                run.status = status
                run.rows_inserted = rows_inserted
                run.error_message = error_message
                if source_checksum:
                    run.source_checksum = source_checksum
                await session.commit()


def compute_checksum(path: Path) -> str:
    data = path.read_bytes()
    return sha256(data).hexdigest()


def run_ingest(
    config: SupplierConfig,
    artifact_path: Path,
    *,
    observed_at: datetime,
    source_checksum: str,
) -> list[dict[str, Any]]:
    """Parse a supplier artifact into tariff payloads."""
    return yaml_parser.parse_file(
        config,
        artifact_path,
        observed_at=observed_at,
        source_checksum=source_checksum,
    )


if __name__ == "__main__":
    import argparse
    import asyncio
    import json
    import sys

    from api.app.core.config import settings

    parser = argparse.ArgumentParser(description="Run Spec-Kit ingest pipeline")
    parser.add_argument("supplier", help="Supplier code, e.g. edf")
    parser.add_argument("--html", help="Path to the HTML/PDF artifact to parse")
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Download the source defined in parsers/config/<supplier>.yaml before parsing",
    )
    parser.add_argument(
        "--persist", action="store_true", help="Persist parsed rows into the database"
    )
    parser.add_argument("--observed-at", help="ISO timestamp override (default: now UTC)")
    parser.add_argument(
        "--output",
        help=(
            "Where to write the parsed JSON "
            "(default: artifacts/parsed/<supplier>_<timestamp>.json)"
        ),
    )
    parser.add_argument(
        "--raw-dir",
        help="Directory to store fetched raw artifacts (default: artifacts/raw)",
    )
    args = parser.parse_args()

    configure_logging()
    configure_sentry()

    observed = (
        datetime.fromisoformat(args.observed_at) if args.observed_at else datetime.now(timezone.utc)
    )
    config = load_supplier_config(args.supplier)

    async def run_pipeline_with_logging() -> None:
        """Run pipeline with ingest_runs logging."""
        run_id: int | None = None
        run_logger: IngestRunLogger | None = None
        checksum: str | None = None

        if args.persist and settings.enable_db:
            run_logger = IngestRunLogger()
            run_id = await run_logger.start_run(
                supplier=config.supplier,
                source_url=str(config.source.url) if args.fetch else None,
            )
            logger.info("ingest_run_started", run_id=run_id)

        try:
            if args.fetch:
                raw_path, checksum = fetch_supplier_artifact(
                    config, raw_dir=Path(args.raw_dir) if args.raw_dir else None
                )
                artifact_path = raw_path
                logger.info(
                    "artifact_fetched",
                    url=str(config.source.url),
                    path=str(raw_path),
                    checksum=checksum,
                )
            else:
                if not args.html:
                    parser.error("Provide --html path or use --fetch to download the latest artifact")
                artifact_path = Path(args.html)
                if not artifact_path.exists():
                    if run_id and run_logger:
                        await run_logger.complete_run(
                            run_id,
                            status="failed",
                            error_message=f"Artifact not found: {artifact_path}",
                        )
                    parser.error(f"Artifact not found: {artifact_path}")
                checksum = compute_checksum(artifact_path)

            rows = run_ingest(
                config,
                artifact_path,
                observed_at=observed,
                source_checksum=checksum,
            )

            if args.output:
                output_path = Path(args.output)
            else:
                DEFAULT_PARSED_DIR.mkdir(parents=True, exist_ok=True)
                safe_supplier = args.supplier.lower()
                output_path = (
                    DEFAULT_PARSED_DIR / f"{safe_supplier}_{observed.strftime('%Y%m%dT%H%M%SZ')}.json"
                )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            logger.info("payload_written", path=str(output_path), row_count=len(rows))

            if args.persist:
                if not settings.enable_db:
                    parser.error(
                        "Set OPENWATT_ENABLE_DB=1 and OPENWATT_DATABASE_URL to enable persistence"
                    )
                count = await TariffPersister().persist(config, rows)
                logger.info("rows_persisted", count=count)

                if run_id and run_logger:
                    await run_logger.complete_run(
                        run_id,
                        status="success",
                        rows_inserted=count,
                        source_checksum=checksum,
                    )
                    logger.info("ingest_run_completed", run_id=run_id, status="success")
            elif run_id and run_logger:
                await run_logger.complete_run(
                    run_id,
                    status="success",
                    rows_inserted=0,
                    source_checksum=checksum,
                )

        except Exception as e:
            logger.exception("pipeline_failed", error=str(e))
            if run_id and run_logger:
                await run_logger.complete_run(
                    run_id,
                    status="failed",
                    error_message=str(e),
                    source_checksum=checksum,
                )
                logger.info("ingest_run_completed", run_id=run_id, status="failed")
            sys.exit(1)

    logger.info("pipeline_started", supplier=args.supplier, observed_at=observed)

    try:
        asyncio.run(run_pipeline_with_logging())
    except Exception as e:
        logger.exception("pipeline_execution_failed", error=str(e))
        sys.exit(1)
