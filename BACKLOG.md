# OpenWatt Backlog

## Backend / Ingestion Issues

### EDF Parser: Price values 100x too high
**Priority**: High
**Status**: To Do
**Discovered**: 2025-11-24

**Problem**:
- EDF tariff prices are stored as 100x their actual value
- Database shows: `19.52 €/kWh` (should be `0.1952 €/kWh`)
- The PDF displays prices in centimes (c€/kWh): "19,52 c€"
- Parser reads the numeric value without converting from centimes to euros

**Impact**:
- Annual costs for EDF are massively inflated (234,381 € instead of ~976 €)
- EDF tariffs appear extremely expensive in comparisons

**Root Cause**:
- Located in: `parsers/config/edf.yaml`
- Parser version: `edf_pdf_v1`
- Source: https://particulier.edf.fr/content/dam/2-Actifs/Documents/Offres/Grille_prix_Tarif_Bleu.pdf

**Affected Data**:
- All EDF BASE tariffs: `price_kwh_ttc` = 19.52 (should be 0.1952)
- All EDF HPHC tariffs:
  - `price_kwh_hp_ttc` = 20.81 (should be 0.2081)
  - `price_kwh_hc_ttc` = 16.35 (should be 0.1635)

**Solution**:
1. Update parser to detect and convert centimes to euros (divide by 100)
2. Re-run ingestion job for EDF data
3. Verify corrected values in database
4. Add test case to prevent regression

**Related Files**:
- `parsers/config/edf.yaml`
- `artifacts/parsed/edf_20250215T000000Z.json`
- `tests/snapshots/edf/edf_2025_02_expected.json`

---

## Frontend Improvements

### CORS Configuration
**Priority**: Medium
**Status**: To Do

**Problem**:
- CORS currently set to wildcard `["*"]` for development
- Security risk if deployed to production

**Solution**:
- Implement environment-based CORS configuration
- Create `.env.development` and `.env.production` files
- Update `api/app/main.py` to use environment variables
- Document in deployment guide

**Timeline**: Before production deployment

---

## Completed

### ✅ React Re-rendering Bug in Tariff Calculations
**Completed**: 2025-11-24

Fixed issue where annual costs stopped updating after changing consumption profiles multiple times.

### ✅ Table Layout Improvements
**Completed**: 2025-11-24

- Increased max-width to 1000px
- Split complex price column into separate columns
- Added zebra striping and hover effects
- Improved header formatting
- Right-aligned numeric columns
