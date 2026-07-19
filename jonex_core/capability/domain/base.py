#!/usr/bin/python3



from abc import abstractmethod
from typing import Any, Dict, Optional

from jonex_core.capability.base import BaseCapability
from jonex_core.capability.models import CapabilityType, CapabilityRequest, CapabilityResponse


class DomainCapability(BaseCapability):


    @property
    def capability_type(self) -> CapabilityType:

        return CapabilityType.DOMAIN

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:

        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:

        pass
