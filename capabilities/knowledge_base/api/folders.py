
from fastapi import APIRouter, Query, Request

from jonex_core.common.response import success_response
from jonex_core.common.tenant import extract_tenant_id

from ..services import FolderService

router = APIRouter()
_service = FolderService()


@router.get("/knowledge-base/folders")
async def list_folders(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128),
):
    tenant_id = extract_tenant_id(request)
    result = await _service.list_folders(tenant_id, knowledge_base_id)
    return success_response(data=result)


@router.post("/knowledge-base/folders")
async def create_folder(request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    result = await _service.create_folder(tenant_id, body)
    return success_response(data=result, message="Folder created successfully")


@router.patch("/knowledge-base/folders/{folder_id}")
async def rename_folder(
    folder_id: str,
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128),
):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    result = await _service.rename_folder(tenant_id, folder_id, knowledge_base_id, body.get("name", ""))
    return success_response(data=result, message="Folder renamed successfully")


@router.delete("/knowledge-base/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128),
):
    tenant_id = extract_tenant_id(request)
    await _service.delete_folder(tenant_id, folder_id, knowledge_base_id)
    return success_response(message="Folder deleted successfully")
