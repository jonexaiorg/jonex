
import uuid

from jonex_core.common import get_db_session
from jonex_core.common.tenant import require_tenant

from capabilities.business_domain.repository.skill_repository import (
    SkillCatalogRepository,
    TenantSkillRepository,
)


class SkillService:


    async def list(
        self,
        tenant_id: str,
        offset: int = 0,
        limit: int = 20,
        category: str | None = None,
        keyword: str | None = None,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            catalog_repo = SkillCatalogRepository(session)
            tenant_repo = TenantSkillRepository(session)

            catalogs = await catalog_repo.list_published(offset, limit, category, keyword)
            total = await catalog_repo.count_published(category, keyword)
            tenant_rows = await tenant_repo.list_by_skill_ids(
                tenant_id, [item.id for item in catalogs],
            )
            status_by_skill = {item.skill_id: item.status for item in tenant_rows}

            return {
                "items": [
                    item.to_skill_item(status_by_skill.get(item.id))
                    for item in catalogs
                ],
                "total": total,
                "offset": offset,
                "limit": limit,
            }

    async def get(self, tenant_id: str, skill_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            catalog_repo = SkillCatalogRepository(session)
            tenant_repo = TenantSkillRepository(session)

            catalog = await catalog_repo.get_published_required(skill_id)
            tenant_skill = await tenant_repo.get_by_skill_id(tenant_id, skill_id)
            return catalog.to_skill_item(tenant_skill.status if tenant_skill else None)

    async def enable(self, tenant_id: str, skill_id: str) -> dict:
        return await self._set_status(tenant_id, skill_id, "enabled")

    async def disable(self, tenant_id: str, skill_id: str) -> dict:
        return await self._set_status(tenant_id, skill_id, "disabled")

    async def list_enabled_mcp_tools(self, tenant_id: str) -> dict:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            catalog_repo = SkillCatalogRepository(session)
            tenant_repo = TenantSkillRepository(session)

            catalogs = await catalog_repo.list_published(offset=0, limit=500)
            tenant_rows = await tenant_repo.list_by_skill_ids(
                tenant_id, [item.id for item in catalogs],
            )
            enabled_ids = {
                item.skill_id
                for item in tenant_rows
                if item.status == "enabled"
            }

            return {
                "items": [
                    item.to_mcp_tool_definition()
                    for item in catalogs
                    if item.id in enabled_ids
                ],
            }

    async def _set_status(
        self, tenant_id: str, skill_id: str, status: str,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            catalog_repo = SkillCatalogRepository(session)
            tenant_repo = TenantSkillRepository(session)

            await catalog_repo.get_published_required(skill_id)
            tenant_skill = await tenant_repo.get_by_skill_id(tenant_id, skill_id)

            if tenant_skill is None:
                tenant_skill = await tenant_repo.create(
                    id=uuid.uuid4().hex,
                    tenant_id=tenant_id,
                    skill_id=skill_id,
                    status=status,
                )
            else:
                tenant_skill.status = status
                await session.flush()

            await session.commit()
            return {
                "id": tenant_skill.id,
                "skill_id": tenant_skill.skill_id,
                "tenant_status": tenant_skill.status,
                "enabled": tenant_skill.status == "enabled",
            }