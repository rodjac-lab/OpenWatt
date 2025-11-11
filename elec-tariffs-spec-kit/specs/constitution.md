---
speckit: 1.0
id: elec-tariffs-fr
title: "Constitution du projet Elec Tariffs FR"
version: 0.1.0
status: draft
owners: [rodjac-lab, buddy]
last_updated: 2025-11-11
---

# 🎯 Mission
Fournir une base de données publique, fiable et historisée des tarifs électricité résidentiels en France,
afin de permettre la transparence et la comparaison libre.

# 🧭 Principes
1. **Open Data by Design** — données publiques, réutilisables, traçables.
2. **Insert-Only History** — jamais d’écrasement de données (historisation immuable).
3. **TRVE as Ground Truth** — le tarif réglementé sert de garde-fou pour QA.
4. **Spec-Driven Build** — toute évolution passe par mise à jour de la spec avant le code.
5. **Simplicité > Perfection** — commencer petit, itérer.

# 🪪 Domaines clés
- Tarification électricité FR métropolitaine ≤36 kVA
- Offres BASE / HPHC / (plus tard) TEMPO
- API de consultation publique

# 🧩 Rôles
| Rôle | Responsable | Responsabilités |
|------|-------------|------------------|
| Product Owner | rodjac-lab | Vision, roadmap, validation fonctionnelle |
| Tech Lead | buddy | Architecture, qualité des specs et du code |
| Contributor | open | Ajout de parsers, doc et tests validés |

# 🔁 Cycle Spec-Kit
1. Modifier une spec (.md/.json)
2. Ouvrir PR `spec-change`
3. Validation pair-review
4. Génération/validation automatique (lint, schemas, tests)
5. Déploiement CI après merge
