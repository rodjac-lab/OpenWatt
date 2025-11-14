---
id: elec-tariffs-fr.plan
version: 0.1.0
status: draft
last_updated: 2025-11-11
---

# 🗓️ Roadmap (MVP)
| Phase | Durée | Objectif | Livrables |
|------|-------|----------|-----------|
| M1 | Sem. 1-2 | Extraction 5 fournisseurs (EDF, Engie, TotalEnergies, Ekwateur, Mint) | DB Postgres (insert-only), parsers v1, ingest nightly |
| M2 | Sem. 3 | API /v1 + règles fresh/stale | Endpoints FastAPI, tests snapshot |
| M3 | Sem. 4 | UI comparateur | Page Next.js + doc publique |
| M4 | Plus tard | Robustesse & transparence | Historique visuel, changelog, double parseur, partenariats data |

# 🎯 KPI
- ≥ 5 fournisseurs actifs
- Données ≤ 7 j pour ≥ 80 % des combinaisons
- 0 UPDATE / 0 DELETE en DB (historisation immuable)

# 📌 Hypothèses
- Sources publiques HTML/PDF
- Aucune dépendance LLM/OCR au MVP
## Backlog / To-do
- Ajouter un outil CLI d'inspection des PDF (afficher colonnes/lignes extraites selon `parsers/config/*.yaml`) pour valider visuellement les tables avant régénération des snapshots.
- Importer les grilles TRVE dans `trve_reference` et brancher `/v1/guards/trve-diff` sur ces données (au lieu du stub actuel).

