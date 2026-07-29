#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Milvus 向量数据库适配器

对接 Milvus 向量数据库，提供向量存储和检索能力。
"""

from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.vector.base_vector import BaseVectorCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError
from jonex_core.common.i18n import translate

logger = get_logger("atomic.vector.milvus")


class MilvusVectorCapability(BaseVectorCapability):
    """Milvus 向量检索能力适配器"""

    def _build_metadata(self) -> CapabilityMetadata:
        """构建能力元数据"""
        return CapabilityMetadata(
            capability_id="vector.milvus",
            capability_name="Milvus 向量检索",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="Milvus 向量数据库，支持向量存储和相似度检索",
            tags=["vector", "milvus"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        """验证输入参数"""
        if not request.payload:
            raise InvalidParameterError(message=translate("err.vector.payload_required", fallback="向量检索请求 payload 不能为空"))

        action = request.payload.get("action", "search")
        collection_name = request.payload.get("collection_name")

        if not collection_name:
            raise InvalidParameterError(message=translate("err.vector.collection_required", fallback="必须提供 collection_name 参数"))

        if action == "insert":
            if "vectors" not in request.payload:
                raise InvalidParameterError(message=translate("err.capability.missing_action_param", params={"action": "insert", "param": "vectors"}, fallback="insert 模式必须提供 vectors 参数"))
        elif action == "search":
            if "query_vector" not in request.payload:
                raise InvalidParameterError(message=translate("err.capability.missing_action_param", params={"action": "search", "param": "query_vector"}, fallback="search 模式必须提供 query_vector 参数"))
        elif action == "delete":
            if "ids" not in request.payload:
                raise InvalidParameterError(message=translate("err.capability.missing_action_param", params={"action": "delete", "param": "ids"}, fallback="delete 模式必须提供 ids 参数"))
        else:
            raise InvalidParameterError(message=translate("err.capability.unsupported_action", params={"action": action}, fallback=f"不支持的 action: {action}"))

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """执行向量检索能力调用"""
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
            logger.error(f"Milvus 调用失败: {e}")
            raise CapabilityInvokeError(
                message=translate("err.vector.invoke_failed", fallback="向量检索调用失败"),
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
        插入向量数据

        注意：当前为 mock 实现，实际部署时需要接入真实 Milvus。
        """
        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] 插入 {len(vectors)} 条向量到 {collection_name}")
            return True

        # TODO: 接入真实的 Milvus 客户端
        # from pymilvus import connections, Collection
        # connections.connect(
        #     alias="default",
        #     host=config.MILVUS_HOST,
        #     port=config.MILVUS_PORT,
        # )
        # collection = Collection(collection_name)
        # mr = collection.insert(data)
        # return mr.succ_count == len(vectors)

        raise CapabilityInvokeError(message=translate("err.capability.service_not_configured", params={"service_name": "Milvus"}, fallback="Milvus 未配置"))

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        向量相似度检索

        注意：当前为 mock 实现，实际部署时需要接入真实 Milvus。
        """
        config = get_config()

        if config.ENV == "dev":
            # Mock 实现：返回模拟检索结果
            logger.warning(f"[Mock] 在 {collection_name} 中检索 Top-{top_k} 相似向量")
            return [
                {"id": f"mock_id_{i}", "score": 0.9 - i * 0.05, "metadata": {"source": "mock"}}
                for i in range(min(top_k, 5))
            ]

        # TODO: 接入真实的 Milvus 客户端
        raise CapabilityInvokeError(message=translate("err.capability.service_not_configured", params={"service_name": "Milvus"}, fallback="Milvus 未配置"))

    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """
        删除向量数据

        注意：当前为 mock 实现，实际部署时需要接入真实 Milvus。
        """
        config = get_config()

        if config.ENV == "dev":
            logger.warning(f"[Mock] 从 {collection_name} 删除 {len(ids)} 条向量")
            return True

        # TODO: 接入真实的 Milvus 客户端
        raise CapabilityInvokeError(message=translate("err.capability.service_not_configured", params={"service_name": "Milvus"}, fallback="Milvus 未配置"))
