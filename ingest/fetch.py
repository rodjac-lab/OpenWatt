from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter, Retry

from parsers.core.config import SupplierConfig
from api.app.core.logging import get_logger

logger = get_logger(__name__)


DEFAULT_RAW_DIR = Path("artifacts/raw")
DEFAULT_TIMEOUT = 60
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OpenWattBot/0.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def _http_session() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_supplier_artifact(
    config: SupplierConfig, raw_dir: Path | None = None, timeout: int = DEFAULT_TIMEOUT
) -> tuple[Path, str]:
    """Download the supplier source (HTML/PDF) and store it locally."""
    raw_dir = raw_dir or DEFAULT_RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    session = _http_session()
    logger.info("fetch_started", url=str(config.source.url))
    try:
        response = session.get(str(config.source.url), timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("fetch_failed", url=str(config.source.url), error=str(e))
        raise

    content = response.content
    checksum = sha256(content).hexdigest()

    suffix = ".html" if config.source.format == "html" else ".pdf"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_path = raw_dir / f"{config.supplier.lower()}_{timestamp}{suffix}"
    file_path.write_bytes(content)
    return file_path, checksum
