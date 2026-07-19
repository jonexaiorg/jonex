

from collections import defaultdict
from datetime import datetime

from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import ResourceNotFoundError
from jonex_core.common.tenant import require_tenant

from ..repository import KnowledgeSearchFeedbackRepository
from .document_service import _payload


class SearchFeedbackService:


    async def submit_feedback(
        self,
        tenant_id: str,
        user_id: str,
        request: dict,
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        session_id = request["session_id"]
        query = request["query"]
        answer_preview = request.get("answer_preview")
        feedback_type = request["feedback_type"]
        kb_ids = request["knowledge_base_ids"]
        kb_names = request.get("knowledge_base_names") or {}
        searched_at_str = request.get("searched_at")
        searched_at = datetime.fromisoformat(searched_at_str) if searched_at_str else None

        async with get_db_session() as session:
            repo = KnowledgeSearchFeedbackRepository(session)
            records = []
            for kb_id in kb_ids:
                record = await repo.create_feedback(
                    tenant_id,
                    {
                        "user_id": user_id,
                        "session_id": session_id,
                        "query": query,
                        "answer_preview": answer_preview,
                        "knowledge_base_id": kb_id,
                        "knowledge_base_name": kb_names.get(kb_id),
                        "feedback_type": feedback_type,
                        "searched_at": searched_at,
                    },
                )
                records.append(record)
        return {
            "records": [r.to_dict() for r in records],
            "count": len(records),
        }

    async def cancel_feedback(
        self,
        tenant_id: str,
        user_id: str,
        request: dict,
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        session_id = request["session_id"]
        feedback_type = request["feedback_type"]
        kb_ids = request["knowledge_base_ids"]

        async with get_db_session() as session:
            repo = KnowledgeSearchFeedbackRepository(session)
            from sqlalchemy import delete, select

            from ..models import KnowledgeSearchFeedback

            conditions = [
                KnowledgeSearchFeedback.tenant_id == repo._tenant_id(tenant_id),
                KnowledgeSearchFeedback.session_id == session_id,
                KnowledgeSearchFeedback.feedback_type == feedback_type,
                KnowledgeSearchFeedback.user_id == user_id,
                KnowledgeSearchFeedback.knowledge_base_id.in_(kb_ids),
            ]
            stmt = select(KnowledgeSearchFeedback).where(*conditions)
            result = await session.execute(stmt)
            records = list(result.scalars())
            for r in records:
                await session.delete(r)
            await session.flush()
        return {"deleted_count": len(records)}

    async def list_feedback(
        self,
        tenant_id: str,
        request: dict,
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        kb_id = request["knowledge_base_id"]
        feedback_type = request.get("feedback_type")
        page = request.get("page", 1)
        page_size = request.get("page_size", 50)
        offset = (page - 1) * page_size

        async with get_db_session() as session:
            repo = KnowledgeSearchFeedbackRepository(session)
            items = await repo.list_by_knowledge_base(
                tenant_id, kb_id, feedback_type=feedback_type,
                offset=offset, limit=page_size,
            )
            total = await repo.count_by_knowledge_base(
                tenant_id, kb_id, feedback_type=feedback_type,
            )
            stats = await repo.get_stats(tenant_id, kb_id)

        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "like_count": stats["like_count"],
            "dislike_count": stats["dislike_count"],
            "page": page,
            "page_size": page_size,
        }

    async def toggle_adopted(
        self,
        tenant_id: str,
        request: dict,
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        feedback_id = request["feedback_id"]

        async with get_db_session() as session:
            repo = KnowledgeSearchFeedbackRepository(session)
            record = await repo.toggle_adopted(tenant_id, feedback_id)
            if not record:
                raise ResourceNotFoundError(message="Feedback record not found")
        return record.to_dict()

    async def get_stats(
        self,
        tenant_id: str,
        request: dict,
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        kb_id = request["knowledge_base_id"]

        async with get_db_session() as session:
            repo = KnowledgeSearchFeedbackRepository(session)
            stats = await repo.get_stats(tenant_id, kb_id)
        return stats


__all__ = ["SearchFeedbackService"]
