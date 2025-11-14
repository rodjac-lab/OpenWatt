# EDF parser runbook (`edf_pdf_v1`)

- **PDF source**: https://particulier.edf.fr/content/dam/2-Actifs/Documents/Offres/Grille_prix_Tarif_Bleu.pdf (grille officielle Tarif Bleu / TRV).
- **Extraction**: `parsers/config/edf.yaml` decrit deux tables PDF (Base et HP/HC) et les colonnes a lire (abonnement TTC, prix kWh). Le parser `pdfplumber` + `parse_float()` convertit `12,34` -> `12.34`.
- **Cadence**: EDF publie les mises a jour TRV lors des hausses reglementaires (~fevrier / aout). La job nightly telecharge le PDF, calcule le hash, puis persiste les nouvelles lignes (insert-only).
- **Pieges** :
  - pdfplumber loggue parfois des warnings, mais l'extraction reste correcte.
  - L'option Tempo n'est pas encore couverte (backlog).
- **Recovery steps** :
  1. Telecharger la derniere grille PDF et la deposer sous `tests/snapshots/edf/`.
  2. Adapter `pdf.tables` si la structure change (indices de colonnes).
  3. Regenerer le JSON attendu :  
     `python -m ingest.pipeline edf --html tests/snapshots/edf/<file>.pdf --observed-at <ISO> --output tests/snapshots/edf/edf_<date>_expected.json`
  4. Lancer `pytest -k edf` avant merge.
