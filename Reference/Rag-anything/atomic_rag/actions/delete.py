"""Delete action handler — remove document from index."""

from atomic_rag.actions import ActionRegistry


@ActionRegistry.register("delete")
async def handle_delete(params: dict, tenant_id: str, task_manager=None, **kwargs):
    """Handle document delete action."""
    from fastapi import HTTPException

    doc_id = params.get("doc_id", "")
    if not doc_id:
        raise HTTPException(400, "doc_id 不能为空")

    success = await task_manager.lightrag.delete_doc(doc_id=doc_id)
    return {"success": True, "code": 0, "message": "success", "data": {"success": success}}
