from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from parsers.core import parser as yaml_parser


def run_ingest(supplier: str, html_input: Path, observed_at: datetime | None = None) -> list[dict[str, Any]]:
    """Parse a supplier HTML artifact into tariff payloads."""
    timestamp = observed_at or datetime.now(timezone.utc)
    return yaml_parser.parse_file(supplier, html_input, observed_at=timestamp)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Spec-Kit ingest pipeline")
    parser.add_argument("supplier", help="Supplier code, e.g. edf")
    parser.add_argument("html", help="Path to the HTML artifact to parse")
    parser.add_argument("--observed-at", help="ISO timestamp override")
    args = parser.parse_args()

    html_path = Path(args.html)
    observed = datetime.fromisoformat(args.observed_at) if args.observed_at else None
    rows = run_ingest(args.supplier, html_path, observed_at=observed)
    import json

    print(json.dumps(rows, indent=2, ensure_ascii=False))
