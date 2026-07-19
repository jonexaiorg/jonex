

from typing import Any, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class ParseResultScopeRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)


class ParseResultPageRequest(ParseResultScopeRequest):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    keyword: Optional[str] = Field(default=None, max_length=255)


class ParseResultDocumentListRequest(ParseResultPageRequest):
    status: Optional[str] = Field(default=None, max_length=32)


class ParseResultEntityListRequest(ParseResultPageRequest):
    entity_type: Optional[str] = Field(default=None, max_length=64)
    file_path: Optional[str] = Field(default=None, max_length=1024)
    document_id: Optional[str] = Field(default=None, max_length=64)


class ParseResultRelationshipListRequest(ParseResultPageRequest):
    file_path: Optional[str] = Field(default=None, max_length=1024)
    document_id: Optional[str] = Field(default=None, max_length=64)
    source_entity: Optional[str] = Field(default=None, max_length=255)
    target_entity: Optional[str] = Field(default=None, max_length=255)


class ParseResultGraphRequest(ParseResultScopeRequest):
    keyword: Optional[str] = Field(default=None, max_length=255)
    file_path: Optional[str] = Field(default=None, max_length=1024)
    document_id: Optional[str] = Field(default=None, max_length=64)
    limit: int = Field(default=200, ge=1, le=1000)


class DocumentParseResultRequest(ParseResultScopeRequest):
    document_id: str = Field(..., min_length=1, max_length=64)


class ParseResultResponse(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class OntologyRetryRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
