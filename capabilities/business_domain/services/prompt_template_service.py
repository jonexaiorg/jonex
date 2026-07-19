
import uuid
from datetime import datetime
import re
from typing import Any

from sqlalchemy import or_

from jonex_core.common import get_db_session
from jonex_core.common.exceptions import (
    InvalidParameterError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from jonex_core.common.tenant import require_tenant

from capabilities.business_domain.models.prompt_template import PromptTemplate
from capabilities.business_domain.repository.prompt_template_repository import (
    PromptTemplateRepository,
)


VALID_CATEGORIES = {"通用问答", "文档处理", "金融分析", "合同审查", "数据分析", "其他"}


class PromptTemplateService:




    async def list_templates(
        self,
        tenant_id: str,
        scope: str | None = None,
        category: str | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict:

        result_items: list[dict] = []
        total = 0

        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)


            extra: list = []
            if category:
                extra.append(PromptTemplate.category == category)
            if keyword:
                pattern = f"%{keyword}%"
                extra.append(
                    or_(
                        PromptTemplate.name.ilike(pattern),
                        PromptTemplate.description.ilike(pattern),
                    )
                )

            need_system = scope is None or scope == "system"
            need_domain = scope is None or scope == "domain"

            if need_system:
                sys_items = await repo.list_system_templates(
                    offset=0, limit=1000, extra_conditions=extra
                )

                if keyword:
                    sys_items = [
                        t for t in sys_items
                        if self._match_content(t, keyword) or self._match_name_desc(t, keyword)
                    ]
                total += len(sys_items)
                result_items.extend(t.to_dict() for t in sys_items)

            if need_domain:
                try:
                    dom_items = await repo.list_domain_templates(
                        tenant_id, offset=0, limit=1000, extra_conditions=extra
                    )
                    if keyword:
                        dom_items = [
                            t for t in dom_items
                            if self._match_content(t, keyword) or self._match_name_desc(t, keyword)
                        ]
                    total += len(dom_items)
                    result_items.extend(t.to_dict() for t in dom_items)
                except Exception:

                    pass


            result_items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
            paged = result_items[offset : offset + limit]

            return {
                "items": paged,
                "total": total,
                "offset": offset,
                "limit": limit,
            }



    async def get_template(self, template_id: str, tenant_id: str) -> dict:

        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_any(template_id)
            if obj is None:
                raise ResourceNotFoundError(
                    message=f"Prompt template not found: {template_id}",
                    details={"id": template_id},
                )


            if obj.scope == "domain":
                require_tenant(tenant_id)
                if obj.tenant_id != tenant_id:
                    raise PermissionDeniedError(
                        message="You do not have permission to access this prompt template",
                        details={"id": template_id},
                    )

            data = obj.to_dict()
            data["versions"] = obj.versions_json or []

            versions = obj.versions_json or []
            data["current_content"] = versions[0]["content"] if versions else ""
            return data



    async def create_template(self, tenant_id: str, data: dict, user_id: str | None = None) -> dict:

        tenant_id = require_tenant(tenant_id)
        name = data.get("name", "").strip()
        content = data.get("content", "").strip()
        category = data.get("category", "其他")

        if not name:
            raise InvalidParameterError(message="Template name must not be empty")
        if not content:
            raise InvalidParameterError(message="Prompt content must not be empty")
        if category not in VALID_CATEGORIES:
            raise InvalidParameterError(
                message=f"Invalid category: {category}",
                details={"valid_categories": sorted(VALID_CATEGORIES)},
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        operator = user_id or data.get("created_by", "系统用户")
        version_entry = {
            "version": "1.0",
            "content": content,
            "updated_by": operator,
            "updated_at": now,
            "remark": "初始版本",
        }

        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                name=name,
                category=category,
                scope="domain",
                description=data.get("description"),
                status=data.get("status", "启用"),
                current_version="1.0",
                versions_json=[version_entry],
                created_by=operator,
            )
            await session.commit()
            return obj.to_dict()



    async def update_template(
        self, template_id: str, tenant_id: str, data: dict, user_id: str | None = None
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_required_domain_template(template_id, tenant_id)


            if obj.scope == "system":
                raise PermissionDeniedError(
                    message="System-wide templates cannot be modified",
                    details={"id": template_id, "scope": "system"},
                )

            new_content = data.get("content")
            old_versions = list(obj.versions_json or [])
            old_current = old_versions[0] if old_versions else None


            if data.get("name") is not None:
                obj.name = data["name"].strip()
            if data.get("description") is not None:
                obj.description = data["description"]
            if data.get("status") is not None:
                obj.status = data["status"]
            if data.get("category") is not None:
                cat = data["category"]
                if cat not in VALID_CATEGORIES:
                    raise InvalidParameterError(message=f"Invalid category: {cat}")
                obj.category = cat


            content_changed = (
                new_content is not None
                and (old_current is None or new_content != old_current.get("content"))
            )
            if content_changed:
                new_ver = self._resolve_next_version(
                    obj.current_version,
                    data.get("target_version"),
                    old_versions,
                )
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                operator = user_id or "系统用户"
                remark = data.get("version_remark", "").strip() or "内容更新"
                new_entry = {
                    "version": new_ver,
                    "content": new_content,
                    "updated_by": operator,
                    "updated_at": now,
                    "remark": remark,
                }
                obj.current_version = new_ver
                obj.versions_json = [new_entry] + old_versions

            await session.commit()
            return obj.to_dict()



    async def delete_template(self, template_id: str, tenant_id: str) -> bool:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_any(template_id)
            if obj is None:
                raise ResourceNotFoundError(
                    message=f"Prompt template not found: {template_id}"
                )

            if obj.scope == "system":
                raise PermissionDeniedError(
                    message="System-wide templates cannot be deleted",
                    details={"id": template_id, "scope": "system"},
                )

            if obj.tenant_id != tenant_id:
                raise PermissionDeniedError(
                    message="You do not have permission to delete this prompt template",
                    details={"id": template_id},
                )

            deleted = await repo.delete_soft(obj, tenant_id)
            await session.commit()
            return deleted



    async def copy_template(
        self, template_id: str, tenant_id: str, user_id: str | None = None
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            src = await repo.get_any(template_id)
            if src is None:
                raise ResourceNotFoundError(
                    message=f"Prompt template not found: {template_id}"
                )

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            operator = user_id or "系统用户"

            new_versions = [
                {
                    "version": "1.0",
                    "content": (
                        src.versions_json[0]["content"]
                        if src.versions_json
                        else ""
                    ),
                    "updated_by": operator,
                    "updated_at": now,
                    "remark": f"从{'系统全局' if src.scope == 'system' else '领域'}模板复制",
                }
            ]

            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                name=f"{src.name} (副本)",
                category=src.category,
                scope="domain",
                description=src.description,
                status="启用",
                current_version="1.0",
                versions_json=new_versions,
                created_by=operator,
            )
            await session.commit()
            return obj.to_dict()



    async def list_versions(self, template_id: str, tenant_id: str) -> dict:

        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_required_domain_template(template_id, tenant_id)
            return {
                "items": obj.versions_json or [],
                "current_version": obj.current_version,
            }

    async def rollback_version(
        self, template_id: str, tenant_id: str, target_version: str, user_id: str | None = None
    ) -> dict:

        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_required_domain_template(template_id, tenant_id)

            versions = list(obj.versions_json or [])
            target = next((v for v in versions if v.get("version") == target_version), None)
            if target is None:
                raise ResourceNotFoundError(
                    message=f"Version not found: {target_version}",
                    details={"template_id": template_id, "target_version": target_version},
                )

            if target_version == obj.current_version:
                raise InvalidParameterError(message="Cannot roll back to the current version")

            new_ver = self._bump_version(obj.current_version)
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            operator = user_id or "系统用户"
            new_entry = {
                "version": new_ver,
                "content": target["content"],
                "updated_by": operator,
                "updated_at": now,
                "remark": f"回滚自 v{target_version}",
            }

            obj.current_version = new_ver
            obj.versions_json = [new_entry] + versions
            await session.commit()
            return obj.to_dict()



    @staticmethod
    def _bump_version(current: str) -> str:

        parts = str(current or "1.0").split(".")
        last = int(parts[-1] or 0)
        parts[-1] = str(last + 1)
        return ".".join(parts)

    @classmethod
    def _resolve_next_version(
        cls,
        current: str,
        target_version: str | None,
        existing_versions: list[dict],
    ) -> str:

        requested = (target_version or "").strip()
        if not requested:
            return cls._bump_version(current)

        if not re.fullmatch(r"\d+\.\d+", requested):
            raise InvalidParameterError(message="Invalid version format. Use a format such as 1.1 or 2.0")

        if cls._version_key(requested) <= cls._version_key(current or "1.0"):
            raise InvalidParameterError(message="The new version must be greater than the current version")

        if any(str(v.get("version")) == requested for v in existing_versions):
            raise InvalidParameterError(message=f"Version already exists: {requested}")

        return requested

    @staticmethod
    def _version_key(version: str) -> tuple[int, int]:
        major, minor = str(version or "0.0").split(".", 1)
        return int(major), int(minor)

    @staticmethod
    def _match_content(template: PromptTemplate, keyword: str) -> bool:

        kw = keyword.lower()
        for v in (template.versions_json or []):
            if kw in (v.get("content", "") or "").lower():
                return True
        return False

    @staticmethod
    def _match_name_desc(template: PromptTemplate, keyword: str) -> bool:

        kw = keyword.lower()
        if kw in (template.name or "").lower():
            return True
        if kw in (template.description or "").lower():
            return True
        return False
