"""
知识库能力 — 领域空间服务
"""
from __future__ import annotations

import uuid

from sqlalchemy import select

from jonex_core.common import get_db_session
from jonex_core.common.audit import schedule_emit
from jonex_core.common.audit_enums import ResourceType
from jonex_core.common.tenant import require_tenant

from ..models.space import SpacePermission
from ..repository import SpacePermissionRepository, SpaceRepository


class SpaceService:
    """领域空间 CRUD + 权限"""

    async def create(self, tenant_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = SpaceRepository(session)
            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                name=data["name"],
                description=data.get("description"),
                owner_id=data.get("owner_id"),
            )
            await session.commit()
            schedule_emit({
                "tenant_id": tenant_id,
                "log_type": "OPERATION",
                "action": "create_space",
                "outcome": "SUCCESS",
                "service_name": "knowledge_base",
                "resource": ResourceType.SPACE.value,
                "resource_id": obj.id,
            })
            return obj.to_dict()

    async def get(self, space_id: str, tenant_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = SpaceRepository(session)
            obj = await repo.get_required(space_id, tenant_id)
            return obj.to_dict()

    async def list(self, tenant_id: str, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = SpaceRepository(session)
            items = await repo.list_all(tenant_id, offset, limit)
            total = await repo.count(tenant_id)
            return {
                "items": [o.to_dict() for o in items],
                "total": total, "offset": offset, "limit": limit,
            }

    async def update(self, space_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = SpaceRepository(session)
            obj = await repo.get_required(space_id, tenant_id)
            updatable = {"name", "description", "status"}
            values = {k: v for k, v in data.items() if k in updatable and v is not None}
            if values:
                obj = await repo.update(space_id, tenant_id, **values)
                await session.commit()
            schedule_emit({
                "tenant_id": tenant_id,
                "log_type": "OPERATION",
                "action": "update_space",
                "outcome": "SUCCESS",
                "service_name": "knowledge_base",
                "resource": ResourceType.SPACE.value,
                "resource_id": space_id,
            })
            return obj.to_dict()

    async def delete(self, space_id: str, tenant_id: str) -> bool:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = SpaceRepository(session)
            await repo.get_required(space_id, tenant_id)
            await repo.delete_soft(space_id, tenant_id)

            # 级联删除权限记录
            existing_perm = await session.execute(
                select(SpacePermission).where(
                    SpacePermission.space_id == space_id,
                    SpacePermission.tenant_id == tenant_id,
                    SpacePermission.is_deleted == 0,
                )
            )
            for sp in existing_perm.scalars().all():
                await session.delete(sp)

            await session.commit()
            schedule_emit({
                "tenant_id": tenant_id,
                "log_type": "OPERATION",
                "action": "delete_space",
                "outcome": "SUCCESS",
                "service_name": "knowledge_base",
                "resource": ResourceType.SPACE.value,
                "resource_id": space_id,
            })
            return True

    async def get_permissions(self, space_id: str, tenant_id: str) -> list:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            result = await session.execute(
                select(SpacePermission).where(
                    SpacePermission.space_id == space_id,
                    SpacePermission.tenant_id == tenant_id,
                    SpacePermission.is_deleted == 0,
                )
            )
            return [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "role": row.role,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in result.scalars().all()
            ]

    async def set_permissions(self, space_id: str, tenant_id: str, permissions: list) -> bool:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            # 移除已有权限
            existing = await session.execute(
                select(SpacePermission).where(
                    SpacePermission.space_id == space_id,
                    SpacePermission.tenant_id == tenant_id,
                    SpacePermission.is_deleted == 0,
                )
            )
            for sp in existing.scalars().all():
                await session.delete(sp)

            # 添加新权限
            for perm in permissions:
                perm_obj = SpacePermission(
                    id=uuid.uuid4().hex,
                    tenant_id=tenant_id,
                    space_id=space_id,
                    user_id=perm["user_id"],
                    role=perm.get("role", "viewer"),
                )
                session.add(perm_obj)

            await session.commit()
            schedule_emit({
                "tenant_id": tenant_id,
                "log_type": "OPERATION",
                "action": "set_space_permissions",
                "outcome": "SUCCESS",
                "service_name": "knowledge_base",
                "resource": ResourceType.SPACE.value,
                "resource_id": space_id,
            })
            return True
