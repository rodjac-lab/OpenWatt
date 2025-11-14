# Mint Energie parser runbook (Online & Green / Classic & Green / Smart & Green)

- **PDF sources** :
  - Online & Green (indexee TRV) : https://doc.mint-energie.com/MintEnergie/MINT_ENERGIE_Fiche_Tarifs_21912_ONLINE_GREEN.pdf
  - Classic & Green : https://doc.mint-energie.com/MintEnergie/MINT_ENERGIE_Fiche_Tarifs_23012_CLASSIC_GREEN.pdf
  - Smart & Green : https://doc.mint-energie.com/MintEnergie/MINT_ENERGIE_Fiche_Tarifs_23224_SMART_GREEN.pdf
- **Extraction** : chaque YAML (`mint_indexe_trv`, `mint_classic_green`, `mint_smart_green`) decrit deux tables PDF (Base + HP/HC). Les colonnes TTC sont converties via `parse_float`.
- **Cadence** : Mint met a jour ces fiches lors des evolutions TRV ou des offres commerciales. Rejouer `python -m ingest.pipeline <config>` (ex: `mint_indexe_trv`) avec `--fetch --persist` pour consommer les nouvelles grilles.
- **Recovery** :
  1. Archiver les PDF dans `tests/snapshots/mint/`.
  2. Ajuster les index de colonnes si la maquette evolue (attention aux lignes \"vides\" generees par pdfplumber).
  3. Regenerer le JSON attendu :
     `python -m ingest.pipeline <config> --html tests/snapshots/mint/<file>.pdf --observed-at <ISO> --output tests/snapshots/mint/<config>_expected.json`
  4. Lancer `pytest tests/parsers -k mint`.
