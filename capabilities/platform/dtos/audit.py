"""审计日志 DTO：写入数据载体"""

from datetime import datetime
from typing import Any, Optional, Dict, List

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class AuditEntry(BaseModel):
    """审计日志条目（写入数据载体）

    采集点到落库之间的通用数据载体，脱敏在 service 层完成。
    """

    tenant_id: Optional[str] = None  # None 表示系统事件
    log_type: str = Field(..., description="日志大类：LOGIN / OPERATION / SYSTEM / TASK")
    action: str = Field(..., description="细粒度动作码")
    outcome: str = Field(default="SUCCESS", description="SUCCESS / FAILED")
    service_name: str = Field(default="platform", description="来源服务名")

    # 用户与网络
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip: Optional[str] = None

    # 资源
    resource: Optional[str] = None
    resource_id: Optional[str] = None

    # HTTP 上下文
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[int] = None

    # 请求/响应数据（入参已脱敏，response_body 已截断）
    request_params: Optional[Dict[str, Any]] = None
    response_body: Optional[Dict[str, Any]] = None

    # 错误信息
    error_message: Optional[str] = None
    error_stack: Optional[str] = None

    # 追踪
    trace_id: Optional[str] = None

    # 日志级别（不填则由 outcome 推导）
    log_level: Optional[str] = None

    class Config:
        extra = "forbid"


class AuditEntryBatch(BaseModel):
    """批量入库载体"""
    entries: List[AuditEntry]
