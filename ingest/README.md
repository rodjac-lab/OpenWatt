# Ingest pipeline

Commands
========

Fetch + parse snapshot (local PDF/HTML)
---------------------------------------
python -m ingest.pipeline edf --html tests/snapshots/edf/edf_tarif_bleu.pdf --observed-at 2025-02-12T08:00:00Z

Fetch from live source
----------------------
python -m ingest.pipeline edf --fetch --observed-at 2025-02-12T08:00:00Z

Persist into Postgres
----------------------
OPENWATT_DATABASE_URL=postgresql+asyncpg://openwatt:openwatt@localhost:5432/openwatt OPENWATT_ENABLE_DB=1 python -m ingest.pipeline edf --fetch --persist

Artifacts
=========
Raw files -> artifacts/raw/
Parsed outputs -> artifacts/parsed/

