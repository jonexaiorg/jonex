from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityHealth,
)


class BaseCapability(ABC):


    def __init__(self):
        self._metadata = self._build_metadata()

    @abstractmethod
    def _build_metadata(self) -> CapabilityMetadata:

        pass

    def get_metadata(self) -> CapabilityMetadata:

        return self._metadata

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:

        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:

        pass

    async def __call__(self, request: CapabilityRequest) -> CapabilityResponse:

        if not await self.validate_input(request):
            return CapabilityResponse.error(
                request_id=request.request_id,
                code=400,
                message="Parameter validation failed"
            )
        return await self.execute(request)

    def get_health_status(self) -> CapabilityHealth:

        return CapabilityHealth(
            capability_id=self.get_metadata().full_id,
            is_healthy=True,
            message="Healthy"
        )

    async def initialize(self) -> None:

        pass

    async def shutdown(self) -> None:

        pass

    def register_routes(self, app) -> None:

        pass
