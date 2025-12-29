# Stratégies d'ingestion avancées (v2.0)

> **Note :** Ce document a été mis à jour suite à la révision de la constitution v2.0.0 (29 déc 2025).
> Les contraintes initiales du MVP ont été levées pour permettre une couverture complète des fournisseurs.

## ⚠️ Clarification critique : Deux problèmes distincts

**NE PAS CONFONDRE :**

| Problème | Symptôme | Cause | Solution | Outil |
|----------|----------|-------|----------|-------|
| **Blocage IP** | HTTP 403 Forbidden | IP datacenter blacklistée | Infrastructure résidentielle | `requests` suffit |
| **Site dynamique** | Contenu vide | JavaScript requis pour charger les prix | Playwright/Selenium | `playwright` requis |

**Pour EDF/Engie :** Problème = blocage IP uniquement (PDFs statiques). Solution = Raspberry Pi + `requests`.

## Vue d'ensemble

Avec la constitution v2.0, nous adoptons une approche **pragmatique** : utiliser l'outil le plus simple qui fonctionne pour chaque source, sans s'interdire les technologies modernes nécessaires.

## Méthodes de scraping par type de source

### 1. PDF statiques (méthode privilégiée)

**Outil :** `pdfplumber`

**Fournisseurs :** EDF, Engie, TotalEnergies, Mint Energie (PDFs)

**Avantages :**
- ✅ Pas de blocage IP (fichiers statiques)
- ✅ Parsing fiable et stable
- ✅ Rapide et léger
- ✅ Fonctionne dans GitHub Actions

**Exemple de configuration YAML :**
```yaml
supplier: EDF
source:
  url: https://particulier.edf.fr/tarifs.pdf
  format: pdf
  method: pdfplumber
```

**Statut :** ✅ **Production ready**

---

### 2. HTML statique (sans JavaScript)

**Outil :** `requests + BeautifulSoup4`

**Fournisseurs :** Sites anciens, pages informatives

**Avantages :**
- ✅ Simple et rapide
- ✅ Pas de dépendances lourdes
- ✅ Fonctionne dans GitHub Actions

**Exemple de configuration YAML :**
```yaml
supplier: ExampleProvider
source:
  url: https://example.com/tarifs
  format: html
  method: requests
  selectors:
    price: "div.tarif span.prix"
```

**Statut :** ✅ **Production ready**

---

### 3. HTML dynamique (React/Vue/Next.js)

**Outil :** `Playwright` (recommandé) ou `Selenium`

**Fournisseurs :** Sites modernes avec JavaScript chargement AJAX (futurs fournisseurs alternatifs)

**⚠️ IMPORTANT :** Playwright ne contourne PAS le blocage IP ! Si un site bloque GitHub Actions, Playwright sur GitHub Actions sera également bloqué. Playwright est nécessaire uniquement si le contenu est chargé en JavaScript.

**Pourquoi Playwright :**
- ✅ Plus rapide que Selenium
- ✅ Meilleure gestion des navigateurs headless
- ✅ API moderne (async/await)
- ✅ Debugging intégré (screenshots, vidéos)

**Exemple de configuration YAML :**
```yaml
supplier: EDFWeb
source:
  url: https://particulier.edf.fr/tarifs-interactifs
  format: html
  method: playwright
  browser: chromium
  wait_for: "div.tarif-loaded"
  selectors:
    price: "span.prix-kwh"
```

**Installation :**
```bash
pip install playwright
playwright install chromium  # Télécharge le navigateur
```

**Statut :** ✅ **Production ready** (mais nécessite infrastructure résidentielle si blocage IP)

**Note :** Si le site bloque les IPs datacenter, voir [SELF-HOSTED-SETUP.md](SELF-HOSTED-SETUP.md)

---

### 4. PDF scannés (images)

**Outil :** `pytesseract` (OCR)

**Fournisseurs :** Rares (anciens documents scannés)

**Exemple :**
```yaml
supplier: LegacyProvider
source:
  url: https://example.com/old-tarif-scan.pdf
  format: pdf-scanned
  method: ocr
  ocr_lang: fra
```

**Statut :** 🔧 **Expérimental** (à éviter si possible)

---

## Gestion des blocages IP (EDF, Engie)

### Problème confirmé (29 déc 2025)

Les sites EDF et Engie **bloquent les IPs des datacenters** (AWS, Azure, GitHub Actions) pour protéger leurs documents contre le scraping massif.

**Test effectué :**
- ✅ Depuis IP résidentielle : `curl` EDF/Engie → HTTP 200 OK
- ❌ Depuis GitHub Actions : HTTP 403 Forbidden

**Type de contenu :** PDFs statiques (pas de JavaScript requis)

**Outil nécessaire :** `requests` + `pdfplumber` (déjà implémenté)

**Playwright nécessaire ?** ❌ **NON** (ce sont des PDFs directs, pas des pages React)

### Solutions (par ordre de préférence)

#### ✅ Solution 1 : Serveur dédié avec IP résidentielle

**Recommandé pour la production**

Mettre en place un petit serveur avec IP résidentielle :

**Options :**
- **VPS résidentiel** : GCORE, Leaseweb (50-100€/mois)
- **Raspberry Pi à domicile** : IP résidentielle, coût ~50€ one-time
- **Serveur physique** : Kimsufi, So you Start avec IP clean

**Configuration :**
```yaml
# .github/workflows/ingest-live.yml
# Exécuter sur self-hosted runner au lieu de ubuntu-latest
jobs:
  ingest:
    runs-on: self-hosted  # Votre serveur dédié
```

**Coût :** 0-100€/mois selon l'option

**Guide complet :** Voir [SELF-HOSTED-SETUP.md](SELF-HOSTED-SETUP.md)

---

#### ✅ Solution 2 : Proxy résidentiel payant

**Pour une mise en production rapide**

Services de proxies résidentiels légaux :

| Service | Coût estimé | Avantages |
|---------|-------------|-----------|
| [Bright Data](https://brightdata.com) | ~75€/mois | Leader du marché, légal |
| [Oxylabs](https://oxylabs.io) | ~100€/mois | Excellent support |
| [SmartProxy](https://smartproxy.com) | ~50€/mois | Bon rapport qualité/prix |

**Configuration :**
```python
import requests

proxies = {
    'http': 'http://user:pass@proxy.brightdata.com:22225',
    'https': 'http://user:pass@proxy.brightdata.com:22225'
}

response = requests.get(url, proxies=proxies)
```

**Coût :** 50-150€/mois

---

#### ⚠️ Solution 3 : Ingestion manuelle locale

**Solution temporaire (workaround MVP)**

Exécuter l'ingestion depuis votre machine locale (IP résidentielle) :

```bash
# Depuis votre machine
python -m ingest.pipeline edf --fetch --persist
python -m ingest.pipeline engie --fetch --persist

# Pusher les résultats dans la DB de prod
OPENWATT_DATABASE_URL=postgresql://prod python -m ingest.pipeline edf --persist
```

**Avantages :** Gratuit, simple
**Inconvénients :** Pas automatisé, nécessite intervention manuelle

---

#### ❌ Solution 4 : Téléchargement manuel des PDFs

**À éviter** (non scalable)

Si vraiment bloqué :
1. Télécharger le PDF manuellement depuis votre navigateur
2. Le placer dans `artifacts/raw/edf_[date].pdf`
3. Exécuter : `python -m ingest.pipeline edf --html artifacts/raw/edf_[date].pdf --persist`

---

## Stratégie recommandée (Production)

### Phase 1 : PDFs uniquement (actuel)
- ✅ Tous les fournisseurs proposent des PDFs
- ✅ Pas de blocage IP sur les PDFs statiques
- ✅ Fonctionne dans GitHub Actions
- ❌ Nécessite mise à jour manuelle si le fournisseur change d'URL

### Phase 2 : Ajout Playwright pour sites web (recommandé)
- ✅ Détection automatique des changements de prix
- ✅ Couverture des sites sans PDF
- ⚠️ Nécessite serveur dédié ou proxy

**Setup recommandé :**
```
GitHub Actions (gratuit)
  ↓
  Scrape PDFs (EDF, Engie, Total, Mint)

Serveur dédié (50€/mois)
  ↓
  Scrape sites web dynamiques (si nécessaire)
  ↓
  Push vers même DB
```

---

## Tests et validation

Avant de déployer une nouvelle méthode de scraping :

```bash
# 1. Vérifier l'accessibilité
python scripts/check_sources.py --supplier edf

# 2. Tester le scraping en local
python -m ingest.pipeline edf --fetch --dry-run

# 3. Valider le snapshot
pytest tests/parsers/test_pipeline.py::test_parser_matches_expected_snapshot[edf]

# 4. Commit et push si OK
```

---

## État actuel par fournisseur

| Fournisseur | Méthode | Statut GitHub Actions | Solution |
|-------------|---------|----------------------|----------|
| **EDF** | PDF | ✅ Fonctionne | Aucune action nécessaire |
| **Engie** | PDF | ✅ Fonctionne | Aucune action nécessaire |
| **TotalEnergies** | PDF | ✅ Fonctionne | Aucune action nécessaire |
| **Mint Energie** | PDF | ✅ Fonctionne | Aucune action nécessaire |

**⚠️ Clarification importante (29 déc 2025) :**

EDF et Engie bloquent GitHub Actions, mais leurs PDFs sont accessibles depuis une IP résidentielle avec un simple `requests`. **Playwright n'est PAS nécessaire** pour EDF/Engie car ce sont des PDFs statiques, pas des sites dynamiques.

**Solution pour EDF/Engie :** Raspberry Pi / VPS résidentiel + `requests` (voir [SELF-HOSTED-SETUP.md](SELF-HOSTED-SETUP.md))

---

## Prochaines étapes (Roadmap)

### Q1 2026
1. ✅ Constitution v2.0 adoptée
2. 🔧 Installer Playwright en local : `pip install playwright`
3. 🔧 Tester scraping EDF web en local
4. 🔧 Créer config YAML avec `method: playwright`

### Q2 2026
1. Évaluer coût/bénéfice serveur dédié vs proxy
2. Setup serveur dédié (Raspberry Pi ou VPS résidentiel)
3. Migrer workflow `ingest-live.yml` vers `self-hosted`
4. Activer scraping web pour EDF/Engie

### Q3 2026
1. Ajouter 10+ nouveaux fournisseurs
2. Publier API publique
3. Partenariat data.gouv.fr

---

## Support et documentation

- **Runbooks** : `/docs/parsers/{supplier}.md` pour chaque fournisseur
- **Constitution** : `/specs/constitution.md` (v2.0)
- **Issues GitHub** : Créées automatiquement en cas d'échec
- **Logs** : Structlog JSON dans stdout

---

## Notes légales

**Tous les scrapings respectent :**
- ✅ Directive EU 2019/1024 (Open Data)
- ✅ Jurisprudence Ryanair vs PR Aviation (2015)
- ✅ Robots.txt et rate limiting
- ✅ Attribution claire des sources
- ❌ Aucun bypass de sécurité ou captcha
- ❌ Aucune revente de données (open source)

**Voir :** Section "Charte de légalité du scraping" dans la constitution.
