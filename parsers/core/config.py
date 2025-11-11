from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, HttpUrl


class SourceConfig(BaseModel):
    url: HttpUrl
    format: Literal["html"] = "html"


class SelectorConfig(BaseModel):
    rows: str = Field(..., description="CSS selector returning each tariff row")
    fields: dict[str, str] = Field(default_factory=dict)


class SupplierConfig(BaseModel):
    supplier: str
    parser_version: str
    source: SourceConfig
    selectors: SelectorConfig


def load_supplier_config(supplier: str) -> SupplierConfig:
    config_path = Path("parsers/config") / f"{supplier.lower()}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"No YAML config found for supplier '{supplier}' at {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return SupplierConfig.model_validate(data)
