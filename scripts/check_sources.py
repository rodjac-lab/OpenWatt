from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml


class SourceChecker:
    def __init__(self, timeout: int = 10, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        # Set a realistic User-Agent to avoid bot detection
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def check_url(self, supplier: str, url: str) -> dict[str, str | int | float | None]:
        """Check if a URL is accessible via HEAD request with retries."""
        attempts = 0
        last_error: str | None = None

        while attempts <= self.max_retries:
            try:
                start_time = time.time()
                response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
                response_time_ms = int((time.time() - start_time) * 1000)

                timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
                result = {
                    "timestamp": timestamp,
                    "supplier": supplier,
                    "url": url,
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "error": None,
                }

                if response.status_code >= 400:
                    result["error"] = "ERROR"

                return result

            except requests.exceptions.Timeout:
                last_error = "TIMEOUT"
                attempts += 1
                if attempts <= self.max_retries:
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                last_error = f"REQUEST_ERROR: {str(e)}"
                attempts += 1
                if attempts <= self.max_retries:
                    time.sleep(1)

        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return {
            "timestamp": timestamp,
            "supplier": supplier,
            "url": url,
            "status_code": None,
            "response_time_ms": None,
            "error": last_error,
        }

    def load_config(self, config_path: Path) -> dict[str, Any]:
        """Load YAML configuration file."""
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def check_all_sources(self, config_dir: Path, supplier_filter: str | None = None) -> list[dict]:
        """Check all source URLs from config directory."""
        results = []

        for config_path in sorted(config_dir.glob("*.yaml")):
            supplier_slug = config_path.stem

            if supplier_filter and supplier_slug != supplier_filter:
                continue

            config = self.load_config(config_path)
            supplier = config.get("supplier", supplier_slug)
            source_url = config.get("source", {}).get("url")

            if not source_url:
                print(
                    f"WARNING: No source URL found in {config_path.name}",
                    file=sys.stderr,
                )
                continue

            result = self.check_url(supplier, source_url)
            results.append(result)
            self._print_result(result)

        return results

    def _print_result(self, result: dict[str, Any]) -> None:
        """Print result in standardized format."""
        timestamp = result["timestamp"]
        supplier = result["supplier"]
        url = result["url"]
        status = result["status_code"]
        response_time = result["response_time_ms"]
        error = result["error"]

        status_str = str(status) if status else "N/A"
        time_str = f"{response_time}ms" if response_time else "N/A"

        output_parts = [timestamp, supplier, url, status_str, time_str]

        if error:
            output_parts.append(error)

        print(" | ".join(output_parts))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check availability of source URLs from parser configs"
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("parsers/config"),
        help="Directory containing YAML config files (default: parsers/config)",
    )
    parser.add_argument(
        "--supplier",
        help="Check only this specific supplier (default: all)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum number of retries on failure (default: 2)",
    )
    args = parser.parse_args()

    if not args.config_dir.exists():
        print(f"ERROR: Config directory not found: {args.config_dir}", file=sys.stderr)
        sys.exit(1)

    checker = SourceChecker(timeout=args.timeout, max_retries=args.max_retries)
    results = checker.check_all_sources(args.config_dir, args.supplier)

    if not results:
        print("WARNING: No sources checked", file=sys.stderr)
        sys.exit(1)

    failures = [r for r in results if r.get("error") or (r.get("status_code") or 0) >= 400]

    if failures:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
