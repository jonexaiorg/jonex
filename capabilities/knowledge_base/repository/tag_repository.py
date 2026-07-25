#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Repository for KB-level tags."""

from sqlalchemy import select

from jonex_core.common.repository import BaseRepository
from jonex_core.common.tenant import require_tenant

from ..models.tag import Tag


class TagRepository(BaseRepository[Tag]):
    model = Tag

    async def list_by_kb(
        self,
        tenant_id: str,
        knowledge_base_id: str,
    ) -> list[Tag]:
        """按 KB 列出所有未删除标签（按创建时间降序）。"""
        tid = require_tenant(tenant_id)
        result = await self.session.execute(
            select(Tag).where(
                Tag.tenant_id == tid,
                Tag.knowledge_base_id == knowledge_base_id,
                Tag.is_deleted == 0,
            ).order_by(Tag.created_at.desc())
        )
        return list(result.scalars())

    async def get_by_name(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        name: str,
    ) -> Tag | None:
        """按名称查找标签（同 KB 内名称唯一）。"""
        tid = require_tenant(tenant_id)
        result = await self.session.execute(
            select(Tag).where(
                Tag.tenant_id == tid,
                Tag.knowledge_base_id == knowledge_base_id,
                Tag.name == name,
                Tag.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()


__all__ = ["TagRepository"]
