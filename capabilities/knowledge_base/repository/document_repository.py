#!/usr/bin/python3



from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.repository import BaseRepository

from ..models import DocStatus, KnowledgeDocument, OntologyStatus


def _value(status: str | DocStatus | OntologyStatus | None) -> str | None:
    return status.value if hasattr(status, "value") else status


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    model = KnowledgeDocument

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_documents(
        self,
        tenant_id: str,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[KnowledgeDocument]:
        conditions = []
        if status:
            conditions.append(KnowledgeDocument.status == status)
        return await self.list_all(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
            extra_conditions=conditions,
        )

    async def list_by_knowledge_base(
        self,
        tenant_id: str,
        knowledge_base_id: str,
    ) -> list[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.tenant_id == self._tenant_id(tenant_id),
            KnowledgeDocument.is_deleted == 0,
            KnowledgeDocument.knowledge_base_id == knowledge_base_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def list_by_folder(
        self,
        tenant_id: str,
        folder_id: str,
    ) -> list[KnowledgeDocument]:

        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.tenant_id == self._tenant_id(tenant_id),
            KnowledgeDocument.is_deleted == 0,
            KnowledgeDocument.folder_id == folder_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def list_by_status_for_reconciliation(
        self,
        status: str | DocStatus,
        limit: int = 100,
    ) -> list[KnowledgeDocument]:


        stmt = (
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.is_deleted == 0,
                KnowledgeDocument.status == _value(status),
            )
            .order_by(KnowledgeDocument.updated_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def list_by_ontology_status_for_reconciliation(
        self,
        statuses: list[str | OntologyStatus],
        limit: int = 50,
    ) -> list[KnowledgeDocument]:


        stmt = (
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.is_deleted == 0,
                KnowledgeDocument.status == DocStatus.READY.value,
                KnowledgeDocument.ontology_status.in_([_value(status) for status in statuses]),
            )
            .order_by(KnowledgeDocument.updated_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def set_status(
        self,
        doc: KnowledgeDocument,
        status: str | DocStatus,
        *,
        rag_task_id: str | None = None,
        rag_doc_ids: list[str] | None = None,
        error_message: str | None = None,
    ) -> KnowledgeDocument:
        fresh = await self.get_by_id(doc.id, doc.tenant_id)
        if fresh is None:

            fresh = await self.session.merge(doc)
        fresh.status = _value(status)
        if rag_task_id is not None:
            fresh.rag_task_id = rag_task_id
        if rag_doc_ids is not None:
            fresh.rag_doc_ids = rag_doc_ids
        if error_message is not None:
            fresh.error_message = error_message
        await self.session.flush()
        return fresh

    async def set_ontology_status(
        self,
        doc: KnowledgeDocument,
        status: str | OntologyStatus,
        *,
        error: str | None = None,
        increment_retry: bool = False,
    ) -> KnowledgeDocument:
        fresh = await self.get_by_id(doc.id, doc.tenant_id)
        if fresh is None:
            fresh = await self.session.merge(doc)
        fresh.ontology_status = _value(status)
        if error is not None:
            fresh.ontology_error = error
        if increment_retry:
            fresh.ontology_retry_count = (fresh.ontology_retry_count or 0) + 1
        await self.session.flush()
        return fresh

    async def count_by_knowledge_bases(self, tenant_id: str, kb_ids: list[str]) -> dict[str, int]:

        if not kb_ids:
            return {}
        deduped = list(dict.fromkeys(kb_ids))
        stmt = (
            select(KnowledgeDocument.knowledge_base_id, func.count())
            .where(
                *self._tenant_conditions(tenant_id),
                *self._soft_delete_conditions(),
                KnowledgeDocument.knowledge_base_id.in_(deduped),
            )
            .group_by(KnowledgeDocument.knowledge_base_id)
        )
        rows = await self.session.execute(stmt)
        return {row[0]: row[1] for row in rows.all()}

    async def count_by_source_type(self, tenant_id: str, knowledge_base_id: str) -> dict[str, int]:

        stmt = (
            select(KnowledgeDocument.data_source_type, func.count())
            .where(
                *self._tenant_conditions(tenant_id),
                *self._soft_delete_conditions(),
                KnowledgeDocument.knowledge_base_id == knowledge_base_id,
                KnowledgeDocument.data_source_type.is_not(None),
            )
            .group_by(KnowledgeDocument.data_source_type)
        )
        rows = await self.session.execute(stmt)
        return {row[0]: row[1] for row in rows.all()}

    async def get_by_ids(self, doc_ids: list[str], tenant_id: str) -> list[KnowledgeDocument]:

        if not doc_ids:
            return []
        deduped = list(dict.fromkeys(doc_ids))
        conditions = [
            self._primary_key().in_(deduped),
            *self._tenant_conditions(tenant_id),
            *self._soft_delete_conditions(),
        ]
        result = await self.session.execute(
            select(KnowledgeDocument).where(*conditions)
        )
        return list(result.scalars())


    async def reset_ontology_for_kb(self, tenant_id: str, knowledge_base_id: str) -> int:

        from sqlalchemy import update

        stmt = (
            update(KnowledgeDocument)
            .where(
                KnowledgeDocument.tenant_id == tenant_id,
                KnowledgeDocument.knowledge_base_id == knowledge_base_id,
                KnowledgeDocument.status == DocStatus.READY.value,
                KnowledgeDocument.is_deleted == 0,
            )
            .values(
                ontology_status=OntologyStatus.PENDING.value,
                ontology_retry_count=0,
                ontology_error=None,
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0


__all__ = ["KnowledgeDocumentRepository"]
