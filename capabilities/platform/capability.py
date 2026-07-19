
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

        try:
            from capabilities.platform.services.audit_log_sink import get_audit_log_sink
            sink = get_audit_log_sink()
            sink.start()
            logger.info("AuditLogSink started")
        except Exception:
            logger.exception("Failed to start AuditLogSink")

    async def shutdown(self) -> None:

        try:
            from capabilities.platform.services.audit_log_sink import get_audit_log_sink
            sink = get_audit_log_sink()
            await sink.stop()
            logger.info("AuditLogSink stopped")
        except Exception:
            logger.exception("Failed to stop AuditLogSink")

    def register_routes(self, app):

        from capabilities.platform.api import create_platform_router

        router = create_platform_router()
        app.include_router(router, prefix="/api/v1")
