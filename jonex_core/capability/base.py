from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityHealth,
)


class BaseCapability(ABC):
    """Base class for capability plugins

    All capabilities must implement this abstract base class, following the unified invocation contract.
    """

    def __init__(self):
        self._metadata = self._build_metadata()

    @abstractmethod
    def _build_metadata(self) -> CapabilityMetadata:
        """Build capability metadata (implemented by subclasses)"""
        pass

    def get_metadata(self) -> CapabilityMetadata:
        """Get capability metadata"""
        return self._metadata

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:
        """Validate input parameters (implemented by subclasses)"""
        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """Execute capability logic (implemented by subclasses)"""
        pass

    async def __call__(self, request: CapabilityRequest) -> CapabilityResponse:
        """Convenient invocation method"""
        if not await self.validate_input(request):
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=400,
                message="Parameter validation failed"
            )
        return await self.execute(request)

    def get_health_status(self) -> CapabilityHealth:
        """Get capability health status"""
        return CapabilityHealth(
            capability_id=self.get_metadata().full_id,
            is_healthy=True,
            message="Running normally"
        )

    async def initialize(self) -> None:
        """Capability initialize hook"""
        pass

    async def shutdown(self) -> None:
        """Capability shutdown hook"""
        pass

    def register_routes(self, app) -> None:
        """Register custom routes (optional override)

        Invoked when capability service starts, allowing capability to add additional FastAPI routes.
        """
        pass
