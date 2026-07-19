#!/usr/bin/python3



import asyncio
from typing import Optional, Dict

from jonex_core.discovery.registry import ServiceRegistry, ServiceInstance
from jonex_core.common import get_logger

logger = get_logger("heartbeat")


class HeartbeatManager:


    def __init__(
        self,
        registry: ServiceRegistry,
        instance: ServiceInstance,
        interval: int = 30,
    ):

        self.registry = registry
        self.instance = instance
        self.interval = interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:

        if self._running:
            logger.warning(f"Heartbeat is already running: {self.instance.service_name}")
            return

        self._running = True


        try:
            await self.registry.register(self.instance)
            logger.info(f"Initial service registration succeeded: {self.instance.service_name} @ {self.instance.endpoint}")
        except Exception as e:
            logger.error(f"Initial service registration failed: {e}")


        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Heartbeat started: {self.instance.service_name}, interval {self.interval} seconds")

    async def stop(self) -> None:

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.exception(f"Error while stopping heartbeat task: {e}")


        try:
            await self.registry.deregister(
                service_name=self.instance.service_name,
                endpoint=self.instance.endpoint,
            )
        except Exception as e:
            logger.exception(f"Failed to deregister service: {e}")

        logger.info(f"Heartbeat stopped: {self.instance.service_name}")

    async def _heartbeat_loop(self) -> None:

        while self._running:
            try:
                await self.registry.heartbeat(self.instance)
                logger.debug(
                    f"Heartbeat sent successfully: {self.instance.service_name} @ {self.instance.endpoint}"
                )
            except Exception as e:
                logger.exception(f"Failed to send heartbeat: {e}")


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
