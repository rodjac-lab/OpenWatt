# Elec Tariffs FR — Spec-Kit Skeleton

Ce dépôt contient le **squelette Spec-Kit** pour le projet de comparaison des tarifs électricité FR.

## Contenu
- `specs/constitution.md` — Vision & principes
- `specs/plan.md` — Roadmap MVP
- `specs/system.md` — Architecture & flux
- `specs/api.md` — Contrat d'API (extrait OpenAPI)
- `specs/data-contracts/*.json` — Schémas JSON
- `specs/tests.md` — Scénarios d'acceptance
- `specs/governance.md` — Règles d'évolution
- `db/ddl.sql` — DDL Postgres (historisation insert-only)
- `.github/workflows/nightly.yml` — Cron placeholder

## Prochaines étapes
1. Initialiser le repo GitHub et pousser ce squelette.
2. Remplir `suppliers` et implémenter le premier parseur (EDF).
3. Écrire un premier test snapshot et une route `/v1/tariffs` minimale.
