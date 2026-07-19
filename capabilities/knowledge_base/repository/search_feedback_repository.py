#!/usr/bin/python3



from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.repository import BaseRepository

from ..models import KnowledgeSearchFeedback


class KnowledgeSearchFeedbackRepository(BaseRepository[KnowledgeSearchFeedback]):
    model = KnowledgeSearchFeedback

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_by_knowledge_base(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        feedback_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[KnowledgeSearchFeedback]:

        conditions = [
            KnowledgeSearchFeedback.tenant_id == self._tenant_id(tenant_id),
            KnowledgeSearchFeedback.knowledge_base_id == knowledge_base_id,
        ]
        if feedback_type:
            conditions.append(KnowledgeSearchFeedback.feedback_type == feedback_type)

        stmt = (
            select(KnowledgeSearchFeedback)
            .where(*conditions)
            .order_by(KnowledgeSearchFeedback.searched_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def count_by_knowledge_base(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        feedback_type: str | None = None,
    ) -> int:

        conditions = [
            KnowledgeSearchFeedback.tenant_id == self._tenant_id(tenant_id),
            KnowledgeSearchFeedback.knowledge_base_id == knowledge_base_id,
        ]
        if feedback_type:
            conditions.append(KnowledgeSearchFeedback.feedback_type == feedback_type)

        result = await self.session.execute(
            select(func.count())
            .select_from(KnowledgeSearchFeedback)
            .where(*conditions)
        )
        return result.scalar_one()

    async def create_feedback(
        self,
        tenant_id: str,
        data: dict,
    ) -> KnowledgeSearchFeedback:

        record = KnowledgeSearchFeedback(
            tenant_id=self._tenant_id(tenant_id),
            user_id=data["user_id"],
            session_id=data["session_id"],
            query=data["query"],
            answer_preview=data.get("answer_preview"),
            knowledge_base_id=data["knowledge_base_id"],
            knowledge_base_name=data.get("knowledge_base_name"),
            feedback_type=data["feedback_type"],
            adopted=False,
            searched_at=data.get("searched_at"),
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def toggle_adopted(
        self,
        tenant_id: str,
        feedback_id: str,
    ) -> KnowledgeSearchFeedback | None:

        conditions = [
            KnowledgeSearchFeedback.id == feedback_id,
            KnowledgeSearchFeedback.tenant_id == self._tenant_id(tenant_id),
        ]
        stmt = select(KnowledgeSearchFeedback).where(*conditions)
        result = await self.session.execute(stmt)
        record: KnowledgeSearchFeedback | None = result.scalar_one_or_none()
        if not record:
            return None
        record.adopted = not record.adopted
        await self.session.flush()
        return record

    async def get_stats(
        self,
        tenant_id: str,
        knowledge_base_id: str,
    ) -> dict:

        conditions = [
            KnowledgeSearchFeedback.tenant_id == self._tenant_id(tenant_id),
            KnowledgeSearchFeedback.knowledge_base_id == knowledge_base_id,
        ]


        total_result = await self.session.execute(
            select(func.count()).select_from(KnowledgeSearchFeedback).where(*conditions)
        )
        total = total_result.scalar_one()


        like_conditions = conditions + [KnowledgeSearchFeedback.feedback_type == "like"]
        like_result = await self.session.execute(
            select(func.count()).select_from(KnowledgeSearchFeedback).where(*like_conditions)
        )
        like_count = like_result.scalar_one()


        dislike_conditions = conditions + [KnowledgeSearchFeedback.feedback_type == "dislike"]
        dislike_result = await self.session.execute(
            select(func.count()).select_from(KnowledgeSearchFeedback).where(*dislike_conditions)
        )
        dislike_count = dislike_result.scalar_one()

        return {
            "total": total,
            "like_count": like_count,
            "dislike_count": dislike_count,
        }


__all__ = ["KnowledgeSearchFeedbackRepository"]
