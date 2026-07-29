"""
TemplatePublishService — 模板发布与编译预览服务。

职责：
1. 发布模板场景：校验 -> 计算结构哈希 -> 更新 version/published_at/structure_hash
2. 编译预览：将 DB 模板编译为 ontology schema（不持久化）
3. 影响范围分析：查询绑定该场景的 KB
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import InvalidParameterError
from jonex_core.common.i18n import translate

from ..models.template import (
    TemplateAttribute,
    TemplateDomain,
    TemplateObject,
    TemplateRelation,
    TemplateScenario,
)
from ..repository import (
    TemplateAttributeRepository,
    TemplateDomainRepository,
    TemplateObjectRepository,
    TemplateRelationRepository,
    TemplateScenarioRepository,
)
from ..services import _check_tenant

logger = logging.getLogger(__name__)

# 编译时允许的 status 值
_PUBLISHABLE_STATUSES = ("active", "draft", "published")

# 标准属性类型集合
_VALID_ATTR_TYPES = {"string", "text", "number", "date", "enum", "boolean"}

# 中文 -> 标准类型映射（用于校验时的修复提示）
_ATTR_TYPE_NORMALIZE = {
    "字符串": "string",
    "文本": "text",
    "数值": "number",
    "数字": "number",
    "日期": "date",
    "枚举": "enum",
    "布尔": "boolean",
    "布尔值": "boolean",
}


def _compute_structure_hash(scenario_id: str, objects: list[dict], relations: list[dict]) -> str:
    """计算场景 + 对象/属性/关系的结构哈希。"""
    payload = {
        "scenario_id": scenario_id,
        "objects": [
            {
                "id": o["id"],
                "ontology_code": o.get("ontology_code"),
                "attributes": [
                    {
                        "id": a["id"],
                        "ontology_code": a.get("ontology_code"),
                        "type": _ATTR_TYPE_NORMALIZE.get(a.get("attr_type", "string"), a.get("attr_type", "string")),
                    }
                    for a in o.get("attributes", [])
                ],
            }
            for o in objects
        ],
        "relations": [
            {
                "id": r["id"],
                "ontology_code": r.get("ontology_code"),
                "source": r.get("source_object_id"),
                "target": r.get("target_object_id"),
            }
            for r in relations
        ],
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


class TemplatePublishService:
    """模板发布与编译预览服务。"""

    @staticmethod
    async def publish_scenario(tenant_id: str, scenario_id: str) -> dict:
        """发布模板场景。

        校验 -> 计算 hash -> 更新版本号/发布时间/hash
        """
        tenant_id = _check_tenant(tenant_id)

        async with get_db_session() as session:
            scenario_repo = TemplateScenarioRepository(session)
            domain_repo = TemplateDomainRepository(session)
            object_repo = TemplateObjectRepository(session)
            attribute_repo = TemplateAttributeRepository(session)
            relation_repo = TemplateRelationRepository(session)

            scenario = await scenario_repo.get_required(scenario_id, tenant_id)
            domain = await domain_repo.get_required(scenario.domain_id, tenant_id)

            # 加载数据
            objects = await object_repo.list_all(
                tenant_id, 0, 10000,
                extra_conditions=[TemplateObject.scenario_id == scenario_id, TemplateObject.is_deleted == 0],
            )
            object_ids = [o.id for o in objects]
            attrs_by_obj: dict[str, list[Any]] = {}
            if object_ids:
                attr_result = await session.execute(
                    select(TemplateAttribute).where(
                        TemplateAttribute.tenant_id == tenant_id,
                        TemplateAttribute.is_deleted == 0,
                        TemplateAttribute.template_object_id.in_(object_ids),
                    )
                )
                for attr in attr_result.scalars():
                    attrs_by_obj.setdefault(attr.template_object_id, []).append(attr)

            relations = await relation_repo.list_all(
                tenant_id, 0, 10000,
                extra_conditions=[TemplateRelation.scenario_id == scenario_id, TemplateRelation.is_deleted == 0],
            )

            # ---- 校验 ----
            errors = []

            # 1. ontology_code 唯一性（同一场景下）
            obj_codes = [o.ontology_code for o in objects if o.ontology_code]
            if len(obj_codes) != len(set(obj_codes)):
                errors.append("同一场景下 TemplateObject.ontology_code 必须唯一")
            rel_codes = [r.ontology_code for r in relations if r.ontology_code]
            if len(rel_codes) != len(set(rel_codes)):
                errors.append("同一场景下 TemplateRelation.ontology_code 必须唯一")

            # 2. 同一对象下 ontology_code 唯一
            for o in objects:
                attrs = attrs_by_obj.get(o.id, [])
                attr_codes = [a.ontology_code for a in attrs if a.ontology_code]
                if len(attr_codes) != len(set(attr_codes)):
                    errors.append(f"对象 {o.name} 下 TemplateAttribute.ontology_code 必须唯一")

            # 3. relation 的 source/target 必须属于同一场景
            obj_id_set = set(object_ids)
            for r in relations:
                if r.source_object_id not in obj_id_set:
                    errors.append(f"关系 {r.name} 的源对象 ID {r.source_object_id} 不在当前场景中")
                if r.target_object_id not in obj_id_set:
                    errors.append(f"关系 {r.name} 的目标对象 ID {r.target_object_id} 不在当前场景中")

            # 4. 属性类型标准化
            invalid_types = set()
            for o in objects:
                for a in attrs_by_obj.get(o.id, []):
                    normalized = _ATTR_TYPE_NORMALIZE.get(a.attr_type, a.attr_type)
                    if normalized not in _VALID_ATTR_TYPES:
                        invalid_types.add(f"{o.name}.{a.attr_name}: {a.attr_type}")

            if errors:
                raise InvalidParameterError(message=translate("err.template.validation_failed", fallback="模板校验失败"), details={"errors": errors})  # 原消息

            # 如果属性类型不标准但可自动修复，记录警告不阻断
            if invalid_types:
                logger.warning("发现非标准属性类型（发布后仍可编译）: %s", invalid_types)

            # ---- 计算哈希 ----
            objects_dicts = [
                {
                    "id": o.id,
                    "ontology_code": o.ontology_code,
                    "attributes": [
                        {
                            "id": a.id,
                            "ontology_code": a.ontology_code,
                            "attr_type": a.attr_type,
                        }
                        for a in attrs_by_obj.get(o.id, [])
                    ],
                }
                for o in objects
            ]
            relations_dicts = [
                {
                    "id": r.id,
                    "ontology_code": r.ontology_code,
                    "source_object_id": r.source_object_id,
                    "target_object_id": r.target_object_id,
                }
                for r in relations
            ]
            structure_hash = _compute_structure_hash(scenario_id, objects_dicts, relations_dicts)

            # ---- 更新版本 ----
            now = datetime.now(timezone.utc)
            new_version = (scenario.version or 1) + 1

            await scenario_repo.update(
                scenario, tenant_id,
                version=new_version,
                published_at=now,
                structure_hash=structure_hash,
            )

            # 同步更新 domain 的哈希
            await domain_repo.update(
                domain, tenant_id,
                version=(domain.version or 1) + 1,
                published_at=now,
                structure_hash=structure_hash,
            )

            await session.commit()

            # 发布后仅标记受影响 KB schema 过期，避免覆盖知识库侧人工编辑。
            try:
                from capabilities.knowledge_base.services.ontology_compiler import OntologyCompiler
                react = await OntologyCompiler().react_to_publish(tenant_id, scenario_id)
            except Exception as e:
                logger.warning("发布后标记受影响 KB schema 过期失败（非致命）: %s", e)
                react = {"outdated_kbs": [], "recompiled_kbs": [], "reset_documents": 0}

            return {
                "scenario_id": scenario_id,
                "domain_id": scenario.domain_id,
                "version": new_version,
                "structure_hash": structure_hash,
                "published_at": now.isoformat(),
                "object_count": len(objects),
                "relation_count": len(relations),
                "impacted": react,
            }

    @staticmethod
    async def compile_preview(tenant_id: str, scenario_id: str) -> dict:
        """编译预览：将 DB 模板编译为 ontology schema（不持久化）。"""
        tenant_id = _check_tenant(tenant_id)

        from capabilities.knowledge_base.services.template_schema_provider import TemplateSchemaProvider
        from capabilities.knowledge_base.services.ontology_compiler import OntologyCompiler

        async with get_db_session() as session:
            provider = TemplateSchemaProvider(session)
            scenario = await provider.load_scenario(tenant_id, scenario_id)
            if scenario is None:
                raise InvalidParameterError(message=translate("err.template.scenario_not_available", params={"scenario_id": scenario_id}, fallback=f"模板场景不存在或不可用: {scenario_id}"))  # 原消息

            compiler = OntologyCompiler()
            compiled = compiler._compile_from_scenario(scenario)

            return {
                "entity_types": compiled["entity_types"],
                "relation_types": compiled["relation_types"],
                "source_version": compiled["source_version"],
                "source_hash": compiled["source_hash"],
            }

    @staticmethod
    async def list_impacted_kbs(tenant_id: str, scenario_id: str) -> dict:
        """查询模板变更影响哪些知识库。"""
        tenant_id = _check_tenant(tenant_id)

        from capabilities.knowledge_base.services.ontology_compiler import OntologyCompiler

        compiler = OntologyCompiler()
        items = await compiler.list_impacted_knowledge_bases(tenant_id, scenario_id)

        return {
            "items": items,
            "total": len(items),
        }


__all__ = ["TemplatePublishService"]
