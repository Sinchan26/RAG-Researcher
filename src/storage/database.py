import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.core.config.settings import Settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, settings: Settings) -> None:
        self.timeout = settings.database_timeout_seconds
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        if settings.database_url is not None:
            self.engine = create_async_engine(
                settings.database_url.get_secret_value(), pool_pre_ping=True,
                connect_args={"timeout": self.timeout},
            )
            self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self.session_factory is None:
            raise RuntimeError("Database is not configured")
        async with self.session_factory() as session:
            yield session

    async def is_ready(self) -> bool:
        if self.engine is None:
            return False
        try:
            async with asyncio.timeout(self.timeout):
                async with self.engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
            return True
        except Exception:
            # Database driver errors may include credentials; do not log exception text.
            logger.warning("Database readiness check failed")
            return False

    async def close(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()
