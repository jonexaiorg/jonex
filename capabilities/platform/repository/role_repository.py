from typing import Optional, Sequence

from sqlalchemy import select, func

from jonex_core.common.tenant import require_tenant

from capabilities.platform.models.role import Role
from capabilities.platform.repository.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    async def get_by_name(self, tenant_id: str, name: str) -> Optional[Role]:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(Role).where(
                Role.tenant_id == tenant_id,
                Role.name == name,
                Role.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self, tenant_id: str, offset: int = 0, limit: int = 20
    ) -> Sequence[Role]:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(Role)
            .where(Role.tenant_id == tenant_id, Role.is_deleted == 0)
            .order_by(Role.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_tenant(self, tenant_id: str) -> int:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(func.count()).select_from(Role).where(
                Role.tenant_id == tenant_id, Role.is_deleted == 0
            )
        )
        return result.scalar() or 0