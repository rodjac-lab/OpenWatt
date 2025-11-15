# OpenWatt

Open Data electricity tariffs comparator for France — transparent, reproducible, historical.

## Contents
- specs/: project specifications (Spec-Kit)
- db/: PostgreSQL DDL (insert-only)
- .github/: workflows and automation
- api/, ingest/, parsers/: backend + ingest code
- tests/: unit and snapshot tests
- ui/: Next.js client (alpha scaffold)

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
1. Copy `.env.example` to `.env` and adjust credentials if needed.
2. Start PostgreSQL locally: `docker compose up -d db` (or point to an existing instance).
3. Apply the canonical schema:
   - Postgres: `python scripts/apply_ddl.py` (wraps `psql -f db/ddl.sql`).
   - Any SQLAlchemy-compatible URL (incl. SQLite for local dev): `python scripts/bootstrap_db.py --database-url sqlite+aiosqlite:///artifacts/dev.sqlite`.
4. Import the TRVE reference grid (official CRE annex B PDF parsed under `tests/snapshots/trve/`):
   `OPENWATT_DATABASE_URL=<db-url> python scripts/import_trve.py tests/snapshots/trve/trve_cre_2025_07_expected.json --valid-from 2025-08-01 --truncate`
5. Export `OPENWATT_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/openwatt` (or the SQLite URL above) and set `OPENWATT_ENABLE_DB=1` before launching uvicorn.
5. Alembic is ready for future migrations (`alembic init migrations`).

## Ingestion & parsers
- Supplier scrapers are declared in `parsers/config/<supplier>.yaml` (selectors ou tables PDF, parser version).
- Run the parser against an existing artifact (HTML ou PDF) :
    python -m ingest.pipeline edf --html tests/snapshots/edf/edf_tarif_bleu.pdf --observed-at 2025-02-12T08:00:00Z
- Or download the latest source defined in YAML et persister en base :
    python -m ingest.pipeline total_heures_eco --fetch --persist
  The raw file lands in `artifacts/raw/` and the parsed JSON in `artifacts/parsed/`.
- Automate all suppliers sequentially (ideal for cron) :
    python scripts/run_ingest_all.py --observed-at 2025-02-15T00:00:00+00:00
- Snapshot outputs live in `tests/snapshots/<supplier>/` et sont valides par `pytest`.
- Current coverage: EDF (`edf_pdf_v1`), Engie (`engie_pdf_v1`), TotalEnergies (`total_heures_eco_v1`, `total_standard_fixe_v1`) et Mint Energie (`mint_indexe_trv_v1`, `mint_classic_green_v1`, `mint_smart_green_v1`). Ajoutez un fournisseur en clonant ce pattern YAML + snapshot.

## UI hand-off
- Generate an OpenAPI payload for frontend tooling:
    python scripts/export_openapi.py --out specs/openapi.generated.json
- Reuse the status badge guidance + starter types in `docs/ui/`.
- Spin up the Next.js skeleton in `ui/`:
    cd ui && npm install && npm run dev
- Set `NEXT_PUBLIC_API_BASE` to point at your FastAPI instance before fetching data.

## API endpoints (alpha)
- GET /health - liveness probe for CI/CD monitors.
- GET /v1/tariffs - latest observations filtered by option, puissance, include_stale (`data_status = fresh|verifying|stale|broken`).
- GET /v1/tariffs/history - insert-only log with supplier/option/puissance/since/until filters.
- GET /v1/guards/trve-diff - compares last observations against TRVE reference to flag ok/alert.
- GET /v1/admin/runs - expose l'état des jobs ingestion (console opérateur).
- GET/POST /v1/admin/overrides - journalise/déclenche un override manuel (`--fetch` temporaire).
- POST /v1/admin/inspect - upload d'un PDF pour visualiser les lignes extraites via YAML.

## Tests
1. Snapshot fixtures live in `tests/snapshots/` (EDF, Engie, TotalEnergies).
2. Run the suite locally:
    pytest
3. CI should block on failing snapshots or API regressions per Spec-Kit charter.

## License

Licensed under the MIT License — see `LICENSE` for details.
