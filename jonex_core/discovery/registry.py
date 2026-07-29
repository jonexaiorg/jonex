#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
服务注册与发现（基于 Redis）

实现能力服务的动态注册和发现，支持水平扩展
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
    服务实例信息

    Attributes:
        service_name: 服务名 (如: knowledge_base)
        service_type: 服务类型 (capability/sidecar/gateway)
        endpoint: 服务端点 (如: http://knowledge-base:8000)
        capability_id: 能力ID（仅能力服务需要，如: business.knowledge_base.v1）
        version: 版本号
        metadata: 额外元数据
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
    """服务注册中心（基于 Redis 实现）"""

    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self._key_prefix = "service:"
        # 服务过期时间（秒），超过此时间未心跳则被清理
        self._expire_seconds = 60

    async def register(self, instance: ServiceInstance) -> None:
        """
        注册服务

        Args:
            instance: 服务实例信息
        """
        key = f"{self._key_prefix}{instance.service_name}:{instance.endpoint.replace(':', '_')}"
        value = asdict(instance)
        value["last_heartbeat"] = time.time()

        # 将字典转为可存储的格式
        redis_data = {}
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                redis_data[k] = json.dumps(v, ensure_ascii=False)
            elif v is None:
                redis_data[k] = ""
            else:
                redis_data[k] = str(v)

        await self.redis.hset(key, mapping=redis_data)
        # 设置过期时间
        await self.redis.expire(key, self._expire_seconds)

        logger.info(f"服务已注册: {instance.service_name} @ {instance.endpoint}")

    async def deregister(self, service_name: str, endpoint: str) -> None:
        """
        注销服务

        Args:
            service_name: 服务名
            endpoint: 服务端点
        """
        key = f"{self._key_prefix}{service_name}:{endpoint.replace(':', '_')}"
        await self.redis.delete(key)
        logger.info(f"服务已注销: {service_name} @ {endpoint}")

    async def discover(self, service_name: str) -> Optional[str]:
        """
        发现服务（返回一个可用的服务端点）

        Args:
            service_name: 服务名

        Returns:
            服务端点 URL，如果没有可用服务则返回 None
        """
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
        """
        列出所有服务

        Args:
            service_type: 按服务类型过滤（可选）

        Returns:
            服务实例列表
        """
        pattern = f"{self._key_prefix}*"
        keys = await self.redis.keys(pattern)

        services = []
        for key in keys:
            data = await self.redis.hgetall(key)
            if data:
                # 过滤类型
                if service_type and data.get("service_type") != service_type:
                    continue

                # 解析 metadata
                if data.get("metadata"):
                    try:
                        data["metadata"] = json.loads(data["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        data["metadata"] = {}

                services.append(data)

        return services

    async def heartbeat(self, instance: ServiceInstance) -> None:
        """
        服务心跳（续期）

        Args:
            instance: 服务实例信息
        """
        await self.register(instance)

    async def cleanup_expired(self) -> int:
        """
        手动清理过期的服务（一般不需要，Redis 自动过期）

        Returns:
            清理的服务数量
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
            logger.info(f"清理了 {count} 个过期服务")
        return count


# 全局单例
_registry_instance: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """
    获取服务注册中心实例（单例）

    Returns:
        ServiceRegistry 实例
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistry()
    return _registry_instance
