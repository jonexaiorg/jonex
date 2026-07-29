"""
服务注册与发现模块

基于 Redis 实现服务注册与发现，支持：
- 服务实例注册与注销
- 服务心跳续期
- 服务发现
- 服务列表查询
"""

from jonex_core.discovery.registry import (
    ServiceInstance,
    ServiceRegistry,
    get_service_registry,
)
from jonex_core.discovery.heartbeat import (
    HeartbeatManager,
)

__all__ = [
    "ServiceInstance",
    "ServiceRegistry",
    "get_service_registry",
    "HeartbeatManager",
]
