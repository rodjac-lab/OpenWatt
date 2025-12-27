# OpenWatt

[![CI Status](https://github.com/rodjac-lab/OpenWatt/actions/workflows/ci.yml/badge.svg)](https://github.com/rodjac-lab/OpenWatt/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/rodjac-lab/OpenWatt/branch/main/graph/badge.svg)](https://codecov.io/gh/rodjac-lab/OpenWatt)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Production Ready](https://img.shields.io/badge/status-production--ready-green.svg)](docs/audit.md)

Open Data electricity tariffs comparator for France — transparent, reproducible, historical.

**✅ Production-ready** (Nov 2025) - Docker + CI/CD + Tests + Monitoring

---

## 🎉 What's New (Sprint 1 & 2 - Nov 2025)

### Sprint 1 - Production Readiness ✅

- **Docker**: Multi-stage Dockerfiles (API + UI) + docker-compose.prod.yaml
- **CI/CD**: Complete GitHub Actions workflow (linting, tests, builds)
- **Linting**: black, flake8, mypy (Python) + ESLint, Prettier (TypeScript)
- **Pre-commit hooks**: Automated code quality checks
- **Coverage**: 70% enforced (backend), 99% (frontend)

### Sprint 2 - Monitoring & Robustness ✅

- **Logging**: Structured JSON logs (structlog) for production
- **Monitoring**: Sentry error tracking + Prometheus metrics (code ready)
- **Tracing**: Request-ID middleware for distributed tracing
- **Robustness**: Retry logic (tenacity) + Rate limiting (token bucket)
- **Frontend Tests**: Vitest + React Testing Library (15 tests, 99% coverage)
- **Documentation**: Complete guides for testing, monitoring, logging

### Sprint 3 - Code Quality (In Progress) ⏳

- **AdminConsole Refactoring**: 462 → 269 lines (-42%), 6 modular components ✅
- **Type Safety**: Centralized TypeScript interfaces (types.ts) ✅
- **Maintainability**: Component size < 100 lines, clean architecture ✅

**See**: [Sprint 1](docs/sprint-1-summary.md), [Sprint 2](docs/sprint-2-summary.md), [AdminConsole Refactoring](docs/adminConsole-refactoring-complete.md), [Audit](docs/audit.md)

---

## 🚀 Quick Start (Production Mode)

**New!** Run the entire stack with Docker:

```bash
# 1. Clone and configure
git clone https://github.com/rodjac-lab/OpenWatt.git
cd OpenWatt
cp .env.example .env  # Edit if needed

# 2. Start all services (PostgreSQL + API + UI)
docker compose -f docker-compose.prod.yaml up -d

# 3. Apply database schema
docker compose -f docker-compose.prod.yaml exec api python scripts/apply_ddl.py

# 4. Access services
# - UI: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Metrics: http://localhost:8000/metrics
```

**See**: [Deployment Guide](docs/deployment.md) (coming soon)

---

## Contents

- specs/: project specifications (Spec-Kit)
- db/: PostgreSQL DDL (insert-only)
- .github/: workflows and automation
- api/, ingest/, parsers/: backend + ingest code
- tests/: unit and snapshot tests (backend + frontend)
- ui/: Next.js client with Vitest tests
- docs/: comprehensive documentation (Sprint 1 & 2 guides)

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
6. Alembic is ready for future migrations (`alembic init migrations`).

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

### Backend Tests (pytest)

1. Snapshot fixtures live in `tests/snapshots/` (EDF, Engie, TotalEnergies).
2. Run the suite locally:
   ```bash
   pytest                           # Run all tests
   pytest --cov                     # With coverage report
   pytest --cov --cov-report=html   # Generate HTML coverage report
   ```
3. **Coverage enforced**: 70% minimum (CI fails if < 70%)

### Frontend Tests (Vitest) - **NEW!**

1. Test files: `ui/components/__tests__/*.test.tsx`
2. Run the suite:
   ```bash
   cd ui
   npm test                 # Run tests once
   npm run test:watch       # Watch mode
   npm run test:ui          # Browser UI
   npm run test:coverage    # With coverage report
   ```
3. **Coverage**: 99.43% (FreshnessBadge: 100%, TariffList: 99.36%)
4. **CI validation**: Automatic on every PR/push

**See**: [Frontend Testing Guide](docs/frontend-testing.md)

### CI/CD

- GitHub Actions runs **all tests** (backend + frontend) on every PR/push
- Linting (black, flake8, mypy, ESLint, Prettier)
- Docker builds validation
- Coverage upload to Codecov
- **Blocks merge if any check fails** ✅

---

## 📚 Documentation

### Getting Started

- [README](README.md) - This file (Quick start, development setup)
- [Audit Report](docs/audit.md) - Complete project audit (updated post-Sprint 1 & 2)

### Sprint Documentation

- [Sprint 1 Summary](docs/sprint-1-summary.md) - Production readiness (Docker, CI/CD, linting)
- [Sprint 2 Summary](docs/sprint-2-summary.md) - Monitoring & robustness (logs, Sentry, tests)
- [Sprint 2 Frontend Tests](docs/sprint-2-frontend-tests-complete.md) - Detailed frontend testing report
- [AdminConsole Refactoring Complete](docs/adminConsole-refactoring-complete.md) - Sprint 3 refactoring report ✨ NEW

### Development Guides

- [Frontend Testing Guide](docs/frontend-testing.md) - Vitest + React Testing Library (complete guide)
- [Logging Guide](docs/logging.md) - Structured logging with structlog
- [Monitoring Setup Guide](docs/monitoring-setup-guide.md) - Sentry + Prometheus + Grafana deployment
- [AdminConsole Refactor Guide (OLD)](docs/refactoring-admin-console.md) - Original guide (superseded by complete report)

### Specifications

- [specs/constitution.md](specs/constitution.md) - Spec-Kit principles and charter
- [specs/api.md](specs/api.md) - OpenAPI specification
- [specs/openapi.generated.json](specs/openapi.generated.json) - Generated OpenAPI schema

### Architecture

- **Stack**: FastAPI (Python 3.11+) + Next.js 14 + PostgreSQL 16
- **Pattern**: Insert-only history (immutable database)
- **Testing**: pytest (backend 70%+) + Vitest (frontend 99%+)
- **Monitoring**: structlog + Sentry + Prometheus
- **Deployment**: Docker multi-stage + docker-compose

---

## 📊 Project Status

**Current Version**: Production-ready beta (Nov 2025)
**Note**: 8.5/10 (see [audit report](docs/audit.md))

### Completed ✅

- Sprint 1: Production readiness (100%)
- Sprint 2: Monitoring & robustness (87.5%)

### Roadmap (Sprint 3-4)

1. AdminConsole refactoring
2. Alembic migrations active
3. PostgreSQL backup automation
4. End-to-end tests (Playwright)
5. Secrets management (dotenv-vault)
6. State management UI (TanStack Query)

**See**: [Audit Report - Plan d'Action](docs/audit.md#plan-daction---statut-actuel)

---

## License

Licensed under the MIT License — see `LICENSE` for details.
