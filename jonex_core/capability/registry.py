from typing import Dict, Optional, List
from .base import BaseCapability
from .models import CapabilityRequest, CapabilityResponse
import logging

logger = logging.getLogger(__name__)


class CapabilityRegistry:


    def __init__(self):
        self._capabilities: Dict[str, BaseCapability] = {}
        logger.info("Capability registry initialized")

    def register(self, capability: BaseCapability) -> None:

        metadata = capability.get_metadata()
        full_id = metadata.full_id
        if full_id in self._capabilities:
            logger.warning(f"Capability {full_id} already exists and will be overwritten")
        self._capabilities[full_id] = capability
        logger.info(f"Capability {full_id} ({metadata.capability_name}) registered successfully")

    def unregister(self, capability_id: str, version: str = "v1") -> None:

        full_id = f"{capability_id}.{version}"
        if full_id in self._capabilities:
            del self._capabilities[full_id]
            logger.info(f"Capability {full_id} unregistered")

    def get_capability(self, capability_id: str, version: Optional[str] = None) -> Optional[BaseCapability]:

        if "." in capability_id:
            full_id = capability_id
        elif version:

            for cap_type in ["business", "domain", "atomic"]:
                full_id = f"{cap_type}.{capability_id}.{version}"
                if full_id in self._capabilities:
                    return self._capabilities[full_id]
            return None
        else:

            for cid, cap in self._capabilities.items():
                if capability_id in cid:
                    return cap
            return None

        return self._capabilities.get(full_id)

    async def invoke(self, capability_id: str, request: CapabilityRequest) -> CapabilityResponse:

        capability = self.get_capability(capability_id)
        if not capability:
            logger.error(f"Capability {capability_id} not found")
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=404,
                message=f"Capability {capability_id} not found"
            )

        try:
            logger.info(f"Invoking capability {capability_id}, request_id={request.request_id}")
            response = await capability(request)
            logger.info(f"Capability {capability_id} invocation completed, success={response.success}")
            return response
        except Exception as e:
            logger.exception(f"Capability {capability_id} invocation raised an exception: {e}")
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=500,
                message=f"Capability call failed: {str(e)}"
            )

    def list_capabilities(self) -> List[dict]:

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



_global_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:

    global _global_registry
    if _global_registry is None:
        _global_registry = CapabilityRegistry()
    return _global_registry
