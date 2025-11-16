from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from api.app.models.enums import FreshnessStatus, TariffOption
from parsers.core.config import SupplierConfig
from parsers.core import pdf_parser

NUMERIC_FIELDS = {"abo_month_ttc", "price_kwh_ttc", "price_kwh_hp_ttc", "price_kwh_hc_ttc"}
INT_FIELDS = {"puissance_kva"}


class YamlTariffParser:
    def __init__(self, config: SupplierConfig):
        self.config = config

    def parse_html(
        self,
        html: str,
        *,
        observed_at: datetime,
        source_checksum: str,
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select(self.config.selectors.rows)
        parsed: list[dict[str, Any]] = []
        observed_iso = observed_at.isoformat().replace("+00:00", "Z")
        for row in rows:
            payload: dict[str, Any] = {
                "supplier": self.config.supplier,
                "parser_version": self.config.parser_version,
                "source_url": str(self.config.source.url),
                "source_checksum": source_checksum,
                "observed_at": observed_iso,
                "data_status": FreshnessStatus.FRESH.value,
            }
            for field, expr in self.config.selectors.fields.items():
                raw = self._extract_value(row, expr)
                payload[field] = self._cast_field(field, raw)
            option_value = (payload.get("option") or row.get("data-option", "BASE")).upper()
            try:
                payload["option"] = TariffOption(option_value).value
            except ValueError:
                payload["option"] = option_value
            parsed.append(payload)
        return parsed

    @staticmethod
    def _extract_value(node, expr: str) -> Any:
        if expr.startswith("@"):
            return node.get(expr[1:])
        target = node.select_one(expr)
        return target.text.strip() if target else None

    @staticmethod
    def _cast_field(field: str, value: Any) -> Any:
        if value in (None, ""):
            return None
        if field in INT_FIELDS:
            return int(value)
        if field in NUMERIC_FIELDS:
            return float(value)
        return value


def parse_file(
    config: SupplierConfig,
    artifact_path: Path,
    *,
    observed_at: datetime,
    source_checksum: str,
) -> list[dict[str, Any]]:
    if config.source.format == "pdf":
        return pdf_parser.parse_pdf(
            config, artifact_path, observed_at=observed_at, source_checksum=source_checksum
        )
    parser = YamlTariffParser(config)
    html = artifact_path.read_text(encoding="utf-8")
    return parser.parse_html(html, observed_at=observed_at, source_checksum=source_checksum)
