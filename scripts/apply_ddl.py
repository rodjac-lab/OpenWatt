from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_psql(database_url: str, ddl_path: Path) -> None:
    psql = shutil.which("psql")
    if not psql:
        sys.exit("psql executable not found. Install PostgreSQL client tools or run inside the docker container.")

    cmd = [psql, database_url, "-f", str(ddl_path)]
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply db/ddl.sql to the configured PostgreSQL instance")
    parser.add_argument("--ddl", default="db/ddl.sql", help="Path to the DDL file (default: db/ddl.sql)")
    parser.add_argument(
        "--database-url",
        default=os.getenv("OPENWATT_DATABASE_URL"),
        help="Database URL (default: env OPENWATT_DATABASE_URL)",
    )
    args = parser.parse_args()

    if not args.database_url:
        sys.exit("Set --database-url or OPENWATT_DATABASE_URL before running this command")

    ddl_path = Path(args.ddl).resolve()
    if not ddl_path.exists():
        sys.exit(f"DDL file not found: {ddl_path}")

    run_psql(args.database_url, ddl_path)
    print(f"Applied {ddl_path} to {args.database_url}")


if __name__ == "__main__":
    main()
