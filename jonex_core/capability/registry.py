from typing import Dict, Optional, List
from .base import BaseCapability
from .models import CapabilityRequest, CapabilityResponse
import logging

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """Capability registration center

    Responsible for capability registration, discovery, routing and invocation.
    """

    def __init__(self):
        self._capabilities: Dict[str, BaseCapability] = {}
        logger.info("Capability registration center initialized")

    def register(self, capability: BaseCapability) -> None:
        """Register capability"""
        metadata = capability.get_metadata()
        full_id = metadata.full_id
        if full_id in self._capabilities:
            logger.warning(f"Capability {full_id} already exists, will be overwritten")
        self._capabilities[full_id] = capability
        logger.info(f"Capability {full_id} ({metadata.capability_name}) registered successfully")

    def unregister(self, capability_id: str, version: str = "v1") -> None:
        """Deregister capability"""
        full_id = f"{capability_id}.{version}"
        if full_id in self._capabilities:
            del self._capabilities[full_id]
            logger.info(f"Capability {full_id} has been deregistered")

    def get_capability(self, capability_id: str, version: Optional[str] = None) -> Optional[BaseCapability]:
        """Get capability instance

        Args:
            capability_id: Capability ID, supports full format "type.id.version" or shorthand "id"
            version: Version, required when using shorthand ID
        """
        if "." in capability_id:
            full_id = capability_id
        elif version:
            # First try matching each type
            for cap_type in ["business", "domain", "atomic"]:
                full_id = f"{cap_type}.{capability_id}.{version}"
                if full_id in self._capabilities:
                    return self._capabilities[full_id]
            return None
        else:
            # No version, find the latest version
            for cid, cap in self._capabilities.items():
                if capability_id in cid:
                    return cap
            return None

        return self._capabilities.get(full_id)

    async def invoke(self, capability_id: str, request: CapabilityRequest) -> CapabilityResponse:
        """Invoke capability

        Args:
            capability_id: Capability ID
            request: Invocation request

        Returns:
            CapabilityResponse: Invocation response
        """
        capability = self.get_capability(capability_id)
        if not capability:
            logger.error(f"Capability {capability_id} Not found")
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=404,
                message=f"Capability {capability_id} Not found"
            )

        try:
            logger.info(f"Invoke capability {capability_id}, request_id={request.request_id}")
            response = await capability(request)
            logger.info(f"Capability {capability_id} invocation completed, success={response.success}")
            return response
        except Exception as e:
            logger.exception(f"Capability {capability_id} invocation exception: {e}")
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=500,
                message=f"Capability invocation exception: {str(e)}"
            )

    def list_capabilities(self) -> List[dict]:
        """List all registered capabilities"""
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


# Global singleton
_global_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    """Get global capability registration center instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = CapabilityRegistry()
    return _global_registry
