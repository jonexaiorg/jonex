#!/usr/bin/python3



from abc import abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse


class BaseLLMCapability(AtomicCapability):


    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:

        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:

        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:

        pass

    @abstractmethod
    async def embedding(self, text: str) -> List[float]:

        pass
