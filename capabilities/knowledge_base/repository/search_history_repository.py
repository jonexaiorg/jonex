#!/usr/bin/python3



from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.repository import BaseRepository

from ..models import KnowledgeSearchHistory, build_query_hash


class KnowledgeSearchHistoryRepository(BaseRepository[KnowledgeSearchHistory]):
    model = KnowledgeSearchHistory

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_by_user(
        self,
        tenant_id: str,
        user_id: str,
        knowledge_base_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[KnowledgeSearchHistory]:
        conditions = [
            KnowledgeSearchHistory.tenant_id == self._tenant_id(tenant_id),
            KnowledgeSearchHistory.user_id == user_id,
            KnowledgeSearchHistory.is_deleted == 0,
        ]
        if knowledge_base_id:
            conditions.append(KnowledgeSearchHistory.knowledge_base_id == knowledge_base_id)
        stmt = (
            select(KnowledgeSearchHistory)
            .where(*conditions)
            .order_by(KnowledgeSearchHistory.searched_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def count_by_user(
        self,
        tenant_id: str,
        user_id: str,
        knowledge_base_id: str,
    ) -> int:
        conditions = [
            KnowledgeSearchHistory.tenant_id == self._tenant_id(tenant_id),
            KnowledgeSearchHistory.user_id == user_id,
            KnowledgeSearchHistory.is_deleted == 0,
        ]
        if knowledge_base_id:
            conditions.append(KnowledgeSearchHistory.knowledge_base_id == knowledge_base_id)
        result = await self.session.execute(
            select(func.count())
            .select_from(KnowledgeSearchHistory)
            .where(*conditions)
        )
        return result.scalar_one()

    async def upsert_for_user(
        self,
        tenant_id: str,
        user_id: str,
        data: dict,
    ) -> KnowledgeSearchHistory:
        normalized_tenant = self._tenant_id(tenant_id)
        query = data["query"]
        values = {
            "tenant_id": normalized_tenant,
            "user_id": user_id,
            "query": query,
            "query_hash": build_query_hash(query),
            "knowledge_base_id": data["knowledge_base_id"],
            "mode": data.get("mode") or "hybrid",
            "top_k": data.get("top_k") or 5,
            "status": data.get("status") or "done",
            "answer_preview": data.get("answer_preview"),
            "reference_count": data.get("reference_count") or 0,
            "result_count": data.get("result_count") or 0,
            "duration_ms": data.get("duration_ms"),
            "extra_metadata": data.get("extra_metadata") or {},
            "is_deleted": 0,
        }
        stmt = (
            insert(KnowledgeSearchHistory)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[
                    KnowledgeSearchHistory.tenant_id,
                    KnowledgeSearchHistory.user_id,
                    KnowledgeSearchHistory.query_hash,
                    KnowledgeSearchHistory.knowledge_base_id,
                ],
                set_={
                    **values,
                    "searched_at": func.now(),
                    "updated_at": func.now(),
                },
            )
            .returning(KnowledgeSearchHistory)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_for_user(
        self,
        tenant_id: str,
        user_id: str,
        knowledge_base_id: str,
        history_id: str,
    ) -> bool:
        history = await self.get_by_id(history_id, tenant_id)
        if (
            not history
            or history.user_id != user_id
            or (knowledge_base_id and history.knowledge_base_id != knowledge_base_id)
        ):
            return False
        history.is_deleted = 1
        await self.session.flush()
        return True

    async def clear_for_user(self, tenant_id: str, user_id: str, knowledge_base_id: str) -> int:
        histories = await self.list_by_user(
            tenant_id,
            user_id,
            knowledge_base_id=knowledge_base_id,
            offset=0,
            limit=1000,
        )
        for history in histories:
            history.is_deleted = 1
        await self.session.flush()
        return len(histories)


__all__ = ["KnowledgeSearchHistoryRepository"]
