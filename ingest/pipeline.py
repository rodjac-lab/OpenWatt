from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingest.fetch import fetch_supplier_artifact
from parsers.core import parser as yaml_parser
from parsers.core.config import load_supplier_config

DEFAULT_PARSED_DIR = Path("artifacts/parsed")


def run_ingest(supplier: str, html_input: Path, observed_at: datetime | None = None) -> list[dict[str, Any]]:
    """Parse a supplier artifact into tariff payloads."""
    timestamp = observed_at or datetime.now(timezone.utc)
    return yaml_parser.parse_file(supplier, html_input, observed_at=timestamp)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run Spec-Kit ingest pipeline")
    parser.add_argument("supplier", help="Supplier code, e.g. edf")
    parser.add_argument("--html", help="Path to the HTML/PDF artifact to parse")
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Download the source defined in parsers/config/<supplier>.yaml before parsing",
    )
    parser.add_argument("--observed-at", help="ISO timestamp override (default: now UTC)")
    parser.add_argument(
        "--output",
        help="Where to write the parsed JSON (default: artifacts/parsed/<supplier>_<timestamp>.json)",
    )
    parser.add_argument(
        "--raw-dir",
        help="Directory to store fetched raw artifacts (default: artifacts/raw)",
    )
    args = parser.parse_args()

    observed = datetime.fromisoformat(args.observed_at) if args.observed_at else datetime.now(timezone.utc)

    if args.fetch:
        config = load_supplier_config(args.supplier)
        raw_path, checksum = fetch_supplier_artifact(
            config, raw_dir=Path(args.raw_dir) if args.raw_dir else None
        )
        html_path = raw_path
        print(f"Fetched {config.source.url} -> {raw_path} (sha256={checksum})")
    else:
        if not args.html:
            parser.error("Provide --html path or use --fetch to download the latest artifact")
        html_path = Path(args.html)
        if not html_path.exists():
            parser.error(f"Artifact not found: {html_path}")

    rows = run_ingest(args.supplier, html_path, observed_at=observed)

    if args.output:
        output_path = Path(args.output)
    else:
        DEFAULT_PARSED_DIR.mkdir(parents=True, exist_ok=True)
        safe_supplier = args.supplier.lower()
        output_path = DEFAULT_PARSED_DIR / f"{safe_supplier}_{observed.strftime('%Y%m%dT%H%M%SZ')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote parsed payload to {output_path}")
