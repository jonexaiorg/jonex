#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Service registration and discovery (based on Redis)

Implements dynamic registration and discovery of capability services, supports horizontal scaling
"""

import json
import time
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

from jonex_core.common import get_redis_client, get_logger

logger = get_logger("discovery")


@dataclass
class ServiceInstance:
    """
    Service instance information

    Attributes:
        service_name: Service name (e.g.: knowledge_base)
        service_type: Service type (capability/sidecar/gateway)
        endpoint: Service endpoint (e.g.: http://knowledge-base:8000)
        capability_id: Capability ID (only required for Capability service, e.g.: business.knowledge_base.v1)
        version: Version
        metadata: Additional Metadata
    """
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
    """Service registry (based on Redis implementation)"""

    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self._key_prefix = "service:"
        # Service expiration time (seconds), services that do not send heartbeat within this time will be cleaned up
        self._expire_seconds = 60

    async def register(self, instance: ServiceInstance) -> None:
        """
        Register service

        Args:
            instance: Service instance information
        """
        key = f"{self._key_prefix}{instance.service_name}:{instance.endpoint.replace(':', '_')}"
        value = asdict(instance)
        value["last_heartbeat"] = time.time()

        # Convert dict to storable format
        redis_data = {}
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                redis_data[k] = json.dumps(v, ensure_ascii=False)
            elif v is None:
                redis_data[k] = ""
            else:
                redis_data[k] = str(v)

        await self.redis.hset(key, mapping=redis_data)
        # Set expiration time
        await self.redis.expire(key, self._expire_seconds)

        logger.info(f"Service registered: {instance.service_name} @ {instance.endpoint}")

    async def deregister(self, service_name: str, endpoint: str) -> None:
        """
        Deregister service

        Args:
            service_name: Service name
            endpoint: Service endpoint
        """
        key = f"{self._key_prefix}{service_name}:{endpoint.replace(':', '_')}"
        await self.redis.delete(key)
        logger.info(f"Service deregistered: {service_name} @ {endpoint}")

    async def discover(self, service_name: str) -> Optional[str]:
        """
        Discover service (returns an available service endpoint)

        Args:
            service_name: Service name

        Returns:
            Service endpoint URL, returns None if no available service
        """
        pattern = f"{self._key_prefix}{service_name}:*"
        keys = await self.redis.keys(pattern)

        if not keys:
            return None

        # Simple round-robin strategy, return the first available
        for key in keys:
            data = await self.redis.hgetall(key)
            if data:
                return data.get("endpoint")
        return None

    async def list_services(self, service_type: Optional[str] = None) -> List[Dict]:
        """
        List all services

        Args:
            service_type: Filter by service type (optional)

        Returns:
            Service instance list
        """
        pattern = f"{self._key_prefix}*"
        keys = await self.redis.keys(pattern)

        services = []
        for key in keys:
            data = await self.redis.hgetall(key)
            if data:
                # Filter by type
                if service_type and data.get("service_type") != service_type:
                    continue

                # Parse metadata
                if data.get("metadata"):
                    try:
                        data["metadata"] = json.loads(data["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        data["metadata"] = {}

                services.append(data)

        return services

    async def heartbeat(self, instance: ServiceInstance) -> None:
        """
        Service heartbeat (renewal)

        Args:
            instance: Service instance information
        """
        await self.register(instance)

    async def cleanup_expired(self) -> int:
        """
        Manually clean up expired services (usually not needed, Redis auto-expires)

        Returns:
            Count of cleaned services
        """
        pattern = f"{self._key_prefix}*"
        keys = await self.redis.keys(pattern)
        count = 0

        for key in keys:
            ttl = await self.redis.ttl(key)
            if ttl <= 0:
                await self.redis.delete(key)
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired services")
        return count


# Global singleton
_registry_instance: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """
    Get service registry instance (singleton)

    Returns:
        ServiceRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistry()
    return _registry_instance
