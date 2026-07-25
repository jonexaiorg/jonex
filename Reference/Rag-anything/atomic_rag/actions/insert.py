"""Insert action handler — submit document for parsing and indexing."""

from atomic_rag.actions import ActionRegistry


@ActionRegistry.register("insert")
async def handle_insert(params: dict, tenant_id: str, task_manager=None, **kwargs):
    """Handle document insert action."""
    from fastapi import HTTPException

    file_path = params.get("file_path", "") or None
    mps_video_url = params.get("mps_video_url", "") or None
    if not file_path and not mps_video_url:
        raise HTTPException(400, "file_path and mps_video_url 至少传一个")

    task_id = task_manager.create_task(
        file_path=file_path,
        tenant_id=tenant_id,
        output_dir=params.get("output_dir"),
        mps_video_url=mps_video_url,
    )
    return {
        "success": True, "code": 0, "message": "success",
        "data": {"task_id": task_id, "status": "pending",
                 "file_path": file_path, "tenant_id": tenant_id},
    }
