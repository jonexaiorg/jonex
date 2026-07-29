"""Knowledge Base search DTOs."""

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
    domain_space_id: Optional[str] = Field(default=None, max_length=64)


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
    """本体优先检索请求（多 KB）"""
    query: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field(default="hybrid", min_length=1, max_length=32)
    top_k: int = Field(default=5, ge=1, le=50)
    knowledge_base_ids: list[str] = Field(default_factory=list)
    save_history: bool = True
    with_reasoning: bool = False          # 是否返回编排推理链（P0 非流式）
    domain_space_id: Optional[str] = Field(default=None, max_length=64)


class OntologySearchResponse(BaseModel):
    """本体优先检索响应（多 KB）"""
    answer: str
    source: str
    references: list[dict[str, Any]] = Field(default_factory=list)
    ontology_instances: list[dict[str, Any]] = Field(default_factory=list)
    rag_used: bool
    knowledge_base_ids: list[str] = Field(default_factory=list)
    reasoning: Optional[dict[str, Any]] = None    # 编排推理链（默认 None，仅契约对齐）
