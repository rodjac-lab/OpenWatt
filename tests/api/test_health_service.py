from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.app.db.base import Base
from api.app.db.models import IngestRun
from api.app.services.health_service import HealthService


@pytest.fixture
def session_factory():
    """Create an in-memory SQLite session factory for testing."""
    import asyncio

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_setup())

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory

    asyncio.run(engine.dispose())


def find_supplier(suppliers: list[dict], name: str) -> dict | None:
    """Helper to find a supplier by name in health check results."""
    for supplier in suppliers:
        # Match both exact name and lowercase stem (e.g., "EDF" matches "edf")
        if supplier["supplier"].lower() == name.lower():
            return supplier
    return None


class TestHealthService:
    """Test suite for HealthService class."""

    @pytest.mark.asyncio
    async def test_get_ingest_health_no_runs(self, session_factory):
        """Test health check when there are no runs in the database.

        Now returns all configured suppliers from parsers/config/*.yaml
        even if they've never been run.
        """
        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        assert "generated_at" in result
        # Should return all configured suppliers, not empty list
        assert isinstance(result["suppliers"], list)
        assert len(result["suppliers"]) > 0  # We have config files
        # All suppliers should have "unknown" status since no runs exist
        for supplier_stat in result["suppliers"]:
            assert supplier_stat["data_status"] == "unknown"
            assert supplier_stat["last_run_at"] is None

    @pytest.mark.asyncio
    async def test_get_ingest_health_unknown_status_no_runs(self, session_factory):
        """Test supplier with no run history returns unknown status."""
        # This test verifies that all configured suppliers are returned
        # even if they've never been run
        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        # All suppliers should have unknown status when no runs exist
        assert len(result["suppliers"]) > 0
        for supplier_stat in result["suppliers"]:
            assert supplier_stat["data_status"] == "unknown"
            assert supplier_stat["last_run_at"] is None

    @pytest.mark.asyncio
    async def test_get_ingest_health_fresh_status(self, session_factory):
        """Test data_status=fresh when last success is < 7 days."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            run = IngestRun(
                supplier="edf",  # Use lowercase to match config file stem
                started_at=now - timedelta(days=5),  # Changed to 5 days to avoid verifying status
                finished_at=now - timedelta(days=5),
                status="success",
                rows_inserted=12,
                source_url="https://edf.example.com/tarifs.pdf",
                source_checksum="a" * 64,
            )
            session.add(run)
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        # Now returns all configured suppliers, find the one we care about
        supplier_health = find_supplier(result["suppliers"], "edf")
        assert supplier_health is not None
        assert supplier_health["data_status"] == "fresh"
        assert supplier_health["last_run_status"] == "success"
        assert supplier_health["rows_last_inserted"] == 12
        assert supplier_health["consecutive_failures"] == 0
        assert supplier_health["error_message"] is None

    @pytest.mark.asyncio
    async def test_get_ingest_health_stale_status(self, session_factory):
        """Test data_status=stale when last success is > 14 days."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            run = IngestRun(
                supplier="engie",
                started_at=now - timedelta(days=20),
                finished_at=now - timedelta(days=20),
                status="success",
                rows_inserted=15,
                source_url="https://engie.example.com/tarifs.pdf",
                source_checksum="b" * 64,
            )
            session.add(run)
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        supplier_health = find_supplier(result["suppliers"], "Engie")
        assert supplier_health is not None
        assert supplier_health["data_status"] == "stale"
        assert supplier_health["last_run_status"] == "success"

    @pytest.mark.asyncio
    async def test_get_ingest_health_broken_status_failed(self, session_factory):
        """Test data_status=broken when last run failed."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            run = IngestRun(
                supplier="total_standard_fixe",
                started_at=now - timedelta(hours=2),
                finished_at=now - timedelta(hours=2),
                status="failed",
                rows_inserted=0,
                error_message="PDF structure changed - table index out of range",
                source_url="https://total.example.com/tarifs.pdf",
                source_checksum="c" * 64,
            )
            session.add(run)
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        supplier_health = find_supplier(result["suppliers"], "total_standard_fixe")
        assert supplier_health is not None
        assert supplier_health["data_status"] == "broken"
        assert supplier_health["last_run_status"] == "failed"
        assert supplier_health["consecutive_failures"] == 1
        assert "PDF structure changed" in supplier_health["error_message"]

    @pytest.mark.asyncio
    async def test_get_ingest_health_broken_status_source_unavailable(self, session_factory):
        """Test data_status=broken when source is unavailable."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            run = IngestRun(
                supplier="mint_indexe_trv",
                started_at=now - timedelta(hours=1),
                finished_at=now - timedelta(hours=1),
                status="source_unavailable",
                rows_inserted=0,
                error_message="URL returned 404",
                source_url="https://mint.example.com/tarifs.pdf",
            )
            session.add(run)
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        supplier_health = find_supplier(result["suppliers"], "mint_indexe_trv")
        assert supplier_health is not None
        assert supplier_health["data_status"] == "broken"
        assert supplier_health["last_run_status"] == "source_unavailable"

    @pytest.mark.asyncio
    async def test_get_ingest_health_verifying_status(self, session_factory):
        """Test data_status=verifying when last run < 48h."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            run = IngestRun(
                supplier="edf",
                started_at=now - timedelta(hours=12),
                finished_at=now - timedelta(hours=12),
                status="success",
                rows_inserted=10,
                source_url="https://edf.example.com/tarifs.pdf",
                source_checksum="d" * 64,
            )
            session.add(run)
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        supplier_health = find_supplier(result["suppliers"], "EDF")
        assert supplier_health is not None
        assert supplier_health["data_status"] == "verifying"

    @pytest.mark.asyncio
    async def test_consecutive_failures_count(self, session_factory):
        """Test correct counting of consecutive failures."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            # Add successful run first (oldest)
            success = IngestRun(
                supplier="engie",
                started_at=now - timedelta(days=5),
                finished_at=now - timedelta(days=5),
                status="success",
                rows_inserted=10,
            )
            session.add(success)

            # Add 3 consecutive failures
            for i in range(3):
                failure = IngestRun(
                    supplier="engie",
                    started_at=now - timedelta(days=4 - i),
                    finished_at=now - timedelta(days=4 - i),
                    status="failed",
                    rows_inserted=0,
                    error_message=f"Error {i}",
                )
                session.add(failure)

            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        supplier_health = find_supplier(result["suppliers"], "engie")
        assert supplier_health is not None
        assert supplier_health["consecutive_failures"] == 3
        assert supplier_health["data_status"] == "broken"

    @pytest.mark.asyncio
    async def test_consecutive_failures_mixed_statuses(self, session_factory):
        """Test consecutive failures with mixed failure types."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            # Add runs in reverse chronological order
            runs = [
                IngestRun(
                    supplier="total_standard_fixe",
                    started_at=now - timedelta(hours=i),
                    finished_at=now - timedelta(hours=i),
                    status=status,
                    rows_inserted=0,
                )
                for i, status in enumerate(
                    [
                        "failed",
                        "source_unavailable",
                        "failed",
                        "success",  # This breaks the consecutive failures
                    ]
                )
            ]
            session.add_all(runs)
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        supplier_health = find_supplier(result["suppliers"], "total_standard_fixe")
        assert supplier_health is not None
        assert supplier_health["consecutive_failures"] == 3
        # Most recent 3 runs are failures, so consecutive count should be 3

    @pytest.mark.asyncio
    async def test_multiple_suppliers(self, session_factory):
        """Test health check with multiple suppliers."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            edf_run = IngestRun(
                supplier="edf",
                started_at=now - timedelta(days=5),
                finished_at=now - timedelta(days=5),
                status="success",
                rows_inserted=12,
            )
            engie_run = IngestRun(
                supplier="engie",
                started_at=now - timedelta(hours=1),
                finished_at=now - timedelta(hours=1),
                status="failed",
                rows_inserted=0,
                error_message="Parser error",
            )
            total_run = IngestRun(
                supplier="total_standard_fixe",
                started_at=now - timedelta(days=20),
                finished_at=now - timedelta(days=20),
                status="success",
                rows_inserted=8,
            )
            session.add_all([edf_run, engie_run, total_run])
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        # All suppliers returned, check the 3 we created
        suppliers_map = {s["supplier"]: s for s in result["suppliers"]}

        assert suppliers_map["edf"]["data_status"] == "fresh"
        assert suppliers_map["engie"]["data_status"] == "broken"
        assert suppliers_map["total_standard_fixe"]["data_status"] == "stale"

    @pytest.mark.asyncio
    async def test_last_success_at_different_from_last_run(self, session_factory):
        """Test that last_success_at is tracked separately from last_run_at."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            success_run = IngestRun(
                supplier="edf",
                started_at=now - timedelta(days=5),
                finished_at=now - timedelta(days=5),
                status="success",
                rows_inserted=10,
            )
            failed_run = IngestRun(
                supplier="edf",
                started_at=now - timedelta(hours=1),
                finished_at=now - timedelta(hours=1),
                status="failed",
                rows_inserted=0,
            )
            session.add_all([success_run, failed_run])
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        supplier_health = find_supplier(result["suppliers"], "edf")  # Adjust supplier name as needed
        assert supplier_health is not None
        assert supplier_health["last_run_status"] == "failed"
        assert supplier_health["last_success_at"] is not None
        # last_success_at should be ~5 days ago, last_run_at should be ~1 hour ago
        last_run = datetime.fromisoformat(supplier_health["last_run_at"])
        last_success = datetime.fromisoformat(supplier_health["last_success_at"])
        # Ensure timezone-aware comparison
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)
        if last_success.tzinfo is None:
            last_success = last_success.replace(tzinfo=timezone.utc)
        assert (now - last_run).total_seconds() < 3600 * 2  # Less than 2 hours
        assert (now - last_success).total_seconds() > 3600 * 24 * 4  # More than 4 days

    @pytest.mark.asyncio
    async def test_running_status_not_counted_as_failure(self, session_factory):
        """Test that 'running' status doesn't count as a failure."""
        now = datetime.now(timezone.utc)

        async with session_factory() as session:
            running_run = IngestRun(
                supplier="edf",
                started_at=now - timedelta(minutes=5),
                status="running",
                rows_inserted=0,
            )
            session.add(running_run)
            await session.commit()

        service = HealthService(session_factory=session_factory)
        result = await service.get_ingest_health()

        supplier_health = find_supplier(result["suppliers"], "edf")  # Adjust supplier name as needed
        assert supplier_health is not None
        assert supplier_health["consecutive_failures"] == 0
        # Running status is not considered broken, but it's also not fresh/stale
        # so it should default to verifying
        assert supplier_health["data_status"] == "verifying"
