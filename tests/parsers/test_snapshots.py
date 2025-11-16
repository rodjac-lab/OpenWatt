from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

TARIFF_SCHEMA = json.loads(
    Path("specs/data-contracts/tariff.schema.json").read_text(encoding="utf-8")
)
SNAPSHOT_DIR = Path(__file__).parent.parent / "snapshots"

SNAPSHOT_CASES = [
    ("edf", "edf_tarif_bleu.pdf", "edf_2025_02_expected.json"),
    ("engie", "engie_reference.pdf", "engie_2025_02_expected.json"),
    ("total", "total_heures_eco.pdf", "total_heures_eco_expected.json"),
    ("total", "total_standard_fixe.pdf", "total_standard_fixe_expected.json"),
    ("mint", "mint_indexe_trv.pdf", "mint_indexe_trv_expected.json"),
    ("mint", "mint_classic_green.pdf", "mint_classic_green_expected.json"),
    ("mint", "mint_smart_green.pdf", "mint_smart_green_expected.json"),
]


@pytest.mark.parametrize("supplier,artifact_name,_", SNAPSHOT_CASES)
def test_snapshot_artifacts_exist(supplier: str, artifact_name: str, _: str):
    artifact_file = SNAPSHOT_DIR / supplier / artifact_name
    assert artifact_file.exists(), f"Snapshot artifact missing for {supplier}"
    assert artifact_file.stat().st_size > 1000


@pytest.mark.parametrize("supplier,_,expected_name", SNAPSHOT_CASES)
def test_snapshot_expected_payload_matches_schema(supplier: str, _: str, expected_name: str):
    expected_path = SNAPSHOT_DIR / supplier / expected_name
    payload = json.loads(expected_path.read_text(encoding="utf-8"))
    assert payload, f"Aucune donnée attendue pour {supplier}"
    validator = jsonschema.Draft7Validator(TARIFF_SCHEMA)
    for row in payload:
        validator.validate(row)
