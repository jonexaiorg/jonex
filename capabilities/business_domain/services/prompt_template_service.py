"""
提示词模板 Service。

业务规则：
- system 模板：只读（查看/列表/复制），不可增删改
- domain 模板：完整 CRUD + 版本管理 + 回滚
- copy：可将 system 或 domain 模板复制为当前租户的 domain 模板
- 版本管理：versions_json[0] 始终为当前版本；编辑时内容变化则自动生成新版本
"""
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
from jonex_core.common.i18n import translate
from jonex_core.common.tenant import require_tenant

from capabilities.business_domain.models.prompt_template import PromptTemplate
from capabilities.business_domain.repository.prompt_template_repository import (
    PromptTemplateRepository,
)

# 分类枚举值（与种子 SQL + 原型 UI 保持一致）
VALID_CATEGORIES = {"通用问答", "文档处理", "金融分析", "合同审查", "数据分析", "其他"}


class PromptTemplateService:
    """提示词模板服务"""

    # ── 列表查询 ──

    async def list_templates(
        self,
        tenant_id: str,
        scope: str | None = None,
        category: str | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
        domain_space_id: str | None = None,
    ) -> dict:
        """分页列表。scope 决定查询路径：system 共享查询，domain 租户隔离查询。
        当 domain_space_id 提供时，domain 模板按空间过滤。"""
        result_items: list[dict] = []
        total = 0

        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)

            # 构建公共筛选条件
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
                # keyword 额外匹配 content（version 内容）
                if keyword:
                    sys_items = [
                        t for t in sys_items
                        if self._match_content(t, keyword) or self._match_name_desc(t, keyword)
                    ]
                total += len(sys_items)
                result_items.extend(t.to_dict() for t in sys_items)

            if need_domain:
                # SDD-DDD: 领域空间隔离 — 无 domain_space_id 时不返回任何领域模板
                if not domain_space_id:
                    pass  # 空间上下文中不返回归属不明的模板
                else:
                    try:
                        dom_items = await repo.list_domain_templates(
                            tenant_id, offset=0, limit=1000, space_id=domain_space_id, extra_conditions=extra
                        )
                        if keyword:
                            dom_items = [
                                t for t in dom_items
                                if self._match_content(t, keyword) or self._match_name_desc(t, keyword)
                            ]
                        total += len(dom_items)
                        result_items.extend(t.to_dict() for t in dom_items)
                    except Exception:
                        # tenant 校验失败时忽略 domain 结果
                        pass

            # 分页（内存分页，因为两个来源合并）
            result_items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
            paged = result_items[offset : offset + limit]

            return {
                "items": paged,
                "total": total,
                "offset": offset,
                "limit": limit,
            }

    # ── 详情 ──

    async def get_template(self, template_id: str, tenant_id: str, domain_space_id: str | None = None) -> dict:
        """获取模板详情。
        system 模板不过滤租户，domain 模板校验租户归属 + 可选的 space_id 校验。"""
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_any(template_id)
            if obj is None:
                raise ResourceNotFoundError(
                    message=translate("err.prompt.not_found", params={"template_id": template_id}, fallback=f"提示词模板不存在: {template_id}"),  # 原消息
                    details={"id": template_id},
                )

            # SDD-DDD: 领域空间隔离 — domain 模板必须校验空间归属
            if obj.scope == "domain":
                require_tenant(tenant_id)
                if obj.tenant_id != tenant_id:
                    raise PermissionDeniedError(
                        message=translate("err.prompt.access_denied", fallback="无权访问该提示词模板"),  # 原消息
                        details={"id": template_id},
                    )
                if domain_space_id is None:
                    raise InvalidParameterError(
                        message=translate("err.prompt.space_id_required",
                                          fallback="查询领域模板必须指定领域空间ID"),
                        details={"id": template_id, "scope": "domain"},
                    )
                if not obj.space_id:
                    raise PermissionDeniedError(
                        message=translate("err.prompt.space_mismatch",
                                          params={"template_id": template_id},
                                          fallback="旧版模板缺少空间归属，请联系管理员迁移"),
                        details={"id": template_id, "space_id": None},
                    )
                if obj.space_id != domain_space_id:
                    raise PermissionDeniedError(
                        message=translate("err.prompt.space_mismatch",
                                          params={"template_id": template_id, "space_id": obj.space_id},
                                          fallback="无权访问该领域空间的提示词模板"),
                        details={"id": template_id, "expected_space": domain_space_id, "actual_space": obj.space_id},
                    )

            data = obj.to_dict()
            data["versions"] = obj.versions_json or []
            # 当前版本内容便捷字段
            versions = obj.versions_json or []
            data["current_content"] = versions[0]["content"] if versions else ""
            return data

    # ── 创建（仅 domain） ──

    async def create_template(self, tenant_id: str, data: dict, user_id: str | None = None, domain_space_id: str | None = None) -> dict:
        """创建领域模板（scope 固定 domain，初始化 v1.0，可指定 space_id）"""
        tenant_id = require_tenant(tenant_id)
        name = data.get("name", "").strip()
        content = data.get("content", "").strip()
        category = data.get("category", "其他")
        space_id = domain_space_id or data.get("domain_space_id")

        if not name:
            raise InvalidParameterError(message=translate("err.template.name_required", fallback="模板名称不能为空"))  # 原消息
        if not content:
            raise InvalidParameterError(message=translate("err.prompt.content_required", fallback="提示词内容不能为空"))  # 原消息
        if category not in VALID_CATEGORIES:
            raise InvalidParameterError(
                message=translate("err.prompt.invalid_category", params={"category": category}, fallback=f"无效分类: {category}"),  # 原消息
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
                space_id=space_id,
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

    # ── 更新（仅 domain） ──

    async def update_template(
        self, template_id: str, tenant_id: str, data: dict,
        user_id: str | None = None,
        domain_space_id: str | None = None,
    ) -> dict:
        """更新领域模板。内容变化时自动生成新版本号。强制 domain_space_id 空间隔离。"""
        tenant_id = require_tenant(tenant_id)
        if domain_space_id is None:
            raise InvalidParameterError(
                message=translate("err.prompt.space_id_required",
                                  fallback="更新领域模板必须指定领域空间ID"),
                details={"id": template_id, "scope": "domain"},
            )
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_required_domain_template(template_id, tenant_id, space_id=domain_space_id)

            # scope 写保护
            if obj.scope == "system":
                raise PermissionDeniedError(
                    message=translate("err.prompt.system_template_readonly", fallback="系统全局模板不可修改"),  # 原消息
                    details={"id": template_id, "scope": "system"},
                )

            new_content = data.get("content")
            old_versions = list(obj.versions_json or [])
            old_current = old_versions[0] if old_versions else None

            # 更新基本字段
            if data.get("name") is not None:
                obj.name = data["name"].strip()
            if data.get("description") is not None:
                obj.description = data["description"]
            if data.get("status") is not None:
                obj.status = data["status"]
            if data.get("category") is not None:
                cat = data["category"]
                if cat not in VALID_CATEGORIES:
                    raise InvalidParameterError(message=translate("err.prompt.invalid_category", params={"category": cat}, fallback=f"无效分类: {cat}"))  # 原消息
                obj.category = cat

            # 内容变化 → 生成新版本
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

    # ── 删除（仅 domain） ──

    async def delete_template(self, template_id: str, tenant_id: str, domain_space_id: str | None = None) -> bool:
        """软删除领域模板。校验租户归属 + 强制 space_id 校验。"""
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_any(template_id)
            if obj is None:
                raise ResourceNotFoundError(
                    message=translate("err.prompt.not_found", params={"template_id": template_id}, fallback=f"提示词模板不存在: {template_id}")  # 原消息
                )

            if obj.scope == "system":
                raise PermissionDeniedError(
                    message=translate("err.prompt.system_template_readonly", fallback="系统全局模板不可删除"),  # 原消息
                    details={"id": template_id, "scope": "system"},
                )

            if obj.tenant_id != tenant_id:
                raise PermissionDeniedError(
                    message=translate("err.prompt.access_denied", fallback="无权删除该提示词模板"),  # 原消息
                    details={"id": template_id},
                )

            # SDD-DDD: 领域空间隔离 — domain 模板必须校验空间归属
            if domain_space_id is None:
                raise InvalidParameterError(
                    message=translate("err.prompt.space_id_required",
                                      fallback="删除领域模板必须指定领域空间ID"),
                    details={"id": template_id, "scope": "domain"},
                )
            if not obj.space_id:
                raise PermissionDeniedError(
                    message=translate("err.prompt.space_mismatch",
                                      params={"template_id": template_id},
                                      fallback="旧版模板缺少空间归属，请联系管理员迁移"),
                    details={"id": template_id, "space_id": None},
                )
            if obj.space_id != domain_space_id:
                raise PermissionDeniedError(
                    message=translate("err.prompt.space_mismatch",
                                      params={"template_id": template_id, "space_id": obj.space_id},
                                      fallback="无权删除该领域空间的提示词模板"),
                    details={"id": template_id, "expected_space": domain_space_id, "actual_space": obj.space_id},
                )

            deleted = await repo.delete_soft(obj, tenant_id)
            await session.commit()
            return deleted

    # ── 复制 ──

    async def copy_template(
        self, template_id: str, tenant_id: str, user_id: str | None = None, domain_space_id: str | None = None
    ) -> dict:
        """复制模板到当前租户。system 模板复制后变为 domain 模板。可指定目标 space_id。"""
        tenant_id = require_tenant(tenant_id)
        space_id = domain_space_id
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            src = await repo.get_any(template_id)
            if src is None:
                raise ResourceNotFoundError(
                    message=translate("err.prompt.not_found", params={"template_id": template_id}, fallback=f"提示词模板不存在: {template_id}")  # 原消息
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
                space_id=space_id,
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

    # ── 版本管理（仅 domain） ──

    async def list_versions(self, template_id: str, tenant_id: str, domain_space_id: str | None = None) -> dict:
        """获取版本历史列表。强制 space_id 校验确保空间隔离。"""
        tenant_id = require_tenant(tenant_id)
        if domain_space_id is None:
            raise InvalidParameterError(
                message=translate("err.prompt.space_id_required",
                                  fallback="查看版本历史必须指定领域空间ID"),
                details={"id": template_id, "scope": "domain"},
            )
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_required_domain_template(template_id, tenant_id, space_id=domain_space_id)
            return {
                "items": obj.versions_json or [],
                "current_version": obj.current_version,
            }

    async def rollback_version(
        self, template_id: str, tenant_id: str, target_version: str,
        user_id: str | None = None, domain_space_id: str | None = None,
    ) -> dict:
        """回滚到指定历史版本（生成新版本号，保留历史）。强制 space_id 校验。"""
        tenant_id = require_tenant(tenant_id)
        if domain_space_id is None:
            raise InvalidParameterError(
                message=translate("err.prompt.space_id_required",
                                  fallback="回滚版本必须指定领域空间ID"),
                details={"id": template_id, "scope": "domain"},
            )
        async with get_db_session() as session:
            repo = PromptTemplateRepository(session)
            obj = await repo.get_required_domain_template(template_id, tenant_id, space_id=domain_space_id)

            versions = list(obj.versions_json or [])
            target = next((v for v in versions if v.get("version") == target_version), None)
            if target is None:
                raise ResourceNotFoundError(
                    message=translate("err.prompt.version_not_found", params={"version": target_version}, fallback=f"版本不存在: {target_version}"),  # 原消息
                    details={"template_id": template_id, "target_version": target_version},
                )

            if target_version == obj.current_version:
                raise InvalidParameterError(message=translate("err.prompt.cannot_rollback_to_current", fallback="不能回滚到当前版本"))  # 原消息

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

    # ── 工具方法 ──

    @staticmethod
    def _bump_version(current: str) -> str:
        """版本号自增末位：1.0 → 1.1, 2.3 → 2.4"""
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
        """返回下一版本号；用户未指定时沿用小版本自增，指定时校验格式与递增关系。"""
        requested = (target_version or "").strip()
        if not requested:
            return cls._bump_version(current)

        if not re.fullmatch(r"\d+\.\d+", requested):
            raise InvalidParameterError(message=translate("err.prompt.invalid_version_format", fallback="版本号格式无效，请使用如 1.1 或 2.0 的格式"))  # 原消息

        if cls._version_key(requested) <= cls._version_key(current or "1.0"):
            raise InvalidParameterError(message=translate("err.prompt.new_version_must_be_higher", fallback="新版本号必须大于当前版本"))  # 原消息

        if any(str(v.get("version")) == requested for v in existing_versions):
            raise InvalidParameterError(message=translate("err.prompt.version_exists", params={"version": requested}, fallback=f"版本号已存在: {requested}"))  # 原消息

        return requested

    @staticmethod
    def _version_key(version: str) -> tuple[int, int]:
        major, minor = str(version or "0.0").split(".", 1)
        return int(major), int(minor)

    @staticmethod
    def _match_content(template: PromptTemplate, keyword: str) -> bool:
        """检查模板内容是否匹配关键词（搜索 versions_json 中的 content）"""
        kw = keyword.lower()
        for v in (template.versions_json or []):
            if kw in (v.get("content", "") or "").lower():
                return True
        return False

    @staticmethod
    def _match_name_desc(template: PromptTemplate, keyword: str) -> bool:
        """检查名称/描述是否匹配（辅助 filter 用）"""
        kw = keyword.lower()
        if kw in (template.name or "").lower():
            return True
        if kw in (template.description or "").lower():
            return True
        return False
