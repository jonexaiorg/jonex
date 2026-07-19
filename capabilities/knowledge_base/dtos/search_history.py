

from datetime import datetime
from typing import Any, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class SearchHistoryCreateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    knowledge_base_id: str = Field(default="", min_length=0, max_length=128)
    mode: str = Field(default="hybrid", min_length=1, max_length=32)
    top_k: int = Field(default=5, ge=1, le=50, alias="topK")
    status: str = Field(default="done", max_length=32)
    domain: Optional[str] = Field(default=None, max_length=128)
    domain_id: Optional[str] = Field(default=None, max_length=128, alias="domainId")
    answer_preview: Optional[str] = Field(default=None, alias="answerPreview")
    reference_count: int = Field(default=0, ge=0, alias="referenceCount")
    result_count: int = Field(default=0, ge=0, alias="resultCount")
    duration_ms: Optional[int] = Field(default=None, ge=0, alias="durationMs")
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        allow_population_by_field_name = True


class SearchHistoryListRequest(BaseModel):
    knowledge_base_id: str = Field(default="", min_length=0, max_length=128)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchHistoryDeleteRequest(BaseModel):
    knowledge_base_id: str = Field(default="", min_length=0, max_length=128)


class SearchOverviewRequest(BaseModel):
    knowledge_base_id: str = Field(default="", min_length=0, max_length=128)


class SearchHistoryResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    query: str
    query_hash: str
    knowledge_base_id: str
    mode: str
    top_k: int
    status: str
    answer_preview: Optional[str] = None
    reference_count: int = 0
    result_count: int = 0
    duration_ms: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    searched_at: Optional[datetime | str] = None
    created_at: Optional[datetime | str] = None
    updated_at: Optional[datetime | str] = None


class SearchHistoryListResponse(BaseModel):
    items: list[SearchHistoryResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class SearchOverviewResponse(BaseModel):
    total_history: int = 0
    recent_items: list[SearchHistoryResponse] = Field(default_factory=list)
