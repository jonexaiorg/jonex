

from datetime import datetime
from typing import Any, Optional, Dict, List

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class AuditEntry(BaseModel):


    tenant_id: Optional[str] = None
    log_type: str = Field(..., description="日志大类：LOGIN / OPERATION / SYSTEM / TASK")
    action: str = Field(..., description="细粒度动作码")
    outcome: str = Field(default="SUCCESS", description="SUCCESS / FAILED")
    service_name: str = Field(default="platform", description="来源服务名")


    user_id: Optional[int] = None
    username: Optional[str] = None
    ip: Optional[str] = None


    resource: Optional[str] = None
    resource_id: Optional[str] = None


    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[int] = None


    request_params: Optional[Dict[str, Any]] = None
    response_body: Optional[Dict[str, Any]] = None


    error_message: Optional[str] = None
    error_stack: Optional[str] = None


    trace_id: Optional[str] = None


    log_level: Optional[str] = None

    class Config:
        extra = "forbid"


class AuditEntryBatch(BaseModel):

    entries: List[AuditEntry]
