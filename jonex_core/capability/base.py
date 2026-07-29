from abc import ABC, abstractmethod
from typing import Dict, Any
from jonex_core.common.i18n import translate
from .models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityHealth,
)


class BaseCapability(ABC):
    """能力插件基类

    所有能力必须实现此抽象基类，遵循统一的调用契约。
    """

    def __init__(self):
        self._metadata = self._build_metadata()

    @abstractmethod
    def _build_metadata(self) -> CapabilityMetadata:
        """构建能力元数据（由子类实现）"""
        pass

    def get_metadata(self) -> CapabilityMetadata:
        """获取能力元数据"""
        return self._metadata

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:
        """输入参数验证（由子类实现）"""
        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """执行能力逻辑（由子类实现）"""
        pass

    async def __call__(self, request: CapabilityRequest) -> CapabilityResponse:
        """便捷调用方式"""
        if not await self.validate_input(request):
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=400,
                message=translate("err.capability.validation_failed", fallback="参数验证失败")
            )
        return await self.execute(request)

    def get_health_status(self) -> CapabilityHealth:
        """获取能力健康状态"""
        return CapabilityHealth(
            capability_id=self.get_metadata().full_id,
            is_healthy=True,
            message=translate("err.capability.healthy", fallback="运行正常")
        )

    async def initialize(self) -> None:
        """能力初始化钩子"""
        pass

    async def shutdown(self) -> None:
        """能力关闭钩子"""
        pass

    def register_routes(self, app) -> None:
        """注册自定义路由（可选覆盖）

        能力服务启动时调用，允许能力添加额外的 FastAPI 路由。
        """
        pass
