

import asyncio
import atexit
import functools
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional, Set, TypeVar

import httpx

from jonex_core.common.logger import get_logger
from jonex_core.security.internal_auth import get_internal_auth

logger = get_logger(__name__)


AUDIT_INGEST_URL = os.getenv("AUDIT_INGEST_URL", "").rstrip("/")

F = TypeVar("F", bound=Callable[..., Any])


async def emit_audit(entry: Dict[str, Any], *, sync: bool = False):

    try:
        if AUDIT_INGEST_URL:
            await _emit_remote(entry)
        else:




            await _emit_local(entry, sync=sync)
    except Exception:
        logger.warning("emit_audit failed (suppressed): action=%s", entry.get("action"))


async def _emit_local(entry: Dict[str, Any], *, sync: bool = False):


    from capabilities.platform.services.audit_log_service import AuditLogService
    from jonex_core.common.database import get_db_session


    data = dict(entry)
    tenant_id = data.pop("tenant_id", None)

    if sync:
        async with get_db_session() as session:
            svc = AuditLogService(session)
            if tenant_id:
                await svc.record(tenant_id=tenant_id, **data, sync=True)
            else:
                await svc.record_system(**data, sync=True)
    else:
        svc = AuditLogService()
        if tenant_id:
            await svc.record(tenant_id=tenant_id, **data)
        else:
            await svc.record_system(**data)


async def _emit_remote(entry: Dict[str, Any]):

    internal_auth = get_internal_auth()
    token = internal_auth.generate_token("sidecar")
    url = f"{AUDIT_INGEST_URL}/api/v1/platform/audit-logs:ingest"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url,
            json={"entries": [entry]},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Request-ID": entry.get("trace_id", ""),
            },
        )
        if resp.status_code >= 400:
            logger.warning("emit_audit failed to forward ingest request: %s %s", resp.status_code, resp.text)





















_pending_tasks: Set["asyncio.Task[Any]"] = set()


_bg_loop: Optional[asyncio.AbstractEventLoop] = None
_bg_thread: Optional[threading.Thread] = None
_bg_lock = threading.Lock()


def _ensure_bg_loop() -> asyncio.AbstractEventLoop:

    global _bg_loop, _bg_thread
    if _bg_loop is not None and _bg_loop.is_running():
        return _bg_loop
    with _bg_lock:
        if _bg_loop is not None and _bg_loop.is_running():
            return _bg_loop
        loop = asyncio.new_event_loop()

        def _run() -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        thread = threading.Thread(target=_run, name="audit-emit-loop", daemon=True)
        thread.start()
        _bg_loop = loop
        _bg_thread = thread
        atexit.register(_shutdown_bg_loop)
        return loop


def _shutdown_bg_loop() -> None:

    loop = _bg_loop
    if loop is None:
        return
    try:
        loop.call_soon_threadsafe(loop.stop)
    except Exception:
        pass


def _on_task_done(task: "asyncio.Task[Any]") -> None:
    _pending_tasks.discard(task)
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.warning("emit_audit background task failed (suppressed): %s", exc)


def schedule_emit(entry: Dict[str, Any]) -> None:

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:

        task = loop.create_task(emit_audit(entry))
        _pending_tasks.add(task)
        task.add_done_callback(_on_task_done)
        return


    try:
        bg = _ensure_bg_loop()
        asyncio.run_coroutine_threadsafe(emit_audit(entry), bg)
    except Exception:
        logger.warning("emit_audit scheduling failed (suppressed): action=%s", entry.get("action"))


def audit_action(
    log_type: str,
    action: str,
    resource: Optional[str] = None,
    service_name: str = "platform",
):

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.monotonic()

            tenant_id = None
            if args and hasattr(args[0], "__dict__"):
                tenant_id = getattr(args[0], "tenant_id", None)
            if not tenant_id:
                tenant_id = kwargs.get("tenant_id")
            if not tenant_id:
                for arg in args:
                    if isinstance(arg, str) and len(arg) > 5:
                        continue
                    if hasattr(arg, "tenant_id"):
                        tenant_id = arg.tenant_id
                        break

            try:
                result = await func(*args, **kwargs)
                duration = int((time.monotonic() - start) * 1000)
                entry = {
                    "tenant_id": tenant_id,
                    "log_type": log_type,
                    "action": action,
                    "outcome": "SUCCESS",
                    "service_name": service_name,
                    "resource": resource,
                    "duration_ms": duration,
                }
                schedule_emit(entry)
                return result
            except Exception as e:
                duration = int((time.monotonic() - start) * 1000)
                entry = {
                    "tenant_id": tenant_id,
                    "log_type": log_type,
                    "action": action,
                    "outcome": "FAILED",
                    "service_name": service_name,
                    "resource": resource,
                    "duration_ms": duration,
                    "error_message": str(e),
                }
                schedule_emit(entry)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
                duration = int((time.monotonic() - start) * 1000)
                entry = {
                    "tenant_id": kwargs.get("tenant_id"),
                    "log_type": log_type,
                    "action": action,
                    "outcome": "SUCCESS",
                    "service_name": service_name,
                    "resource": resource,
                    "duration_ms": duration,
                }
                schedule_emit(entry)
                return result
            except Exception as e:
                duration = int((time.monotonic() - start) * 1000)
                entry = {
                    "tenant_id": kwargs.get("tenant_id"),
                    "log_type": log_type,
                    "action": action,
                    "outcome": "FAILED",
                    "service_name": service_name,
                    "resource": resource,
                    "duration_ms": duration,
                    "error_message": str(e),
                }
                schedule_emit(entry)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
