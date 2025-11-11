# TotalEnergies parser runbook (totale_v1)

- **URL**: https://www.totalenergies.fr/offres-electricite
- **Selectors**: `section.tariffs article` rows with data-* attributes for option, puissance, abonnement, kwht.
- **Cadence**: updates roughly monthly; rely on nightly checksum + TRVE guard.
- **Notes**: TEMPO option currently simplified (single price field). Extend selectors when HP/HC become available.
- **Recovery**:
  1. Store latest HTML in `tests/snapshots/total/`.
  2. Update YAML if attributes change.
  3. Regenerate JSON expectation via `python -m ingest.pipeline totalenergies tests/snapshots/total/<file>.html --observed-at <ISO>`.
  4. Run `pytest tests/parsers -k total` before merge.
