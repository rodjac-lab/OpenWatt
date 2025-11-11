from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Tuple

import requests

from parsers.core.config import SupplierConfig

DEFAULT_RAW_DIR = Path("artifacts/raw")


def fetch_supplier_artifact(config: SupplierConfig, raw_dir: Path | None = None) -> tuple[Path, str]:
    """Download the supplier source (HTML/PDF) and store it locally."""
    raw_dir = raw_dir or DEFAULT_RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(str(config.source.url), timeout=30)
    response.raise_for_status()
    content = response.content
    checksum = sha256(content).hexdigest()

    suffix = ".html" if config.source.format == "html" else ".pdf"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_path = raw_dir / f"{config.supplier.lower()}_{timestamp}{suffix}"
    file_path.write_bytes(content)
    return file_path, checksum
