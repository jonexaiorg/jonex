#!/usr/bin/python3



from abc import abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse


class BaseVectorCapability(AtomicCapability):


    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:

        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:

        pass

    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:

        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:

        pass

    @abstractmethod
    async def delete(self, collection_name: str, ids: List[str]) -> bool:

        pass
