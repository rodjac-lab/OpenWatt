from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.app.core.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        pool_class = None
        if "test" in settings.database_url or "sqlite" in settings.database_url:
            from sqlalchemy.pool import NullPool
            pool_class = NullPool
        
        _engine = create_async_engine(
            settings.database_url, 
            echo=False, 
            future=True,
            poolclass=pool_class
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncSession:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
