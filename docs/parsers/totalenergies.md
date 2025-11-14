# TotalEnergies parser runbook (Heures Eco & Standard Fixe)

- **PDF sources** :
  - Heures Eco : https://www.totalenergies.fr/fileadmin/Digital/Groupe/PDF/Documents_contractuels/Particuliers/Tarifs_TotalEnergies/fr/grille-tarifaire-heures-eco-particuliers.pdf
  - Standard Fixe : https://www.totalenergies.fr/fileadmin/Digital/Groupe/PDF/Documents_contractuels/Particuliers/Tarifs_TotalEnergies/fr/grille-tarifaire-standard-fixe-particuliers.pdf
- **Extraction** : `parsers/config/total_heures_eco.yaml` et `.../total_standard_fixe.yaml` decrivent les tables Base + HP/HC (page 1) et les colonnes TTC a conserver. Les colonnes TRV affichees dans le PDF sont ignorees. Les tables melangent puissances Linky (4, 5, 7 kVA, etc.) avec les puissances Enedis : le YAML filtre explicitement sur `[3,6,9,12,15,18,24,30,36]` (HPHC commence a 6 kVA).
- **Cadence** : mises a jour lors des evolutions TRV ou promotions internes. La job nightly telecharge le PDF, calcule un hash, parse les tables et persiste en insert-only.
- **Recovery** :
  1. Placer le PDF mis a jour dans `tests/snapshots/total/`.
  2. Verifier les index de colonnes (Total reorganise parfois les colonnes TRV/Offre).
  3. Regenerer le JSON :  
     `python -m ingest.pipeline total_heures_eco --html tests/snapshots/total/<file>.pdf --observed-at <ISO> --output tests/snapshots/total/total_heures_eco_expected.json`
  4. Lancer `pytest tests/parsers -k total`.
