from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.app.db.models import IngestRun
from api.app.db.session import get_session_factory
from api.app.core.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    """Service for checking ingest health status."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None):
        self.session_factory = session_factory or get_session_factory()

    async def get_ingest_health(self) -> dict[str, Any]:
        """Get health status for all suppliers."""
        async with self.session_factory() as session:
            suppliers = await self._get_all_suppliers(session)
            supplier_stats = []

            for supplier in suppliers:
                stats = await self._get_supplier_stats(session, supplier)
                supplier_stats.append(stats)

            return {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "suppliers": supplier_stats,
            }

    async def _get_all_suppliers(self, session: AsyncSession) -> list[str]:
        """Get list of unique suppliers from ingest_runs."""
        result = await session.execute(
            select(IngestRun.supplier).distinct().order_by(IngestRun.supplier)
        )
        return [row[0] for row in result.all()]

    async def _get_supplier_stats(self, session: AsyncSession, supplier: str) -> dict[str, Any]:
        """Get stats for a specific supplier."""
        # Get last run
        last_run_result = await session.execute(
            select(IngestRun)
            .where(IngestRun.supplier == supplier)
            .order_by(IngestRun.started_at.desc())
            .limit(1)
        )
        last_run = last_run_result.scalar_one_or_none()

        if not last_run:
            return {
                "supplier": supplier,
                "last_run_at": None,
                "last_run_status": None,
                "last_success_at": None,
                "rows_last_inserted": 0,
                "data_status": "unknown",
                "consecutive_failures": 0,
            }

        # Get last successful run
        last_success_result = await session.execute(
            select(IngestRun)
            .where(and_(IngestRun.supplier == supplier, IngestRun.status == "success"))
            .order_by(IngestRun.started_at.desc())
            .limit(1)
        )
        last_success = last_success_result.scalar_one_or_none()

        # Count consecutive failures
        consecutive_failures = await self._count_consecutive_failures(session, supplier)

        # Determine data_status
        data_status = self._determine_data_status(last_run, last_success, consecutive_failures)

        return {
            "supplier": supplier,
            "last_run_at": last_run.started_at.isoformat() if last_run else None,
            "last_run_status": last_run.status if last_run else None,
            "last_success_at": last_success.started_at.isoformat() if last_success else None,
            "rows_last_inserted": last_run.rows_inserted if last_run else 0,
            "data_status": data_status,
            "consecutive_failures": consecutive_failures,
            "error_message": (
                last_run.error_message if last_run and last_run.status == "failed" else None
            ),
        }

    async def _count_consecutive_failures(self, session: AsyncSession, supplier: str) -> int:
        """Count consecutive failures from the most recent run."""
        result = await session.execute(
            select(IngestRun.status)
            .where(IngestRun.supplier == supplier)
            .order_by(IngestRun.started_at.desc())
            .limit(20)
        )
        runs = [row[0] for row in result.all()]

        count = 0
        for status in runs:
            if status in ("failed", "source_unavailable"):
                count += 1
            else:
                break

        return count

    def _determine_data_status(
        self,
        last_run: IngestRun | None,
        last_success: IngestRun | None,
        consecutive_failures: int,
    ) -> str:
        """Determine data status based on run history."""
        if not last_run:
            return "unknown"

        now = datetime.now(timezone.utc)

        # broken: dernier run failed ou source_unavailable
        if last_run.status in ("failed", "source_unavailable"):
            return "broken"

        # stale: dernier success > 14 jours
        if last_success:
            # Ensure timezone-aware comparison
            success_time = last_success.started_at
            if success_time.tzinfo is None:
                success_time = success_time.replace(tzinfo=timezone.utc)

            days_since_success = (now - success_time).days
            if days_since_success > 14:
                return "stale"

            # verifying: dernier run < 48h mais en attente de validation
            if days_since_success <= 2:
                return "verifying"

            # fresh: dernier run success il y a < 7 jours
            if days_since_success <= 7:
                return "fresh"

        # Default to verifying if we can't determine
        return "verifying"
