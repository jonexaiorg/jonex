#!/usr/bin/python3



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



class RedisPoolManager:

    _pool: Optional[ConnectionPool] = None

    @classmethod
    def get_pool(cls) -> ConnectionPool:

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

        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None
            logger.info("✅ Redis connection pool closed")


def get_redis_client() -> Redis:

    return Redis(connection_pool=RedisPoolManager.get_pool())



def redis_retry(max_retries: int = 3, delay: float = 0.1):

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
                        f"Redis operation failed; retrying ({attempt + 1}/{max_retries}): {e}"
                    )
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(delay * (attempt + 1))
            logger.error(f"Redis operation failed after all retries: {last_exception}")
            raise last_exception
        return wrapper
    return decorator



class CacheUtil:



    @staticmethod
    @redis_retry(max_retries=3)
    async def ping() -> bool:

        client = get_redis_client()
        try:
            return await client.ping()
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def get(key: str) -> Optional[Any]:

        client = get_redis_client()
        try:
            return await client.get(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def set(key: str, value: Any, expire: Optional[int] = None) -> bool:

        client = get_redis_client()
        try:
            result = await client.set(name=key, value=value, ex=expire)
            return result is not None
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def delete(key: str) -> int:

        client = get_redis_client()
        try:
            return await client.delete(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def exists(key: str) -> bool:

        client = get_redis_client()
        try:
            return await client.exists(key) > 0
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def ttl(key: str) -> int:

        client = get_redis_client()
        try:
            return await client.ttl(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def expire(key: str, seconds: int) -> bool:

        client = get_redis_client()
        try:
            return await client.expire(key, seconds)
        finally:
            await client.aclose()


    @staticmethod
    @redis_retry(max_retries=3)
    async def hgetall(key: str) -> dict:

        client = get_redis_client()
        try:
            return await client.hgetall(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def hget(key: str, field: str) -> Optional[Any]:

        client = get_redis_client()
        try:
            return await client.hget(key, field)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def hset(key: str, field: str, value: Any) -> int:

        client = get_redis_client()
        try:
            return await client.hset(key, field, value)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def hdel(key: str, *fields: str) -> int:

        client = get_redis_client()
        try:
            return await client.hdel(key, *fields)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def hincrby(key: str, field: str, amount: int = 1) -> int:

        client = get_redis_client()
        try:
            return await client.hincrby(key, field, amount)
        finally:
            await client.aclose()


    @staticmethod
    @redis_retry(max_retries=3)
    async def sadd(key: str, *members: Any) -> int:

        client = get_redis_client()
        try:
            return await client.sadd(key, *members)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def smembers(key: str) -> set:

        client = get_redis_client()
        try:
            return await client.smembers(key)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def srem(key: str, *members: Any) -> int:

        client = get_redis_client()
        try:
            return await client.srem(key, *members)
        finally:
            await client.aclose()


    @staticmethod
    @redis_retry(max_retries=3)
    async def acquire_lock(lock_key: str, lock_timeout: int) -> str:

        lock_id = str(uuid.uuid4())
        client = get_redis_client()
        try:
            acquired = await client.set(
                lock_key,
                lock_id,
                nx=True,
                px=lock_timeout
            )
            return lock_id if acquired else ""
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def release_lock(lock_key: str, lock_id: str) -> bool:

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


    @staticmethod
    @redis_retry(max_retries=3)
    async def incr(key: str, amount: int = 1) -> int:

        client = get_redis_client()
        try:
            return await client.incr(key, amount)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def decr(key: str, amount: int = 1) -> int:

        client = get_redis_client()
        try:
            return await client.decr(key, amount)
        finally:
            await client.aclose()


    @staticmethod
    @redis_retry(max_retries=3)
    async def mget(*keys: str) -> list:

        client = get_redis_client()
        try:
            return await client.mget(*keys)
        finally:
            await client.aclose()

    @staticmethod
    @redis_retry(max_retries=3)
    async def mset(mapping: dict) -> bool:

        client = get_redis_client()
        try:
            return await client.mset(mapping)
        finally:
            await client.aclose()



class TenantCache:


    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._prefix = f"tenant:{tenant_id}:"

    def _make_key(self, key: str) -> str:

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



async def check_redis_health() -> bool:

    try:
        return await CacheUtil.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
