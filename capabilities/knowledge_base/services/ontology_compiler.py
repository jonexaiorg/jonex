
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from jonex_core.common.cache import CacheUtil
from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import (
    InvalidParameterError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from jonex_core.common.tenant import require_tenant

from ..repository.ontology_schema_repository import OntologySchemaRepository
from .template_schema_provider import ObjectDef, ScenarioDef, TemplateSchemaProvider

logger = logging.getLogger(__name__)

ONTOLOGY_AUTO_COMPILE = os.getenv("ONTOLOGY_AUTO_COMPILE", "true").lower() == "true"
ONTOLOGY_COMPILED_SCHEMA_TTL = int(os.getenv("ONTOLOGY_COMPILED_SCHEMA_TTL", "3600"))
ONTOLOGY_SCHEMA_FALLBACK_PATH = os.getenv(
    "ONTOLOGY_SCHEMA_FALLBACK_PATH",
    "deploy/config/ontology/default.yaml",
)

VALID_ATTR_TYPES = {"string", "text", "number", "date", "enum", "boolean"}
VALID_CARDINALITY = {"one_to_one", "one_to_many", "many_to_many", "custom"}

CARDINALITY_MAP = {
    "一对多": "one_to_many",
    "多对多": "many_to_many",
    "一对一": "one_to_one",
    "自定义": "custom",
    "one_to_many": "one_to_many",
    "many_to_many": "many_to_many",
    "one_to_one": "one_to_one",
    "custom": "custom",
}


def _compiled_key(tenant_id: str, knowledge_base_id: str) -> str:
    return f"ontology:compiled:{tenant_id}:{knowledge_base_id}"


def _hash_key(tenant_id: str, knowledge_base_id: str) -> str:
    return f"ontology:compiled:hash:{tenant_id}:{knowledge_base_id}"


def _normalize_cardinality(raw: str) -> str:
    return CARDINALITY_MAP.get((raw or "").strip(), "custom")


def _normalize_editor_status(raw: Optional[str]) -> str:
    value = (raw or "").strip().lower()
    if value in {"inactive", "disabled", "draft", "off"}:
        return "inactive"
    return "active"


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = (item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


class OntologyCompiler:


    async def bind_template(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        template_domain_id: Optional[str] = None,
        template_scenario_id: Optional[str] = None,
        source_type: str = "business_template",
    ) -> dict:
        tenant_id = require_tenant(tenant_id)

        async with get_db_session() as session:
            repo = OntologySchemaRepository(session)
            binding = await repo.upsert_binding(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                template_domain_id=template_domain_id,
                template_scenario_id=template_scenario_id,
                source_type=source_type,
            )
            await session.commit()

        if ONTOLOGY_AUTO_COMPILE:
            try:
                await self.compile_for_knowledge_base(tenant_id, knowledge_base_id, force=True)
            except Exception as e:
                logger.warning("Auto-compile failed after binding: %s", e)

        return binding.to_dict()

    async def compile_for_knowledge_base(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        force: bool = False,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)

        async with get_db_session() as session:
            repo = OntologySchemaRepository(session)
            binding = await repo.get_binding(tenant_id, knowledge_base_id)

            if binding and binding.template_scenario_id:
                provider = TemplateSchemaProvider(session)
                scenario = await provider.load_scenario(tenant_id, binding.template_scenario_id)
                if scenario is None:
                    raise ResourceNotFoundError(
                        message=f"Template scenario does not exist or is unavailable: {binding.template_scenario_id}",
                    )
                compiled = self._compile_from_scenario(scenario, source_type=binding.source_type or "business_template")
            else:
                compiled = await self._compile_from_yaml_fallback()
                compiled["template_domain_id"] = None
                compiled["template_scenario_id"] = None
                compiled["source_type"] = "yaml_default"

            compiled["tenant_id"] = tenant_id
            compiled["knowledge_base_id"] = knowledge_base_id

            cs = await repo.upsert_compiled_schema(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                template_domain_id=compiled.get("template_domain_id"),
                template_scenario_id=compiled.get("template_scenario_id"),
                source_type=compiled["source_type"],
                source_version=compiled.get("source_version", 1),
                source_hash=compiled.get("source_hash"),
                entity_types=compiled["entity_types"],
                relation_types=compiled["relation_types"],
                constraints=compiled.get("constraints", []),
                disambiguation=compiled.get("disambiguation", {}),
                prompt_schema=compiled["prompt_schema"],
                schema_mode="template_seeded",
                sync_status="synced",
            )
            await session.commit()

        await self._set_cache(tenant_id, knowledge_base_id, cs.to_dict())
        return cs.to_dict()

    async def get_compiled_schema(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        auto_compile: bool = True,
    ) -> Optional[dict]:
        tenant_id = require_tenant(tenant_id)

        cached = await self._get_cache(tenant_id, knowledge_base_id)
        if cached is not None:
            return cached

        async with get_db_session() as session:
            repo = OntologySchemaRepository(session)
            schema = await repo.get_compiled_schema(tenant_id, knowledge_base_id)
            if schema is not None:
                result = schema.to_dict()
                await self._set_cache(tenant_id, knowledge_base_id, result)
                return result

        if auto_compile and ONTOLOGY_AUTO_COMPILE:
            try:
                return await self.compile_for_knowledge_base(tenant_id, knowledge_base_id)
            except Exception as e:
                logger.warning("Auto-compile failed for %s/%s: %s", tenant_id, knowledge_base_id, e)

        try:
            return await self._compile_from_yaml_fallback()
        except Exception as e:
            logger.error(
                "Compiled schema unavailable for %s/%s: %s",
                tenant_id,
                knowledge_base_id,
                e,
            )
            return None

    async def get_editor_state(
        self,
        tenant_id: str,
        knowledge_base_id: str,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)

        async with get_db_session() as session:
            repo = OntologySchemaRepository(session)
            binding = await repo.get_binding(tenant_id, knowledge_base_id)
            schema = await repo.get_compiled_schema(tenant_id, knowledge_base_id)

            current_template = None
            if binding and binding.template_scenario_id:
                provider = TemplateSchemaProvider(session)
                scenario = await provider.load_scenario(tenant_id, binding.template_scenario_id)
                if scenario is not None:
                    current_template = {
                        "domain_id": scenario.domain_id,
                        "domain_name": scenario.domain_name,
                        "scenario_id": scenario.scenario_id,
                        "scenario_name": scenario.scenario_name,
                        "source_version": scenario.version,
                        "source_hash": scenario.structure_hash,
                    }

        return {
            "knowledge_base_id": knowledge_base_id,
            "binding": binding.to_dict() if binding else None,
            "compiled_schema": schema.to_dict() if schema else None,
            "current_template": current_template,
        }

    async def save_compiled_schema(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        entity_types: list[dict],
        relation_types: list[dict],
        edited_by: Optional[str] = None,
        constraints: Optional[list[dict]] = None,
        expected_schema_version: Optional[int] = None,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)


        if expected_schema_version is None:
            raise InvalidParameterError(message="缺少 expected_schema_version")

        normalized_entities = self._normalize_entity_types(entity_types)
        normalized_relations = self._normalize_relation_types(relation_types, normalized_entities)
        prompt_schema = self._build_prompt_schema(normalized_entities, normalized_relations)
        edited_at = datetime.now(timezone.utc)

        async with get_db_session() as session:
            repo = OntologySchemaRepository(session)
            binding = await repo.get_binding(tenant_id, knowledge_base_id)
            current = await repo.get_compiled_schema(tenant_id, knowledge_base_id)

            source_type = current.source_type if current else "manual"
            template_domain_id = current.template_domain_id if current else None
            template_scenario_id = current.template_scenario_id if current else None
            source_version = current.source_version if current else 1
            source_hash = current.source_hash if current else None
            disambiguation = current.disambiguation if current else {"case_insensitive": True, "alias_merge": True}


            if constraints is None:
                final_constraints = self._strip_legacy_stub(current.constraints if current else [])
            else:
                final_constraints = self._normalize_constraints(
                    constraints, normalized_entities, normalized_relations
                )

            if binding and binding.template_scenario_id:
                source_type = binding.source_type or source_type
                if not current or not source_hash:
                    provider = TemplateSchemaProvider(session)
                    scenario = await provider.load_scenario(tenant_id, binding.template_scenario_id)
                    if scenario is not None:
                        template_domain_id = scenario.domain_id
                        template_scenario_id = scenario.scenario_id
                        source_version = scenario.version
                        source_hash = scenario.structure_hash

            compiled = await repo.upsert_compiled_schema(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                template_domain_id=template_domain_id,
                template_scenario_id=template_scenario_id,
                source_type=source_type,
                source_version=source_version,
                source_hash=source_hash,
                entity_types=normalized_entities,
                relation_types=normalized_relations,
                constraints=final_constraints,
                disambiguation=disambiguation or {"case_insensitive": True, "alias_merge": True},
                prompt_schema=prompt_schema,
                schema_mode="manual_edited",
                sync_status="synced",
                edited_at=edited_at,
                edited_by=edited_by,
                expected_version=expected_schema_version,
            )
            await session.commit()

        await self._set_cache(tenant_id, knowledge_base_id, compiled.to_dict())
        return compiled.to_dict()

    async def reseed_from_template(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        template_scenario_id: str,
        template_domain_id: Optional[str] = None,
        source_type: str = "business_template",
    ) -> dict:
        tenant_id = require_tenant(tenant_id)

        async with get_db_session() as session:
            repo = OntologySchemaRepository(session)
            await repo.upsert_binding(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                template_domain_id=template_domain_id,
                template_scenario_id=template_scenario_id,
                source_type=source_type,
            )
            await session.commit()

        return await self.compile_for_knowledge_base(tenant_id, knowledge_base_id, force=True)

    async def list_impacted_knowledge_bases(
        self,
        tenant_id: str,
        template_scenario_id: str,
    ) -> list[dict]:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = OntologySchemaRepository(session)
            bindings = await repo.list_by_template_scenario(tenant_id, template_scenario_id)
            items = []
            for binding in bindings:
                schema = await repo.get_compiled_schema(tenant_id, binding.knowledge_base_id)
                items.append({
                    "tenant_id": binding.tenant_id,
                    "knowledge_base_id": binding.knowledge_base_id,
                    "schema_outdated": schema is None or schema.sync_status == "outdated",
                })
            return items

    async def react_to_publish(self, tenant_id: str, template_scenario_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = OntologySchemaRepository(session)
            bindings = await repo.list_by_template_scenario(tenant_id, template_scenario_id)
            outdated = []
            for binding in bindings:
                changed = await repo.mark_schema_outdated(tenant_id, binding.knowledge_base_id)
                if changed:
                    outdated.append(binding.knowledge_base_id)
            await session.commit()

        for knowledge_base_id in outdated:
            await self.invalidate_cache(tenant_id, knowledge_base_id)

        logger.info(
            "react_to_publish scenario=%s marked %d KB schemas outdated",
            template_scenario_id,
            len(outdated),
        )
        return {"outdated_kbs": outdated, "recompiled_kbs": [], "reset_documents": 0}

    def _compile_from_scenario(
        self,
        scenario: ScenarioDef,
        source_type: str = "business_template",
    ) -> dict:
        entity_types: list[dict] = []
        for obj in scenario.objects:
            code = obj.ontology_code or self._slugify(obj.name)
            entity_types.append({
                "name": code,
                "display_name": obj.name,
                "description": obj.description or "",
                "requirement": "",
                "status": _normalize_editor_status(obj.status),
                "aliases": obj.aliases or [],
                "source_object_id": obj.id,
                "attributes": [
                    {
                        "name": attr.ontology_code or self._slugify(attr.attr_name),
                        "display_name": attr.attr_name,
                        "description": attr.description or "",
                        "type": attr.attr_type,
                        "required": attr.is_required,
                        "is_primary_key": bool(attr.is_primary_key),
                        "source_attribute_id": attr.id,
                    }
                    for attr in obj.attributes
                ],
            })

        relation_types: list[dict] = []
        for rel in scenario.relations:
            source_name = self._resolve_entity_code(rel.source_object_id, scenario.objects)
            target_name = self._resolve_entity_code(rel.target_object_id, scenario.objects)
            if not source_name or not target_name:
                logger.warning("Skip relation %s due to unresolved endpoints", rel.id)
                continue
            relation_types.append({
                "name": rel.ontology_code or self._slugify(rel.name),
                "display_name": rel.name,
                "description": rel.description or "",
                "status": _normalize_editor_status(rel.status),
                "aliases": rel.aliases or [],
                "source": source_name,
                "target": target_name,
                "source_relation_id": rel.id,
                "cardinality": _normalize_cardinality(rel.relation_type),
            })

        return {
            "template_domain_id": scenario.domain_id,
            "template_scenario_id": scenario.scenario_id,
            "source_type": source_type,
            "source_version": scenario.version,
            "source_hash": scenario.structure_hash,
            "entity_types": entity_types,
            "relation_types": relation_types,
            "constraints": [],
            "disambiguation": {"case_insensitive": True, "alias_merge": True},
            "prompt_schema": self._build_prompt_schema(entity_types, relation_types),
            "compiled_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _compile_from_yaml_fallback(self) -> dict:
        try:
            from jonex_core.capability.atomic.ontology.registry import OntologyRegistry

            registry = OntologyRegistry()
            schema = registry.load(ONTOLOGY_SCHEMA_FALLBACK_PATH)
            prompt = json.loads(registry.to_prompt_json(schema.domain))

            entity_types = [
                {
                    "name": entity_type.name,
                    "display_name": entity_type.name,
                    "description": "",
                    "requirement": "",
                    "status": "active",
                    "aliases": entity_type.aliases,
                    "source_object_id": None,
                    "attributes": [
                        {
                            "name": attr.name,
                            "display_name": attr.name,
                            "description": "",
                            "type": attr.type,
                            "required": attr.required,
                            "is_primary_key": False,
                            "source_attribute_id": None,
                        }
                        for attr in entity_type.attributes
                    ],
                }
                for entity_type in schema.entity_types
            ]
            relation_types = [
                {
                    "name": relation_type.name,
                    "display_name": relation_type.name,
                    "description": "",
                    "status": "active",
                    "aliases": [],
                    "source": relation_type.source,
                    "target": relation_type.target,
                    "source_relation_id": None,
                    "cardinality": "custom",
                }
                for relation_type in schema.relation_types
            ]

            return {
                "template_domain_id": None,
                "template_scenario_id": None,
                "source_type": "yaml_default",
                "source_version": 1,
                "source_hash": None,
                "entity_types": entity_types,
                "relation_types": relation_types,
                "constraints": [],
                "disambiguation": {"case_insensitive": True, "alias_merge": True},
                "prompt_schema": prompt or self._build_prompt_schema(entity_types, relation_types),
                "compiled_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error("YAML fallback compile failed: %s", e)
            raise

    def _normalize_entity_types(self, entity_types: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        names_seen: set[str] = set()

        for index, item in enumerate(entity_types, start=1):
            name = self._require_name(item.get("name"), f"entity_types[{index}].name")
            if name in names_seen:
                raise InvalidParameterError(message=f"实体编码重复: {name}")
            names_seen.add(name)

            attr_names_seen: set[str] = set()
            attributes = []
            for attr_index, attr in enumerate(item.get("attributes") or [], start=1):
                attr_name = self._require_name(attr.get("name"), f"entity_types[{index}].attributes[{attr_index}].name")
                if attr_name in attr_names_seen:
                    raise InvalidParameterError(message=f"实体 {name} 下属性编码重复: {attr_name}")
                attr_names_seen.add(attr_name)
                attr_type = (attr.get("type") or "string").strip().lower()
                if attr_type not in VALID_ATTR_TYPES:
                    raise InvalidParameterError(message=f"属性类型不合法: {name}.{attr_name}={attr_type}")
                attributes.append({
                    "name": attr_name,
                    "display_name": (attr.get("display_name") or attr_name).strip(),
                    "description": (attr.get("description") or "").strip(),
                    "type": attr_type,
                    "required": bool(attr.get("required")),
                    "is_primary_key": bool(attr.get("is_primary_key")),
                    "source_attribute_id": attr.get("source_attribute_id"),
                })

            normalized.append({
                "name": name,
                "display_name": (item.get("display_name") or name).strip(),
                "description": (item.get("description") or "").strip(),
                "requirement": (item.get("requirement") or "").strip(),
                "status": _normalize_editor_status(item.get("status")),
                "aliases": _dedupe_strings(item.get("aliases") or []),
                "source_object_id": item.get("source_object_id"),
                "attributes": attributes,
            })

        return normalized

    def _normalize_relation_types(self, relation_types: list[dict], entity_types: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        names_seen: set[str] = set()
        entity_names = {item["name"] for item in entity_types}

        for index, item in enumerate(relation_types, start=1):
            name = self._require_name(item.get("name"), f"relation_types[{index}].name")
            if name in names_seen:
                raise InvalidParameterError(message=f"关系编码重复: {name}")
            names_seen.add(name)

            source = self._require_name(item.get("source"), f"relation_types[{index}].source")
            target = self._require_name(item.get("target"), f"relation_types[{index}].target")
            if source not in entity_names:
                raise InvalidParameterError(message=f"关系 {name} 的 source 不存在: {source}")
            if target not in entity_names:
                raise InvalidParameterError(message=f"关系 {name} 的 target 不存在: {target}")

            cardinality = _normalize_cardinality(item.get("cardinality") or "custom")
            if cardinality not in VALID_CARDINALITY:
                raise InvalidParameterError(message=f"关系基数不合法: {name}={cardinality}")

            normalized.append({
                "name": name,
                "display_name": (item.get("display_name") or name).strip(),
                "description": (item.get("description") or "").strip(),
                "status": _normalize_editor_status(item.get("status")),
                "aliases": _dedupe_strings(item.get("aliases") or []),
                "source": source,
                "target": target,
                "source_relation_id": item.get("source_relation_id"),
                "cardinality": cardinality,
            })

        return normalized

    @staticmethod
    def _strip_legacy_stub(constraints: Optional[list[dict]]) -> list[dict]:

        result: list[dict] = []
        for item in constraints or []:
            if isinstance(item, dict) and (item.get("target_code") or "").strip():
                result.append(item)
        return result

    def _normalize_constraints(
        self,
        constraints: list[dict],
        entity_types: list[dict],
        relation_types: list[dict],
    ) -> list[dict]:

        entity_codes = {item["name"] for item in entity_types}
        attribute_codes = {
            f'{item["name"]}.{attr["name"]}'
            for item in entity_types
            for attr in item.get("attributes", [])
        }
        relation_codes = {item["name"] for item in relation_types}

        normalized: list[dict] = []
        names_seen: set[str] = set()

        for index, item in enumerate(constraints, start=1):
            name = self._require_name(item.get("name"), f"constraints[{index}].name")
            if name in names_seen:
                raise InvalidParameterError(message=f"约束名称重复: {name}")
            names_seen.add(name)

            target_type = (item.get("target_type") or "").strip().lower()
            if target_type not in {"entity", "attribute", "relation"}:
                raise InvalidParameterError(message=f"约束目标类型不合法: {name}={target_type}")

            target_code = self._require_name(
                item.get("target_code"), f"constraints[{index}].target_code"
            )
            valid_targets = {
                "entity": entity_codes,
                "attribute": attribute_codes,
                "relation": relation_codes,
            }[target_type]
            if target_code not in valid_targets:
                raise InvalidParameterError(
                    message=f"约束目标不存在: {target_code}",
                    details={"name": name, "target_type": target_type},
                )

            normalized.append({
                "name": name,
                "target_type": target_type,
                "target_code": target_code,
                "target_label": (item.get("target_label") or "").strip() or None,
                "constraint_type": (item.get("constraint_type") or "custom").strip(),
                "expression": (item.get("expression") or "").strip(),
                "suggestion": (item.get("suggestion") or "").strip(),
            })

        return normalized

    def _build_prompt_schema(self, entity_types: list[dict], relation_types: list[dict]) -> dict:
        return {
            "entity_types": [
                {
                    "name": entity_type["name"],
                    "aliases": entity_type.get("aliases", []),
                    "attributes": [
                        {
                            "name": attr["name"],
                            "type": attr["type"],
                            "required": attr["required"],
                        }
                        for attr in entity_type.get("attributes", [])
                    ],
                }
                for entity_type in entity_types
            ],
            "relation_types": [
                {
                    "name": relation_type["name"],
                    "source": relation_type["source"],
                    "target": relation_type["target"],
                }
                for relation_type in relation_types
            ],
        }

    async def _set_cache(self, tenant_id: str, knowledge_base_id: str, data: dict) -> None:
        try:
            key = _compiled_key(tenant_id, knowledge_base_id)
            raw = json.dumps(data, ensure_ascii=False, default=str)
            await CacheUtil.set(key, raw, expire=ONTOLOGY_COMPILED_SCHEMA_TTL)
        except Exception as e:
            logger.warning("Redis cache write failed: %s", e)

    async def _get_cache(self, tenant_id: str, knowledge_base_id: str) -> Optional[dict]:
        try:
            raw = await CacheUtil.get(_compiled_key(tenant_id, knowledge_base_id))
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning("Redis cache read failed: %s", e)
        return None

    async def invalidate_cache(self, tenant_id: str, knowledge_base_id: str) -> None:
        try:
            await CacheUtil.delete(_compiled_key(tenant_id, knowledge_base_id))
            await CacheUtil.delete(_hash_key(tenant_id, knowledge_base_id))
        except Exception as e:
            logger.warning("Redis cache invalidation failed: %s", e)

    @staticmethod
    def _slugify(name: str) -> str:
        import re

        value = (name or "").strip()
        value = re.sub(r"[\s/\\]+", "_", value)
        value = re.sub(r"[^a-zA-Z0-9_\u4e00-\u9fff]", "", value)
        return value or "unknown"

    @staticmethod
    def _resolve_entity_code(object_id: str, objects: list[ObjectDef]) -> Optional[str]:
        for obj in objects:
            if obj.id == object_id:
                return obj.ontology_code or OntologyCompiler._slugify(obj.name)
        return None

    @staticmethod
    def _require_name(value: Optional[str], field_name: str) -> str:
        name = (value or "").strip()
        if not name:
            raise InvalidParameterError(message=f"{field_name} 不能为空")
        return name


__all__ = ["OntologyCompiler"]
