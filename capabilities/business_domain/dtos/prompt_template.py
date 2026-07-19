
from datetime import datetime
from typing import Any, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field





class CreatePromptTemplateRequest(BaseModel):

    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    status: str = Field(default="启用", max_length=16)


class UpdatePromptTemplateRequest(BaseModel):

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = Field(None, max_length=16)
    version_remark: Optional[str] = Field(None, max_length=512)
    target_version: Optional[str] = Field(None, max_length=32)


class RollbackVersionRequest(BaseModel):

    target_version: str = Field(..., min_length=1, max_length=32)


class ListPromptTemplatesQuery(BaseModel):

    scope: Optional[str] = Field(None, max_length=16)
    category: Optional[str] = Field(None, max_length=64)
    keyword: Optional[str] = Field(None, max_length=255)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)





class VersionItem(BaseModel):

    version: str
    content: str
    updated_by: Optional[str] = None
    updated_at: Optional[str] = None
    remark: Optional[str] = None


class PromptTemplateResponse(BaseModel):

    id: str
    tenant_id: Optional[str] = None
    name: str
    category: str
    scope: str
    description: Optional[str] = None
    status: str
    current_version: str
    versions_json: list[dict] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PromptTemplateDetailResponse(PromptTemplateResponse):

    versions: list[VersionItem] = Field(default_factory=list)
    current_content: Optional[str] = None


class PromptTemplateListResponse(BaseModel):

    items: list[PromptTemplateResponse]
    total: int
    offset: int
    limit: int


class VersionListResponse(BaseModel):

    items: list[VersionItem]
    current_version: str
