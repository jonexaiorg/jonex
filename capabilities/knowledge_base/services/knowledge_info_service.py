#!/usr/bin/python3


import uuid

from sqlalchemy import select

from jonex_core.common import get_db_session
from jonex_core.common.tenant import require_tenant

from ..models.knowledge_info import KnowledgeInfo
from ..repository.knowledge_info_repository import KnowledgeInfoRepository


class KnowledgeInfoService:


    async def create(self, tenant_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeInfoRepository(session)
            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                space_id=data["space_id"],
                name=data["name"],
                description=data.get("description"),
                data_source_types=data.get("data_source_types", []),
                status=data.get("status", "synced"),
                owner_id=data.get("owner_id"),
            )
            await session.commit()
            return obj.to_dict()

    async def get(self, kb_id: str, tenant_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            from ..models.space import Space

            repo = KnowledgeInfoRepository(session)
            obj = await repo.get_required(kb_id, tenant_id)

            space_name = ""
            space_row = await session.execute(
                select(Space.name).where(
                    Space.id == obj.space_id,
                    Space.tenant_id == tenant_id,
                    Space.is_deleted == 0,
                )
            )
            result = space_row.scalar()
            if result:
                space_name = result


            from ..repository.document_repository import KnowledgeDocumentRepository
            doc_count_map = await KnowledgeDocumentRepository(session).count_by_knowledge_bases(
                tenant_id, [obj.id]
            )
            data = obj.to_dict(space_name=space_name)
            data["document_count"] = doc_count_map.get(obj.id, 0)




        from .ontology_query_service import OntologyQueryService
        try:
            stats = await OntologyQueryService().get_kb_statistics(
                tenant_id, {"knowledge_base_id": kb_id}
            )
            data["entity_count"] = stats.get("ontology_instance_count", 0)
            data["relation_count"] = stats.get("ontology_relation_count", 0)
            data["ontology_degraded"] = stats.get("ontology_degraded", False)
        except Exception:
            data["entity_count"] = 0
            data["relation_count"] = 0
            data["ontology_degraded"] = True

        return data

    async def list(self, tenant_id: str, space_id: str = None, status: str = None,
                   keyword: str = None, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            from ..models.space import Space

            repo = KnowledgeInfoRepository(session)
            conditions = []
            if space_id:
                conditions.append(KnowledgeInfo.space_id == space_id)
            if status:
                conditions.append(KnowledgeInfo.status == status)

            items = await repo.list_all(tenant_id, offset, limit, extra_conditions=conditions)
            total = await repo.count(tenant_id, extra_conditions=conditions)


            from ..repository.document_repository import KnowledgeDocumentRepository
            doc_count_map = await KnowledgeDocumentRepository(session).count_by_knowledge_bases(
                tenant_id, [o.id for o in items]
            )


            space_ids = list({o.space_id for o in items})
            space_name_map: dict[str, str] = {}
            if space_ids:
                space_rows = await session.execute(
                    select(Space.id, Space.name).where(
                        Space.id.in_(space_ids),
                        Space.tenant_id == tenant_id,
                        Space.is_deleted == 0,
                    )
                )
                space_name_map = {row[0]: row[1] for row in space_rows.all()}

            result_items = []
            for o in items:
                d = o.to_dict(space_name=space_name_map.get(o.space_id, ""))
                d["document_count"] = doc_count_map.get(o.id, 0)
                result_items.append(d)
            if keyword:
                kw = keyword.lower()
                result_items = [
                    i for i in result_items
                    if kw in (i.get("name") or "").lower()
                    or kw in (i.get("description") or "").lower()
                ]

            return {
                "items": result_items,
                "total": len(result_items) if keyword else total,
                "offset": offset, "limit": limit,
            }

    async def update(self, kb_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeInfoRepository(session)
            await repo.get_required(kb_id, tenant_id)
            updatable = {"name", "description", "data_source_types", "status", "space_id", "owner_id"}
            values = {k: v for k, v in data.items() if k in updatable and v is not None}
            if values:
                obj = await repo.update(kb_id, tenant_id, **values)
                await session.commit()
                return obj.to_dict()
            obj = await repo.get_required(kb_id, tenant_id)
            return obj.to_dict()

    async def delete(self, kb_id: str, tenant_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeInfoRepository(session)
            await repo.get_required(kb_id, tenant_id)
            await repo.delete_soft(kb_id, tenant_id)


            from ..repository.ontology_synonym_repository import OntologySynonymRepository
            syn_repo = OntologySynonymRepository(session)
            for group in await syn_repo.list_all_by_kb(tenant_id, kb_id):
                await syn_repo.delete_soft(group)

            await session.commit()
            return {"deleted": True}