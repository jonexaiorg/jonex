#!/usr/bin/python3


from typing import Optional

from jonex_core.capability.atomic.rag.client import RAGClient, get_rag_client
from jonex_core.capability.domain.base import DomainCapability
from jonex_core.capability.models import CapabilityMetadata, CapabilityRequest, CapabilityResponse, CapabilityType
from jonex_core.common import get_logger, require_tenant
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("domain.rag.text")


class DomainRAGText(DomainCapability):
    def __init__(self, rag_client: Optional[RAGClient] = None):
        super().__init__()
        self.rag_client = rag_client or get_rag_client()

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="rag.text",
            capability_name="文本 RAG 领域能力",
            capability_type=CapabilityType.DOMAIN,
            version="v1",
            description="文本模态 RAG 编排能力，向下调用 atomic.rag.lightrag.v1",
            tags=["rag", "text", "knowledge"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        if not request.payload:
            raise InvalidParameterError(message="文本 RAG 请求 payload 不能为空")
        require_tenant(request.tenant_id)

        action = request.payload.get("action")
        if action not in {"ingest", "query", "delete", "get_task_status"}:
            raise InvalidParameterError(message=f"不支持的 action: {action}")
        if action == "ingest" and "file_path" not in request.payload:
            raise InvalidParameterError(message="ingest 必须提供 file_path 参数")
        if action == "query" and "query" not in request.payload:
            raise InvalidParameterError(message="query 必须提供 query 参数")
        if action == "delete" and "doc_id" not in request.payload:
            raise InvalidParameterError(message="delete 必须提供 doc_id 参数")
        if action == "get_task_status" and "task_id" not in request.payload:
            raise InvalidParameterError(message="get_task_status 必须提供 task_id 参数")
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        await self.validate_input(request)

        tenant_id = require_tenant(request.tenant_id)
        action = request.payload["action"]
        try:
            if action == "ingest":
                result = await self.rag_client.insert(
                    file_path=request.payload["file_path"],
                    tenant_id=tenant_id,
                    output_dir=request.payload.get("output_dir"),
                )
                return CapabilityResponse.ok(request_id=request.request_id, data=result, message="文本 RAG 入库任务已提交")

            if action == "query":
                answer = await self.rag_client.query(
                    query=request.payload["query"],
                    tenant_id=tenant_id,
                    mode=request.payload.get("mode", "hybrid"),
                    top_k=request.payload.get("top_k", 5),
                )
                return CapabilityResponse.ok(request_id=request.request_id, data={"answer": answer}, message="文本 RAG 查询成功")

            if action == "delete":
                removed = await self.rag_client.delete(
                    doc_id=request.payload["doc_id"],
                    tenant_id=tenant_id,
                    knowledge_base_id=request.payload.get("knowledge_base_id", ""),
                )
                return CapabilityResponse.ok(request_id=request.request_id, data={"success": removed}, message="文本 RAG 删除成功")

            status = await self.rag_client.get_task_status(
                task_id=request.payload["task_id"],
                tenant_id=tenant_id,
            )
            return CapabilityResponse.ok(request_id=request.request_id, data=status, message="文本 RAG 任务状态查询成功")
        except CapabilityInvokeError:
            raise
        except Exception as e:
            logger.error(f"Text RAG processing failed: {e}")
            raise CapabilityInvokeError(
                message=f"文本 RAG 处理失败: {e}",
                details={"action": action, "tenant_id": tenant_id},
                cause=e,
            )
