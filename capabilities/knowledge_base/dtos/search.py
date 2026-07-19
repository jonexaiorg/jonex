

from typing import Any, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field(default="hybrid", min_length=1, max_length=32)
    top_k: int = Field(default=5, ge=1, le=50)
    knowledge_base_id: str = Field(default="", min_length=0, max_length=128)
    save_history: bool = True


class SearchResponse(BaseModel):
    query: str
    answer: str
    mode: str
    top_k: int
    references: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnhancedSearchResponse(SearchResponse):
    entities: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    graph: dict[str, Any] = Field(default_factory=dict)


class OntologySearchRequest(BaseModel):

    query: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field(default="hybrid", min_length=1, max_length=32)
    top_k: int = Field(default=5, ge=1, le=50)
    knowledge_base_ids: list[str] = Field(default_factory=list)
    save_history: bool = True
    with_reasoning: bool = False


class OntologySearchResponse(BaseModel):

    answer: str
    source: str
    references: list[dict[str, Any]] = Field(default_factory=list)
    ontology_instances: list[dict[str, Any]] = Field(default_factory=list)
    rag_used: bool
    knowledge_base_ids: list[str] = Field(default_factory=list)
    reasoning: Optional[dict[str, Any]] = None
