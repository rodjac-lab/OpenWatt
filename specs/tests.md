---
id: elec-tariffs-fr.tests
version: 0.1.0
status: draft
last_updated: 2025-11-11
---

# ✅ Scénarios d'acceptance (Gherkin)

## Parser EDF v1
```
Feature: Extraction EDF
  Scenario: Snapshot HTML février 2025
    Given un fichier HTML "edf_2025_02.html"
    When j'exécute le parseur "edf_v1"
    Then j'obtiens des lignes BASE et HPHC pour puissances [3..36] kVA
    And chaque ligne respecte "tariff.schema.json"
    And un INSERT-only avec observed_at=now()
```

## API /v1/tariffs
```
Feature: Derniers tarifs
  Scenario: Liste fresh par défaut
    Given la base contient des observations < 7 jours et > 14 jours
    When j'appelle GET /v1/tariffs
    Then seules les observations fresh sont retournées
    And le champ last_verified est présent
    And les observations en validation exposent data_status = verifying
```
