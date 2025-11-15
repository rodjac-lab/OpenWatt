from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def detect_suppliers(config_dir: Path) -> list[str]:
    suppliers = []
    for path in config_dir.glob("*.yaml"):
        suppliers.append(path.stem)
    return sorted(suppliers)


def run_pipeline(supplier: str, observed_at: str | None) -> int:
    cmd = [sys.executable, "-m", "ingest.pipeline", supplier, "--fetch", "--persist"]
    if observed_at:
        cmd.extend(["--observed-at", observed_at])
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(output)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ingest.pipeline for all suppliers sequentially")
    parser.add_argument(
        "--suppliers",
        help="Comma-separated list of suppliers (default: all configs under parsers/config)",
    )
    parser.add_argument("--observed-at", help="Optional ISO timestamp override (e.g. 2025-02-15T00:00:00+00:00)")
    args = parser.parse_args()

    if args.suppliers:
        suppliers = [item.strip() for item in args.suppliers.split(",") if item.strip()]
    else:
        suppliers = detect_suppliers(Path("parsers/config"))

    if not suppliers:
        parser.error("No suppliers found. Provide --suppliers or add YAML files under parsers/config/")

    print(f"Running ingest pipeline for {len(suppliers)} suppliers...")
    failures: list[str] = []
    for supplier in suppliers:
        print(f"\n=== {supplier} ===")
        code = run_pipeline(supplier, args.observed_at)
        if code != 0:
            failures.append(supplier)

    if failures:
        print(f"\nCompleted with failures: {', '.join(failures)}")
        sys.exit(1)
    print("\nAll suppliers processed successfully.")


if __name__ == "__main__":
    main()
