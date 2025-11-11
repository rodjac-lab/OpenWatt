from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi.openapi.utils import get_openapi

from api.app.main import app


def export_openapi(path: Path) -> None:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"OpenAPI schema written to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI schema to disk")
    parser.add_argument("--out", default="specs/openapi.generated.json", help="Output file path")
    args = parser.parse_args()
    export_openapi(Path(args.out))
