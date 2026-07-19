from typing import Sequence

from sqlalchemy import select, delete

from jonex_core.common.tenant import require_tenant

from capabilities.platform.models.role_permission import RolePermission
from capabilities.platform.repository.base import BaseRepository


class RolePermissionRepository(BaseRepository[RolePermission]):
    model = RolePermission

    async def get_permission_ids(self, tenant_id: str, role_id: int) -> Sequence[int]:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(RolePermission.permission_id).where(
                RolePermission.tenant_id == tenant_id,
                RolePermission.role_id == role_id
            )
        )
        return result.scalars().all()

    async def set_permissions(
        self,
        tenant_id: str,
        role_id: int,
        permission_ids: list[int],
    ) -> None:
        tenant_id = require_tenant(tenant_id)
        await self.session.execute(
            delete(RolePermission).where(
                RolePermission.tenant_id == tenant_id,
                RolePermission.role_id == role_id,
            )
        )
        for pid in permission_ids:
            self.session.add(
                RolePermission(
                    tenant_id=tenant_id,
                    role_id=role_id,
                    permission_id=pid,
                )
            )
        await self.session.flush()

    async def get_roles_for_permission(
        self,
        tenant_id: str,
        permission_id: int,
    ) -> Sequence[int]:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(RolePermission.role_id).where(
                RolePermission.tenant_id == tenant_id,
                RolePermission.permission_id == permission_id
            )
        )
        return result.scalars().all()