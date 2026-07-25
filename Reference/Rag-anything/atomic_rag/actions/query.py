"""Query action handler — search indexed documents."""

from atomic_rag.actions import ActionRegistry


@ActionRegistry.register("query")
async def handle_query(params: dict, tenant_id: str, task_manager=None, **kwargs):
    """Handle document query action."""
    from fastapi import HTTPException

    query_text = params.get("query", "")
    mode = params.get("mode", "hybrid")
    top_k = int(params.get("top_k", 5))
    if not query_text.strip():
        raise HTTPException(400, "query 不能为空")

    workspace = f"tenant_{_safe_tenant(tenant_id)}"
    answer = await task_manager.lightrag.query(
        query=query_text, workspace=workspace, mode=mode, top_k=top_k,
    )
    return {"success": True, "code": 0, "message": "success", "data": {"answer": answer}}


def _safe_tenant(tenant_id: str) -> str:
    """Sanitize tenant ID for workspace naming."""
    import re
    return re.sub(r"[^A-Za-z0-9_\-]", "_", tenant_id) if tenant_id else "default"
