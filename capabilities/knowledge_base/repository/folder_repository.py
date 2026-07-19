#!/usr/bin/python3



from sqlalchemy import select

from jonex_core.common.repository import BaseRepository
from jonex_core.common.tenant import require_tenant

from ..models.folder import Folder


class FolderRepository(BaseRepository[Folder]):
    model = Folder

    async def list_by_kb(
        self,
        tenant_id: str,
        knowledge_base_id: str,
    ) -> list[Folder]:

        tid = require_tenant(tenant_id)
        result = await self.session.execute(
            select(Folder).where(
                Folder.tenant_id == tid,
                Folder.knowledge_base_id == knowledge_base_id,
                Folder.is_deleted == 0,
            ).order_by(
                Folder.is_preset.desc(),
                Folder.name.asc().nullslast(),
                Folder.created_at.desc(),
            )
        )
        return list(result.scalars())

    async def get_by_name(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        name: str,
    ) -> Folder | None:
        tid = require_tenant(tenant_id)
        result = await self.session.execute(
            select(Folder).where(
                Folder.tenant_id == tid,
                Folder.knowledge_base_id == knowledge_base_id,
                Folder.name == name,
                Folder.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()


__all__ = ["FolderRepository"]
