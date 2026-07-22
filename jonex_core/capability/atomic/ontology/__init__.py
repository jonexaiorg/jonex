"""
Ontology engine - TBox Definition and registration.

Provides OntologyRegistry and related data models (EntityTypeDef, RelationTypeDef).
Used by atomic-rag's Stage4 OntologyExtractor during document extraction, also available for knowledge-base
service to search type definitions during query.
"""

from .models import EntityTypeDef, AttributeDef, RelationTypeDef, OntologySchema
from .registry import OntologyRegistry

__all__ = [
    "EntityTypeDef",
    "AttributeDef",
    "RelationTypeDef",
    "OntologySchema",
    "OntologyRegistry",
]
