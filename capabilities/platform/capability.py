"""
平台管理能力 (business.platform.v1)

作为独立容器运行，提供：
- 认证业务逻辑（login/refresh/ticket，由 Sidecar 代理调用）
- 平台管理 CRUD（用户/角色/权限/菜单/应用/配置/审计/任务）
"""
import logging

from jonex_core.capability import BaseCapability
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityType,
)

logger = logging.getLogger(__name__)


class PlatformCapability(BaseCapability):
    """平台管理能力 — 独立容器"""

    def __init__(self):
        super().__init__()

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="platform",
            capability_name="平台管理能力",
            capability_type=CapabilityType.BUSINESS,
            version="v1",
            description="用户认证、RBAC、菜单、应用、系统配置、审计日志、任务调度",
            author="jonex",
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        return CapabilityResponse.ok(data={"message": "platform capability"})

    async def initialize(self) -> None:
        """启动审计日志 sink 后台任务"""
        try:
            from capabilities.platform.services.audit_log_sink import get_audit_log_sink
            sink = get_audit_log_sink()
            sink.start()
            logger.info("AuditLogSink 已启动")
        except Exception:
            logger.exception("AuditLogSink 启动失败")

    async def shutdown(self) -> None:
        """停止审计日志 sink，flush 剩余条目"""
        try:
            from capabilities.platform.services.audit_log_sink import get_audit_log_sink
            sink = get_audit_log_sink()
            await sink.stop()
            logger.info("AuditLogSink 已停止")
        except Exception:
            logger.exception("AuditLogSink 停止失败")

    def register_routes(self, app):
        """注册平台管理 REST API 路由"""
        from capabilities.platform.api import create_platform_router

        router = create_platform_router()
        app.include_router(router, prefix="/api/v1")
