# Engie parser runbook (engie_v1)

- **URLs**: https://particuliers.engie.fr/tarifs (HTML snippet similar to EDF tables).
- **Selectors**: see `parsers/config/engie.yaml` (rows = `section#tariffs article`, values in `data-*`).
- **Cadence**: Engie publishes updates roughly monthly; nightly digest monitors checksums and goes `verifying` until TRVE diff clears.
- **Known quirks**:
  - BASE option exposes `data-kwht`; HPHC exposes both `data-kwhhp` and `data-kwhhc`.
  - Some power tiers disappear temporarily; parser should handle missing rows gracefully.
- **Recovery steps**:
  1. Save offending HTML/PDF into `tests/snapshots/engie/`.
  2. Adjust YAML selectors if attributes changed.
  3. Regenerate JSON expectations via `python -m ingest.pipeline engie tests/snapshots/engie/<file>.html --observed-at <ISO>`.
  4. Run `pytest tests/parsers -k engie` to confirm schema + parser output before merging.
