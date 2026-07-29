#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
服务心跳管理器

定期发送心跳到注册中心，维持服务的存活状态
"""

import asyncio
from typing import Optional, Dict

from jonex_core.discovery.registry import ServiceRegistry, ServiceInstance
from jonex_core.common import get_logger

logger = get_logger("heartbeat")


class HeartbeatManager:
    """
    服务心跳管理器

    定期发送心跳到服务注册中心，维持服务的存活状态
    服务停止时自动注销
    """

    def __init__(
        self,
        registry: ServiceRegistry,
        instance: ServiceInstance,
        interval: int = 30,
    ):
        """
        初始化心跳管理器

        Args:
            registry: 服务注册中心实例
            instance: 服务实例信息
            interval: 心跳间隔（秒），默认 30 秒
        """
        self.registry = registry
        self.instance = instance
        self.interval = interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """
        启动心跳循环

        首次启动时立即注册一次，然后按固定间隔发送心跳
        """
        if self._running:
            logger.warning(f"心跳已在运行中: {self.instance.service_name}")
            return

        self._running = True

        # 首次立即注册
        try:
            await self.registry.register(self.instance)
            logger.info(f"服务首次注册成功: {self.instance.service_name} @ {self.instance.endpoint}")
        except Exception as e:
            logger.error(f"服务首次注册失败: {e}")

        # 启动后台心跳任务
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"心跳已启动: {self.instance.service_name}, 间隔 {self.interval} 秒")

    async def stop(self) -> None:
        """
        停止心跳并注销服务

        取消心跳任务，并从注册中心注销该服务实例
        """
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.exception(f"停止心跳任务时发生错误: {e}")

        # 注销服务
        try:
            await self.registry.deregister(
                service_name=self.instance.service_name,
                endpoint=self.instance.endpoint,
            )
        except Exception as e:
            logger.exception(f"注销服务失败: {e}")

        logger.info(f"心跳已停止: {self.instance.service_name}")

    async def _heartbeat_loop(self) -> None:
        """心跳循环（内部使用）"""
        while self._running:
            try:
                await self.registry.heartbeat(self.instance)
                logger.debug(
                    f"心跳发送成功: {self.instance.service_name} @ {self.instance.endpoint}"
                )
            except Exception as e:
                logger.exception(f"心跳发送失败: {e}")

            # 等待下一次心跳
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
    快捷创建心跳管理器

    Args:
        service_name: 服务名
        service_type: 服务类型 (capability/sidecar/gateway)
        endpoint: 服务端点
        capability_id: 能力ID（仅能力服务需要）
        version: 版本号
        metadata: 额外元数据
        interval: 心跳间隔（秒）

    Returns:
        HeartbeatManager 实例
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
