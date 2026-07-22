#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Knowledge base business capability DAO layer
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    DocStatus,
    KnowledgeDocument,
    KnowledgeSearchHistory,
    build_query_hash,
    normalize_query,
)


class KnowledgeDocumentDAO:
    """Knowledge base document DAO

    All queries force tenant_id condition to ensure tenant isolation.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        tenant_id: str,
        file_name: str,
        file_path: str,
        file_size: int = 0,
        mime_type: Optional[str] = None,
        extra_metadata: Optional[dict] = None,
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            status=DocStatus.PENDING.value,
            extra_metadata=extra_metadata or {},
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def get(self, doc_id: str, tenant_id: str) -> Optional[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.tenant_id == tenant_id,
            KnowledgeDocument.is_deleted == 0,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: str,
        status: Optional[DocStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.tenant_id == tenant_id,
            KnowledgeDocument.is_deleted == 0,
        )
        if status:
            stmt = stmt.where(KnowledgeDocument.status == status.value if isinstance(status, DocStatus) else status)
        stmt = (
            stmt.order_by(KnowledgeDocument.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def list_by_status(
        self,
        status: DocStatus,
        offset: int = 0,
        limit: int = 100,
    ) -> List[KnowledgeDocument]:
        """Query documents by status (cross-tenant, for background reconciliation)"""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.is_deleted == 0,
            KnowledgeDocument.status == status.value if isinstance(status, DocStatus) else status,
        )
        stmt = (
            stmt.order_by(KnowledgeDocument.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def list_by_ontology_status(
        self,
        statuses: list,
        limit: int = 50,
    ) -> List[KnowledgeDocument]:
        """Query documents by ontology extraction status (cross-tenant, for ontology reconciliation)"""
        str_statuses = [s.value if hasattr(s, "value") else s for s in statuses]
        stmt = (
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.is_deleted == 0,
                KnowledgeDocument.status.in_([DocStatus.READY.value]),
                KnowledgeDocument.ontology_status.in_(str_statuses),
            )
            .order_by(KnowledgeDocument.updated_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def list_by_knowledge_base(
        self,
        knowledge_base_id: str,
        tenant_id: str,
    ) -> List[KnowledgeDocument]:
        """Query indexed documents under same knowledge base (for building parse scope)"""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.tenant_id == tenant_id,
            KnowledgeDocument.is_deleted == 0,
            KnowledgeDocument.status.in_([DocStatus.READY.value, DocStatus.PARSING.value]),
            KnowledgeDocument.extra_metadata["knowledge_base_id"].astext == knowledge_base_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def update_status(
        self,
        doc_id: str,
        tenant_id: str,
        status: DocStatus,
        rag_task_id: Optional[str] = None,
        rag_doc_ids: Optional[List[str]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        values = {"status": status.value if isinstance(status, DocStatus) else status}
        if rag_task_id is not None:
            values["rag_task_id"] = rag_task_id
        if rag_doc_ids is not None:
            values["rag_doc_ids"] = rag_doc_ids
        if error_message is not None:
            values["error_message"] = error_message
        stmt = (
            update(KnowledgeDocument)
            .where(
                KnowledgeDocument.id == doc_id,
                KnowledgeDocument.tenant_id == tenant_id,
            )
            .values(**values)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def update_rag_task_id(
        self,
        doc_id: str,
        tenant_id: str,
        rag_task_id: str,
    ) -> bool:
        """Only update rag_task_id (for ontology retry scenario)."""
        stmt = (
            update(KnowledgeDocument)
            .where(
                KnowledgeDocument.id == doc_id,
                KnowledgeDocument.tenant_id == tenant_id,
            )
            .values(rag_task_id=rag_task_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def increment_ontology_retry(
        self,
        doc_id: str,
        tenant_id: str,
    ) -> bool:
        """Ontology retry count +1."""
        stmt = (
            update(KnowledgeDocument)
            .where(
                KnowledgeDocument.id == doc_id,
                KnowledgeDocument.tenant_id == tenant_id,
            )
            .values(ontology_retry_count=KnowledgeDocument.ontology_retry_count + 1)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def update_ontology_status(
        self,
        doc_id: str,
        tenant_id: str,
        status: str,
        error: Optional[str] = None,
    ) -> bool:
        """Update document ontology extraction status (operation on knowledge_documents table, not ontology.* tables)."""
        values = {"ontology_status": status}
        if error is not None:
            values["ontology_error"] = error
        stmt = (
            update(KnowledgeDocument)
            .where(
                KnowledgeDocument.id == doc_id,
                KnowledgeDocument.tenant_id == tenant_id,
            )
            .values(**values)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0


class KnowledgeSearchHistoryDAO:
    """Search history DAO

    All queries force tenant_id + user_id to ensure tenant and user isolation.
    Deletion uses soft delete (is_deleted = True).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[KnowledgeSearchHistory]:
        stmt = (
            select(KnowledgeSearchHistory)
            .where(
                KnowledgeSearchHistory.tenant_id == tenant_id,
                KnowledgeSearchHistory.user_id == user_id,
                KnowledgeSearchHistory.is_deleted == False,  # noqa: E712
            )
            .order_by(KnowledgeSearchHistory.searched_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def count_by_user(self, tenant_id: str, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(KnowledgeSearchHistory)
            .where(
                KnowledgeSearchHistory.tenant_id == tenant_id,
                KnowledgeSearchHistory.user_id == user_id,
                KnowledgeSearchHistory.is_deleted == False,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_today_by_user(self, tenant_id: str, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(KnowledgeSearchHistory)
            .where(
                KnowledgeSearchHistory.tenant_id == tenant_id,
                KnowledgeSearchHistory.user_id == user_id,
                KnowledgeSearchHistory.is_deleted == False,  # noqa: E712
                func.date(KnowledgeSearchHistory.searched_at) == func.current_date(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_existing(
        self,
        tenant_id: str,
        user_id: str,
        query_hash: str,
        domain_id: str,
    ) -> KnowledgeSearchHistory | None:
        stmt = select(KnowledgeSearchHistory).where(
            KnowledgeSearchHistory.tenant_id == tenant_id,
            KnowledgeSearchHistory.user_id == user_id,
            KnowledgeSearchHistory.query_hash == query_hash,
            KnowledgeSearchHistory.domain_id == domain_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_history(
        self,
        tenant_id: str,
        user_id: str,
        data: dict,
    ) -> KnowledgeSearchHistory:
        query_text = data.get("query", "")
        query_hash = build_query_hash(query_text)
        domain_id = data.get("domain_id") or data.get("domainId") or "all"
        if not domain_id or domain_id == "all":
            domain_id = "all"

        existing = await self.find_existing(tenant_id, user_id, query_hash, domain_id)

        if existing:
            existing.query = query_text
            existing.domain_name = data.get("domain_name") or data.get("domain") or data.get("domainName")
            existing.mode = data.get("mode") or "hybrid"
            existing.top_k = data.get("top_k") or data.get("topK") or 5
            existing.answer_preview = data.get("answer_preview") or data.get("answerPreview")
            existing.reference_count = data.get("reference_count") or data.get("referenceCount") or 0
            existing.result_count = data.get("result_count") or data.get("resultCount") or 0
            existing.duration_ms = data.get("duration_ms") or data.get("durationMs")
            existing.extra_metadata = data.get("extra_metadata") or data.get("extraMetadata") or {}
            existing.searched_at = datetime.now(timezone.utc)
            existing.updated_at = datetime.now(timezone.utc)
            existing.is_deleted = False  # Restore soft deleted record
            await self.session.flush()
            return existing

        new_item = KnowledgeSearchHistory(
            id=uuid.uuid4().hex,
            tenant_id=tenant_id,
            user_id=user_id,
            query=query_text,
            query_hash=query_hash,
            domain_id=domain_id,
            domain_name=data.get("domain_name") or data.get("domain") or data.get("domainName"),
            mode=data.get("mode") or "hybrid",
            top_k=data.get("top_k") or data.get("topK") or 5,
            status=data.get("status") or "done",
            answer_preview=data.get("answer_preview") or data.get("answerPreview"),
            reference_count=data.get("reference_count") or data.get("referenceCount") or 0,
            result_count=data.get("result_count") or data.get("resultCount") or 0,
            duration_ms=data.get("duration_ms") or data.get("durationMs"),
            extra_metadata=data.get("extra_metadata") or data.get("extraMetadata") or {},
        )
        self.session.add(new_item)
        await self.session.flush()
        return new_item

    async def delete_one(self, tenant_id: str, user_id: str, history_id: str) -> bool:
        stmt = (
            update(KnowledgeSearchHistory)
            .where(
                KnowledgeSearchHistory.id == history_id,
                KnowledgeSearchHistory.tenant_id == tenant_id,
                KnowledgeSearchHistory.user_id == user_id,
                KnowledgeSearchHistory.is_deleted == False,  # noqa: E712
            )
            .values(is_deleted=True, updated_at=func.now())
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def clear_by_user(self, tenant_id: str, user_id: str) -> int:
        stmt = (
            update(KnowledgeSearchHistory)
            .where(
                KnowledgeSearchHistory.tenant_id == tenant_id,
                KnowledgeSearchHistory.user_id == user_id,
                KnowledgeSearchHistory.is_deleted == False,  # noqa: E712
            )
            .values(is_deleted=True, updated_at=func.now())
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def prune_by_user(self, tenant_id: str, user_id: str, keep: int = 20) -> int:
        """Soft delete history records exceeding keep count"""
        keep_stmt = (
            select(KnowledgeSearchHistory.id)
            .where(
                KnowledgeSearchHistory.tenant_id == tenant_id,
                KnowledgeSearchHistory.user_id == user_id,
                KnowledgeSearchHistory.is_deleted == False,  # noqa: E712
            )
            .order_by(KnowledgeSearchHistory.searched_at.desc())
            .limit(keep)
        )
        keep_result = await self.session.execute(keep_stmt)
        keep_ids = [row[0] for row in keep_result.fetchall()]

        if not keep_ids:
            return 0

        stmt = (
            update(KnowledgeSearchHistory)
            .where(
                KnowledgeSearchHistory.tenant_id == tenant_id,
                KnowledgeSearchHistory.user_id == user_id,
                KnowledgeSearchHistory.is_deleted == False,  # noqa: E712
                KnowledgeSearchHistory.id.notin_(keep_ids),
            )
            .values(is_deleted=True, updated_at=func.now())
        )
        result = await self.session.execute(stmt)
        return result.rowcount
