"""
Knowledge base business capability wrapper class (business.knowledge_base.v1)

Implements the standard business capability pattern:
- Inherit BaseCapability
- Unify invoke Sidecar -> atomic-rag via _call_rag
- Only handle JSON protocol, not involved in file IO
"""

import logging
from typing import Optional

from jonex_core.capability import BaseCapability
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityType,
    CapabilityRequest,
    CapabilityResponse,
)
from jonex_core.common.exceptions import TenantIsolationError
from jonex_core.common.neo4j_client import ensure_ontology_schema

from .service import KnowledgeBaseService

logger = logging.getLogger(__name__)


class KnowledgeBaseCapability(BaseCapability):
    """Knowledge base Capability - Business capability layer"""

    def __init__(self):
        super().__init__()
        # Service internally manages DB session, not passed here
        self.service = KnowledgeBaseService()

    async def initialize(self) -> None:
        """Initialize: start background reconciliation loop + Neo4j schema initialize"""
        await self.service.start_reconciliation(interval=30)
        # Neo4j schema initialize (failure does not block service, only warning)
        try:
            await ensure_ontology_schema()
        except Exception as e:
            logger.warning(f"Neo4j schema initialize failed (ontology degradation, does not affect main path): {e}")
        logger.info("Knowledge base Capability initialized (Background reconciliation loop started)")

    async def shutdown(self) -> None:
        """Shutdown: stop background reconciliation loop + close Neo4j connection"""
        await self.service.stop_reconciliation()
        from jonex_core.common.neo4j_client import close_neo4j_driver
        await close_neo4j_driver()
        logger.info("Knowledge base Capability closed (background reconciliation loop stopped)")

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="knowledge_base",
            capability_name="Knowledge base Capability",
            capability_type=CapabilityType.BUSINESS,
            version="v1",
            description="Support complete business flow of Knowledge base: document upload, search, delete, async task reconciliation, etc.",
            author="jonex",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "upload", "list", "get", "query",
                            "delete", "reconcile_task",
                            "get_search_overview",
                            "list_search_history",
                            "save_search_history",
                            "delete_search_history",
                            "clear_search_history",
                            "get_parse_result_summary",
                            "get_parse_result_documents",
                            "get_parse_result_entities",
                            "get_parse_result_relationships",
                            "get_parse_result_graph_summary",
                            "get_parse_result_graph",
                            "get_document_parse_result",
                            "retry_ontology_extract",
                            "query_with_ontology",
                        ],
                        "description": "Operation type",
                    },
                    "data": {
                        "type": "object",
                        "description": "Operation data",
                    },
                },
                "required": ["action"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
            tags=["Knowledge base", "Document management", "Business capability"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        payload = request.payload
        action = payload.get("action")
        data = payload.get("data", {})

        if not action:
            return False

        valid_actions = [
            "upload", "list", "get", "query", "delete", "reconcile_task",
            "get_search_overview",
            "list_search_history",
            "save_search_history",
            "delete_search_history",
            "clear_search_history",
            "get_parse_result_summary", "get_parse_result_documents",
            "get_parse_result_entities", "get_parse_result_relationships",
            "get_parse_result_graph_summary", "get_parse_result_graph",
            "get_document_parse_result",
            "retry_ontology_extract",
            "query_with_ontology",
        ]
        if action not in valid_actions:
            return False

        # Required parameter validation
        if action == "get" and not data.get("doc_id"):
            return False
        if action == "delete" and not data.get("doc_id"):
            return False
        if action == "reconcile_task" and not data.get("doc_id"):
            return False
        if action == "save_search_history" and not data.get("query"):
            return False
        if action == "delete_search_history" and not data.get("history_id"):
            return False
        if action.startswith("get_parse_result") or action == "get_document_parse_result":
            if not data.get("knowledge_base_id"):
                return False
        if action == "retry_ontology_extract":
            if not data.get("document_id") or not data.get("knowledge_base_id"):
                return False
        if action == "query_with_ontology":
            if not data.get("query"):
                return False

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        payload = request.payload
        action = payload.get("action")
        data = payload.get("data", {})
        tenant_id = request.tenant_id

        # Prohibit default tenant
        if not tenant_id or tenant_id == "default":
            return CapabilityResponse.error(
                request.request_id, 403, "Default tenant is prohibited",
            )

        try:
            if action == "upload":
                result = await self.service.upload_document(
                    tenant_id=tenant_id,
                    file_name=data["file_name"],
                    file_path=data["file_path"],
                    file_size=data.get("file_size", 0),
                    mime_type=data.get("mime_type"),
                    knowledge_base_id=data.get("knowledge_base_id"),
                )
                return CapabilityResponse.ok(request.request_id, result, "Upload success")

            elif action == "list":
                docs = await self.service.list_documents(
                    tenant_id=tenant_id,
                    status=data.get("status"),
                    offset=data.get("offset", 0),
                    limit=data.get("limit", 20),
                )
                return CapabilityResponse.ok(
                    request.request_id,
                    {
                        "items": docs,
                        "total": len(docs),
                        "offset": data.get("offset", 0),
                        "limit": data.get("limit", 20),
                    },
                    "List retrieved successfully",
                )

            elif action == "get":
                doc = await self.service.get_document(
                    doc_id=data["doc_id"],
                    tenant_id=tenant_id,
                )
                # If still in PARSING, reconcile along the way
                if doc.get("status") == "parsing":
                    doc = await self.service.reconcile_task(
                        doc_id=data["doc_id"],
                        tenant_id=tenant_id,
                    )
                return CapabilityResponse.ok(request.request_id, doc, "Retrieved detail successfully")

            elif action == "query":
                answer = await self.service.query(
                    tenant_id=tenant_id,
                    query=data["query"],
                    mode=data.get("mode", "hybrid"),
                    top_k=data.get("top_k", 5),
                )
                return CapabilityResponse.ok(
                    request.request_id,
                    {"query": data["query"], "answer": answer},
                    "Query succeeded",
                )

            elif action == "delete":
                success = await self.service.delete_document(
                    doc_id=data["doc_id"],
                    tenant_id=tenant_id,
                )
                return CapabilityResponse.ok(
                    request.request_id,
                    {"doc_id": data["doc_id"], "deleted": success},
                    "Deleted successfully" if success else "Partial deletion failed",
                )

            elif action == "reconcile_task":
                doc = await self.service.reconcile_task(
                    doc_id=data["doc_id"],
                    tenant_id=tenant_id,
                )
                return CapabilityResponse.ok(request.request_id, doc, "Reconciliation completed")

            elif action == "get_search_overview":
                result = await self.service.get_search_overview(
                    tenant_id=tenant_id,
                    user_id=request.user_id or "anonymous",
                )
                return CapabilityResponse.ok(request.request_id, result, "Search overview retrieved successfully")

            elif action == "list_search_history":
                result = await self.service.list_search_history(
                    tenant_id=tenant_id,
                    user_id=data.get("user_id") or request.user_id or "anonymous",
                    limit=data.get("limit", 20),
                    offset=data.get("offset", 0),
                )
                return CapabilityResponse.ok(request.request_id, result, "Search history retrieved successfully")

            elif action == "save_search_history":
                result = await self.service.save_search_history(
                    tenant_id=tenant_id,
                    user_id=data.get("user_id") or request.user_id or "anonymous",
                    data=data,
                )
                return CapabilityResponse.ok(request.request_id, result, "Save search history succeeded")

            elif action == "delete_search_history":
                result = await self.service.delete_search_history(
                    tenant_id=tenant_id,
                    user_id=data.get("user_id") or request.user_id or "anonymous",
                    history_id=data.get("history_id"),
                )
                return CapabilityResponse.ok(request.request_id, result, "Delete search history succeeded")

            elif action == "clear_search_history":
                result = await self.service.clear_search_history(
                    tenant_id=tenant_id,
                    user_id=data.get("user_id") or request.user_id or "anonymous",
                )
                return CapabilityResponse.ok(request.request_id, result, "Clear search history succeeded")

            elif action == "get_parse_result_summary":
                result = await self.service.get_parse_result_summary(
                    knowledge_base_id=data["knowledge_base_id"],
                    tenant_id=tenant_id,
                )
                return CapabilityResponse.ok(request.request_id, result, "Parse result summary retrieved successfully")

            elif action == "get_parse_result_documents":
                result = await self.service.get_parse_result_documents(
                    knowledge_base_id=data["knowledge_base_id"],
                    tenant_id=tenant_id,
                    page=data.get("page", 1),
                    page_size=data.get("page_size", 20),
                    keyword=data.get("keyword"),
                    status=data.get("status"),
                )
                return CapabilityResponse.ok(request.request_id, result, "List documents succeeded")

            elif action == "get_parse_result_entities":
                result = await self.service.get_parse_result_entities(
                    knowledge_base_id=data["knowledge_base_id"],
                    tenant_id=tenant_id,
                    page=data.get("page", 1),
                    page_size=data.get("page_size", 20),
                    keyword=data.get("keyword"),
                    entity_type=data.get("entity_type"),
                    file_path=data.get("file_path"),
                    document_id=data.get("document_id"),
                )
                return CapabilityResponse.ok(request.request_id, result, "Entity list retrieved successfully")

            elif action == "get_parse_result_relationships":
                result = await self.service.get_parse_result_relationships(
                    knowledge_base_id=data["knowledge_base_id"],
                    tenant_id=tenant_id,
                    page=data.get("page", 1),
                    page_size=data.get("page_size", 20),
                    keyword=data.get("keyword"),
                    file_path=data.get("file_path"),
                    document_id=data.get("document_id"),
                    source_entity=data.get("source_entity"),
                    target_entity=data.get("target_entity"),
                )
                return CapabilityResponse.ok(request.request_id, result, "Relation list retrieved successfully")

            elif action == "get_parse_result_graph_summary":
                result = await self.service.get_parse_result_graph_summary(
                    knowledge_base_id=data["knowledge_base_id"],
                    tenant_id=tenant_id,
                )
                return CapabilityResponse.ok(request.request_id, result, "GetGraph summarySuccess")

            elif action == "get_parse_result_graph":
                result = await self.service.get_parse_result_graph(
                    knowledge_base_id=data["knowledge_base_id"],
                    tenant_id=tenant_id,
                    limit=data.get("limit", 200),
                    keyword=data.get("keyword"),
                    file_path=data.get("file_path"),
                    document_id=data.get("document_id"),
                )
                return CapabilityResponse.ok(request.request_id, result, "GetGraph dataSuccess")

            elif action == "get_document_parse_result":
                result = await self.service.get_document_parse_result(
                    knowledge_base_id=data["knowledge_base_id"],
                    tenant_id=tenant_id,
                )
                return CapabilityResponse.ok(request.request_id, result, "Document parse result retrieved successfully")

            elif action == "retry_ontology_extract":
                result = await self.service.rag.retry_ontology_extract(
                    document_id=data["document_id"],
                    knowledge_base_id=data["knowledge_base_id"],
                    tenant_id=tenant_id,
                    file_path=data.get("file_path", ""),
                )
                return CapabilityResponse.ok(request.request_id, result, "Ontology retry triggered")

            elif action == "query_with_ontology":
                result = await self.service.query_with_ontology(
                    tenant_id=tenant_id,
                    query=data["query"],
                    mode=data.get("mode", "hybrid"),
                    top_k=data.get("top_k", 5),
                    kb_id=data.get("knowledge_base_id"),
                )
                return CapabilityResponse.ok(request.request_id, result, "Query succeeded")

            else:
                return CapabilityResponse.error(
                    request.request_id, 400, f"Unsupported operation: {action}",
                )

        except TenantIsolationError as e:
            return CapabilityResponse.error(request.request_id, 403, str(e))
        except Exception as e:
            logger.exception(f"Execute Knowledge base Capability failed: {e}")
            return CapabilityResponse.error(
                request.request_id, 500, f"Execution failed: {str(e)}",
            )