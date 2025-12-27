from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, HttpUrl


class SourceConfig(BaseModel):
    url: HttpUrl
    format: Literal["html", "pdf"] = "html"


class SelectorConfig(BaseModel):
    rows: str = Field(..., description="CSS selector returning each tariff row")
    fields: dict[str, str] = Field(default_factory=dict)


class PdfSliceConfig(BaseModel):
    option: str
    puissance_column: int
    columns: dict[str, int]
    notes: Optional[str] = None
    use_clean_rows: Optional[bool] = None
    puissance_values: Optional[list[int]] = None
    price_unit: Optional[Literal["EUR", "cts"]] = "EUR"  # "cts" for centimes, "EUR" for euros


class PdfTableConfig(BaseModel):
    page: int = 0
    table_index: int = 0
    skip_rows: int = 0
    use_clean_rows: bool = False
    slices: list[PdfSliceConfig]


class PdfConfig(BaseModel):
    tables: list[PdfTableConfig]


class SupplierConfig(BaseModel):
    supplier: str
    parser_version: str
    source: SourceConfig
    selectors: SelectorConfig | None = None
    pdf: PdfConfig | None = None

    @property
    def is_pdf(self) -> bool:
        return self.source.format == "pdf"

    @property
    def is_html(self) -> bool:
        return self.source.format == "html"

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        instance = super().model_validate(obj, *args, **kwargs)
        if instance.is_html and instance.selectors is None:
            raise ValueError("HTML sources require 'selectors' configuration")
        if instance.is_pdf and instance.pdf is None:
            raise ValueError("PDF sources require 'pdf' configuration")
        return instance


def load_supplier_config(supplier: str) -> SupplierConfig:
    config_path = Path("parsers/config") / f"{supplier.lower()}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"No YAML config found for supplier '{supplier}' at {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return SupplierConfig.model_validate(data)
