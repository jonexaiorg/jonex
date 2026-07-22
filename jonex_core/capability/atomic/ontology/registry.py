"""
Ontology registry — Load, cache, query TBox schema.

OntologyRegistry Is a lightweight registry, responsible for:
1. Load ontology definitions from YAML files
2. Cache multiple schemas by domain
3. Provide search and validation methods for entity type / relation type

Usage example::

    registry = OntologyRegistry()
    registry.load("deploy/config/ontology/default.yaml")
    schema = registry.get("default")
    et = schema.find_entity_type("Organization")  # -> EntityTypeDef
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import EntityTypeDef, OntologySchema, RelationTypeDef

# Try to import yaml, give a friendly hint if not present
try:
    from yaml import SafeLoader
except ImportError:
    SafeLoader = None  # type: ignore[assignment]


class OntologyRegistry:
    """Ontology registry - read-only TBox cache managed by domain."""

    def __init__(self):
        self._schemas: Dict[str, OntologySchema] = {}

    # ── Load ────────────────────────────────────

    def load(self, path: str | Path) -> OntologySchema:
        """Load ontology schema from YAML file."""
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Ontology schema file does not exist: {path}")

        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        schema = OntologySchema.from_dict(raw)
        self._schemas[schema.domain] = schema
        return schema

    def load_from_dict(self, data: dict, domain: str = "default") -> OntologySchema:
        """Load ontology schema from dict (for testing or dynamic definition)."""
        schema = OntologySchema.from_dict(data)
        # If domain is specified in data, override it
        if schema.domain != domain:
            schema.domain = domain
        self._schemas[domain] = schema
        return schema

    # ── Query ────────────────────────────────────

    def get(self, domain: str = "default") -> Optional[OntologySchema]:
        """Get the schema of the specified domain."""
        return self._schemas.get(domain)

    def get_or_default(self, domain: str = "default") -> OntologySchema:
        """Get the schema of the specified domain, return default schema (empty definition) if not exists."""
        schema = self._schemas.get(domain)
        if schema is not None:
            return schema
        # If default has been loaded, use it as fallback
        if domain != "default":
            return self._schemas.get("default", OntologySchema())
        return OntologySchema()

    def list_domains(self) -> List[str]:
        return list(self._schemas.keys())

    # ── Validation ────────────────────────────────────

    def validate_entity_type(self, type_name: str, domain: str = "default") -> bool:
        """Check whether the entity type is defined in the schema."""
        schema = self.get(domain)
        if schema is None:
            return True  # Do not block when schema is missing
        return schema.find_entity_type(type_name) is not None

    def validate_relation_type(self, type_name: str, domain: str = "default") -> bool:
        """Check whether the relation type is defined in the schema."""
        schema = self.get(domain)
        if schema is None:
            return True
        return schema.find_relation_type(type_name) is not None

    # ── Serialization ──────────────────────────────────

    def to_prompt_json(self, domain: str = "default") -> str:
        """Convert schema to JSON, for LLM prompt concatenation."""
        import json

        schema = self.get_or_default(domain)
        payload = {
            "entity_types": [
                {
                    "name": et.name,
                    "aliases": et.aliases,
                    "attributes": [
                        {"name": a.name, "type": a.type, "required": a.required}
                        for a in et.attributes
                    ],
                }
                for et in schema.entity_types
            ],
            "relation_types": [
                {
                    "name": rt.name,
                    "source": rt.source,
                    "target": rt.target,
                }
                for rt in schema.relation_types
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
