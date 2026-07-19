
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import InvalidParameterError

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


_PUBLISHABLE_STATUSES = ("active", "draft", "published")


_VALID_ATTR_TYPES = {"string", "text", "number", "date", "enum", "boolean"}


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


    @staticmethod
    async def publish_scenario(tenant_id: str, scenario_id: str) -> dict:

        tenant_id = _check_tenant(tenant_id)

        async with get_db_session() as session:
            scenario_repo = TemplateScenarioRepository(session)
            domain_repo = TemplateDomainRepository(session)
            object_repo = TemplateObjectRepository(session)
            attribute_repo = TemplateAttributeRepository(session)
            relation_repo = TemplateRelationRepository(session)

            scenario = await scenario_repo.get_required(scenario_id, tenant_id)
            domain = await domain_repo.get_required(scenario.domain_id, tenant_id)


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


            errors = []


            obj_codes = [o.ontology_code for o in objects if o.ontology_code]
            if len(obj_codes) != len(set(obj_codes)):
                errors.append("TemplateObject.ontology_code must be unique within a scenario")
            rel_codes = [r.ontology_code for r in relations if r.ontology_code]
            if len(rel_codes) != len(set(rel_codes)):
                errors.append("TemplateRelation.ontology_code must be unique within a scenario")


            for o in objects:
                attrs = attrs_by_obj.get(o.id, [])
                attr_codes = [a.ontology_code for a in attrs if a.ontology_code]
                if len(attr_codes) != len(set(attr_codes)):
                    errors.append(f"TemplateAttribute.ontology_code must be unique within object {o.name}")


            obj_id_set = set(object_ids)
            for r in relations:
                if r.source_object_id not in obj_id_set:
                    errors.append(f"Source object ID {r.source_object_id} for relation {r.name} is not in the current scenario")
                if r.target_object_id not in obj_id_set:
                    errors.append(f"Target object ID {r.target_object_id} for relation {r.name} is not in the current scenario")


            invalid_types = set()
            for o in objects:
                for a in attrs_by_obj.get(o.id, []):
                    normalized = _ATTR_TYPE_NORMALIZE.get(a.attr_type, a.attr_type)
                    if normalized not in _VALID_ATTR_TYPES:
                        invalid_types.add(f"{o.name}.{a.attr_name}: {a.attr_type}")

            if errors:
                raise InvalidParameterError(message="Template validation failed", details={"errors": errors})


            if invalid_types:
                logger.warning("Nonstandard attribute types found (compilation remains available after publishing): %s", invalid_types)


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


            now = datetime.now(timezone.utc)
            new_version = (scenario.version or 1) + 1

            await scenario_repo.update(
                scenario, tenant_id,
                version=new_version,
                published_at=now,
                structure_hash=structure_hash,
            )


            await domain_repo.update(
                domain, tenant_id,
                version=(domain.version or 1) + 1,
                published_at=now,
                structure_hash=structure_hash,
            )

            await session.commit()


            try:
                from capabilities.knowledge_base.services.ontology_compiler import OntologyCompiler
                react = await OntologyCompiler().react_to_publish(tenant_id, scenario_id)
            except Exception as e:
                logger.warning("Failed to mark affected KB schema entries as stale after publishing (nonfatal): %s", e)
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

        tenant_id = _check_tenant(tenant_id)

        from capabilities.knowledge_base.services.template_schema_provider import TemplateSchemaProvider
        from capabilities.knowledge_base.services.ontology_compiler import OntologyCompiler

        async with get_db_session() as session:
            provider = TemplateSchemaProvider(session)
            scenario = await provider.load_scenario(tenant_id, scenario_id)
            if scenario is None:
                raise InvalidParameterError(message=f"Template scenario does not exist or is unavailable: {scenario_id}")

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

        tenant_id = _check_tenant(tenant_id)

        from capabilities.knowledge_base.services.ontology_compiler import OntologyCompiler

        compiler = OntologyCompiler()
        items = await compiler.list_impacted_knowledge_bases(tenant_id, scenario_id)

        return {
            "items": items,
            "total": len(items),
        }


__all__ = ["TemplatePublishService"]
