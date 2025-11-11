# EDF parser runbook (edf_v1)

- **URLs**: https://edf.fr/tarifs (public HTML, no auth).
- **Selectors**: configured via `parsers/config/edf.yaml` using `section#tariffs article` rows and data-* attributes for option, puissance, and prices.
- **Cadence**: EDF typically updates residential tariffs monthly; nightly ingest monitors SHA-256 changes and flips rows into `verifying` state until TRVE diff passes.
- **Known issues**:
  - `data-kwhhp` or `data-kwhhc` can disappear for BASE-only offers (treat as `null`).
  - HTML sometimes ships with comma decimal separators ? ensure normalisation before casting.
- **Recovery steps**:
  1. Grab freshest HTML/PDF and drop it under `tests/snapshots/edf/`.
  2. Update `edf.yaml` selectors if attributes changed.
  3. Regenerate expected JSON via `python -m ingest.pipeline edf tests/snapshots/edf/<file>.html --observed-at <ISO>`.
  4. Run `pytest` to validate schema + parser output before committing.
