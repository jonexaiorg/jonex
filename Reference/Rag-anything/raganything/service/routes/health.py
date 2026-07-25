"""
GET /health  — Liveness probe
GET /ready   — Readiness probe
GET /metrics — Prometheus metrics
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request):
    tm = request.app.state.task_manager
    if tm.accepting_tasks:
        return {"status": "ready"}
    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "reason": "Shutting down or full"},
    )


@router.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics endpoint (Spec §4.10)."""
    tm = request.app.state.task_manager

    # Count tasks by status
    status_counts: dict[str, int] = {}
    for t in tm._tasks.values():
        status_counts[t.status.value] = status_counts.get(t.status.value, 0) + 1

    lines = [
        "# HELP rag_tasks_total Task count by status",
        "# TYPE rag_tasks_total gauge",
    ]
    for status, count in status_counts.items():
        lines.append(f'rag_tasks_total{{status="{status}"}} {count}')

    lines.extend([
        f"# HELP rag_queue_depth Current queue depth",
        f"# TYPE rag_queue_depth gauge",
        f"rag_queue_depth {tm.queue_depth}",
        f"# HELP rag_slots_available Available capacity slots",
        f"# TYPE rag_slots_available gauge",
        f"rag_slots_available {tm.slots_available}",
    ])

    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain")
