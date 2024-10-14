from typing import AsyncIterator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_session, async_sessionmaker, AsyncSession

from core import config

SQLALCHEMY_SYNC_DATABASE_URL = f"postgresql+psycopg2://{config.POSTGRESQL_USER}:{config.POSTGRESQL_PASSWORD}@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DATABASE}"
SQLALCHEMY_ASYNC_DATABASE_URL = f"postgresql+asyncpg://{config.POSTGRESQL_USER}:{config.POSTGRESQL_PASSWORD}@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DATABASE}"


class DatabaseSessionManager:
    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.session_maker = None
        self.session = None

    def init_db(self):
        self.engine = create_async_engine(
            SQLALCHEMY_ASYNC_DATABASE_URL, pool_size=100, max_overflow=0, pool_pre_ping=False
        )

        self.session_maker = async_sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        self.session = async_session(self.session_maker)

    async def close(self):
        if self.engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self.engine.dispose()


engine = create_engine(SQLALCHEMY_SYNC_DATABASE_URL, echo=True)

sessionmanager = DatabaseSessionManager()
sessionmanager.init_db()


async def get_db() -> AsyncIterator[AsyncSession]:
    session = sessionmanager.session_maker()
    if session is None:
        raise Exception("DatabaseSessionManager is not initialized")
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db_non_gen() -> AsyncIterator[AsyncSession]:
    session = sessionmanager.session_maker()
    try:
        return await session
    finally:
        await session.close()
