from typing import Optional, Sequence

from sqlalchemy import select, func

from capabilities.platform.models.permission import Permission
from capabilities.platform.repository.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    model = Permission

    async def get_by_code(self, code: str) -> Optional[Permission]:
        result = await self.session.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none()

    async def list_all_sorted(self, offset: int = 0, limit: int = 100) -> Sequence[Permission]:
        result = await self.session.execute(
            select(Permission)
            .order_by(Permission.resource, Permission.action)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()