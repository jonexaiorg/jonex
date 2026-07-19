#!/usr/bin/python3


from datetime import datetime
from typing import Any, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field

ACCESS_TYPES = {"api", "api_push", "storage", "file"}


class DataSourceCreateRequest(BaseModel):
    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    access_method_id: Optional[str] = Field(default=None, max_length=64)
    access_type: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=255)
    config_json: dict[str, Any] = Field(default_factory=dict)
    sync_mode: str = Field(default="manual", max_length=16)
    cron_expr: Optional[str] = Field(default=None, max_length=128)


class DataSourceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    config_json: Optional[dict[str, Any]] = None
    sync_mode: Optional[str] = Field(default=None, max_length=16)
    cron_expr: Optional[str] = Field(default=None, max_length=128)
    status: Optional[str] = Field(default=None, max_length=32)


class DataSourceResponse(BaseModel):
    id: str
    tenant_id: str
    knowledge_base_id: str
    access_method_id: Optional[str] = None
    access_type: str
    name: str
    config_json: dict[str, Any] = Field(default_factory=dict)
    sync_mode: str = "manual"
    cron_expr: Optional[str] = None
    status: str = "active"
    last_sync_at: Optional[datetime | str] = None
    last_sync_status: Optional[str] = None
    last_sync_message: Optional[str] = None
    document_count: int = 0
    created_at: Optional[datetime | str] = None
    updated_at: Optional[datetime | str] = None

    class Config:
        extra = "allow"


class DataSourceListResponse(BaseModel):
    items: list[DataSourceResponse] = Field(default_factory=list)
    total: int = 0


__all__ = [
    "DataSourceCreateRequest",
    "DataSourceUpdateRequest",
    "DataSourceResponse",
    "DataSourceListResponse",
]
