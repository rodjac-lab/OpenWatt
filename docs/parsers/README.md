# Parser runbooks

Each supplier must ship a YAML file under `parsers/config/` plus a short runbook in this folder. The YAML keeps the scraping logic declarative (selectors, URLs, validation rules) while the runbook explains edge cases, history of breakages, and manual recovery steps.

Current coverage:

| Supplier      | Parser version                                                       | Notes                                                                           |
| ------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| EDF           | `edf_pdf_v1`                                                         | Grille Tarif Bleu (PDF) -> `tests/snapshots/edf/edf_tarif_bleu.pdf`.            |
| Engie         | `engie_pdf_v1`                                                       | Fiche Elec Reference 3 ans (PDF) -> `tests/snapshots/engie/`.                   |
| TotalEnergies | `total_heures_eco_v1` / `total_standard_fixe_v1`                     | Deux grilles (Heures Eco & Standard Fixe) sous `tests/snapshots/total/`.        |
| Mint Energie  | `mint_indexe_trv_v1`, `mint_classic_green_v1`, `mint_smart_green_v1` | Trois fiches PDF (Online & Green, Classic, Smart) dans `tests/snapshots/mint/`. |

Add one Markdown file per supplier (e.g. `docs/parsers/edf.md`) describing:

- URLs to monitor and expected update cadence.
- Selectors or heuristics encoded in YAML.
- Known anomalies (`structure_changed`, `prix_anomal`, etc.).
- Recovery checklist (target: fix in < 2 hours without deep debugging).
