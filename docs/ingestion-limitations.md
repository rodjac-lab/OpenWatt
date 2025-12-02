# Limitations de l'ingestion automatique

## Blocage des IPs GitHub Actions

**Problème :** Les sites web d'EDF et Engie bloquent les IPs des services cloud (AWS, Azure, GitHub Actions, etc.) pour protéger leurs documents PDF contre le scraping automatisé.

**Impact :** L'ingestion automatique quotidienne via le workflow GitHub Actions `ingest-live.yml` échoue systématiquement pour EDF et Engie avec une erreur 403 Forbidden, même avec un User-Agent valide.

### Fournisseurs affectés

- ❌ **EDF** : Bloqué depuis GitHub Actions
- ❌ **Engie** : Bloqué depuis GitHub Actions
- ✅ **Mint Energie** : Fonctionne normalement
- ✅ **TotalEnergies** : Fonctionne normalement

### Solutions de contournement

#### Option 1 : Ingestion manuelle (recommandée pour l'instant)

Exécuter l'ingestion localement depuis une machine avec IP résidentielle :

```bash
# Depuis votre machine locale
python -m ingest.pipeline edf --fetch --persist
python -m ingest.pipeline engie --fetch --persist
```

#### Option 2 : Serveur dédié (moyen terme)

Mettre en place un serveur dédié avec IP résidentielle pour exécuter l'ingestion :
- VPS avec IP résidentielle
- Serveur physique dans un datacenter avec IP non bloquée
- Raspberry Pi à domicile avec IP résidentielle

#### Option 3 : Proxy résidentiel (coûteux)

Utiliser un service de proxy résidentiel payant :
- Bright Data (ex-Luminati)
- Oxylabs
- SmartProxy

Coût estimé : ~50-200€/mois selon le volume

#### Option 4 : Téléchargement manuel des PDFs

Télécharger manuellement les PDFs et les placer dans `artifacts/raw/` :

```bash
# Télécharger le PDF manuellement depuis votre navigateur
# Le placer dans artifacts/raw/edf_[timestamp].pdf

# Puis exécuter l'ingestion sans fetch
python -m ingest.pipeline edf --html artifacts/raw/edf_[timestamp].pdf --persist
```

### État actuel

Le workflow `ingest-live.yml` a été modifié pour **exclure EDF et Engie** de l'ingestion automatique quotidienne, afin d'éviter de créer des issues GitHub inutiles chaque jour.

Ces fournisseurs doivent être ingérés manuellement selon les options ci-dessus.

### Tests locaux

Pour vérifier que votre environnement peut accéder aux sources :

```bash
# Vérifier l'accessibilité des sources
python scripts/check_sources.py --supplier edf
python scripts/check_sources.py --supplier engie

# Si vous obtenez 200 OK, vous pouvez ingérer :
python -m ingest.pipeline edf --fetch --persist
python -m ingest.pipeline engie --fetch --persist
```

### Suivi

Pour réactiver l'ingestion automatique d'un fournisseur, modifier le fichier `.github/workflows/ingest-live.yml` :

```yaml
matrix:
  supplier: [edf, engie, mint_indexe_trv, ...]  # Ajouter edf/engie ici
```

**Note :** Ne réactiver que si vous avez mis en place une des solutions de contournement (serveur dédié, proxy, etc.).
