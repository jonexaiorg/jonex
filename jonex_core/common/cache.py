#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - cache connection module

Based on Redis async client, supports:
- Async Redis operation
- Distributed lock
- Connection pool management
- Retry mechanism
- Tenant-level cache isolation
"""

import logging
import uuid
from functools import wraps
from typing import Any, Optional, Union

import redis
from redis import ConnectionError, TimeoutError, RedisError
from redis.asyncio import ConnectionPool, Redis

from jonex_core.common.config import get_config

logger = logging.getLogger(__name__)

config = get_config()


# ==================== Connection pool management ====================
class RedisPoolManager:
    """Redis connection pool manager"""
    _pool: Optional[ConnectionPool] = None

    @classmethod
    def get_pool(cls) -> ConnectionPool:
        """Get async connection pool (lazy loading)"""
        if cls._pool is None:
            cls._pool = ConnectionPool(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD,
                max_connections=config.REDIS_MAX_CONNECTIONS,
                socket_timeout=config.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=config.REDIS_CONNECT_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=config.REDIS_HEALTH_CHECK_INTERVAL,
                decode_responses=config.REDIS_DECODE_RESPONSES,
            )
            logger.info(f"✅ Redis connection pool initialized (host={config.REDIS_HOST}:{config.REDIS_PORT})")
        return cls._pool

    @classmethod
    async def close_pool(cls):
        """Close connection pool"""
        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None
            logger.info("✅ Redis connection pool closed")


def get_redis_client() -> Redis:
    """Get async Redis client"""
    return Redis(connection_pool=RedisPoolManager.get_pool())


# ==================== Retry decorator ====================
def redis_retry(max_retries: int = 3, delay: float = 0.1):
    """
    Redis operation retry decorator

    Args:
        max_retries: Maximum retry count
        delay: Retry delay base (seconds)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, TimeoutError, RedisError) as e:
                    last_exception = e
                    logger.warning(
                        f"Redis operation failed, retrying ({attempt + 1}/{max_retries}): {e}"
                    )
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(delay * (attempt + 1))
            logger.error(f"Redis operation ultimately failed: {last_exception}")
            raise last_exception
        return wrapper
    return decorator


# ==================== Cache utility class ====================
class CacheUtil:
    """Redis cache utility class (async)"""

    # ==================== Basic operations ====================
    @staticmethod
    @redis_retry(max_retries=3)
    async def ping() -> bool:
        """Health check"""
        client = get_redis_client()
        try:
            return await client.ping()
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def get(key: str) -> Optional[Any]:
        """Get value"""
        client = get_redis_client()
        try:
            return await client.get(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def set(key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set value

        Args:
            key: Key name
            value: Value
            expire: Expiration time (seconds), None means no expiration
        """
        client = get_redis_client()
        try:
            result = await client.set(name=key, value=value, ex=expire)
            return result is not None
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def delete(key: str) -> int:
        """Delete key"""
        client = get_redis_client()
        try:
            return await client.delete(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def exists(key: str) -> bool:
        """Check if key exists"""
        client = get_redis_client()
        try:
            return await client.exists(key) > 0
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def ttl(key: str) -> int:
        """Get remaining expiration time (seconds)"""
        client = get_redis_client()
        try:
            return await client.ttl(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def expire(key: str, seconds: int) -> bool:
        """Set expiration time"""
        client = get_redis_client()
        try:
            return await client.expire(key, seconds)
        finally:
            await client.aclose()

    # ==================== Hash operations ====================
    @staticmethod
    @redis_retry(max_retries=3)
    async def hgetall(key: str) -> dict:
        """Get all hash fields"""
        client = get_redis_client()
        try:
            return await client.hgetall(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def hget(key: str, field: str) -> Optional[Any]:
        """Get hash field value"""
        client = get_redis_client()
        try:
            return await client.hget(key, field)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def hset(key: str, field: str, value: Any) -> int:
        """Set hash field value"""
        client = get_redis_client()
        try:
            return await client.hset(key, field, value)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def hdel(key: str, *fields: str) -> int:
        """Delete hash fields"""
        client = get_redis_client()
        try:
            return await client.hdel(key, *fields)
        finally:
            await client.aclose()

    # ==================== Set operations ====================
    @staticmethod
    @redis_retry(max_retries=3)
    async def sadd(key: str, *members: Any) -> int:
        """Add members to set"""
        client = get_redis_client()
        try:
            return await client.sadd(key, *members)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def smembers(key: str) -> set:
        """Get all set members"""
        client = get_redis_client()
        try:
            return await client.smembers(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def srem(key: str, *members: Any) -> int:
        """Delete set members"""
        client = get_redis_client()
        try:
            return await client.srem(key, *members)
        finally:
            await client.aclose()

    # ==================== Distributed lock ====================
    @staticmethod
    @redis_retry(max_retries=3)
    async def acquire_lock(lock_key: str, lock_timeout: int) -> str:
        """
        Get Redis distributed lock

        Args:
            lock_key: Lock key name
            lock_timeout: Lock timeout (milliseconds)

        Returns:
            Lock unique identifier (returns empty string on failure)
        """
        lock_id = str(uuid.uuid4())
        client = get_redis_client()
        try:
            acquired = await client.set(
                lock_key,
                lock_id,
                nx=True,       # Only set when key does not exist
                px=lock_timeout  # Expiration time (milliseconds)
            )
            return lock_id if acquired else ""
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def release_lock(lock_key: str, lock_id: str) -> bool:
        """
        Release Redis distributed lock (uses Lua script for atomicity)

        Args:
            lock_key: Lock key name
            lock_id: Lock unique identifier

        Returns:
            Whether released successfully
        """
        lua_script = """
           if redis.call("get", KEYS[1]) == ARGV[1] then
               return redis.call("del", KEYS[1])
           else
               return 0
           end
           """
        client = get_redis_client()
        try:
            result = await client.eval(lua_script, 1, lock_key, lock_id)
            return result == 1
        finally:
            await client.aclose()

    # ==================== Counter ====================
    @staticmethod
    @redis_retry(max_retries=3)
    async def incr(key: str, amount: int = 1) -> int:
        """Atomic increment"""
        client = get_redis_client()
        try:
            return await client.incr(key, amount)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def decr(key: str, amount: int = 1) -> int:
        """Atomic decrement"""
        client = get_redis_client()
        try:
            return await client.decr(key, amount)
        finally:
            await client.aclose()

    # ==================== Batch operations ====================
    @staticmethod
    @redis_retry(max_retries=3)
    async def mget(*keys: str) -> list:
        """Batch get"""
        client = get_redis_client()
        try:
            return await client.mget(*keys)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def mset(mapping: dict) -> bool:
        """Batch set"""
        client = get_redis_client()
        try:
            return await client.mset(mapping)
        finally:
            await client.aclose()


# ==================== Tenant-level cache wrapper ====================
class TenantCache:
    """Tenant-level cache utility, automatically adds tenant prefix"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._prefix = f"tenant:{tenant_id}:"

    def _make_key(self, key: str) -> str:
        """Build key with tenant prefix"""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        return await CacheUtil.get(self._make_key(key))

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        return await CacheUtil.set(self._make_key(key), value, expire)

    async def delete(self, key: str) -> int:
        return await CacheUtil.delete(self._make_key(key))

    async def exists(self, key: str) -> bool:
        return await CacheUtil.exists(self._make_key(key))

    async def acquire_lock(self, lock_key: str, lock_timeout: int) -> str:
        return await CacheUtil.acquire_lock(self._make_key(lock_key), lock_timeout)

    async def release_lock(self, lock_key: str, lock_id: str) -> bool:
        return await CacheUtil.release_lock(self._make_key(lock_key), lock_id)


# ==================== Helper functions ====================
async def check_redis_health() -> bool:
    """Check Redis connection health status"""
    try:
        return await CacheUtil.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


# Backward compatibility: keep interface consistent with original code
RedisUtil = CacheUtil
