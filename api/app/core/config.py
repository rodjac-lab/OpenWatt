"""Application configuration derived from the Spec-Kit."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "OpenWatt API"
    api_v1_prefix: str = "/v1"
    default_timezone: str = "UTC"
    database_url: str = Field("postgresql+asyncpg://openwatt:openwatt@localhost:5432/openwatt")
    slack_webhook_url: str | None = None
    enable_db: bool = Field(
        default=False,
        description="Set to true to use the PostgreSQL persistence layer instead of the in-memory seed.",
    )

    model_config = SettingsConfigDict(
        env_prefix="OPENWATT_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
