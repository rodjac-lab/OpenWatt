from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class AdminRunItem(BaseModel):
    supplier: str
    status: str = Field(description="ok|nok")
    message: str
    observed_at: datetime | None = None


class AdminRunsResponse(BaseModel):
    generated_at: datetime
    items: list[AdminRunItem]


class OverrideCreatePayload(BaseModel):
    supplier: str
    url: HttpUrl
    observed_at: datetime | None = None


class OverrideEntry(BaseModel):
    id: int
    supplier: str
    url: HttpUrl
    observed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class OverrideHistoryResponse(BaseModel):
    items: list[OverrideEntry]
