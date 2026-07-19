from typing import Mapping, Sequence

from sqlalchemy import select

from capabilities.platform.models.tenant import Tenant
from capabilities.platform.repository.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    model = Tenant

    async def list_active_by_ids(self, tenant_ids: Sequence[str]) -> Mapping[str, Tenant]:
        if not tenant_ids:
            return {}

        result = await self.session.execute(
            select(Tenant).where(
                Tenant.id.in_(tenant_ids),
                Tenant.status == 1,
                Tenant.is_deleted == 0,
            )
        )
        tenants = result.scalars().all()
        return {tenant.id: tenant for tenant in tenants}
