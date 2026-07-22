#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Abstract base class for vector retrieval capabilities."""

from abc import abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse


class BaseVectorCapability(AtomicCapability):
    """Abstract base class for vector retrieval capabilities.

    All vector database adapters must inherit from this class.
    """

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:
        """Validate vector retrieval input parameters."""
        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """Execute a vector retrieval capability request."""
        pass

    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Insert vector data

        Args:
            collection_name: Collection name
            vectors: Vector array
            metadatas: Metadata array (one-to-one with vectors)

        Returns:
            bool: Whether insertedSuccess
        """
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            collection_name: Collection name
            query_vector: Query vector
            top_k: Result count

        Returns:
            List[Dict]: Search results containing id, score, metadata, and other fields
        """
        pass

    @abstractmethod
    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """
        Delete vector data.

        Args:
            collection_name: Collection name
            ids: IDs to delete

        Returns:
            bool: Whether deletion succeeded
        """
        pass
