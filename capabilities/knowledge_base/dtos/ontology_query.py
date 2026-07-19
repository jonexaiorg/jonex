

from typing import Optional

from pydantic import BaseModel


class OntologyStatsRequest(BaseModel):


    knowledge_base_id: str
    include_unknown: bool = True


class OntologyGraphRequest(BaseModel):


    knowledge_base_id: str
    limit: int = 500
    entity_types: Optional[list[str]] = None


class OntologyNeighborRequest(BaseModel):


    knowledge_base_id: str
    entity_type: str
    canonical_name: str
    limit: int = 50


class OntologyInstanceListRequest(BaseModel):


    knowledge_base_id: str
    page: int = 1
    page_size: int = 20
    entity_type: Optional[str] = None
    keyword: Optional[str] = None
    include_unknown: bool = True


class OntologyRelationListRequest(BaseModel):


    knowledge_base_id: str
    page: int = 1
    page_size: int = 20
    relation_type: Optional[str] = None
    source_name: Optional[str] = None
    target_name: Optional[str] = None
    source_type: Optional[str] = None
    target_type: Optional[str] = None