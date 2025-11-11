from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from ingest.pipeline import run_ingest

SNAPSHOT_ROOT = Path(__file__).parent.parent / "snapshots"

CASES = [
    ("edf", "edf/edf_2025_02.html", "edf/edf_2025_02_expected.json"),
    ("engie", "engie/engie_2025_02.html", "engie/engie_2025_02_expected.json"),
    ("totalenergies", "total/total_2025_02.html", "total/total_2025_02_expected.json"),
]


@pytest.mark.parametrize("supplier,html_rel,expected_rel", CASES)
def test_yaml_parser_matches_expected_snapshot(supplier: str, html_rel: str, expected_rel: str):
    html_path = SNAPSHOT_ROOT / html_rel
    expected_path = SNAPSHOT_ROOT / expected_rel
    observed_at = datetime.fromisoformat("2025-02-12T08:00:00+00:00")
    rows = run_ingest(supplier, html_path, observed_at=observed_at)
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert rows == expected
