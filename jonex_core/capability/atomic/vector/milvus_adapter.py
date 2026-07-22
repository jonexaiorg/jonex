#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Milvus vector database adapter.

Provides vector storage and retrieval through Milvus.
"""

from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.vector.base_vector import BaseVectorCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("atomic.vector.milvus")


class MilvusVectorCapability(BaseVectorCapability):
    """Milvus vector retrieval capability adapter."""

    def _build_metadata(self) -> CapabilityMetadata:
        """Build capabilityMetadata"""
        return CapabilityMetadata(
            capability_id="vector.milvus",
            capability_name="Milvus Vector Retrieval",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="Milvus vector database with vector storage and similarity search",
            tags=["vector", "milvus"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        """Validate input parameters"""
        if not request.payload:
            raise InvalidParameterError(message="Vector retrieval request payload cannot be empty")

        action = request.payload.get("action", "search")
        collection_name = request.payload.get("collection_name")

        if not collection_name:
            raise InvalidParameterError(message="collection_name parameter is required")

        if action == "insert":
            if "vectors" not in request.payload:
                raise InvalidParameterError(message="Insert mode requires the vectors parameter")
        elif action == "search":
            if "query_vector" not in request.payload:
                raise InvalidParameterError(message="Search mode requires the query_vector parameter")
        elif action == "delete":
            if "ids" not in request.payload:
                raise InvalidParameterError(message="delete Mode must provide ids parameter")
        else:
            raise InvalidParameterError(message=f"Unsupported action: {action}")

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """Execute a vector retrieval capability request."""
        await self.validate_input(request)

        action = request.payload.get("action", "search")
        collection_name = request.payload["collection_name"]

        try:
            if action == "insert":
                vectors = request.payload["vectors"]
                metadatas = request.payload.get("metadatas")
                result = await self.insert(collection_name, vectors, metadatas)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"success": result},
                    message="Vector insertion succeeded",
                )
            elif action == "search":
                query_vector = request.payload["query_vector"]
                top_k = request.payload.get("top_k", 10)
                results = await self.search(collection_name, query_vector, top_k)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"results": results},
                    message=f"Vector retrieval succeeded; returned {len(results)} results",
                )
            elif action == "delete":
                ids = request.payload["ids"]
                result = await self.delete(collection_name, ids)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"success": result},
                    message="Vector deletion succeeded",
                )
        except Exception as e:
            logger.error(f"Milvus Invocation failed: {e}")
            raise CapabilityInvokeError(
                message=f"Milvus Invocation failed: {str(e)}",
                details={"action": action, "collection": collection_name},
                cause=e,
            )

    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Insert vector data

        Note: This is currently a mock implementation. Production requires a real Milvus integration.
        """
        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] Inserting {len(vectors)} vectors into {collection_name}")
            return True

        # TODO: Connect to real Milvus client
        # from pymilvus import connections, Collection
        # connections.connect(
        #     alias="default",
        #     host=config.MILVUS_HOST,
        #     port=config.MILVUS_PORT,
        # )
        # collection = Collection(collection_name)
        # mr = collection.insert(data)
        # return mr.succ_count == len(vectors)

        raise CapabilityInvokeError(message="Milvus not configured")

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Note: This is currently a mock implementation. Production requires a real Milvus integration.
        """
        config = get_config()

        if config.ENV == "dev":
            # Mock implementation: return simulated search results.
            logger.warning(f"[Mock] Searching {collection_name} for top-{top_k} similar vectors")
            return [
                {"id": f"mock_id_{i}", "score": 0.9 - i * 0.05, "metadata": {"source": "mock"}}
                for i in range(min(top_k, 5))
            ]

        # TODO: Connect to real Milvus client
        raise CapabilityInvokeError(message="Milvus not configured")

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """
        Delete vector data.

        Note: This is currently a mock implementation. Production requires a real Milvus integration.
        """
        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] Deleting {len(ids)} vectors from {collection_name}")
            return True

        # TODO: Connect to real Milvus client
        raise CapabilityInvokeError(message="Milvus not configured")
