"""
POST   /api/v1/tasks          — Create task (inline/yaml/preset)
GET    /api/v1/tasks          — List tasks (paginated, filtered)
GET    /api/v1/tasks/{id}     — Get task detail
DELETE /api/v1/tasks/{id}     — Cancel task
"""

from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from raganything.service.context import get_request_id, get_tenant_id
from raganything.service.models import (
    CancelTaskResponse,
    CreateTaskRequest,
    CreateTaskResponse,
    ErrorResponse,
    TaskInfo,
)
from raganything.service.task_manager import SlotFullError

router = APIRouter(tags=["tasks"])


def _get_tm(request: Request):
    return request.app.state.task_manager


def _get_cr(request: Request):
    return request.app.state.config_resolver


def _tenant(request: Request) -> str:
    tid = get_tenant_id()
    if not tid:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code=40001, request_id=get_request_id(),
                message="X-Tenant-ID header is required",
            ).model_dump(mode="json"),
        )
    return tid


def _err(code: int, message: str) -> HTTPException:
    return HTTPException(
        status_code=code // 100,
        detail=ErrorResponse(code=code, request_id=get_request_id(), message=message).model_dump(mode="json"),
    )


# ── POST /api/v1/tasks ─────────────────────────────────────────────


@router.post("/tasks", status_code=201)
async def create_task(req: CreateTaskRequest, request: Request):
    """Create a new parsing task.

    Three modes (Spec §4.2):
      - inline: all params in request body
      - yaml:    file_path + yaml_path, params from YAML
      - preset:  file_path + preset name, params from config/presets/
    """
    tenant_id = _tenant(request)
    idempotency_key = request.headers.get("Idempotency-Key")

    tm = _get_tm(request)

    try:
        result = await tm.create(req, tenant_id, idempotency_key)
    except SlotFullError:
        raise _err(42901, "Task queue is full. Retry later.")

    # If idempotent hit, return 200 instead of 201
    if isinstance(result, TaskInfo):
        return JSONResponse(
            status_code=200,
            content={"code": 0, "request_id": get_request_id(), "data": result.model_dump(mode="json")},
        )

    return JSONResponse(
        status_code=201,
        content={"code": 0, "request_id": get_request_id(), "data": result.model_dump(mode="json")},
    )


# ── GET /api/v1/tasks ──────────────────────────────────────────────


@router.get("/tasks")
async def list_tasks(
    request: Request,
    status: str = "all",
    file_type: str = "all",
    page: int = 1,
    page_size: int = 20,
    sort: str = "-created_at",
):
    """List tasks with pagination and filtering (Spec §4.3)."""
    tenant_id = _tenant(request)
    tm = _get_tm(request)

    result = await tm.list(tenant_id, status, file_type, page, page_size, sort)
    return {"code": 0, "request_id": get_request_id(), "data": result.model_dump(mode="json")}


# ── GET /api/v1/tasks/{task_id} ────────────────────────────────────


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, request: Request):
    """Get task detail (Spec §4.4)."""
    tenant_id = _tenant(request)
    tm = _get_tm(request)

    task = await tm.get(task_id, tenant_id)
    if task is None:
        raise _err(40401, f"Task not found: {task_id}")

    return {"code": 0, "request_id": get_request_id(), "data": task.model_dump(mode="json")}


# ── DELETE /api/v1/tasks/{task_id} ─────────────────────────────────


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str, request: Request):
    """Cancel a task (Spec §4.5).

    Returns 200 for immediate cancel (CREATED/QUEUED/terminal).
    Returns 202 for cooperative cancel (PROCESSING).
    """
    tenant_id = _tenant(request)
    tm = _get_tm(request)

    result = await tm.cancel(task_id, tenant_id)
    if result is None:
        raise _err(40401, f"Task not found: {task_id}")

    return JSONResponse(
        status_code=result.http_code,
        content={"code": 0, "request_id": get_request_id(), "data": result.model_dump(mode="json")},
    )


# ── GET /api/v1/documents/{doc_id}/chunks ───────────────────────────


@router.get("/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: str, request: Request):
    """List all chunks for a document with positional/timeline metadata.

    Reads directly from LightRAG — works regardless of task retention/cleanup.
    Each chunk carries ``page_idx``, ``line_start``, ``line_end`` (documents)
    or ``start_time``, ``end_time`` (video/audio), along with content and tokens.
    """
    tenant_id = _tenant(request)
    tm = _get_tm(request)

    result = await tm.get_document_chunks(doc_id, tenant_id)
    if result is None:
        return {"code": 0, "request_id": get_request_id(),
                "data": {"doc_id": doc_id, "total": 0, "chunks": []}}

    return {"code": 0, "request_id": get_request_id(), "data": result}


# ── GET /api/v1/documents/{doc_id}/export ───────────────────────────


@router.get("/documents/{doc_id}/export")
async def export_document(
    doc_id: str, request: Request, format: str = "json"
):
    """Export all parsed data for a document as a structured report.

    Reads directly from LightRAG — works regardless of task retention/cleanup.

    Query params:
        format: "json" (default) — reserved for future "markdown", "csv".

    Returns full_text, chunks (with metadata), entities, and relations.
    """
    tenant_id = _tenant(request)
    tm = _get_tm(request)

    result = await tm.export_document(doc_id, tenant_id, fmt=format)
    if result is None:
        return {"code": 0, "request_id": get_request_id(),
                "data": {"doc_id": doc_id, "full_text": "",
                         "chunks": [], "entities": [], "relations": []}}

    return {"code": 0, "request_id": get_request_id(), "data": result}


