

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AttributeDef:


    name: str
    type: str = "string"
    required: bool = False
    description: Optional[str] = None


@dataclass
class EntityTypeDef:


    name: str
    aliases: List[str] = field(default_factory=list)
    attributes: List[AttributeDef] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "EntityTypeDef":
        return cls(
            name=data["name"],
            aliases=data.get("aliases", []),
            attributes=[AttributeDef(**a) for a in data.get("attributes", [])],
        )


@dataclass
class RelationTypeDef:


    name: str
    source: Optional[str] = None
    target: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "RelationTypeDef":
        return cls(
            name=data["name"],
            source=data.get("source"),
            target=data.get("target"),
            description=data.get("description"),
        )


@dataclass
class ConstraintDef:


    type: str
    entity: Optional[str] = None
    attribute: Optional[str] = None
    severity: str = "warning"

    @classmethod
    def from_dict(cls, data: dict) -> "ConstraintDef":
        return cls(
            type=data["type"],
            entity=data.get("entity"),
            attribute=data.get("attribute"),
            severity=data.get("severity", "warning"),
        )


@dataclass
class DisambiguationConfig:


    case_insensitive: bool = True
    alias_merge: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "DisambiguationConfig":
        return cls(
            case_insensitive=data.get("case_insensitive", True),
            alias_merge=data.get("alias_merge", True),
        )


@dataclass
class OntologySchema:


    version: int = 1
    domain: str = "default"
    entity_types: List[EntityTypeDef] = field(default_factory=list)
    relation_types: List[RelationTypeDef] = field(default_factory=list)
    constraints: List[ConstraintDef] = field(default_factory=list)
    disambiguation: DisambiguationConfig = field(default_factory=DisambiguationConfig)
    raw: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "OntologySchema":
        return cls(
            version=data.get("version", 1),
            domain=data.get("domain", "default"),
            entity_types=[EntityTypeDef.from_dict(e) for e in data.get("entity_types", [])],
            relation_types=[RelationTypeDef.from_dict(r) for r in data.get("relation_types", [])],
            constraints=[ConstraintDef.from_dict(c) for c in data.get("constraints", [])],
            disambiguation=DisambiguationConfig.from_dict(data.get("disambiguation", {})),
            raw=data,
        )

    def get_entity_type_names(self) -> List[str]:
        return [et.name for et in self.entity_types]

    def get_relation_type_names(self) -> List[str]:
        return [rt.name for rt in self.relation_types]

    def find_entity_type(self, name: str) -> Optional[EntityTypeDef]:

        for et in self.entity_types:
            if et.name.lower() == name.lower():
                return et
            if name.lower() in [a.lower() for a in et.aliases]:
                return et
        return None

    def find_relation_type(self, name: str) -> Optional[RelationTypeDef]:
        for rt in self.relation_types:
            if rt.name == name:
                return rt
        return None

    @classmethod
    def from_compiled_dict(cls, data: dict) -> "OntologySchema":

        entity_types = []
        for et in data.get("entity_types", []):
            attrs = []
            for a in et.get("attributes", []):
                attrs.append(AttributeDef(
                    name=a.get("name") or a.get("ontology_code", ""),
                    type=a.get("type", "string"),
                    required=a.get("required", False),
                    description=a.get("display_name") or a.get("description"),
                ))
            entity_types.append(EntityTypeDef(
                name=et.get("name", ""),
                aliases=et.get("aliases", []),
                attributes=attrs,
            ))

        relation_types = []
        for rt in data.get("relation_types", []):
            relation_types.append(RelationTypeDef(
                name=rt.get("name", ""),
                source=rt.get("source"),
                target=rt.get("target"),
                description=rt.get("display_name") or rt.get("description"),
            ))

        disamb = data.get("disambiguation", {})
        return cls(
            version=data.get("schema_version", 1),
            domain=data.get("template_scenario_id") or data.get("domain", "compiled"),
            entity_types=entity_types,
            relation_types=relation_types,
            constraints=[ConstraintDef.from_dict(c) for c in data.get("constraints", [])],
            disambiguation=DisambiguationConfig.from_dict(disamb),
            raw=data,
        )
