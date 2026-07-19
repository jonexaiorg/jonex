#!/usr/bin/python3



from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from jonex_core.common.database import Base
from jonex_core.common.entity import TenantMixin, TimestampMixin


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class KnowledgeSearchFeedback(Base, TenantMixin, TimestampMixin):


    __tablename__ = "knowledge_search_feedback"
    __table_args__ = (
        Index("idx_kb_feedback_tenant_kb_time", "tenant_id", "knowledge_base_id", "searched_at"),
        Index("idx_kb_feedback_tenant_user", "tenant_id", "user_id"),
        Index("idx_kb_feedback_session", "session_id"),
        {"schema": "knowledge_base"},
    )

    id = Column(String(64), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(128), nullable=False, index=True)
    session_id = Column(String(128), nullable=False, comment="搜索会话 ID")
    query = Column(Text, nullable=False, comment="搜索问题")
    answer_preview = Column(Text, nullable=True, comment="回答摘要")
    knowledge_base_id = Column(String(128), nullable=False, index=True, comment="被引用的知识库 ID")
    knowledge_base_name = Column(String(256), nullable=True, comment="被引用的知识库名称（冗余，方便展示）")
    feedback_type = Column(String(16), nullable=False, comment="like / dislike")
    adopted = Column(Boolean, nullable=False, default=False, comment="是否已被管理员采纳")
    searched_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), comment="搜索时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "query": self.query,
            "answer_preview": self.answer_preview,
            "knowledge_base_id": self.knowledge_base_id,
            "knowledge_base_name": self.knowledge_base_name,
            "feedback_type": self.feedback_type,
            "adopted": self.adopted,
            "searched_at": _iso(self.searched_at),
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }


__all__ = ["KnowledgeSearchFeedback"]
