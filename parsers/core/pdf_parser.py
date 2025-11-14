from __future__ import annotations

from datetime import datetime
import re
from pathlib import Path
from typing import Any, Sequence

import pdfplumber

from api.app.models.enums import FreshnessStatus, TariffOption
from parsers.core.config import PdfSliceConfig, PdfTableConfig, SupplierConfig


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def parse_float(value: Any) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    text = text.replace("\u20ac", "").replace("cts", "").replace("%", "")
    text = text.replace(",", ".")
    text = re.sub(r"[^0-9.+-]", "", text)
    if not text or text in {"-", "--"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int_value(value: Any) -> int | None:
    text = normalize_text(value)
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def resolve_row(row: Sequence[str], use_clean: bool) -> list[str]:
    normalized = [normalize_text(cell) for cell in row]
    if use_clean:
        normalized = [cell for cell in normalized if cell]
    return normalized


def parse_pdf(
    config: SupplierConfig,
    artifact_path: Path,
    *,
    observed_at: datetime,
    source_checksum: str,
) -> list[dict[str, Any]]:
    if not config.pdf:
        raise ValueError("PDF parsing requested but no pdf configuration provided.")

    observations: list[dict[str, Any]] = []

    with pdfplumber.open(str(artifact_path)) as pdf:
        for table_spec in config.pdf.tables:
            page = pdf.pages[table_spec.page]
            tables = page.extract_tables()
            if table_spec.table_index >= len(tables):
                raise IndexError(
                    f"Table index {table_spec.table_index} not found on page {table_spec.page}"
                )
            table = tables[table_spec.table_index]
            data_rows = table[table_spec.skip_rows :]
            for raw_row in data_rows:
                for slice_spec in table_spec.slices:
                    use_clean = (
                        slice_spec.use_clean_rows
                        if slice_spec.use_clean_rows is not None
                        else table_spec.use_clean_rows
                    )
                    row = resolve_row(raw_row, use_clean)
                    record = build_record_from_row(
                        config,
                        row,
                        slice_spec,
                        observed_at=observed_at,
                        source_checksum=source_checksum,
                    )
                    if record:
                        observations.append(record)

    return observations


def build_record_from_row(
    config: SupplierConfig,
    row: list[str],
    slice_spec: PdfSliceConfig,
    *,
    observed_at: datetime,
    source_checksum: str,
) -> dict[str, Any] | None:
    if slice_spec.puissance_column >= len(row):
        return None
    puissance = parse_int_value(row[slice_spec.puissance_column])
    if puissance is None:
        return None

    observed_iso = observed_at.isoformat().replace("+00:00", "Z")
    payload: dict[str, Any] = {
        "supplier": config.supplier,
        "parser_version": config.parser_version,
        "source_url": str(config.source.url),
        "source_checksum": source_checksum,
        "observed_at": observed_iso,
        "data_status": FreshnessStatus.FRESH.value,
    }

    for field, column_index in slice_spec.columns.items():
        if column_index >= len(row):
            return None
        value = parse_float(row[column_index])
        payload[field] = value

    for field in slice_spec.columns.keys():
        if payload.get(field) is None:
            return None

    payload["puissance_kva"] = puissance
    try:
        payload["option"] = TariffOption(slice_spec.option.upper()).value
    except ValueError:
        payload["option"] = slice_spec.option

    return payload
