"""DTOs for KB-level tags."""
from typing import Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:  # pragma: no cover
    from pydantic import BaseModel, Field


class TagCreateRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=32)


class TagUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=32)


class TagListQuery(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)


class TagResponse(BaseModel):
    id: str
    name: str
    knowledge_base_id: str
    color: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TagListResponse(BaseModel):
    items: list[TagResponse] = Field(default_factory=list)
    total: int = 0


__all__ = [
    "TagCreateRequest",
    "TagUpdateRequest",
    "TagListQuery",
    "TagListResponse",
    "TagResponse",
]
