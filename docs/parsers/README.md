# Parser runbooks

Each supplier must ship a YAML file under `parsers/config/` plus a short runbook in this directory. The YAML keeps the scraping logic declarative (selectors, URLs, validation rules) while the runbook explains edge cases, history of breakages, and manual recovery steps.

Current coverage:

| Supplier | Parser version | Notes |
|----------|----------------|-------|
| EDF | `edf_v1` | Snapshot parser built from anonymised HTML (see `tests/snapshots/edf`). |
| Engie | `engie_v1` | Same YAML-driven parser with HPHC attributes (`tests/snapshots/engie`). |
| TotalEnergies | `totale_v1` | Tempo/Base placeholder from `tests/snapshots/total`. |

Add one Markdown file per supplier (e.g. `docs/parsers/edf.md`) describing:
- URLs to monitor and expected update cadence.
- Selectors or heuristics encoded in YAML.
- Known anomalies (`structure_changed`, `prix_anomal`, etc.).
- Recovery checklist (target: fix in < 2 hours without deep debugging).
