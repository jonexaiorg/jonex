"""emit_audit — 部署无关的审计日志产出抽象

提供：
- emit_audit(entry, *, sync=False)：根据运行环境选择直写或转发
- @audit_action(...)：方法级装饰器，自动记录成功/异常与耗时
"""

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
from jonex_core.common.audit_enums import ResourceType
from jonex_core.security.internal_auth import get_internal_auth

logger = get_logger(__name__)

# 环境变量：设置了就转发，未设置就本进程直写
AUDIT_INGEST_URL = os.getenv("AUDIT_INGEST_URL", "").rstrip("/")

F = TypeVar("F", bound=Callable[..., Any])


async def emit_audit(entry: Dict[str, Any], *, sync: bool = False):
    """发送审计条目

    根据 AUDIT_INGEST_URL 判定传输方式：
    - 设置了 URL → POST 转发 ingest（remote 模式）
    - 未设置 URL → 本进程直写（local 模式）

    Args:
        entry: 审计条目 dict
        sync: 是否同步发送（仅 local 模式有效，remote 始终异步）
    """
    try:
        if AUDIT_INGEST_URL:
            await _emit_remote(entry)
        else:
            # AUDIT_INGEST_URL 未设置 => 视为运行在 platform 进程内（本地直写）。
            # 注意：不能用 `import capabilities.platform` 判定进程归属，
            # monorepo 下任何容器都能 import 成功（误判）。部署约定：
            # 非 platform 容器必须设置 AUDIT_INGEST_URL 走转发。
            await _emit_local(entry, sync=sync)
    except Exception:
        logger.warning("emit_audit 异常（已被吞）: action=%s", entry.get("action"))


async def _emit_local(entry: Dict[str, Any], *, sync: bool = False):
    """本进程直写 — 调用 AuditLogService"""
    # 延迟导入，避免启动时循环依赖
    from capabilities.platform.services.audit_log_service import AuditLogService
    from jonex_core.common.database import get_db_session

    # 复制并取出 tenant_id，避免与 record(tenant_id=...) 形成重复关键字参数
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
    """转发 ingest — POST 到 AUDIT_INGEST_URL"""
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
            logger.warning("emit_audit 转发 ingest 失败: %s %s", resp.status_code, resp.text)


# ---------------------------------------------------------------------------
# 非阻塞调度：把审计协程安全地交给事件循环执行
#
# 背景（两个必须规避的坑）：
# 1) 高危：同步函数体内直接 asyncio.ensure_future(emit_audit(...))，在“没有运行中
#    事件循环”的纯同步调用场景会抛 RuntimeError: no running event loop，
#    审计装饰器反而把正常业务方法搞挂。
# 2) 中危：fire-and-forget 的 task 不保留引用时，可能在请求结束/GC 时被提前回收，
#    导致审计/计量这类合规数据静默丢失。
#
# 方案：
# - 当前线程已有运行中的 loop  → 在该 loop 上 create_task，并保留强引用（done
#   回调里再移除），异常在回调中记录而非完全静默吞掉。
# - 无运行中的 loop（纯同步上下文）→ 提交到一个后台守护事件循环线程，
#   用 run_coroutine_threadsafe 执行；该 future 由后台 loop 持有，不会被 GC。
# 任何分支都不向调用方抛异常，确保审计绝不影响业务主流程。
# ---------------------------------------------------------------------------

# 运行中 loop 上 task 的强引用，避免被 GC 提前回收
_pending_tasks: Set["asyncio.Task[Any]"] = set()

# 后台事件循环（懒启动），用于无运行 loop 的同步上下文
_bg_loop: Optional[asyncio.AbstractEventLoop] = None
_bg_thread: Optional[threading.Thread] = None
_bg_lock = threading.Lock()


def _ensure_bg_loop() -> asyncio.AbstractEventLoop:
    """获取（必要时启动）后台守护事件循环。"""
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
    """进程退出时停止后台 loop（best-effort）。"""
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
        logger.warning("emit_audit 后台任务异常（已吞）: %s", exc)


def schedule_emit(entry: Dict[str, Any]) -> None:
    """非阻塞调度一条审计条目的发送，对调用方零副作用。

    无论是否存在运行中的事件循环都不会抛异常，避免审计逻辑拖垮业务方法。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # 在当前运行 loop 上调度，并保留强引用避免被 GC
        task = loop.create_task(emit_audit(entry))
        _pending_tasks.add(task)
        task.add_done_callback(_on_task_done)
        return

    # 纯同步上下文：交给后台守护 loop 线程执行
    try:
        bg = _ensure_bg_loop()
        asyncio.run_coroutine_threadsafe(emit_audit(entry), bg)
    except Exception:
        logger.warning("emit_audit 调度失败（已吞）: action=%s", entry.get("action"))


def audit_action(
    log_type: str,
    action: str,
    resource: Optional[str] = None,
    service_name: str = "platform",
):
    """审计日志装饰器

    自动记录被装饰方法的执行结果（成功/异常 + 耗时）。

    用法：
        @audit_action(log_type="OPERATION", action="document.upload")
        async def upload_document(self, ...):
            ...

    装饰器自动从第一个参数（self 之后的参数）尝试提取 tenant_id，
    同时捕获异常转为 FAILED + error_message。
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.monotonic()
            # 尝试从参数中提取 tenant_id
            tenant_id = None
            if args and hasattr(args[0], "__dict__"):
                tenant_id = getattr(args[0], "tenant_id", None)
            if not tenant_id:
                tenant_id = kwargs.get("tenant_id")
            if not tenant_id:
                for arg in args:
                    if isinstance(arg, str) and len(arg) > 5:
                        continue  # 跳过简单字符串
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
                    "resource": resource if resource is not None else (ResourceType.resolve(action) if ResourceType else None),
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
                    "resource": resource if resource is not None else (ResourceType.resolve(action) if ResourceType else None),
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
                    "resource": resource if resource is not None else (ResourceType.resolve(action) if ResourceType else None),
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
                    "resource": resource if resource is not None else (ResourceType.resolve(action) if ResourceType else None),
                    "duration_ms": duration,
                    "error_message": str(e),
                }
                schedule_emit(entry)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
