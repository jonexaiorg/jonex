

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import EntityTypeDef, OntologySchema, RelationTypeDef


try:
    from yaml import SafeLoader
except ImportError:
    SafeLoader = None


class OntologyRegistry:


    def __init__(self):
        self._schemas: Dict[str, OntologySchema] = {}



    def load(self, path: str | Path) -> OntologySchema:

        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"本体 schema 文件不存在: {path}")

        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        schema = OntologySchema.from_dict(raw)
        self._schemas[schema.domain] = schema
        return schema

    def load_from_dict(self, data: dict, domain: str = "default") -> OntologySchema:

        schema = OntologySchema.from_dict(data)

        if schema.domain != domain:
            schema.domain = domain
        self._schemas[domain] = schema
        return schema



    def get(self, domain: str = "default") -> Optional[OntologySchema]:

        return self._schemas.get(domain)

    def get_or_default(self, domain: str = "default") -> OntologySchema:

        schema = self._schemas.get(domain)
        if schema is not None:
            return schema

        if domain != "default":
            return self._schemas.get("default", OntologySchema())
        return OntologySchema()

    def list_domains(self) -> List[str]:
        return list(self._schemas.keys())



    def validate_entity_type(self, type_name: str, domain: str = "default") -> bool:

        schema = self.get(domain)
        if schema is None:
            return True
        return schema.find_entity_type(type_name) is not None

    def validate_relation_type(self, type_name: str, domain: str = "default") -> bool:

        schema = self.get(domain)
        if schema is None:
            return True
        return schema.find_relation_type(type_name) is not None



    def to_prompt_json(self, domain: str = "default") -> str:

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
