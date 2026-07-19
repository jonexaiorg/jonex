
from typing import Sequence

from sqlalchemy import or_, select

from jonex_core.common.repository import BaseRepository
from jonex_core.common.tenant import require_tenant

from capabilities.business_domain.models.prompt_template import PromptTemplate


class PromptTemplateRepository(BaseRepository[PromptTemplate]):
    model = PromptTemplate



    async def list_system_templates(
        self,
        offset: int = 0,
        limit: int = 20,
        extra_conditions: Sequence | None = None,
    ) -> list[PromptTemplate]:

        conditions = [
            PromptTemplate.tenant_id.is_(None),
            PromptTemplate.scope == "system",
            PromptTemplate.is_deleted == 0,
        ]
        if extra_conditions:
            conditions.extend(extra_conditions)
        stmt = (
            select(PromptTemplate)
            .where(*conditions)
            .order_by(PromptTemplate.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def count_system_templates(
        self,
        extra_conditions: Sequence | None = None,
    ) -> int:
        from sqlalchemy import func
        conditions = [
            PromptTemplate.tenant_id.is_(None),
            PromptTemplate.scope == "system",
            PromptTemplate.is_deleted == 0,
        ]
        if extra_conditions:
            conditions.extend(extra_conditions)
        result = await self.session.execute(
            select(func.count()).select_from(PromptTemplate).where(*conditions)
        )
        return result.scalar_one()

    async def get_system_template(self, template_id: str) -> PromptTemplate | None:

        result = await self.session.execute(
            select(PromptTemplate).where(
                PromptTemplate.id == template_id,
                PromptTemplate.tenant_id.is_(None),
                PromptTemplate.scope == "system",
                PromptTemplate.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()



    async def list_domain_templates(
        self,
        tenant_id: str,
        offset: int = 0,
        limit: int = 20,
        extra_conditions: Sequence | None = None,
    ) -> list[PromptTemplate]:

        tenant_id = require_tenant(tenant_id)
        conditions = [
            PromptTemplate.tenant_id == tenant_id,
            PromptTemplate.scope == "domain",
            PromptTemplate.is_deleted == 0,
        ]
        if extra_conditions:
            conditions.extend(extra_conditions)
        stmt = (
            select(PromptTemplate)
            .where(*conditions)
            .order_by(PromptTemplate.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def count_domain_templates(
        self,
        tenant_id: str,
        extra_conditions: Sequence | None = None,
    ) -> int:
        from sqlalchemy import func
        tenant_id = require_tenant(tenant_id)
        conditions = [
            PromptTemplate.tenant_id == tenant_id,
            PromptTemplate.scope == "domain",
            PromptTemplate.is_deleted == 0,
        ]
        if extra_conditions:
            conditions.extend(extra_conditions)
        result = await self.session.execute(
            select(func.count()).select_from(PromptTemplate).where(*conditions)
        )
        return result.scalar_one()

    async def get_domain_template(
        self, template_id: str, tenant_id: str
    ) -> PromptTemplate | None:

        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(PromptTemplate).where(
                PromptTemplate.id == template_id,
                PromptTemplate.tenant_id == tenant_id,
                PromptTemplate.scope == "domain",
                PromptTemplate.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()

    async def get_required_domain_template(
        self, template_id: str, tenant_id: str
    ) -> PromptTemplate:

        from jonex_core.common.exceptions import ResourceNotFoundError

        obj = await self.get_domain_template(template_id, tenant_id)
        if obj is None:
            raise ResourceNotFoundError(
                message=f"Prompt template not found: {template_id}",
                details={"id": template_id, "tenant_id": tenant_id},
            )
        return obj



    async def get_any(self, template_id: str) -> PromptTemplate | None:

        result = await self.session.execute(
            select(PromptTemplate).where(
                PromptTemplate.id == template_id,
                PromptTemplate.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()

    async def search_domain_templates(
        self,
        tenant_id: str,
        keyword: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[PromptTemplate]:

        tenant_id = require_tenant(tenant_id)
        pattern = f"%{keyword}%"
        conditions = [
            PromptTemplate.tenant_id == tenant_id,
            PromptTemplate.scope == "domain",
            PromptTemplate.is_deleted == 0,
            or_(
                PromptTemplate.name.ilike(pattern),
                PromptTemplate.description.ilike(pattern),

            ),
        ]
        stmt = (
            select(PromptTemplate)
            .where(*conditions)
            .order_by(PromptTemplate.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())
