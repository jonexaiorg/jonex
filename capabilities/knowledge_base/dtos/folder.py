
from typing import Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class FolderCreateRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)


class FolderUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class FolderListQuery(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)


class FolderResponse(BaseModel):
    id: str
    name: str
    knowledge_base_id: str
    is_preset: bool = False
    sort_order: int = 0
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FolderListResponse(BaseModel):
    items: list[FolderResponse] = Field(default_factory=list)
    total: int = 0


__all__ = [
    "FolderCreateRequest",
    "FolderListQuery",
    "FolderListResponse",
    "FolderResponse",
    "FolderUpdateRequest",
]
