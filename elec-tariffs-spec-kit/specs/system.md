---
id: elec-tariffs-fr.system
version: 0.1.0
status: draft
last_updated: 2025-11-11
---

# 🧱 Architecture (vue d'ensemble)

```mermaid
graph TD
A[Scrapers HTML/PDF] --> B[Normalizer]
B --> C[(Postgres insert-only)]
C --> D[API FastAPI /v1]
D --> E[UI Comparateur]
C --> F[TRVE Guard Diff (QA)]
```

# 🔌 Flux de données
1. **Scrapers** récupèrent HTML/PDF → checksum SHA-256
2. **Normalizer** mappe vers contrat `tariff.schema.json`
3. **Storage** `INSERT` uniquement (clé idempotente)
4. **API** expose `/v1/tariffs` (latest) & `/v1/tariffs/history`
5. **QA** compare vs **TRVE** pour badges et alertes
