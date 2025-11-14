# Engie parser runbook (`engie_pdf_v1`)

- **PDF source**: https://particuliers.engie.fr/content/dam/pdf/fiches-descriptives/fiche-descriptive-elec-reference-3-ans.pdf (offre Elec Reference).
- **Extraction**: `parsers/config/engie.yaml` reference les tables PDF (page 3) pour l'option Base et HP/HC. Les colonnes TTC sont converties via `parse_float()`.
- **Cadence**: Engie ajuste les prix lors des evolutions TRV (~mensuel). La job nightly telecharge le PDF, calcule un hash et persiste uniquement les nouvelles observations.
- **Pieges** :
  - Certaines lignes comportent `-` pour les puissances non disponibles -> le parser saute ces entrees.
  - Surveiller les intitules de colonnes si Engie change la maquette.
- **Recovery steps** :
  1. Deposer la nouvelle fiche Engie dans `tests/snapshots/engie/`.
  2. Ajuster `pdf.tables` si les colonnes evoluent.
  3. Regenerer le JSON attendu :  
     `python -m ingest.pipeline engie --html tests/snapshots/engie/<file>.pdf --observed-at <ISO> --output tests/snapshots/engie/engie_<date>_expected.json`
  4. Lancer `pytest -k engie`.
