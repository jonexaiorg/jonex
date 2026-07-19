#!/usr/bin/python3



import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import quote

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from jonex_core.common.config import get_config
from jonex_core.common.tenant import TenantContext

logger = logging.getLogger(__name__)


_config = get_config()


_encoded_password = quote(_config.DB_PASSWORD.encode('utf-8'), safe='')
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{_config.DB_USERNAME}:{_encoded_password}@"
    f"{_config.DB_HOST}:{_config.DB_PORT}/{_config.DB_NAME}"
)


_async_engine = None
_async_session_factory = None
_initialized = False


def _initialize_engine():

    global _async_engine, _initialized
    if _async_engine is None:
        logger.info("Initializing database connection pool...")
        _async_engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_size=_config.DB_POOL_SIZE,
            max_overflow=_config.DB_MAX_OVERFLOW,
            pool_timeout=_config.DB_POOL_TIMEOUT,
            pool_recycle=_config.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            echo=_config.DB_ECHO,
            json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
            isolation_level="READ COMMITTED",
            future=True,
        )
        _initialized = True


def _get_engine():

    _initialize_engine()
    return _async_engine


def _get_session_factory():

    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

        _register_session_events(_async_session_factory)
    return _async_session_factory


def _register_session_events(factory):


    pass



Base = declarative_base()



def AsyncSessionLocal():

    factory = _get_session_factory()
    return factory()



@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:

    factory = _get_session_factory()
    session = factory()
    session.info["tenant_id"] = TenantContext.get()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database operation failed; transaction rolled back: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error; transaction rolled back: {str(e)}")
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:

    async with get_db_session() as session:
        yield session



async def init_database(drop_existing: bool = False):

    engine = _get_engine()

    if drop_existing and _config.ENV != "production":
        logger.warning("⚠️  Dropping existing database tables (development environment)")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database schema initialized")


async def close_database():

    global _async_engine, _async_session_factory, _initialized
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
        _initialized = False
        logger.info("✅ Database connection pool closed")



async def check_db_health() -> bool:

    try:
        async with get_db_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False



def get_sync_session():

    raise NotImplementedError(
        "同步数据库会话已废弃，请使用异步版本 get_db_session()"
    )
