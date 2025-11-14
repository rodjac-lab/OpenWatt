from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path

import pytest

from parsers.core.config import load_supplier_config
from parsers.core import parser as core_parser

SNAPSHOT_ROOT = Path(__file__).parent.parent / "snapshots"

CASES = [
    ("edf", "edf/edf_tarif_bleu.pdf", "edf/edf_2025_02_expected.json"),
    ("engie", "engie/engie_reference.pdf", "engie/engie_2025_02_expected.json"),
    ("total_heures_eco", "total/total_heures_eco.pdf", "total/total_heures_eco_expected.json"),
    ("total_standard_fixe", "total/total_standard_fixe.pdf", "total/total_standard_fixe_expected.json"),
    ("mint_indexe_trv", "mint/mint_indexe_trv.pdf", "mint/mint_indexe_trv_expected.json"),
    ("mint_classic_green", "mint/mint_classic_green.pdf", "mint/mint_classic_green_expected.json"),
    ("mint_smart_green", "mint/mint_smart_green.pdf", "mint/mint_smart_green_expected.json"),
]


def run_snapshot(supplier: str, artifact_path: Path, observed_at: datetime):
    config = load_supplier_config(supplier)
    checksum = sha256(artifact_path.read_bytes()).hexdigest()
    return core_parser.parse_file(
        config,
        artifact_path,
        observed_at=observed_at,
        source_checksum=checksum,
    )


@pytest.mark.parametrize("supplier,artifact_rel,expected_rel", CASES)
def test_parser_matches_expected_snapshot(supplier: str, artifact_rel: str, expected_rel: str):
    artifact_path = SNAPSHOT_ROOT / artifact_rel
    expected_path = SNAPSHOT_ROOT / expected_rel
    observed_at = datetime.fromisoformat("2025-02-12T08:00:00+00:00")
    rows = run_snapshot(supplier, artifact_path, observed_at)
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert rows == expected
