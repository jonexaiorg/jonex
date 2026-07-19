
from datetime import datetime
from typing import Any, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class BindTemplateRequest(BaseModel):
    template_domain_id: Optional[str] = Field(default=None, max_length=64)
    template_scenario_id: Optional[str] = Field(default=None, max_length=64)
    source_type: str = Field(default="business_template", max_length=32)


class BindingResponse(BaseModel):
    id: int
    tenant_id: str
    knowledge_base_id: str
    template_domain_id: Optional[str] = None
    template_scenario_id: Optional[str] = None
    source_type: str = "business_template"
    status: str = "active"
    created_at: Optional[datetime | str] = None
    updated_at: Optional[datetime | str] = None


class CompileRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    force: bool = Field(default=False)


class RecompileRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)


class CompiledSchemaResponse(BaseModel):
    id: Optional[int] = None
    tenant_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    template_domain_id: Optional[str] = None
    template_scenario_id: Optional[str] = None
    source_type: Optional[str] = "business_template"
    source_version: int = 1
    source_hash: Optional[str] = None
    schema_version: int = 1
    entity_types: list[dict] = Field(default_factory=list)
    relation_types: list[dict] = Field(default_factory=list)
    constraints: list[dict] = Field(default_factory=list)
    disambiguation: dict = Field(default_factory=lambda: {"case_insensitive": True, "alias_merge": True})
    prompt_schema: dict = Field(default_factory=dict)
    status: str = "active"
    schema_mode: str = "template_seeded"
    sync_status: str = "synced"
    edited_at: Optional[datetime | str] = None
    edited_by: Optional[str] = None
    compiled_at: Optional[datetime | str] = None

    class Config:
        extra = "allow"


class CompiledAttributeInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    type: str = Field(default="string", min_length=1, max_length=32)
    required: bool = False
    is_primary_key: bool = False
    source_attribute_id: Optional[str] = Field(default=None, max_length=64)


class CompiledEntityTypeInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    requirement: Optional[str] = None
    status: Optional[str] = Field(default="active", max_length=32)
    aliases: list[str] = Field(default_factory=list)
    source_object_id: Optional[str] = Field(default=None, max_length=64)
    attributes: list[CompiledAttributeInput] = Field(default_factory=list)


class CompiledRelationTypeInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(default="active", max_length=32)
    aliases: list[str] = Field(default_factory=list)
    source: str = Field(..., min_length=1, max_length=128)
    target: str = Field(..., min_length=1, max_length=128)
    source_relation_id: Optional[str] = Field(default=None, max_length=64)
    cardinality: str = Field(default="custom", min_length=1, max_length=32)


class CompiledConstraintInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    target_type: str = Field(..., min_length=1, max_length=16)
    target_code: str = Field(..., min_length=1, max_length=257)
    target_label: Optional[str] = Field(default=None, max_length=255)
    constraint_type: str = Field(default="custom", min_length=1, max_length=32)
    expression: Optional[str] = None
    suggestion: Optional[str] = None


class SaveCompiledSchemaRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    entity_types: list[CompiledEntityTypeInput] = Field(default_factory=list)
    relation_types: list[CompiledRelationTypeInput] = Field(default_factory=list)

    constraints: Optional[list[CompiledConstraintInput]] = None

    expected_schema_version: Optional[int] = None


class ReseedCompiledSchemaRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    template_domain_id: Optional[str] = Field(default=None, max_length=64)
    template_scenario_id: str = Field(..., min_length=1, max_length=64)
    source_type: str = Field(default="business_template", max_length=32)


class TemplateSummaryResponse(BaseModel):
    domain_id: Optional[str] = None
    domain_name: Optional[str] = None
    scenario_id: Optional[str] = None
    scenario_name: Optional[str] = None
    source_version: Optional[int] = None
    source_hash: Optional[str] = None


class EditorStateResponse(BaseModel):
    knowledge_base_id: str
    binding: Optional[BindingResponse | dict[str, Any]] = None
    compiled_schema: Optional[CompiledSchemaResponse | dict[str, Any]] = None
    current_template: Optional[TemplateSummaryResponse | dict[str, Any]] = None


class EntityTypeItem(BaseModel):
    name: str
    display_name: Optional[str] = None
    aliases: list[str] = Field(default_factory=list)
    attributes: list[dict] = Field(default_factory=list)


class RelationTypeItem(BaseModel):
    name: str
    display_name: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None
    cardinality: Optional[str] = None


class ImpactedKBItem(BaseModel):
    tenant_id: str
    knowledge_base_id: str
    schema_outdated: bool = False


class ImpactedKBResponse(BaseModel):
    items: list[ImpactedKBItem] = Field(default_factory=list)
    total: int = 0


__all__ = [
    "BindTemplateRequest",
    "BindingResponse",
    "CompileRequest",
    "CompiledAttributeInput",
    "CompiledConstraintInput",
    "CompiledEntityTypeInput",
    "CompiledRelationTypeInput",
    "CompiledSchemaResponse",
    "EditorStateResponse",
    "EntityTypeItem",
    "ImpactedKBItem",
    "ImpactedKBResponse",
    "RecompileRequest",
    "RelationTypeItem",
    "ReseedCompiledSchemaRequest",
    "SaveCompiledSchemaRequest",
    "TemplateSummaryResponse",
]
