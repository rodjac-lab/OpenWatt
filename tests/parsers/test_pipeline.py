from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ingest.pipeline import run_ingest

SNAPSHOT_DIR = Path(__file__).parent.parent / "snapshots" / "edf"


def test_yaml_parser_matches_expected_snapshot():
    html_path = SNAPSHOT_DIR / "edf_2025_02.html"
    expected_path = SNAPSHOT_DIR / "edf_2025_02_expected.json"
    observed_at = datetime(2025, 2, 12, 8, 0, 0, tzinfo=timezone.utc)
    rows = run_ingest("edf", html_path, observed_at=observed_at)
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert rows == expected
