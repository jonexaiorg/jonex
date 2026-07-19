
from typing import Any, Literal

from pydantic import BaseModel, Field


SkillCatalogStatus = Literal["published", "disabled"]
TenantSkillStatus = Literal["enabled", "disabled"]


class SkillListQuery(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    category: str | None = None
    keyword: str | None = None


class SkillItemResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    category: str
    icon: str | None = None
    status: SkillCatalogStatus
    enabled: bool
    tenant_status: TenantSkillStatus
    tool_name: str
    instruction: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    tags: list[str] = []
    capability: dict[str, Any] = {}


class SkillListResponse(BaseModel):
    items: list[SkillItemResponse]
    total: int
    offset: int
    limit: int


class SkillToggleResponse(BaseModel):
    id: str
    skill_id: str
    tenant_status: TenantSkillStatus
    enabled: bool


class McpToolArtifact(BaseModel):
    bucket: str
    object_key: str
    checksum: str | None = None
    content_type: str | None = None


class McpToolDefinition(BaseModel):
    id: str
    name: str
    description: str | None = None
    tool_name: str
    instruction: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    artifact: McpToolArtifact


class McpToolListResponse(BaseModel):
    items: list[McpToolDefinition]