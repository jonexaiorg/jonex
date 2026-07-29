from typing import Dict, Optional, List
from .base import BaseCapability
from .models import CapabilityRequest, CapabilityResponse
from jonex_core.common.exceptions import JonexException
from jonex_core.common.i18n import translate
import logging

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """能力注册中心

    负责能力的注册、发现、路由和调用。
    """

    def __init__(self):
        self._capabilities: Dict[str, BaseCapability] = {}
        logger.info("能力注册中心初始化完成")

    def register(self, capability: BaseCapability) -> None:
        """注册能力"""
        metadata = capability.get_metadata()
        full_id = metadata.full_id
        if full_id in self._capabilities:
            logger.warning(f"能力 {full_id} 已存在，将覆盖")
        self._capabilities[full_id] = capability
        logger.info(f"能力 {full_id} ({metadata.capability_name}) 注册成功")

    def unregister(self, capability_id: str, version: str = "v1") -> None:
        """注销能力"""
        full_id = f"{capability_id}.{version}"
        if full_id in self._capabilities:
            del self._capabilities[full_id]
            logger.info(f"能力 {full_id} 已注销")

    def get_capability(self, capability_id: str, version: Optional[str] = None) -> Optional[BaseCapability]:
        """获取能力实例

        Args:
            capability_id: 能力ID，支持完整格式 "type.id.version" 或简写 "id"
            version: 版本号，简写ID时需要指定
        """
        if "." in capability_id:
            full_id = capability_id
        elif version:
            # 先尝试各类型匹配
            for cap_type in ["business", "domain", "atomic"]:
                full_id = f"{cap_type}.{capability_id}.{version}"
                if full_id in self._capabilities:
                    return self._capabilities[full_id]
            return None
        else:
            # 没有版本，找最新版本
            for cid, cap in self._capabilities.items():
                if capability_id in cid:
                    return cap
            return None

        return self._capabilities.get(full_id)

    async def invoke(self, capability_id: str, request: CapabilityRequest) -> CapabilityResponse:
        """调用能力

        Args:
            capability_id: 能力ID
            request: 调用请求

        Returns:
            CapabilityResponse: 调用响应
        """
        capability = self.get_capability(capability_id)
        if not capability:
            logger.error(f"能力 {capability_id} 未找到")
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=404,
                message=translate("err.capability.not_found", params={"capability_id": capability_id}, fallback=f"能力 {capability_id} 未找到")
            )

        try:
            logger.info(f"调用能力 {capability_id}, request_id={request.request_id}")
            response = await capability(request)
            logger.info(f"能力 {capability_id} 调用完成, success={response.success}")
            return response
        except JonexException as e:
            logger.warning(f"能力 {capability_id} 业务异常: code={e.code}, message={e.message}")
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=e.code,
                message=e.message,
                details=e.details if e.details else None,
                params=e.params if e.params else None,
            )
        except Exception as e:
            logger.exception(f"能力 {capability_id} 调用异常: {e}")
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=500,
                message=translate("err.capability.invoke_exception", params={"error": str(e)}, fallback=f"能力调用异常: {str(e)}")
            )

    def list_capabilities(self) -> List[dict]:
        """列出所有已注册能力"""
        result = []
        for cap in self._capabilities.values():
            meta = cap.get_metadata()
            result.append({
                "capability_id": meta.full_id,
                "name": meta.capability_name,
                "type": meta.capability_type.value,
                "version": meta.version,
                "description": meta.description,
            })
        return result


# 全局单例
_global_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    """获取全局能力注册中心实例"""
    global _global_registry
    if _global_registry is None:
        _global_registry = CapabilityRegistry()
    return _global_registry
