from __future__ import annotations

import json
from pathlib import Path

import jsonschema

TARIFF_SCHEMA = json.loads(Path("specs/data-contracts/tariff.schema.json").read_text(encoding="utf-8"))
SNAPSHOT_DIR = Path(__file__).parent.parent / "snapshots"


def test_snapshot_artifacts_exist():
    html_file = SNAPSHOT_DIR / "edf" / "edf_2025_02.html"
    assert html_file.exists(), "HTML snapshot missing"
    text = html_file.read_text(encoding="utf-8")
    assert "tarifs" in text.lower()


def test_snapshot_expected_payload_matches_schema():
    expected_path = SNAPSHOT_DIR / "edf" / "edf_2025_02_expected.json"
    payload = json.loads(expected_path.read_text(encoding="utf-8"))
    assert len(payload) >= 2, "Spec requires BASE et HPHC"
    validator = jsonschema.Draft7Validator(TARIFF_SCHEMA)
    for row in payload:
        validator.validate(row)
