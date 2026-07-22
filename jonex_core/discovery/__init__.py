"""
Service registration and discovery module

Based on Redis for service registration and discovery, supports:
- Service instance registration and deregistration
- Service heartbeat renewal
- Service discovery
- Service list query
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
