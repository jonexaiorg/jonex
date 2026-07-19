#!/usr/bin/python3



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
from jonex_core.common import get_logger, require_tenant
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("domain.knowledge.search")


class SemanticSearchCapability(DomainCapability):


    DEFAULT_COLLECTION = "general_knowledge"

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        vector_client: Optional[VectorClient] = None,
    ):
        super().__init__()
        self.llm_client = llm_client
        self.vector_client = vector_client

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="knowledge.semantic_search",
            capability_name="语义检索",
            capability_type=CapabilityType.DOMAIN,
            version="v1",
            description="基于向量检索的语义搜索能力，支持文本相似度检索",
            tags=["knowledge", "search"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        if not request.payload:
            raise InvalidParameterError(message="语义检索请求 payload 不能为空")
        action = request.payload.get("action", "search")
        if action == "search" and "query" not in request.payload:
            raise InvalidParameterError(message="search 模式必须提供 query 参数")
        if action == "insert" and "texts" not in request.payload:
            raise InvalidParameterError(message="insert 模式必须提供 texts 参数")
        if action == "delete" and "ids" not in request.payload:
            raise InvalidParameterError(message="delete 模式必须提供 ids 参数")
        if action not in {"search", "insert", "delete"}:
            raise InvalidParameterError(message=f"不支持的 action: {action}")
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        await self.validate_input(request)

        tenant_id = require_tenant(request.tenant_id)
        action = request.payload.get("action", "search")
        collection = request.payload.get("collection_name", self.DEFAULT_COLLECTION)
        llm_client = self.llm_client or get_llm_client(tenant_id=tenant_id)
        vector_client = self.vector_client or get_vector_client(tenant_id=tenant_id)

        try:
            if action == "search":
                results = await self._search(
                    llm_client=llm_client,
                    vector_client=vector_client,
                    query=request.payload["query"],
                    collection=collection,
                    top_k=request.payload.get("top_k", 10),
                )
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"results": results, "collection": collection},
                    message=f"语义检索成功，返回 {len(results)} 条",
                )

            if action == "insert":
                inserted = await self._insert(
                    llm_client=llm_client,
                    vector_client=vector_client,
                    texts=request.payload["texts"],
                    collection=collection,
                    metadatas=request.payload.get("metadatas"),
                )
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"success": inserted, "collection": collection},
                    message="语义索引插入成功",
                )


            removed = await vector_client.delete(collection, request.payload["ids"])
            return CapabilityResponse.ok(
                request_id=request.request_id,
                data={"success": removed, "collection": collection},
                message="语义索引删除成功",
            )
        except CapabilityInvokeError:
            raise
        except Exception as e:
            logger.error(f"Semantic search processing failed: {e}")
            raise CapabilityInvokeError(
                message=f"语义检索处理失败: {e}",
                details={"action": action, "collection": collection},
                cause=e,
            )

    async def _search(
        self,
        llm_client: LLMClient,
        vector_client: VectorClient,
        query: str,
        collection: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        logger.info(f"Semantic search: query={query[:60]!r}, top_k={top_k}")
        query_vector = await llm_client.embedding(query)
        return await vector_client.search(collection, query_vector, top_k)

    async def _insert(
        self,
        llm_client: LLMClient,
        vector_client: VectorClient,
        texts: List[str],
        collection: str,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        logger.info(f"Semantic index insertion: count={len(texts)}, collection={collection}")
        vectors = [await llm_client.embedding(t) for t in texts]
        meta = metadatas or [{"text": t} for t in texts]
        return await vector_client.insert(collection, vectors, meta)
