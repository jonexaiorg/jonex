

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.logger import get_logger
from jonex_core.common.tenant import require_tenant

from capabilities.platform.dtos.misc import (
    AuditLogDetailResponse,
    AuditLogListResponse,
    AuditLogResponse,
)
from capabilities.platform.models.audit_enums import LogLevel, LogType, Outcome
from capabilities.platform.repository.audit_log_repository import AuditLogRepository
from capabilities.platform.services.audit_log_sink import get_audit_log_sink

logger = get_logger(__name__)


SENSITIVE_KEYS = [
    "password", "passwd", "pwd", "token", "access_token", "refresh_token",
    "authorization", "authorization_code", "secret", "api_key", "apikey",
    "private_key", "ticket",
]

SENSITIVE_PATTERN = re.compile(
    "|".join(re.escape(k) for k in SENSITIVE_KEYS),
    re.IGNORECASE,
)

MAX_BODY_BYTES = 8 * 1024


def _sanitize_params(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:

    if not params:
        return params
    sanitized = {}
    for k, v in params.items():
        if SENSITIVE_PATTERN.search(k):
            sanitized[k] = "***"
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_params(v)
        elif isinstance(v, list):
            sanitized[k] = [_sanitize_params(i) if isinstance(i, dict) else i for i in v]
        else:
            sanitized[k] = v
    return sanitized


def _truncate_body(body: Optional[Any]) -> Optional[Any]:

    if body is None:
        return None
    import json
    dumped = json.dumps(body, ensure_ascii=False, default=str)
    if len(dumped) > MAX_BODY_BYTES:
        return {"_truncated": True, "size": len(dumped)}
    return body


def _derive_log_level(entry: dict) -> str:

    if entry.get("log_level"):
        lvl = entry["log_level"]
        return lvl.value if isinstance(lvl, Enum) else str(lvl)
    outcome = entry.get("outcome", Outcome.SUCCESS)
    if outcome == Outcome.FAILED or outcome == Outcome.FAILED.value:
        return LogLevel.ERROR.value
    return LogLevel.INFO.value


def _coerce(value):

    return value.value if isinstance(value, Enum) else value


def _build_audit_dict(
    tenant_id: Optional[str],
    log_type: str,
    action: str,
    outcome: str = Outcome.SUCCESS,
    service_name: str = "platform",
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    ip: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    request_params: Optional[Dict[str, Any]] = None,
    response_body: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    error_stack: Optional[str] = None,
    trace_id: Optional[str] = None,
    log_level: Optional[str] = None,
) -> dict:

    entry = {
        "tenant_id": tenant_id,
        "log_type": _coerce(log_type),
        "action": action,
        "outcome": _coerce(outcome),
        "service_name": _coerce(service_name),
        "user_id": user_id,
        "username": username,
        "ip": ip,
        "resource": resource,
        "resource_id": resource_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "request_params": _sanitize_params(request_params),
        "response_body": _truncate_body(response_body),
        "error_message": error_message,
        "error_stack": error_stack,
        "trace_id": trace_id,
        "log_level": log_level or _derive_log_level({"outcome": outcome}),
    }

    return {k: v for k, v in entry.items() if v is not None}


class AuditLogService:


    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.repo = AuditLogRepository(session) if session else None
        self.sink = get_audit_log_sink()



    async def record(
        self,
        tenant_id: str,
        log_type: str,
        action: str,
        outcome: str = Outcome.SUCCESS,
        *,
        service_name: str = "platform",
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
        request_params: Optional[Dict[str, Any]] = None,
        response_body: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_stack: Optional[str] = None,
        trace_id: Optional[str] = None,
        log_level: Optional[str] = None,
        sync: bool = False,
    ):

        require_tenant(tenant_id)
        entry = _build_audit_dict(
            tenant_id=tenant_id,
            log_type=log_type,
            action=action,
            outcome=outcome,
            service_name=service_name,
            user_id=user_id,
            username=username,
            ip=ip,
            resource=resource,
            resource_id=resource_id,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            request_params=request_params,
            response_body=response_body,
            error_message=error_message,
            error_stack=error_stack,
            trace_id=trace_id,
            log_level=log_level,
        )
        if sync:
            await self._write_sync(entry)
        else:
            self.sink.put(entry)

    async def record_system(
        self,
        log_type: str,
        action: str,
        outcome: str = Outcome.SUCCESS,
        *,
        service_name: str = "platform",
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
        request_params: Optional[Dict[str, Any]] = None,
        response_body: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_stack: Optional[str] = None,
        trace_id: Optional[str] = None,
        log_level: Optional[str] = None,
        sync: bool = False,
    ):

        if not service_name:
            raise ValueError("系统事件必须提供 service_name")
        entry = _build_audit_dict(
            tenant_id=None,
            log_type=log_type,
            action=action,
            outcome=outcome,
            service_name=service_name,
            user_id=user_id,
            username=username,
            ip=ip,
            resource=resource,
            resource_id=resource_id,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            request_params=request_params,
            response_body=response_body,
            error_message=error_message,
            error_stack=error_stack,
            trace_id=trace_id,
            log_level=log_level,
        )
        if sync:
            await self._write_sync(entry)
        else:
            self.sink.put(entry)

    async def ingest_batch(self, entries: List[Dict[str, Any]]):

        for entry in entries:
            entry = dict(entry)

            if entry.get("request_params") is not None:
                entry["request_params"] = _sanitize_params(entry["request_params"])
            if entry.get("response_body") is not None:
                entry["response_body"] = _truncate_body(entry["response_body"])

            tenant_id = entry.get("tenant_id")
            valid_tenant = False
            if tenant_id:
                try:
                    require_tenant(tenant_id)
                    valid_tenant = True
                except Exception:
                    valid_tenant = False
            if not valid_tenant:

                entry["tenant_id"] = None
                entry["log_type"] = LogType.SYSTEM.value


            if not entry.get("log_level"):
                entry["log_level"] = (
                    LogLevel.ERROR.value
                    if entry.get("outcome") == Outcome.FAILED.value
                    else LogLevel.INFO.value
                )
            self.sink.put(entry)

    async def _write_sync(self, entry: dict):

        if self.session is None:
            raise RuntimeError("同步直写需要 AsyncSession")
        try:
            obj = AuditLogRepository.model(**entry)
            self.session.add(obj)
            await self.session.flush()
        except Exception:
            logger.exception("Failed to write audit log synchronously")



    async def query(
        self,
        tenant_id: str,
        log_type: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        service_name: Optional[str] = None,
        user_id: Optional[int] = None,
        keyword: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogListResponse:

        require_tenant(tenant_id)
        offset = (page - 1) * page_size
        st = datetime.fromisoformat(start_time) if start_time else None
        et = datetime.fromisoformat(end_time) if end_time else None

        items = await self.repo.list_by_tenant(
            tenant_id=tenant_id,
            log_type=log_type,
            action=action,
            outcome=outcome,
            service_name=service_name,
            user_id=user_id,
            keyword=keyword,
            start_time=st,
            end_time=et,
            offset=offset,
            limit=page_size,
        )
        total = await self.repo.count_by_tenant(
            tenant_id=tenant_id,
            log_type=log_type,
            action=action,
            outcome=outcome,
            service_name=service_name,
            user_id=user_id,
            keyword=keyword,
            start_time=st,
            end_time=et,
        )
        return AuditLogListResponse(
            total=total,
            items=[AuditLogResponse.from_orm(item) for item in items],
        )

    async def get_log_detail(self, tenant_id: str, log_id: int) -> Optional[AuditLogDetailResponse]:

        require_tenant(tenant_id)
        log = await self.repo.get_by_id_with_detail(log_id)
        if not log or log.tenant_id != tenant_id:
            return None
        return AuditLogDetailResponse.from_orm(log)

    async def query_system_events(
        self,
        action: Optional[str] = None,
        service_name: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogListResponse:

        offset = (page - 1) * page_size
        st = datetime.fromisoformat(start_time) if start_time else None
        et = datetime.fromisoformat(end_time) if end_time else None

        items = await self.repo.list_system_events(
            action=action,
            service_name=service_name,
            start_time=st,
            end_time=et,
            offset=offset,
            limit=page_size,
        )
        total = await self.repo.count_system_events(
            action=action,
            service_name=service_name,
            start_time=st,
            end_time=et,
        )
        return AuditLogListResponse(
            total=total,
            items=[AuditLogResponse.from_orm(item) for item in items],
        )



    async def cleanup_expired(self, retention_days: int = 90) -> int:

        if self.repo is None:
            raise RuntimeError("cleanup_expired 需要 AsyncSession")
        return await self.repo.delete_expired(retention_days)
