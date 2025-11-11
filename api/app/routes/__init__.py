"""Route modules exposed for FastAPI wiring."""

from api.app.routes import guards, health, tariffs

__all__ = ["guards", "health", "tariffs"]
