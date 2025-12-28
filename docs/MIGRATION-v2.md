# Guide de migration : Constitution v1.0 → v2.0

**Date :** 27 décembre 2025
**Auteur :** OpenWatt Core Team
**Statut :** Stable

---

## 🎯 Résumé exécutif

La constitution v2.0 lève les contraintes bloquantes sur les outils de scraping tout en conservant les principes fondamentaux (traçabilité, open data, tests). Cette migration permet d'atteindre l'objectif de **couverture 100% des fournisseurs français**.

**Impact :** ✅ **Zéro breaking change** - compatibilité totale avec le code existant.

---

## 📋 Tableau comparatif

| Aspect | v1.0 (MVP) | v2.0 (Production) |
|--------|-----------|-------------------|
| **Philosophie** | "Stack simple = BeautifulSoup only" | "Outil adapté à chaque source" |
| **Selenium/Playwright** | ❌ Interdit | ✅ Autorisé et recommandé |
| **OCR** | ❌ Interdit | ✅ Autorisé si nécessaire |
| **Sites dynamiques** | ⏸️ Backlog | ✅ Support actif |
| **Charte légale** | ❌ Absente | ✅ Section dédiée |
| **Couverture** | 4/5 fournisseurs (80%) | 100% visé |
| **Dépendances** | requests, BeautifulSoup4, pdfplumber | + playwright, selenium (optionnel) |

---

## 🔄 Changements détaillés

### 1. Principes fondateurs (section modifiée)

**Avant (v1.0) :**
```markdown
5. **Simplicité et Robustesse** — privilégier les solutions simples, reproductibles et auditables.
```

**Après (v2.0) :**
```markdown
5. **Pragmatisme technique** — utiliser l'outil le plus simple qui fonctionne pour chaque source.
7. **Légalité et éthique** — respecter les robots.txt, ajouter des délais, scraper uniquement des données publiques.
```

**Impact :** Changement de mentalité, pas de code.

---

### 2. Stack technique (section remplacée)

**Avant (v1.0) :**
```markdown
8. **Stack technique figée**
   - **Python 3.11+**, **PostgreSQL**, **FastAPI + uvicorn**, **BeautifulSoup4**, **pytest**.
9. **Pas de dépendances externes lourdes**
   - Pas de LLM, pas d'OCR, pas de Selenium/Playwright.
   - Sites trop dynamiques → mis en backlog jusqu'à alternative viable.
```

**Après (v2.0) :**
```markdown
8. **Stack technique (recommandations)**

### Backend & Base de données (fixes)
- Python 3.11+, PostgreSQL, FastAPI, pytest

### Scraping (adapté à la source)
| Type de source | Outil recommandé | Cas d'usage |
|----------------|------------------|-------------|
| PDF statique | pdfplumber | Grilles tarifaires |
| HTML statique | requests + BeautifulSoup4 | Pages simples |
| HTML dynamique (JS) | Playwright ou Selenium | Sites React/Vue |
| PDF scanné (image) | pytesseract (OCR) | PDFs anciens |
```

**Impact :**
- ✅ Code existant (BeautifulSoup) reste valide
- ✅ Nouveaux parsers peuvent utiliser Playwright
- ✅ Choix de l'outil dans la config YAML (pas dans le code Python)

---

### 3. Ajout : Charte de légalité

**Nouvelle section** qui n'existait pas en v1.0.

**Contenu :**
- Directive EU 2019/1024 (Open Data)
- Jurisprudence Ryanair vs PR Aviation
- Ce qui est autorisé vs interdit
- Respect des robots.txt et rate limiting

**Impact :** Aucun sur le code, mais important pour la légitimité du projet.

---

### 4. Suppression : Backlog des sites dynamiques

**Avant (v1.0) :**
```markdown
Sites trop dynamiques → mis en backlog jusqu'à alternative viable.
```

**Après (v2.0) :**
```markdown
# (Supprimé)
```

**Impact :** Les sites EDF/Engie web peuvent maintenant être scrapés avec Playwright.

---

## 🛠️ Actions de migration

### Étape 1 : Installer les nouvelles dépendances (optionnel)

Si vous voulez utiliser Playwright pour les sites dynamiques :

```bash
# Ajouter à requirements.txt (optionnel)
echo "playwright>=1.40,<2.0" >> requirements.txt
echo "selenium>=4.15,<5.0" >> requirements.txt  # Alternative à Playwright

# Installer
pip install -r requirements.txt

# Télécharger le navigateur Chromium
playwright install chromium
```

**Note :** **Pas obligatoire** si vous utilisez uniquement PDFs (cas actuel).

---

### Étape 2 : Mettre à jour les configs YAML (futur)

Exemple pour un nouveau fournisseur avec site dynamique :

```yaml
# parsers/config/nouveau_fournisseur.yaml
supplier: NouveauFournisseur
parser_version: nouveau_v1
source:
  url: https://example.com/tarifs
  format: html
  method: playwright  # NOUVEAU : spécifier la méthode
  browser: chromium
  wait_for: "div.tarif-loaded"  # Attendre le chargement JS
  rate_limit: 2  # Délai entre requêtes (secondes)

html:
  selectors:
    price: "span.prix-kwh"
    option: "div.option"
```

**Compatibilité :** Les configs YAML existantes (sans `method`) utilisent automatiquement `requests` (comportement par défaut).

---

### Étape 3 : Mettre à jour la documentation

```bash
# 1. Constitution (déjà fait)
cat specs/constitution.md | grep "version: 2.0.0"

# 2. Limitations d'ingestion (déjà fait)
cat docs/ingestion-limitations.md | grep "v2.0"

# 3. Runbooks fournisseurs (si nécessaire)
# Ajouter la méthode de scraping dans chaque runbook
echo "**Méthode :** pdfplumber" >> docs/parsers/edf.md
```

---

### Étape 4 : Tests de régression

Vérifier que rien n'est cassé :

```bash
# 1. Tests existants doivent tous passer
pytest tests/

# 2. Scraping existant doit fonctionner
python -m ingest.pipeline edf --fetch --dry-run
python -m ingest.pipeline mint_indexe_trv --fetch --dry-run

# 3. CI doit être au vert
git push && gh run watch
```

**Résultat attendu :** ✅ Tous les tests passent (aucun breaking change).

---

## 📦 Plan de déploiement

### Phase 1 : Adoption de la constitution v2.0 (aujourd'hui)

✅ **Actions :**
1. Commit de la nouvelle constitution
2. Mise à jour de la documentation
3. Communication aux contributeurs

```bash
git add specs/constitution.md docs/ingestion-limitations.md docs/MIGRATION-v2.md
git commit -m "feat(constitution): adopt v2.0 - remove scraping constraints"
git push
```

**Impact :** Aucun sur le code existant (changement documentaire uniquement).

---

### Phase 2 : Expérimentation Playwright (optionnel, Q1 2026)

🔧 **Actions :**
1. Installer Playwright en local
2. Tester scraping d'un site dynamique (ex: EDF web)
3. Créer une config YAML avec `method: playwright`
4. Valider le snapshot

**Pré-requis :** Serveur dédié avec IP résidentielle (EDF/Engie bloquent GitHub Actions).

---

### Phase 3 : Production à l'échelle (Q2-Q3 2026)

🚀 **Actions :**
1. Setup serveur dédié (Raspberry Pi ou VPS résidentiel)
2. Migrer workflow vers `self-hosted` runner
3. Ajouter 10+ nouveaux fournisseurs
4. Publier API publique

---

## 🧪 Validation de la migration

### Checklist de validation

- [ ] Constitution v2.0 commitée et poussée
- [ ] Documentation mise à jour (`ingestion-limitations.md`, `MIGRATION-v2.md`)
- [ ] Tests de régression passent (`pytest tests/`)
- [ ] CI au vert (GitHub Actions)
- [ ] Scraping existant fonctionne (EDF, Engie, Total, Mint via PDFs)
- [ ] Aucun breaking change détecté
- [ ] Communication aux contributeurs (README, issues)

### Tests de non-régression

```bash
# Backend
pytest tests/ -v

# Parsers
pytest tests/parsers/test_pipeline.py -v

# API
curl http://localhost:8000/health
curl http://localhost:8000/v1/tariffs

# Ingestion
python -m ingest.pipeline edf --fetch --dry-run
```

**Tous les tests doivent passer ✅**

---

## 🆘 Rollback (en cas de problème)

Si un problème majeur est détecté après migration :

```bash
# Revenir à la constitution v1.0
git checkout v1.0.0 -- specs/constitution.md
git commit -m "revert: rollback to constitution v1.0"
git push
```

**Note :** Un rollback ne devrait **jamais être nécessaire** car v2.0 est 100% rétrocompatible.

---

## 📞 Support

- **Issues GitHub :** https://github.com/rodjac-lab/OpenWatt/issues
- **Documentation :** `/docs/` et `/specs/`
- **Runbooks :** `/docs/parsers/{supplier}.md`
- **Product Owner :** @rodjac-lab
- **Tech Lead :** @buddy

---

## 📝 Notes de version

**Constitution v2.0.0** (27 déc 2025)

**Ajouts :**
- ✅ Charte de légalité du scraping
- ✅ Support Playwright/Selenium
- ✅ Support OCR (pytesseract)
- ✅ Tableau des méthodes de scraping recommandées
- ✅ Section "Gestion des protections anti-scraping"

**Modifications :**
- 🔄 "Simplicité et Robustesse" → "Pragmatisme technique"
- 🔄 "Stack technique figée" → "Stack technique (recommandations)"
- 🔄 Scraping tools adaptatifs au lieu de BeautifulSoup4 only

**Suppressions :**
- ❌ "Pas de Selenium/Playwright"
- ❌ "Sites dynamiques → backlog"
- ❌ "Pas d'OCR"

**Compatibilité :**
- ✅ 100% rétrocompatible avec le code existant
- ✅ Configs YAML existantes fonctionnent sans modification
- ✅ Base de données inchangée
- ✅ API inchangée

---

**Fin du guide de migration.**

Pour toute question, ouvrir une issue GitHub avec le tag `[migration-v2]`.
