# OpenWatt ⚡

Open Data electricity tariffs comparator for France — transparent, reproducible, historical.

## Contents
- specs/: project specifications (Spec-Kit)
- db/: PostgreSQL DDL (insert-only)
- .github/: workflows and automation
- api/, ingest/, parsers/: code to come
- tests/: unit and snapshot tests

## Backend development
1. Ensure Python 3.11+ is installed (per Spec-Kit charter).
2. Create a virtual environment and install dependencies:
    python -m venv .venv
    .\\.venv\\Scripts\\activate
    pip install --upgrade pip
    pip install -r requirements.txt
3. Run the FastAPI app, which currently serves `/health` and `/v1/*` routes:
    uvicorn api.app.main:app --reload

### Database setup
1. Start PostgreSQL (or point to a managed instance) and run `psql -f db/ddl.sql` to apply the canonical schema (insert-only tables + views/triggers).
2. Export `OPENWATT_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/openwatt`.
3. Enable the persistence layer by setting `OPENWATT_ENABLE_DB=1` when launching `uvicorn`.
4. Alembic is included for future migrations (`alembic init migrations` once the schema evolves).

## API endpoints (alpha)
- GET /health — liveness probe for CI/CD monitors.
- GET /v1/tariffs — latest observations filtered by option, puissance, include_stale (`data_status = fresh|verifying|stale|broken`).
- GET /v1/tariffs/history — insert-only log with supplier/option/puissance/since/until filters.
- GET /v1/guards/trve-diff — compares last observations against TRVE reference to flag ok/alert.

## Tests
1. Snapshot fixtures live in `tests/snapshots/` (e.g. `edf/edf_2025_02.*`) and mirror scenarios from `specs/tests.md`.
2. Run the suite locally:
    pytest
3. CI should block on failing snapshots or API regressions per Spec-Kit charter.

## License

Licensed under the MIT License — see LICENSE for details.
