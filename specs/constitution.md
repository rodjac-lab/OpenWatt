---
speckit: 1.0
id: openwatt.constitution
title: "Constitution du projet OpenWatt — Comparateur des tarifs d’électricité en France"
version: 1.0.0
status: stable
owners: [rodjac-lab, buddy]
last_updated: 2025-11-11
---

# ⚡ Mission

Offrir un outil **transparent**, **fiable** et **open data** permettant à tout citoyen ou acteur du marché
de **comparer les tarifs d’électricité des particuliers en France**, avec :

- détection automatique des changements,
- validation continue contre les **Tarifs Réglementés de Vente (TRVE)**,
- et historisation complète des données.

OpenWatt s’inscrit dans une démarche de **transparence énergétique** et de **données publiques vérifiables**.

---

# 🧭 Principes fondateurs

1. **Open Data by Design** — toutes les données traitées proviennent de sources publiques (fournisseurs, CRE, data.gouv.fr).
2. **Insert-Only History** — aucune donnée n’est modifiée : chaque observation crée une nouvelle ligne.
3. **TRVE = Source de vérité** — les tarifs réglementés servent de référence pour la validation et la qualité.
4. **Spec-Driven Build** — toute évolution passe d’abord par une mise à jour de la spec avant le code.
5. **Simplicité et Robustesse** — privilégier les solutions simples, reproductibles et auditables.
6. **Traçabilité complète** — chaque observation est associée à un hash, un parser, et un timestamp.

---

# ⚙️ Charte technique (non négociable)

1. **Référence officielle : TRVE**
   - Importés depuis data.gouv.fr (CRE) comme garde-fou.
   - Écart > ±50 % = alerte `erifying`.
   - TRVE n’est jamais “scrapé”, mais importé et versionné séparément.
2. **Configuration déclarative (YAML)**
   - Chaque fournisseur possède un fichier YAML définissant :
     - URLs à surveiller,
     - sélecteurs CSS/regex,
     - règles de validation,
     - cas limites connus.
   - Ajouter un fournisseur = créer un YAML, sans modifier le code Python.
3. **Détection de changements**
   - SHA-256 sur chaque HTML/PDF.
   - Si hash change → re-parse sandbox.
   - Si échec 3× → masquer fournisseur dans l’API.
4. **Fraîcheur des données**
   - `fresh` : dernière observation ≤ 7 jours, aucune alerte active.
   - `verifying` : changement détecté ou validation en attente (≤ 48 h max).
   - `stale` : dernière observation > 14 jours.
   - `broken` : échec de parsing ou données invalides.
   - Chaque tarif expose `observed_at`, `parser_version`, `source_checksum`.
5. **Historisation complète**
   - Jamais d’UPDATE : chaque scrape = nouvelle ligne en DB.
   - Permet graphiques, audits et rollback.
6. **Tests snapshots obligatoires**
   - Un HTML/PDF anonymisé et un JSON attendu par fournisseur.
   - `pytest` casse si le HTML change → alerte développeur.
7. **Alerting & traçabilité**
   - Log JSON : `{date, supplier, url, hash, status}`.
   - GitHub Issue auto-créée si `parse_error`, `prix_anomal`, ou `structure_changed`.
   - Notifications via l'app GitHub mobile.
8. **Stack technique figée**
   - **Python 3.11+**, **PostgreSQL**, **FastAPI + uvicorn**, **BeautifulSoup4**, **pytest**.
   - Orchestration : GitHub Actions (cron 03:15 UTC).
   - Alertes : GitHub Issues auto-créées par les workflows CI.
9. **Pas de dépendances externes lourdes**
   - Pas de LLM, pas d’OCR, pas de Selenium/Playwright.
   - Sites trop dynamiques → mis en backlog jusqu’à alternative viable.
10. **Runbooks par fournisseur**
    - `/docs/parsers/{supplier}.md` documente :
      - URLs, sélecteurs, cas limites, historique de cassures.
      - Objectif : réparation < 2 h sans debugging profond.

---

# 🧩 Domaines clés

- Tarification résidentielle (≤ 36 kVA) sur le réseau Enedis.
- Options : BASE, HPHC (et plus tard TEMPO).
- France métropolitaine (hors zones non interconnectées).
- Données TTC et HT disponibles pour analyses.

---

# 🧑‍💼 Rôles et gouvernance

| Rôle              | Responsable    | Responsabilités                         |
| ----------------- | -------------- | --------------------------------------- |
| **Product Owner** | rodjac-lab     | Vision, priorisation, validation métier |
| **Tech Lead**     | buddy          | Architecture, qualité code/spec, CI/CD  |
| **Contributors**  | open community | Parsers, docs, tests validés par PR     |

---

# 🔁 Cycle Spec-Kit

1. Modifier la spec (`.md` ou `.json` dans `/specs`)
2. Ouvrir PR `spec-change`
3. Validation : PO + Tech Lead
4. CI : lint, tests, build doc, déploiement
5. Merge → release tag → production

---

# 🧱 Stack minimale (MVP)

- **Langage :** Python 3.11+
- **DB :** PostgreSQL (insert-only + vues latest)
- **API :** FastAPI + uvicorn
- **Scraping :** requests + BeautifulSoup4
- **Tests :** pytest + snapshots
- **Automation :** GitHub Actions (cron nightly)
- **Alerting :** GitHub Issues auto-créées par les workflows CI

---

# 🧾 Licences & ouverture

- **Code & specs** sous licence MIT.
- **Données** issues de sources publiques (réutilisation permise sous CC-BY 4.0).
- Objectif : garantir la reproductibilité et la transparence des prix de l’électricité.

---

# 🌐 Vision à long terme

- Étendre la couverture à 100 % des fournisseurs français.
- Offrir une API publique open-source et un tableau de bord temps réel.
- Publier les historiques consolidés en open data.
- Devenir la référence indépendante sur la transparence énergétique.
