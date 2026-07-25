#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""KB-level tag CRUD service."""

import uuid

from jonex_core.common import get_db_session
from jonex_core.common.exceptions import ResourceConflictError, ResourceNotFoundError
from jonex_core.common.i18n import translate
from jonex_core.common.tenant import require_tenant

from ..repository.knowledge_info_repository import KnowledgeInfoRepository
from ..repository.tag_repository import TagRepository


class TagService:
    """知识库标签 CRUD 服务。"""

    async def _ensure_kb(self, session, kb_id: str, tenant_id: str) -> None:
        """校验 KB 归属存在（不存在抛 ResourceNotFoundError）。"""
        await KnowledgeInfoRepository(session).get_required(kb_id, tenant_id)

    async def list_tags(self, tenant_id: str, knowledge_base_id: str) -> dict:
        """列出 KB 下所有未删标签。"""
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            await self._ensure_kb(session, knowledge_base_id, tenant_id)
            repo = TagRepository(session)
            items = await repo.list_by_kb(tenant_id, knowledge_base_id)
            return {
                "items": [t.to_dict() for t in items],
                "total": len(items),
            }

    async def create_tag(self, tenant_id: str, data: dict) -> dict:
        """创建标签（同 KB 内名称唯一）。"""
        tenant_id = require_tenant(tenant_id)
        kb_id = data["knowledge_base_id"]
        name = data["name"]
        color = data.get("color")
        async with get_db_session() as session:
            await self._ensure_kb(session, kb_id, tenant_id)
            repo = TagRepository(session)

            existing = await repo.get_by_name(tenant_id, kb_id, name)
            if existing:
                raise ResourceConflictError(message=translate("err.tag.name_exists", params={"name": name}, fallback=f"标签名称已存在: {name}")  )  # 原消息)

            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                name=name,
                color=color,
            )
            await session.commit()
            return obj.to_dict()

    async def update_tag(
        self, tenant_id: str, tag_id: str, knowledge_base_id: str, data: dict
    ) -> dict:
        """更新标签名称和/或颜色（同 KB 内名称唯一）。"""
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TagRepository(session)

            obj = await repo.get_required(tag_id, tenant_id)
            if obj.knowledge_base_id != knowledge_base_id:
                raise ResourceNotFoundError(
                    message=translate("err.tag.not_belong_to_kb", fallback="标签不属于该知识库")  ,  # 原消息
                    details={"tag_id": tag_id, "knowledge_base_id": knowledge_base_id},
                )

            new_name = data.get("name")
            new_color = data.get("color")

            if new_name is not None:
                existing = await repo.get_by_name(tenant_id, obj.knowledge_base_id, new_name)
                if existing and existing.id != tag_id:
                    raise ResourceConflictError(message=translate("err.tag.name_exists", params={"name": new_name}, fallback=f"标签名称已存在: {new_name}")  )  # 原消息)
                obj.name = new_name

            if new_color is not None:
                obj.color = new_color or None

            await session.commit()
            return obj.to_dict()

    async def delete_tag(
        self, tenant_id: str, tag_id: str, knowledge_base_id: str
    ) -> bool:
        """删除标签：删除标签本身（关联表中的记录由外键级联删除）。"""
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TagRepository(session)

            obj = await repo.get_required(tag_id, tenant_id)
            if obj.knowledge_base_id != knowledge_base_id:
                raise ResourceNotFoundError(
                    message=translate("err.tag.not_belong_to_kb", fallback="标签不属于该知识库")  ,  # 原消息
                    details={"tag_id": tag_id, "knowledge_base_id": knowledge_base_id},
                )

            await repo.delete_soft(obj)
            await session.commit()
            return True


__all__ = ["TagService"]
