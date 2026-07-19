#!/usr/bin/python3



import json
import time
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

from jonex_core.common import get_redis_client, get_logger

logger = get_logger("discovery")


@dataclass
class ServiceInstance:

    service_name: str
    service_type: str
    endpoint: str
    capability_id: Optional[str] = None
    version: str = "v1"
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ServiceRegistry:


    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self._key_prefix = "service:"

        self._expire_seconds = 60

    async def register(self, instance: ServiceInstance) -> None:

        key = f"{self._key_prefix}{instance.service_name}:{instance.endpoint.replace(':', '_')}"
        value = asdict(instance)
        value["last_heartbeat"] = time.time()


        redis_data = {}
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                redis_data[k] = json.dumps(v, ensure_ascii=False)
            elif v is None:
                redis_data[k] = ""
            else:
                redis_data[k] = str(v)

        await self.redis.hset(key, mapping=redis_data)

        await self.redis.expire(key, self._expire_seconds)

        logger.info(f"Service registered: {instance.service_name} @ {instance.endpoint}")

    async def deregister(self, service_name: str, endpoint: str) -> None:

        key = f"{self._key_prefix}{service_name}:{endpoint.replace(':', '_')}"
        await self.redis.delete(key)
        logger.info(f"Service deregistered: {service_name} @ {endpoint}")

    async def discover(self, service_name: str) -> Optional[str]:

        pattern = f"{self._key_prefix}{service_name}:*"
        keys = await self.redis.keys(pattern)

        if not keys:
            return None

        candidates = []
        for key in keys:
            data = await self.redis.hgetall(key)
            endpoint = data.get("endpoint") if data else None
            if not endpoint:
                continue
            try:
                last_heartbeat = float(data.get("last_heartbeat") or 0)
            except (TypeError, ValueError):
                last_heartbeat = 0
            candidates.append((last_heartbeat, endpoint))

        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            return candidates[0][1]
        return None

    async def list_services(self, service_type: Optional[str] = None) -> List[Dict]:

        pattern = f"{self._key_prefix}*"
        keys = await self.redis.keys(pattern)

        services = []
        for key in keys:
            data = await self.redis.hgetall(key)
            if data:

                if service_type and data.get("service_type") != service_type:
                    continue


                if data.get("metadata"):
                    try:
                        data["metadata"] = json.loads(data["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        data["metadata"] = {}

                services.append(data)

        return services

    async def heartbeat(self, instance: ServiceInstance) -> None:

        await self.register(instance)

    async def cleanup_expired(self) -> int:

        pattern = f"{self._key_prefix}*"
        keys = await self.redis.keys(pattern)
        count = 0

        for key in keys:
            ttl = await self.redis.ttl(key)
            if ttl <= 0:
                await self.redis.delete(key)
                count += 1

        if count > 0:
            logger.info(f"Removed {count} expired services")
        return count



_registry_instance: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:

    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistry()
    return _registry_instance
