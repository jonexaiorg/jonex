#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Knowledge Base — 标签模型和文档-标签多对多关联。

对应表：knowledge_base.tags, knowledge_base.document_tags
"""
from sqlalchemy import Column, ForeignKey, String

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class Tag(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    """KB 级标签，用于文档分类与筛选。"""

    __tablename__ = "tags"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True)
    knowledge_base_id = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    color = Column(String(32), nullable=True)  # 标签颜色十六进制值（如 #1890ff）
    created_by = Column(String(64), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "knowledge_base_id": self.knowledge_base_id,
            "color": self.color,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DocumentTag(Base):
    """文档-标签多对多关联，不带租户隔离（文档和标签本身已带租户）。"""

    __tablename__ = "document_tags"
    __table_args__ = {"schema": "knowledge_base"}

    document_id = Column(
        String(64),
        ForeignKey("knowledge_base.knowledge_documents.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    tag_id = Column(
        String(64),
        ForeignKey("knowledge_base.tags.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )


__all__ = ["DocumentTag", "Tag"]
