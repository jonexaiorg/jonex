#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Service heartbeat manager

Periodically sends heartbeat to registry, maintaining service liveness status
"""

import asyncio
from typing import Optional, Dict

from jonex_core.discovery.registry import ServiceRegistry, ServiceInstance
from jonex_core.common import get_logger

logger = get_logger("heartbeat")


class HeartbeatManager:
    """
    Service heartbeat manager

    Periodically sends heartbeat to service registry, maintaining service liveness status
    Automatically deregisters when service stops
    """

    def __init__(
        self,
        registry: ServiceRegistry,
        instance: ServiceInstance,
        interval: int = 30,
    ):
        """
        Initialize heartbeat manager

        Args:
            registry: Service registry instance
            instance: Service instance information
            interval: Heartbeat interval (seconds), default 30 seconds
        """
        self.registry = registry
        self.instance = instance
        self.interval = interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """
        Start heartbeat loop

        Registers once immediately on first start, then sends heartbeat at fixed interval
        """
        if self._running:
            logger.warning(f"Heartbeat already running: {self.instance.service_name}")
            return

        self._running = True

        # Register immediately on first start
        try:
            await self.registry.register(self.instance)
            logger.info(f"Service first registration successful: {self.instance.service_name} @ {self.instance.endpoint}")
        except Exception as e:
            logger.error(f"Service first registration failed: {e}")

        # Start background heartbeat task
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Heartbeat started: {self.instance.service_name}, interval {self.interval} seconds")

    async def stop(self) -> None:
        """
        Stop heartbeat and deregister service

        Cancel heartbeat task, and deregister this service instance from registry
        """
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.exception(f"Error occurred while stopping heartbeat task: {e}")

        # Deregister service
        try:
            await self.registry.deregister(
                service_name=self.instance.service_name,
                endpoint=self.instance.endpoint,
            )
        except Exception as e:
            logger.exception(f"Deregister service failed: {e}")

        logger.info(f"Heartbeat stopped: {self.instance.service_name}")

    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop (internal use)"""
        while self._running:
            try:
                await self.registry.heartbeat(self.instance)
                logger.debug(
                    f"Heartbeat sent successfully: {self.instance.service_name} @ {self.instance.endpoint}"
                )
            except Exception as e:
                logger.exception(f"Heartbeat send failed: {e}")

            # Wait for next heartbeat
            await asyncio.sleep(self.interval)


def create_heartbeat_manager(
    service_name: str,
    service_type: str,
    endpoint: str,
    capability_id: Optional[str] = None,
    version: str = "v1",
    metadata: Optional[Dict] = None,
    interval: int = 30,
) -> HeartbeatManager:
    """
    Quickly create Heartbeat manager

    Args:
        service_name: Service name
        service_type: Service type (capability/sidecar/gateway)
        endpoint: Service endpoint
        capability_id: Capability ID (only required for Capability service)
        version: Version
        metadata: Additional Metadata
        interval: Heartbeat interval (seconds)

    Returns:
        HeartbeatManager instance
    """
    from jonex_core.discovery.registry import get_service_registry

    instance = ServiceInstance(
        service_name=service_name,
        service_type=service_type,
        endpoint=endpoint,
        capability_id=capability_id,
        version=version,
        metadata=metadata,
    )

    registry = get_service_registry()
    return HeartbeatManager(registry, instance, interval)
