---
id: elec-tariffs-fr.governance
version: 0.1.0
status: draft
last_updated: 2025-11-11
---

# 🧑‍⚖️ Gouvernance des specs

- Toute modification de schéma JSON = PR `spec-change`
- Lint automatique (`spec lint`) sur CI
- Validation métier par rodjac-lab, validation technique par buddy
- Tag `spec-release` -> build + déploiement CI

# 🔐 Policies

- `tariffs` est immuable: INSERT-only; UPDATE/DELETE interdits par droits + triggers
- Transparence: chaque observation conserve `source_url` et `source_checksum`
