

import logging

from neo4j.exceptions import AuthError, ServiceUnavailable, SessionExpired, TransientError

from jonex_core.common.database import get_db_session
from jonex_core.common.neo4j_client import get_neo4j_driver
from jonex_core.common.tenant import require_tenant

from ..dtos import (
    OntologyGraphRequest,
    OntologyInstanceListRequest,
    OntologyNeighborRequest,
    OntologyRelationListRequest,
    OntologyStatsRequest,
)
from ..models import KnowledgeDocument, KnowledgeInfo
from ..repository import KnowledgeDocumentRepository, OntologyGraphRepository
from ..repository.knowledge_info_repository import KnowledgeInfoRepository
from .document_service import _payload

logger = logging.getLogger(__name__)


_NEO4J_DOWN_ERRORS = (ServiceUnavailable, SessionExpired, TransientError, AuthError, OSError)
_DEGRADED_REASON = "图数据库（Neo4j）暂不可用，知识图谱无法展示，基础知识库能力不受影响"


class OntologyQueryService:


    async def get_kb_statistics(self, tenant_id: str, request) -> dict:

        tenant_id = require_tenant(tenant_id)
        req = OntologyStatsRequest(**_payload(request))
        kb_id = req.knowledge_base_id

        async with get_db_session() as session:
            doc_count = await KnowledgeDocumentRepository(session).count(
                tenant_id,
                extra_conditions=[KnowledgeDocument.knowledge_base_id == kb_id],
            )
            kb_info = await KnowledgeInfoRepository(session).get_by_id(kb_id, tenant_id)

        gdao = OntologyGraphRepository(get_neo4j_driver())
        try:
            instance_count = await gdao.count_entities(tenant_id, kb_id)
            relation_count = await gdao.count_relations(tenant_id, kb_id)
            ontology_degraded = False
        except _NEO4J_DOWN_ERRORS as e:

            logger.warning("[ontology] Statistics degraded: Neo4j unavailable kb=%s err=%s", kb_id, e)
            instance_count = 0
            relation_count = 0
            ontology_degraded = True

        return {
            "knowledge_base_id": kb_id,
            "knowledge_base_name": kb_info.name if kb_info else "",
            "last_update_time": kb_info.updated_at.isoformat() if kb_info and kb_info.updated_at else None,
            "source_file_count": doc_count,
            "ontology_instance_count": instance_count,
            "ontology_relation_count": relation_count,
            "ontology_degraded": ontology_degraded,
        }

    async def list_instances(self, tenant_id: str, request) -> dict:

        tenant_id = require_tenant(tenant_id)
        req = OntologyInstanceListRequest(**_payload(request))
        offset = (req.page - 1) * req.page_size
        gdao = OntologyGraphRepository(get_neo4j_driver())
        items, total = await gdao.list_entities(
            tenant_id,
            req.knowledge_base_id,
            offset,
            req.page_size,
            entity_type=req.entity_type,
            keyword=req.keyword,
            include_unknown=req.include_unknown,
        )
        return {
            "items": items,
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        }

    async def list_relations(self, tenant_id: str, request) -> dict:

        tenant_id = require_tenant(tenant_id)
        req = OntologyRelationListRequest(**_payload(request))
        offset = (req.page - 1) * req.page_size
        gdao = OntologyGraphRepository(get_neo4j_driver())
        items, total = await gdao.list_relations(
            tenant_id,
            req.knowledge_base_id,
            offset,
            req.page_size,
            relation_type=req.relation_type,
            source_name=req.source_name,
            target_name=req.target_name,
            source_type=req.source_type,
            target_type=req.target_type,
        )
        return {
            "items": items,
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        }

    async def list_entity_types(self, tenant_id: str, request) -> dict:

        tenant_id = require_tenant(tenant_id)
        req = OntologyStatsRequest(**_payload(request))
        kb_id = req.knowledge_base_id

        from .ontology_compiler import OntologyCompiler

        schema = await OntologyCompiler().get_compiled_schema(tenant_id, kb_id) or {}
        gdao = OntologyGraphRepository(get_neo4j_driver())
        counts = await gdao.count_entities_by_type(tenant_id, kb_id)
        if not req.include_unknown:
            counts.pop("unknown", None)

        items = []
        known = set()
        for et in schema.get("entity_types", []):
            name = et["name"]
            known.add(name)
            cnt = counts.get(name, 0)
            items.append({
                "name": name,
                "display_name": et.get("display_name") or name,
                "description": et.get("description", ""),
                "status": et.get("status", "active"),
                "build_status": "built" if cnt > 0 else "empty",
                "instance_count": cnt,
                "attributes": et.get("attributes", []),
                "source_object_id": et.get("source_object_id"),
            })

        for t, c in counts.items():
            if t not in known:
                items.append({
                    "name": t, "display_name": t, "description": "",
                    "status": "unschematized", "build_status": "built",
                    "instance_count": c, "attributes": [], "source_object_id": None,
                })
        return {"items": items, "total": len(items)}

    async def get_kb_graph(self, tenant_id: str, request) -> dict:

        tenant_id = require_tenant(tenant_id)
        req = OntologyGraphRequest(**_payload(request))
        gdao = OntologyGraphRepository(get_neo4j_driver())
        try:
            result = await gdao.get_kb_graph(
                tenant_id,
                req.knowledge_base_id,
                limit=req.limit,
                entity_types=req.entity_types,
            )
            result["degraded"] = False
            return result
        except _NEO4J_DOWN_ERRORS as e:
            logger.warning("[ontology] Graph query degraded: Neo4j unavailable kb=%s err=%s", req.knowledge_base_id, e)
            return {
                "nodes": [], "edges": [],
                "total_nodes": 0, "total_relations": 0,
                "type_counts": {}, "returned_nodes": 0, "returned_edges": 0,
                "truncated": False, "limit": req.limit,
                "degraded": True, "degraded_reason": _DEGRADED_REASON,
            }

    async def expand_ontology_neighbors(self, tenant_id: str, request) -> dict:

        tenant_id = require_tenant(tenant_id)
        req = OntologyNeighborRequest(**_payload(request))
        gdao = OntologyGraphRepository(get_neo4j_driver())
        try:
            result = await gdao.expand_neighbors(
                tenant_id,
                req.knowledge_base_id,
                req.entity_type,
                req.canonical_name,
                limit=req.limit,
            )
            result["degraded"] = False
            return result
        except _NEO4J_DOWN_ERRORS as e:
            logger.warning("[ontology] Neighbor expansion degraded: Neo4j unavailable kb=%s err=%s", req.knowledge_base_id, e)
            return {"nodes": [], "edges": [], "degraded": True, "degraded_reason": _DEGRADED_REASON}

    async def list_relation_types(self, tenant_id: str, request) -> dict:

        tenant_id = require_tenant(tenant_id)
        req = OntologyStatsRequest(**_payload(request))
        kb_id = req.knowledge_base_id

        from .ontology_compiler import OntologyCompiler

        schema = await OntologyCompiler().get_compiled_schema(tenant_id, kb_id) or {}
        gdao = OntologyGraphRepository(get_neo4j_driver())
        counts = await gdao.count_relations_by_type(tenant_id, kb_id)

        entity_display = {
            et["name"]: (et.get("display_name") or et["name"])
            for et in schema.get("entity_types", [])
        }

        items = []
        known = set()
        for rt in schema.get("relation_types", []):
            name = rt["name"]
            known.add(name)
            cnt = counts.get(name, 0)
            src, tgt = rt.get("source"), rt.get("target")
            items.append({
                "name": name,
                "display_name": rt.get("display_name") or name,
                "description": rt.get("description", ""),
                "source": src,
                "target": tgt,
                "source_display_name": entity_display.get(src, src),
                "target_display_name": entity_display.get(tgt, tgt),
                "cardinality": rt.get("cardinality", "custom"),
                "status": rt.get("status", "active"),
                "build_status": "built" if cnt > 0 else "empty",
                "instance_count": cnt,
                "source_relation_id": rt.get("source_relation_id"),
            })
        for t, c in counts.items():
            if t not in known:
                items.append({
                    "name": t, "display_name": t, "description": "",
                    "source": None, "target": None,
                    "source_display_name": None, "target_display_name": None,
                    "cardinality": "custom",
                    "status": "unschematized", "build_status": "built",
                    "instance_count": c, "source_relation_id": None,
                })
        return {"items": items, "total": len(items)}