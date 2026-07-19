
from __future__ import annotations

import uuid

from sqlalchemy import select

from jonex_core.common import get_db_session
from jonex_core.common.tenant import require_tenant

from ..models.space import SpacePermission
from ..repository import SpacePermissionRepository, SpaceRepository


class SpaceService:


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
            return obj.to_dict()

    async def delete(self, space_id: str, tenant_id: str) -> bool:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = SpaceRepository(session)
            await repo.get_required(space_id, tenant_id)
            await repo.delete_soft(space_id, tenant_id)


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

            existing = await session.execute(
                select(SpacePermission).where(
                    SpacePermission.space_id == space_id,
                    SpacePermission.tenant_id == tenant_id,
                    SpacePermission.is_deleted == 0,
                )
            )
            for sp in existing.scalars().all():
                await session.delete(sp)


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
            return True
