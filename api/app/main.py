"""FastAPI entrypoint bootstrapped from the OpenWatt Spec-Kit."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from api.app.core.config import settings
from api.app.core.logging import configure_logging, get_logger
from api.app.core.sentry import configure_sentry
from api.app.middleware import RequestIDMiddleware
from api.app.routes import admin, guards, health, tariffs

# Configure structured logging and Sentry on startup
configure_logging()
configure_sentry()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
)

# Initialize Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Middleware order matters: RequestID first, then CORS
app.add_middleware(RequestIDMiddleware)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Log application startup and expose metrics."""
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    logger.info("application_started", version="0.1.0", metrics_enabled=True)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Log application shutdown."""
    logger.info("application_shutdown")


app.include_router(health.router)
app.include_router(tariffs.router)
app.include_router(guards.router)
app.include_router(admin.router)
