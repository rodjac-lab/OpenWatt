# Proof of Concept : Playwright pour OpenWatt

**Date :** 29 décembre 2025 (mis à jour)
**Auteur :** OpenWatt Core Team
**Statut :** ✅ Validé avec clarifications importantes
**Objectif :** Comprendre quand utiliser Playwright vs requests pour la constitution v2.0

---

## 🎯 Résumé exécutif

**Résultat POC technique :** ✅ Playwright fonctionne et peut scraper des pages web dynamiques.

**MAIS ATTENTION - Clarification critique :**

Playwright n'est **PAS** la solution au problème de blocage IP d'EDF/Engie !

### Les deux problèmes distincts

| Problème | Cause | Solution | Outil nécessaire |
|----------|-------|----------|------------------|
| **Blocage IP** (EDF, Engie) | IPs datacenter bloquées | Raspberry Pi / Proxy résidentiel | `requests` suffit ! |
| **Site dynamique** (React/Vue) | Contenu chargé en JavaScript | Playwright | `playwright` requis |

**Pour EDF/Engie :** Le problème est uniquement le blocage IP, pas le JavaScript. Les PDFs sont statiques et accessibles avec `requests` depuis une IP résidentielle.

---

## 🔍 Investigation détaillée : EDF/Engie

### Test de blocage IP (29 décembre 2025)

**Depuis IP résidentielle (machine locale) :**

```bash
$ curl -I https://particulier.edf.fr/content/dam/2-Actifs/Documents/Offres/Grille_prix_Tarif_Bleu.pdf
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: 169949

$ curl -I https://particuliers.engie.fr/content/dam/pdf/fiches-descriptives/fiche-descriptive-elec-reference-3-ans.pdf
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: 306500
```

✅ **Les PDFs sont accessibles avec un simple `curl` !**

**Depuis GitHub Actions (IP datacenter) :**

```yaml
# .github/workflows/ingest-live.yml (lignes 23-32)
# Note: edf and engie are excluded because GitHub Actions IPs are blocked
# by their websites (403 Forbidden)
```

❌ **GitHub Actions est bloqué (HTTP 403)**

### Conclusion pour EDF/Engie

- **Type de contenu :** PDFs statiques (pas de JavaScript)
- **Outil de scraping :** `requests` + `pdfplumber` (déjà en place)
- **Problème :** Blocage IP uniquement
- **Solution :** Raspberry Pi / Proxy résidentiel / Serveur dédié
- **Playwright nécessaire ?** ❌ **NON** (les PDFs sont statiques)

---

## 📊 Résultats du test POC Playwright

### Test réalisé

**URL testée :** https://www.fournisseurs-electricite.com/fournisseurs/edf/tarifs/bleu-reglemente

Ce site est un **agrégateur tiers** (pas EDF officiel).

| Méthode        | Statut  | Durée (ms) | Taille HTML | Prix trouvés |
|----------------|---------|------------|-------------|--------------|
| BeautifulSoup  | ✅ Success | 355-504    | 186 KB      | 5            |
| Playwright     | ✅ Success | 3721-7698  | 215 KB      | 5            |

**Ratio de performance :** Playwright est environ **10x plus lent** que BeautifulSoup sur une page statique.

### Conclusion du test

✅ **Playwright fonctionne techniquement**
⚠️ **Mais 10x plus lent et inutile pour du contenu statique**

---

## 🎯 Quand utiliser Playwright ?

### ✅ Cas d'usage VALIDES pour Playwright

1. **Sites web avec contenu dynamique (React/Vue/Next.js)**
   - Exemple : calculateurs interactifs
   - Les prix sont chargés en AJAX après le chargement initial
   - `requests` voit une page vide

2. **Sites nécessitant interaction**
   - Cliquer sur des boutons
   - Remplir des formulaires
   - Naviguer entre pages

3. **Agrégateurs temps réel**
   - Sites comparateurs qui chargent dynamiquement les tarifs

### ❌ Cas d'usage INVALIDES pour Playwright

1. **Contourner le blocage IP**
   - Playwright sur GitHub Actions = même IP bloquée
   - Solution = changer d'infrastructure, pas d'outil

2. **PDFs statiques** (EDF, Engie, Total, Mint)
   - `requests` + `pdfplumber` suffit amplement
   - Playwright n'apporte rien

3. **HTML statique simple**
   - `requests` + BeautifulSoup est 10x plus rapide

---

## 💡 Stratégie recommandée par type de source

### 1. PDFs officiels (EDF, Engie, Total, Mint, Vattenfall)

**Outil :** `requests` + `pdfplumber`

**Infrastructure :**
- ✅ Raspberry Pi à domicile (IP résidentielle)
- ✅ VPS avec IP résidentielle
- ✅ Proxy résidentiel payant

**Playwright nécessaire ?** ❌ NON

### 2. Sites web dynamiques (futurs fournisseurs)

**Outil :** `playwright` + `pdfplumber` (si extraction de tableaux)

**Infrastructure :** Même que ci-dessus (IP résidentielle requise)

**Playwright nécessaire ?** ✅ OUI

### 3. Agrégateurs tiers (optionnel)

**Outil :** `playwright` (si dynamique) ou `requests` + BeautifulSoup (si statique)

**Infrastructure :** GitHub Actions fonctionne (pas de blocage IP)

**Playwright nécessaire ?** Dépend du site

---

## 🧪 Script POC disponible

Le script de test complet est disponible dans :

```bash
scripts/test_playwright_poc.py
```

**Usage :**

```bash
# Installer Playwright
pip install playwright
playwright install chromium

# Lancer le test
python scripts/test_playwright_poc.py
```

**Ce que le script teste :**
- ✅ Que Playwright fonctionne techniquement
- ✅ Comparaison de performance vs BeautifulSoup
- ❌ Ne teste PAS le contournement de blocage IP (ce n'est pas son rôle)

---

## ✅ Conclusions finales CORRIGÉES

### Faisabilité technique

✅ **Playwright fonctionne** pour scraper des sites web dynamiques
✅ **L'approche constitution v2.0** (outil adapté à la source) est valide

### Clarifications importantes

❌ **Playwright ne contourne PAS le blocage IP**
✅ **Pour EDF/Engie : Raspberry Pi + requests suffit**
✅ **Playwright réservé aux vrais sites dynamiques (React/Vue)**

### Prochaines étapes

1. ✅ **Court terme :** Setup Raspberry Pi / VPS résidentiel
2. ✅ **Configuration :** GitHub self-hosted runner sur ce serveur
3. ✅ **Stack EDF/Engie :** `requests` + `pdfplumber` (pas de Playwright)
4. 🔄 **Future :** Playwright uniquement pour fournisseurs avec sites dynamiques

---

## 📚 Documentation associée

- **[SELF-HOSTED-SETUP.md](SELF-HOSTED-SETUP.md)** : Guide complet pour Raspberry Pi, VPS, proxy
- **[ingestion-limitations.md](ingestion-limitations.md)** : Stratégies par type de blocage
- **[constitution.md](../specs/constitution.md)** : Constitution v2.0.0

---

**Rapport mis à jour le 29 décembre 2025.**

**Leçons apprises :**
- ⚠️ Ne pas confondre "blocage IP" et "site dynamique"
- ⚠️ Playwright n'est pas une solution magique anti-blocage
- ✅ Toujours tester avec `curl` d'abord pour identifier le vrai problème
