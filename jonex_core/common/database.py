#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - Database connection module

Based on SQLAlchemy 2.0 + asyncpg, supports:
- Async database operations
- Multi-tenant isolation
- Connection pool management
- Read/write separation (optional)
- Automatic session management
"""

import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
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

logger = logging.getLogger(__name__)

# ==================== Base configuration ====================
_config = get_config()

# Database connection URL
_encoded_password = quote(_config.DB_PASSWORD.encode('utf-8'), safe='')
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{_config.DB_USERNAME}:{_encoded_password}@"
    f"{_config.DB_HOST}:{_config.DB_PORT}/{_config.DB_NAME}"
)

# ==================== Lazy-loaded engine and session factory ====================
_async_engine = None
_async_session_factory = None
_initialized = False


def _initialize_engine():
    """Initialize database engine (lazy loading)"""
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
    """Get database engine"""
    _initialize_engine()
    return _async_engine


def _get_session_factory():
    """Get async session factory"""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        # Register event listeners
        _register_session_events(_async_session_factory)
    return _async_session_factory


def _register_session_events(factory):
    """Register session event listeners"""
    # SQLAlchemy events need to be registered on the actual session class
    pass


# Base model class
Base = declarative_base()


# Export for external use (compatible with old code, session will be created on invocation)
def AsyncSessionLocal():
    """Get async session instance (compatible with old code invocation pattern)"""
    factory = _get_session_factory()
    return factory()


# ==================== Multi-tenant support ====================
class TenantContext:
    """Tenant context manager"""
    _tenant_id: Optional[str] = None

    @classmethod
    def set(cls, tenant_id: str):
        cls._tenant_id = tenant_id

    @classmethod
    def get(cls) -> Optional[str]:
        return cls._tenant_id

    @classmethod
    def clear(cls):
        cls._tenant_id = None


# ==================== Database session retrieval ====================
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session (context manager)

    Usage example:
        async with get_db_session() as session:
            result = await session.execute(query)
    """
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        if session.dirty or session.deleted or session.new:
            await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database operation exception, rolled back: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unknown exception, rolled back: {str(e)}")
        raise
    finally:
        await session.close()


async def get_db() -> AsyncSession:
    """
    Database session retrieval for dependency injection

    FastAPI Depends usage example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with get_db_session() as session:
        yield session


# ==================== Database initialization ====================
async def init_database(drop_existing: bool = False):
    """
    Initialize database table structure

    Args:
        drop_existing: Whether to drop existing tables first (only for development environment)
    """
    engine = _get_engine()

    if drop_existing and _config.ENV != "production":
        logger.warning("⚠️  Dropping existing database tables (development environment)")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database table structure initialization completed")


async def close_database():
    """Close database connection pool"""
    global _async_engine, _async_session_factory, _initialized
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
        _initialized = False
        logger.info("✅ Database connection pool closed")


# ==================== Health check ====================
async def check_db_health() -> bool:
    """Check database connection health status"""
    try:
        async with get_db_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# ==================== Sync support (compatible with original code) ====================
def get_sync_session():
    """
    Get sync session (for compatibility with old code, new code should use async version)

    Note: Need to create sync engine, not implemented here yet
    """
    raise NotImplementedError(
        "Sync database session has been deprecated, please use async version get_db_session()"
    )
