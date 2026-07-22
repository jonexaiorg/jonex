#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Semantic search domain capability

Orchestrates atomic capabilities via LLMClient (embedding) + VectorClient (search/insert/delete).
"""

from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.llm.client import LLMClient, get_llm_client
from jonex_core.capability.atomic.vector.client import VectorClient, get_vector_client
from jonex_core.capability.domain.base import DomainCapability
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityType,
)
from jonex_core.common import get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("domain.knowledge.search")


class SemanticSearchCapability(DomainCapability):
    """Semantic search domain capability"""

    DEFAULT_COLLECTION = "knowledge_retrieval"

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        vector_client: Optional[VectorClient] = None,
    ):
        super().__init__()
        self.llm_client: LLMClient = llm_client or get_llm_client()
        self.vector_client: VectorClient = vector_client or get_vector_client()

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="knowledge.semantic_search",
            capability_name="Semantic search",
            capability_type=CapabilityType.DOMAIN,
            version="v1",
            description="Semantic search capability based on vector retrieval, supports text similarity search",
            tags=["knowledge", "search"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        if not request.payload:
            raise InvalidParameterError(message="Semantic search request payload cannot be empty")
        action = request.payload.get("action", "search")
        if action == "search" and "query" not in request.payload:
            raise InvalidParameterError(message="search mode must provide query parameter")
        if action == "insert" and "texts" not in request.payload:
            raise InvalidParameterError(message="insert mode must provide texts parameter")
        if action == "delete" and "ids" not in request.payload:
            raise InvalidParameterError(message="delete Mode must provide ids parameter")
        if action not in {"search", "insert", "delete"}:
            raise InvalidParameterError(message=f"Unsupported action: {action}")
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        await self.validate_input(request)

        action = request.payload.get("action", "search")
        collection = request.payload.get("collection_name", self.DEFAULT_COLLECTION)

        try:
            if action == "search":
                results = await self._search(
                    query=request.payload["query"],
                    collection=collection,
                    top_k=request.payload.get("top_k", 10),
                )
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"results": results, "collection": collection},
                    message=f"Semantic search succeeded, returned {len(results)} items",
                )

            if action == "insert":
                inserted = await self._insert(
                    texts=request.payload["texts"],
                    collection=collection,
                    metadatas=request.payload.get("metadatas"),
                )
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"success": inserted, "collection": collection},
                    message="Semantic index inserted successfully",
                )

            # delete
            removed = await self.vector_client.delete(collection, request.payload["ids"])
            return CapabilityResponse.ok(
                request_id=request.request_id,
                data={"success": removed, "collection": collection},
                message="Semantic index deleted successfully",
            )
        except CapabilityInvokeError:
            raise
        except Exception as e:
            logger.error(f"Semantic search processing failed: {e}")
            raise CapabilityInvokeError(
                message=f"Semantic search processing failed: {e}",
                details={"action": action, "collection": collection},
                cause=e,
            )

    async def _search(
        self,
        query: str,
        collection: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        logger.info(f"Semantic search: query={query[:60]!r}, top_k={top_k}")
        query_vector = await self.llm_client.embedding(query)
        return await self.vector_client.search(collection, query_vector, top_k)

    async def _insert(
        self,
        texts: List[str],
        collection: str,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        logger.info(f"Semantic index insert: count={len(texts)}, collection={collection}")
        vectors = [await self.llm_client.embedding(t) for t in texts]
        meta = metadatas or [{"text": t} for t in texts]
        return await self.vector_client.insert(collection, vectors, meta)
