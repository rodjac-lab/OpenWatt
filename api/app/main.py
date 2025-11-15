"""FastAPI entrypoint bootstrapped from the OpenWatt Spec-Kit."""
from __future__ import annotations

from fastapi import FastAPI

from api.app.core.config import settings
from api.app.routes import admin, guards, health, tariffs

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
)

app.include_router(health.router)
app.include_router(tariffs.router)
app.include_router(guards.router)
app.include_router(admin.router)
