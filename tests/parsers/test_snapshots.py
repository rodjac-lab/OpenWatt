from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

TARIFF_SCHEMA = json.loads(Path("specs/data-contracts/tariff.schema.json").read_text(encoding="utf-8"))
SNAPSHOT_DIR = Path(__file__).parent.parent / "snapshots"

SNAPSHOT_CASES = [
    ("edf", "edf_2025_02.html", "edf_2025_02_expected.json"),
    ("engie", "engie_2025_02.html", "engie_2025_02_expected.json"),
    ("total", "total_2025_02.html", "total_2025_02_expected.json"),
]


@pytest.mark.parametrize("supplier,html_name,_", SNAPSHOT_CASES)
def test_snapshot_artifacts_exist(supplier: str, html_name: str, _: str):
    html_file = SNAPSHOT_DIR / supplier / html_name
    assert html_file.exists(), f"HTML snapshot missing for {supplier}"
    text = html_file.read_text(encoding="utf-8")
    assert "tarifs" in text.lower()


@pytest.mark.parametrize("supplier,_,expected_name", SNAPSHOT_CASES)
def test_snapshot_expected_payload_matches_schema(supplier: str, _: str, expected_name: str):
    expected_path = SNAPSHOT_DIR / supplier / expected_name
    payload = json.loads(expected_path.read_text(encoding="utf-8"))
    assert payload, f"Aucune donnée attendue pour {supplier}"
    validator = jsonschema.Draft7Validator(TARIFF_SCHEMA)
    for row in payload:
        validator.validate(row)
