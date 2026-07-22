#!/usr/bin/python3
# -*- coding:utf-8 -*-

from typing import Optional

from jonex_core.capability.atomic.rag.client import RAGClient, get_rag_client
from jonex_core.capability.domain.base import DomainCapability
from jonex_core.capability.models import CapabilityMetadata, CapabilityRequest, CapabilityResponse, CapabilityType
from jonex_core.common import get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError, TenantIsolationError

logger = get_logger("domain.rag.text")


class DomainRAGText(DomainCapability):
    def __init__(self, rag_client: Optional[RAGClient] = None):
        super().__init__()
        self.rag_client = rag_client or get_rag_client()

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="rag.text",
            capability_name="Text RAG domain capability",
            capability_type=CapabilityType.DOMAIN,
            version="v1",
            description="Text modality RAG orchestration capability, invokes atomic.rag.lightrag.v1 downstream",
            tags=["rag", "text", "knowledge"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        if not request.payload:
            raise InvalidParameterError(message="Text RAG request payload cannot be empty")
        if request.tenant_id == "default":
            raise TenantIsolationError(message="Text RAG must explicitly pass tenant_id, Default tenant is prohibited")

        action = request.payload.get("action")
        if action not in {"ingest", "query", "delete", "get_task_status"}:
            raise InvalidParameterError(message=f"Unsupported action: {action}")
        if action == "ingest" and "file_path" not in request.payload:
            raise InvalidParameterError(message="ingest must provide file_path parameter")
        if action == "query" and "query" not in request.payload:
            raise InvalidParameterError(message="query must provide query parameter")
        if action == "delete" and "doc_id" not in request.payload:
            raise InvalidParameterError(message="delete must provide doc_id parameter")
        if action == "get_task_status" and "task_id" not in request.payload:
            raise InvalidParameterError(message="get_task_status must provide task_id parameter")
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        await self.validate_input(request)

        action = request.payload["action"]
        try:
            if action == "ingest":
                result = await self.rag_client.insert(
                    file_path=request.payload["file_path"],
                    tenant_id=request.tenant_id,
                    output_dir=request.payload.get("output_dir"),
                )
                return CapabilityResponse.ok(request_id=request.request_id, data=result, message="Text RAG ingestion task submitted")

            if action == "query":
                answer = await self.rag_client.query(
                    query=request.payload["query"],
                    tenant_id=request.tenant_id,
                    mode=request.payload.get("mode", "hybrid"),
                    top_k=request.payload.get("top_k", 5),
                )
                return CapabilityResponse.ok(request_id=request.request_id, data={"answer": answer}, message="Text RAG query succeeded")

            if action == "delete":
                removed = await self.rag_client.delete(
                    doc_id=request.payload["doc_id"],
                    tenant_id=request.tenant_id,
                )
                return CapabilityResponse.ok(request_id=request.request_id, data={"success": removed}, message="Text RAG deleted successfully")

            status = await self.rag_client.get_task_status(
                task_id=request.payload["task_id"],
                tenant_id=request.tenant_id,
            )
            return CapabilityResponse.ok(request_id=request.request_id, data=status, message="Text RAG task status query succeeded")
        except CapabilityInvokeError:
            raise
        except Exception as e:
            logger.error(f"Text RAG processing failed: {e}")
            raise CapabilityInvokeError(
                message=f"Text RAG processing failed: {e}",
                details={"action": action, "tenant_id": request.tenant_id},
                cause=e,
            )
