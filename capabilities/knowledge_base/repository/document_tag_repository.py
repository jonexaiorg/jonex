#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Repository for document-tag association."""

from sqlalchemy import delete, select

from jonex_core.common.repository import BaseRepository

from ..models.tag import DocumentTag, Tag


class DocumentTagRepository(BaseRepository[DocumentTag]):
    model = DocumentTag

    async def list_by_document(self, document_id: str) -> list[Tag]:
        """查询文档关联的所有标签（Join Tag 表）。"""
        result = await self.session.execute(
            select(Tag).join(DocumentTag, Tag.id == DocumentTag.tag_id).where(
                DocumentTag.document_id == document_id,
                Tag.is_deleted == 0,
            ).order_by(Tag.created_at.desc())
        )
        return list(result.scalars())

    async def list_by_tag(self, tag_id: str) -> list[DocumentTag]:
        """查询标签关联的所有文档。"""
        result = await self.session.execute(
            select(DocumentTag).where(DocumentTag.tag_id == tag_id)
        )
        return list(result.scalars())

    async def delete_by_document(self, document_id: str) -> None:
        """删除文档的所有标签关联。"""
        await self.session.execute(
            delete(DocumentTag).where(DocumentTag.document_id == document_id)
        )

    async def delete_one(self, document_id: str, tag_id: str) -> bool:
        """删除文档的单个标签关联。"""
        result = await self.session.execute(
            delete(DocumentTag).where(
                DocumentTag.document_id == document_id,
                DocumentTag.tag_id == tag_id,
            )
        )
        return result.rowcount > 0

    async def exists(self, document_id: str, tag_id: str) -> bool:
        """检查文档-标签关联是否存在。"""
        result = await self.session.execute(
            select(DocumentTag).where(
                DocumentTag.document_id == document_id,
                DocumentTag.tag_id == tag_id,
            )
        )
        return result.scalar_one_or_none() is not None


__all__ = ["DocumentTagRepository"]
