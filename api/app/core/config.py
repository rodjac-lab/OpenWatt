"""Application configuration derived from the Spec-Kit."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "OpenWatt API"
    api_v1_prefix: str = "/v1"
    default_timezone: str = "UTC"
    database_url: str = Field(
        "postgresql+asyncpg://openwatt:openwatt@localhost:5432/openwatt",
        env="OPENWATT_DATABASE_URL",
    )
    slack_webhook_url: str | None = Field(default=None, env="OPENWATT_SLACK_WEBHOOK")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
