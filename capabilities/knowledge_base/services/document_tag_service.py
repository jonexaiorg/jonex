#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""文档-标签关联服务。"""

from typing import Optional

from jonex_core.common import get_db_session
from jonex_core.common.exceptions import ResourceConflictError, ResourceNotFoundError
from jonex_core.common.i18n import translate
from jonex_core.common.tenant import require_tenant

from ..models.document import KnowledgeDocument
from ..repository.document_tag_repository import DocumentTagRepository
from ..repository.tag_repository import TagRepository


class DocumentTagService:
    """知识库文档-标签关联服务。"""

    async def _ensure_document(
        self, session, document_id: str, tenant_id: str,
        knowledge_base_id: Optional[str] = None,
    ) -> KnowledgeDocument:
        """校验文档存在，若有传 knowledge_base_id 则校验 KB 归属。"""
        from ..repository.document_repository import KnowledgeDocumentRepository

        doc = await KnowledgeDocumentRepository(session).get_by_id(document_id, tenant_id)
        if doc is None:
            raise ResourceNotFoundError(
                message=translate("err.doc.not_found", fallback="知识文档不存在")  ,  # 原消息
                details={"document_id": document_id},
            )
        if knowledge_base_id is not None and doc.knowledge_base_id != knowledge_base_id:
            raise ResourceNotFoundError(
                message=translate("err.doc.not_found", fallback="知识文档不存在")  ,  # 原消息
                details={"document_id": document_id},
            )
        return doc

    async def _ensure_tag(
        self, session, tag_id: str, knowledge_base_id: str, tenant_id: str
    ) -> None:
        """校验标签存在且属于指定 KB 和租户。"""
        repo = TagRepository(session)
        tag = await repo.get_by_id(tag_id, tenant_id)
        if tag is None or tag.knowledge_base_id != knowledge_base_id:
            raise ResourceNotFoundError(
                message=translate("err.tag.not_found", fallback="标签不存在")  ,  # 原消息
                details={"tag_id": tag_id},
            )

    async def set_document_tags(
        self,
        tenant_id: str,
        document_id: str,
        knowledge_base_id: str,
        tag_ids: list[str],
    ) -> dict:
        """全量替换文档的标签列表。

        先删除文档所有现有标签关联，再插入新的关联。
        """
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            # 校验文档存在
            await self._ensure_document(session, document_id, tenant_id, knowledge_base_id)

            # 校验所有标签存在且属于同一个 KB
            tag_repo = TagRepository(session)
            existing_tags = []
            for tag_id in tag_ids:
                tag = await tag_repo.get_by_id(tag_id, tenant_id)
                if tag is None or tag.knowledge_base_id != knowledge_base_id:
                    raise ResourceNotFoundError(
                        message=translate("err.tag.not_found", params={"tag_id": str(tag_id)}, fallback=f"标签不存在: {tag_id}")  ,  # 原消息
                        details={"tag_id": tag_id},
                    )
                existing_tags.append(tag)

            # 全量替换
            dt_repo = DocumentTagRepository(session)
            await dt_repo.delete_by_document(document_id)
            for tag in existing_tags:
                await dt_repo.create(
                    document_id=document_id,
                    tag_id=tag.id,
                )

            await session.commit()
            return {
                "document_id": document_id,
                "tag_ids": tag_ids,
                "message": "文档标签已更新",
            }

    async def get_document_tags(
        self,
        tenant_id: str,
        document_id: str,
        knowledge_base_id: Optional[str] = None,
    ) -> dict:
        """查询文档的标签列表。"""
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            # 校验文档存在
            await self._ensure_document(session, document_id, tenant_id, knowledge_base_id)

            dt_repo = DocumentTagRepository(session)
            tags = await dt_repo.list_by_document(document_id)

            return {
                "items": [t.to_dict() for t in tags],
                "total": len(tags),
            }

    async def add_document_tag(
        self,
        tenant_id: str,
        document_id: str,
        knowledge_base_id: str,
        tag_id: str,
    ) -> dict:
        """为文档添加单个标签（已存在则跳过）。"""
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            # 校验文档和标签存在
            await self._ensure_document(session, document_id, tenant_id, knowledge_base_id)
            await self._ensure_tag(session, tag_id, knowledge_base_id, tenant_id)

            dt_repo = DocumentTagRepository(session)
            exists = await dt_repo.exists(document_id, tag_id)
            if not exists:
                await dt_repo.create(
                    document_id=document_id,
                    tag_id=tag_id,
                )
                await session.commit()

            return {
                "document_id": document_id,
                "tag_id": tag_id,
                "message": "标签已添加到文档" if not exists else "标签已存在",
            }

    async def remove_document_tag(
        self,
        tenant_id: str,
        document_id: str,
        knowledge_base_id: str,
        tag_id: str,
    ) -> dict:
        """从文档移除单个标签。"""
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            # 校验文档存在
            await self._ensure_document(session, document_id, tenant_id, knowledge_base_id)

            dt_repo = DocumentTagRepository(session)
            deleted = await dt_repo.delete_one(document_id, tag_id)
            await session.commit()

            if not deleted:
                raise ResourceNotFoundError(
                    message=translate("err.doc.tag_not_associated", fallback="文档未关联该标签")  ,  # 原消息
                    details={"document_id": document_id, "tag_id": tag_id},
                )

            return {
                "document_id": document_id,
                "tag_id": tag_id,
                "message": "标签已从文档移除",
            }


__all__ = ["DocumentTagService"]
