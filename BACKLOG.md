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

### Add TRVE (Regulated Tariff) as Reference Baseline
**Priority**: High
**Status**: To Do
**Discovered**: 2025-11-24

**Context**:
- TRVE (Tarif Réglementé de Vente d'Électricité) is the market reference in France
- All suppliers advertise by comparing to TRVE ("X% moins cher que le tarif réglementé")
- Users want to compare market offers both against each other AND against TRVE
- TRVE is not an "option" (like BASE/HPHC/TEMPO) but a tariff category/reference

**Business Value**:
- Enable accurate comparison: "Is this offer really cheaper than TRVE?"
- Highlight best deals vs. regulated reference
- Match how suppliers market their offers
- Help users understand savings vs. staying with EDF

**Problem**:
- Currently EDF Tarif Bleu (TRVE) is mixed with market offers in the same list
- No visual distinction or special treatment for TRVE
- Cannot easily answer "How much cheaper is this vs. TRVE?"
- Missing a key comparison metric that users expect

**Two Possible Approaches**:

**Option A: Flag EDF Tarif Bleu as TRVE**
- Add `is_regulated: boolean` field to schema
- Mark EDF tariffs as regulated in parser config
- Visual badge in UI: "📋 Tarif Réglementé"
- Show savings vs. TRVE in podium/table

**Option B: Separate TRVE supplier (from CRE data)**
- Create dedicated "TRVE" supplier entry
- Source data directly from CRE (official regulator)
- Keep EDF separate as market supplier
- More accurate, official source
- URL: https://www.cre.fr/pages/tarifs-reglementes-de-vente

**Recommended: Option B**
- More accurate (official CRE data)
- Clear separation: TRVE vs. all market offers (including EDF)
- Future-proof if EDF loses TRVE monopoly
- Easier to highlight as special reference

**Implementation Steps**:
1. Create parser for CRE TRVE data (BASE, HPHC, TEMPO)
2. Add `is_regulated: boolean` field to database schema
3. Add database migration
4. Update API to include TRVE flag
5. Frontend: Visual treatment for TRVE tariffs
   - Badge "📋 Tarif Réglementé"
   - Highlight row with distinct background
   - Always show TRVE in comparisons
6. Add "vs. TRVE" comparison in podium/table
   - Show % savings for each offer
   - "120 € moins cher que le TRVE" or "45 € plus cher"
7. Optional filter: "Montrer uniquement offres < TRVE"

**Related Files**:
- `api/app/models/tariff.py` (database model)
- `api/app/schemas/tariff.py` (API schema)
- `parsers/config/trve.yaml` (new CRE parser)
- `ui/components/TariffList.tsx` (UI updates)
- `ui/components/FreshnessBadge.tsx` (add TRVE badge)

**Use Cases**:
- "Show me all offers cheaper than TRVE"
- "How much would I save vs. staying with regulated tariff?"
- "Is Engie really 15% cheaper than TRVE?"
- Visual highlight: market offers that beat TRVE reference

---

### Frontend: TRVE Comparison Features
**Priority**: High
**Status**: To Do
**Depends on**: "Add TRVE (Regulated Tariff) as Reference Baseline"

**Context**:
- Once TRVE data is available in the database, the frontend needs to exploit it
- Users expect to see how market offers compare to the regulated reference
- Visual treatment should make TRVE stand out as the baseline

**Features to Implement**:

1. **Visual Badge for TRVE Tariffs**
   - Add "📋 Tarif Réglementé" badge next to TRVE supplier name
   - Distinct background color for TRVE rows (light blue tint)
   - Always keep TRVE visible in filtered results

2. **Savings vs. TRVE in Podium**
   - Add comparison line below each podium card
   - Show absolute savings: "120 € moins cher que le TRVE"
   - Show percentage: "12% moins cher que le TRVE"
   - Color code: Green if cheaper, Red if more expensive

3. **TRVE Comparison Column in Table**
   - New column: "vs. TRVE"
   - Show difference in €/year
   - Show percentage difference
   - Sort by this column by default (best savings first)

4. **Filter: "Only offers cheaper than TRVE"**
   - New checkbox filter: "Afficher uniquement les offres < TRVE"
   - Automatically highlights offers that beat the regulated tariff
   - Update count: "X offres moins chères que le TRVE"

5. **TRVE Reference Line**
   - Always pin TRVE tariff at top or bottom of table
   - Sticky row that stays visible during scroll
   - Different styling (border, background) to distinguish it

6. **Smart Matching**
   - Compare like-for-like: BASE vs BASE, HPHC vs HPHC
   - Match by puissance (6kVA vs 6kVA)
   - Show "N/A" if no matching TRVE exists

**UI Mockup Ideas**:
```
┌─────────────────────────────────────────────┐
│ 🥇 1er - Engie Elec Référence              │
│ BASE • 6 kVA                                │
│ 976 €/an                                    │
│ ✅ 120 € moins cher que le TRVE (11%)      │
└─────────────────────────────────────────────┘
```

**Table Column Example**:
```
Fournisseur | Option | Puissance | Coût annuel | vs. TRVE        | Fraîcheur
─────────────────────────────────────────────────────────────────────────────
TRVE 📋     | BASE   | 6 kVA     | 1 096 €     | Référence       | ✓ Fresh
Engie       | BASE   | 6 kVA     | 976 €       | -120 € (-11%)   | ✓ Fresh
TotalEnerg. | BASE   | 6 kVA     | 1 050 €     | -46 € (-4%)     | ✓ Fresh
EDF Vert    | BASE   | 6 kVA     | 1 120 €     | +24 € (+2%)     | ✓ Fresh
```

**Related Files**:
- `ui/components/TariffList.tsx` (main comparison logic)
- `ui/components/FreshnessBadge.tsx` (add TRVE badge)
- `ui/app/globals.css` (TRVE styling)

**Success Criteria**:
- Users can immediately identify TRVE tariffs
- Savings vs. TRVE are clearly visible
- Can filter to see only offers cheaper than TRVE
- Like-for-like comparisons (matching option & puissance)

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
