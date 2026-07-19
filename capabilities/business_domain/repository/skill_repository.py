
from sqlalchemy import and_, func, or_, select

from jonex_core.common.repository import BaseRepository
from jonex_core.common.tenant import require_tenant

from capabilities.business_domain.models.skill import SkillCatalog, TenantSkill


class SkillCatalogRepository(BaseRepository[SkillCatalog]):
    model = SkillCatalog

    async def list_published(
        self,
        offset: int,
        limit: int,
        category: str | None = None,
        keyword: str | None = None,
    ) -> list[SkillCatalog]:
        filters = [
            SkillCatalog.is_deleted == 0,
            SkillCatalog.status == "published",
        ]
        if category:
            filters.append(SkillCatalog.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            filters.append(or_(
                SkillCatalog.name.ilike(pattern),
                SkillCatalog.description.ilike(pattern),
            ))

        result = await self.session.execute(
            select(SkillCatalog)
            .where(and_(*filters))
            .order_by(SkillCatalog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_published(
        self,
        category: str | None = None,
        keyword: str | None = None,
    ) -> int:
        filters = [
            SkillCatalog.is_deleted == 0,
            SkillCatalog.status == "published",
        ]
        if category:
            filters.append(SkillCatalog.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            filters.append(or_(
                SkillCatalog.name.ilike(pattern),
                SkillCatalog.description.ilike(pattern),
            ))

        result = await self.session.execute(
            select(func.count()).select_from(SkillCatalog).where(and_(*filters))
        )
        return int(result.scalar_one())

    async def get_published_required(self, skill_id: str) -> SkillCatalog:

        return await self.get_required_shared(skill_id)


class TenantSkillRepository(BaseRepository[TenantSkill]):
    model = TenantSkill

    async def list_by_skill_ids(
        self, tenant_id: str, skill_ids: list[str],
    ) -> list[TenantSkill]:
        tenant_id = require_tenant(tenant_id)
        if not skill_ids:
            return []
        result = await self.session.execute(
            select(TenantSkill).where(
                TenantSkill.tenant_id == tenant_id,
                TenantSkill.skill_id.in_(skill_ids),
                TenantSkill.is_deleted == 0,
            )
        )
        return list(result.scalars().all())

    async def get_by_skill_id(
        self, tenant_id: str, skill_id: str,
    ) -> TenantSkill | None:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(TenantSkill).where(
                TenantSkill.tenant_id == tenant_id,
                TenantSkill.skill_id == skill_id,
                TenantSkill.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()