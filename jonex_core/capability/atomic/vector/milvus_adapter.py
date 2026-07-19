#!/usr/bin/python3



from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.vector.base_vector import BaseVectorCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("atomic.vector.milvus")


class MilvusVectorCapability(BaseVectorCapability):


    def _build_metadata(self) -> CapabilityMetadata:

        return CapabilityMetadata(
            capability_id="vector.milvus",
            capability_name="Milvus 向量检索",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="Milvus 向量数据库，支持向量存储和相似度检索",
            tags=["vector", "milvus"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:

        if not request.payload:
            raise InvalidParameterError(message="向量检索请求 payload 不能为空")

        action = request.payload.get("action", "search")
        collection_name = request.payload.get("collection_name")

        if not collection_name:
            raise InvalidParameterError(message="必须提供 collection_name 参数")

        if action == "insert":
            if "vectors" not in request.payload:
                raise InvalidParameterError(message="insert 模式必须提供 vectors 参数")
        elif action == "search":
            if "query_vector" not in request.payload:
                raise InvalidParameterError(message="search 模式必须提供 query_vector 参数")
        elif action == "delete":
            if "ids" not in request.payload:
                raise InvalidParameterError(message="delete 模式必须提供 ids 参数")
        else:
            raise InvalidParameterError(message=f"不支持的 action: {action}")

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:

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
                    message="向量插入成功",
                )
            elif action == "search":
                query_vector = request.payload["query_vector"]
                top_k = request.payload.get("top_k", 10)
                results = await self.search(collection_name, query_vector, top_k)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"results": results},
                    message=f"向量检索成功，返回 {len(results)} 条结果",
                )
            elif action == "delete":
                ids = request.payload["ids"]
                result = await self.delete(collection_name, ids)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"success": result},
                    message="向量删除成功",
                )
        except Exception as e:
            logger.error(f"Milvus invocation failed: {e}")
            raise CapabilityInvokeError(
                message=f"Milvus 调用失败: {str(e)}",
                details={"action": action, "collection": collection_name},
                cause=e,
            )

    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:

        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] Inserting {len(vectors)} vectors into {collection_name}")
            return True












        raise CapabilityInvokeError(message="Milvus 未配置")

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:

        config = get_config()

        if config.ENV == "dev":

            logger.warning(f"[Mock] Searching {collection_name} for the Top-{top_k} similar vectors")
            return [
                {"id": f"mock_id_{i}", "score": 0.9 - i * 0.05, "metadata": {"source": "mock"}}
                for i in range(min(top_k, 5))
            ]


        raise CapabilityInvokeError(message="Milvus 未配置")

    async def delete(self, collection_name: str, ids: List[str]) -> bool:

        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] Deleting vectors from {collection_name}: count={len(ids)}")
            return True


        raise CapabilityInvokeError(message="Milvus 未配置")
