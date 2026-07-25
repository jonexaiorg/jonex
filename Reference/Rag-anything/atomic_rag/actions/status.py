"""Get task status action handler."""

from atomic_rag.actions import ActionRegistry


@ActionRegistry.register("get_task_status")
async def handle_get_task_status(params: dict, tenant_id: str, task_manager=None, **kwargs):
    """Handle task status query action."""
    from fastapi import HTTPException

    task_id = params.get("task_id", "")
    if not task_id:
        raise HTTPException(400, "task_id 不能为空")

    status = task_manager.get_status(task_id, tenant_id)
    # 兼容 KnowledgeBaseService 预期的 lightrag_doc_ids 字段名
    status["lightrag_doc_ids"] = status.pop("doc_ids", [])
    return {"success": True, "code": 0, "message": "success", "data": status}
