

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common.tenant import require_tenant

from ..dtos import (
    DocumentParseResultRequest,
    ParseResultDocumentListRequest,
    ParseResultEntityListRequest,
    ParseResultGraphRequest,
    ParseResultRelationshipListRequest,
    ParseResultScopeRequest,
)
from .document_service import _payload


class ParseResultService:
    async def get_summary(self, tenant_id: str, request: ParseResultScopeRequest | dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = ParseResultScopeRequest(**_payload(request))
        return await get_rag_client().get_storage_summary(req.knowledge_base_id, tenant_id)

    async def list_documents(
        self,
        tenant_id: str,
        request: ParseResultDocumentListRequest | dict,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = ParseResultDocumentListRequest(**_payload(request))
        return await get_rag_client().get_storage_documents(
            knowledge_base_id=req.knowledge_base_id,
            tenant_id=tenant_id,
            page=req.page,
            page_size=req.page_size,
            keyword=req.keyword,
            status=req.status,
        )

    async def list_entities(
        self,
        tenant_id: str,
        request: ParseResultEntityListRequest | dict,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = ParseResultEntityListRequest(**_payload(request))
        return await get_rag_client().get_storage_entities(
            knowledge_base_id=req.knowledge_base_id,
            tenant_id=tenant_id,
            page=req.page,
            page_size=req.page_size,
            keyword=req.keyword,
            entity_type=req.entity_type,
            file_path=req.file_path,
            document_id=req.document_id,
        )

    async def list_relationships(
        self,
        tenant_id: str,
        request: ParseResultRelationshipListRequest | dict,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = ParseResultRelationshipListRequest(**_payload(request))
        return await get_rag_client().get_storage_relationships(
            knowledge_base_id=req.knowledge_base_id,
            tenant_id=tenant_id,
            page=req.page,
            page_size=req.page_size,
            keyword=req.keyword,
            file_path=req.file_path,
            document_id=req.document_id,
            source_entity=req.source_entity,
            target_entity=req.target_entity,
        )

    async def get_graph_summary(
        self,
        tenant_id: str,
        request: ParseResultScopeRequest | dict,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = ParseResultScopeRequest(**_payload(request))
        return await get_rag_client().get_storage_graph_summary(req.knowledge_base_id, tenant_id)

    async def get_graph(self, tenant_id: str, request: ParseResultGraphRequest | dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = ParseResultGraphRequest(**_payload(request))
        return await get_rag_client().get_storage_graph(
            knowledge_base_id=req.knowledge_base_id,
            tenant_id=tenant_id,
            limit=req.limit,
            keyword=req.keyword,
            file_path=req.file_path,
            document_id=req.document_id,
        )

    async def get_document_parse_result(
        self,
        tenant_id: str,
        request: DocumentParseResultRequest | dict,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = DocumentParseResultRequest(**_payload(request))
        result = await get_rag_client().get_document_parse_result(
            req.knowledge_base_id,
            tenant_id,
            document_id=req.document_id,
        )
        if isinstance(result, dict):
            result["document_id"] = req.document_id
        return result


__all__ = ["ParseResultService"]
