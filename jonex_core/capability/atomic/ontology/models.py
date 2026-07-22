"""
Ontology data model - TBox layer.

Defines the structured types of ontology schema (entity type definition, attribute definition, relation type definition),
and the top-level OntologySchema container, corresponding to the format of the ontology YAML file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AttributeDef:
    """Attribute definition of entity type."""

    name: str
    type: str = "string"
    required: bool = False
    description: Optional[str] = None


@dataclass
class EntityTypeDef:
    """Entity type definition (concept class in TBox)."""

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
    """Relation type definition (role/attribute in TBox)."""

    name: str
    source: Optional[str] = None  # Source entity type constraint
    target: Optional[str] = None  # Target entity type constraint
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
    """Ontology constraint definition."""

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
    """Disambiguation configuration."""

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
    """Top-level ontology schema definition, corresponding to one ontology YAML file."""

    version: int = 1
    domain: str = "default"
    entity_types: List[EntityTypeDef] = field(default_factory=list)
    relation_types: List[RelationTypeDef] = field(default_factory=list)
    constraints: List[ConstraintDef] = field(default_factory=list)
    disambiguation: DisambiguationConfig = field(default_factory=DisambiguationConfig)
    raw: Optional[Dict[str, Any]] = None  # Original dict, for code that needs direct access to YAML fields

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
        """Find entity type definition by name (including alias matching)."""
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
