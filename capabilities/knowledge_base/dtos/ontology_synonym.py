
from typing import Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


MAX_TERMS_PER_GROUP = 50
MAX_TERM_LENGTH = 128
MAX_IMPORT_GROUPS = 500


class SynonymCreate(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    terms: list[str] = Field(..., min_items=2)
    canonical: Optional[str] = Field(default=None, max_length=255)


class SynonymUpdate(BaseModel):
    terms: Optional[list[str]] = None
    canonical: Optional[str] = Field(default=None, max_length=255)


class SynonymResponse(BaseModel):
    id: str
    knowledge_base_id: str
    terms: list[str] = Field(default_factory=list)
    canonical: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SynonymListQuery(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class SynonymListResponse(BaseModel):
    items: list[SynonymResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class SynonymBatchImport(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    groups: list[list[str]] = Field(default_factory=list)


__all__ = [
    "MAX_IMPORT_GROUPS",
    "MAX_TERMS_PER_GROUP",
    "MAX_TERM_LENGTH",
    "SynonymBatchImport",
    "SynonymCreate",
    "SynonymListQuery",
    "SynonymListResponse",
    "SynonymResponse",
    "SynonymUpdate",
]
