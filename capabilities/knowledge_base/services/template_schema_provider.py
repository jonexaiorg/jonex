
import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.tenant import require_tenant

logger = logging.getLogger(__name__)





@dataclass
class AttributeDef:
    ontology_code: Optional[str]
    attr_name: str
    attr_type: str
    is_required: bool
    id: str


@dataclass
class ObjectDef:
    id: str
    name: str
    ontology_code: Optional[str]
    aliases: list[str]
    attributes: list[AttributeDef] = field(default_factory=list)


@dataclass
class RelationDef:
    id: str
    name: str
    ontology_code: Optional[str]
    aliases: list[str]
    source_object_id: str
    target_object_id: str
    relation_type: str


@dataclass
class ScenarioDef:
    scenario_id: str
    scenario_name: str
    domain_id: str
    domain_name: str
    objects: list[ObjectDef] = field(default_factory=list)
    relations: list[RelationDef] = field(default_factory=list)
    version: int = 1
    structure_hash: Optional[str] = None




ATTR_TYPE_MAP = {
    "字符串": "string",
    "文本": "text",
    "数值": "number",
    "数字": "number",
    "日期": "date",
    "枚举": "enum",
    "布尔": "boolean",
    "布尔值": "boolean",
    "string": "string",
    "text": "text",
    "number": "number",
    "date": "date",
    "enum": "enum",
    "boolean": "boolean",
}


def _normalize_attr_type(raw: str) -> str:
    return ATTR_TYPE_MAP.get(raw.strip(), "string")




_ACTIVE_STATUSES = ("active", "published")





class TemplateSchemaProvider:


    def __init__(self, session: AsyncSession):
        self.session = session

    async def load_scenario(
        self,
        tenant_id: str,
        template_scenario_id: str,
    ) -> Optional[ScenarioDef]:

        tenant_id = require_tenant(tenant_id)

        def _as_list(v: Any) -> list:
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    return []
            return v or []


        scenario = (await self.session.execute(
            text(
                """
                SELECT id, name, domain_id, version, structure_hash
                FROM business_domain.template_scenarios
                WHERE id = :sid AND tenant_id = :t AND is_deleted = 0
                """
            ),
            {"sid": template_scenario_id, "t": tenant_id},
        )).mappings().first()
        if scenario is None:
            return None


        domain = (await self.session.execute(
            text(
                """
                SELECT name FROM business_domain.template_domains
                WHERE id = :did AND tenant_id = :t AND is_deleted = 0
                """
            ),
            {"did": scenario["domain_id"], "t": tenant_id},
        )).mappings().first()
        domain_name = domain["name"] if domain else ""


        objects_raw = (await self.session.execute(
            text(
                """
                SELECT id, name, ontology_code, aliases
                FROM business_domain.template_objects
                WHERE scenario_id = :sid AND tenant_id = :t AND is_deleted = 0
                """
            ),
            {"sid": template_scenario_id, "t": tenant_id},
        )).mappings().all()
        object_ids = [o["id"] for o in objects_raw]


        attr_map: dict[str, list[AttributeDef]] = {}
        if object_ids:
            attr_stmt = text(
                """
                SELECT id, template_object_id, attr_name, attr_type, ontology_code, is_required
                FROM business_domain.template_attributes
                WHERE template_object_id IN :oids AND tenant_id = :t AND is_deleted = 0
                """
            ).bindparams(bindparam("oids", expanding=True))
            attributes_raw = (await self.session.execute(
                attr_stmt, {"oids": object_ids, "t": tenant_id},
            )).mappings().all()
            for a in attributes_raw:
                attr_map.setdefault(a["template_object_id"], []).append(
                    AttributeDef(
                        ontology_code=a["ontology_code"],
                        attr_name=a["attr_name"],
                        attr_type=_normalize_attr_type(a["attr_type"] or "string"),
                        is_required=bool(a["is_required"]),
                        id=a["id"],
                    )
                )


        relations_raw = (await self.session.execute(
            text(
                """
                SELECT id, name, ontology_code, aliases, source_object_id, target_object_id, relation_type
                FROM business_domain.template_relations
                WHERE scenario_id = :sid AND tenant_id = :t AND is_deleted = 0
                """
            ),
            {"sid": template_scenario_id, "t": tenant_id},
        )).mappings().all()


        objects = [
            ObjectDef(
                id=o["id"],
                name=o["name"],
                ontology_code=o["ontology_code"],
                aliases=_as_list(o["aliases"]),
                attributes=attr_map.get(o["id"], []),
            )
            for o in objects_raw
        ]

        obj_ids_set = set(object_ids)
        relations = []
        for r in relations_raw:
            if r["source_object_id"] not in obj_ids_set:
                logger.warning("Relation %s source_object %s not in scenario", r["id"], r["source_object_id"])
                continue
            if r["target_object_id"] not in obj_ids_set:
                logger.warning("Relation %s target_object %s not in scenario", r["id"], r["target_object_id"])
                continue
            relations.append(
                RelationDef(
                    id=r["id"],
                    name=r["name"],
                    ontology_code=r["ontology_code"],
                    aliases=_as_list(r["aliases"]),
                    source_object_id=r["source_object_id"],
                    target_object_id=r["target_object_id"],
                    relation_type=r["relation_type"],
                )
            )

        scenario_def = ScenarioDef(
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            domain_id=scenario["domain_id"],
            domain_name=domain_name,
            objects=objects,
            relations=relations,
            version=scenario["version"] or 1,
            structure_hash=scenario["structure_hash"],
        )


        if not scenario_def.structure_hash:
            scenario_def.structure_hash = self._compute_hash(scenario_def)

        return scenario_def

    def _compute_hash(self, scenario: ScenarioDef) -> str:

        payload = {
            "domain_id": scenario.domain_id,
            "scenario_id": scenario.scenario_id,
            "objects": [
                {
                    "id": o.id,
                    "ontology_code": o.ontology_code,
                    "attributes": [{"id": a.id, "code": a.ontology_code, "type": a.attr_type} for a in o.attributes],
                }
                for o in scenario.objects
            ],
            "relations": [
                {
                    "id": r.id,
                    "code": r.ontology_code,
                    "source": r.source_object_id,
                    "target": r.target_object_id,
                }
                for r in scenario.relations
            ],
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()[:64]


__all__ = [
    "AttributeDef",
    "ObjectDef",
    "RelationDef",
    "ScenarioDef",
    "TemplateSchemaProvider",
]