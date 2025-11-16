from __future__ import annotations

from datetime import date, datetime, timezone

from pydantic import BaseModel, Field, HttpUrl

from api.app.models.enums import FreshnessStatus, Puissance, TariffOption


class TariffObservation(BaseModel):
    supplier: str = Field(..., description="Supplier name as published in the spec")
    option: TariffOption
    puissance_kva: Puissance
    price_kwh_ttc: float | None = Field(default=None)
    price_kwh_hp_ttc: float | None = Field(default=None)
    price_kwh_hc_ttc: float | None = Field(default=None)
    abo_month_ttc: float
    observed_at: datetime
    parser_version: str
    source_url: HttpUrl
    source_checksum: str = Field(..., min_length=64, max_length=64)
    data_status: FreshnessStatus = Field(
        ..., description="fresh/verifying/stale/broken per constitution"
    )
    last_verified: datetime | None = None


class TariffCollection(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    items: list[TariffObservation]


class TariffHistoryFilters(BaseModel):
    supplier: str | None = None
    option: TariffOption | None = None
    puissance_kva: Puissance | None = None
    since: date | None = None
    until: date | None = None


class TariffHistoryResponse(BaseModel):
    filters: TariffHistoryFilters
    items: list[TariffObservation]


class TrveDiffEntry(BaseModel):
    supplier: str
    option: TariffOption
    puissance_kva: Puissance
    delta_eur_per_mwh: float
    compared_at: datetime
    status: str = Field(..., description="ok|alert per TRVE guard")


class TrveDiffResponse(BaseModel):
    generated_at: datetime
    items: list[TrveDiffEntry]
