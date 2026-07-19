
from fastapi import APIRouter, Depends, Query, Request

from jonex_core.common.response import success_response, error_response
from jonex_core.common.exceptions import JonexException
from jonex_core.common.tenant import extract_tenant_id

from ..services import SpaceService

router = APIRouter()
_service = SpaceService()


@router.get("/spaces")
async def list_spaces(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list(tenant_id, offset, limit)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/spaces")
async def create_space(request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.create(tenant_id, body)
        return success_response(data=result, message="领域空间已创建")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.get("/spaces/{space_id}")
async def get_space(space_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.get(space_id, tenant_id)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.patch("/spaces/{space_id}")
async def update_space(space_id: str, request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.update(space_id, tenant_id, body)
        return success_response(data=result, message="领域空间已更新")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.delete("/spaces/{space_id}")
async def delete_space(space_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        await _service.delete(space_id, tenant_id)
        return success_response(message="领域空间已删除")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.get("/spaces/{space_id}/permissions")
async def get_space_permissions(space_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.get_permissions(space_id, tenant_id)
        return success_response(data={"permissions": result})
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.put("/spaces/{space_id}/permissions")
async def set_space_permissions(space_id: str, request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        await _service.set_permissions(space_id, tenant_id, body.get("permissions", []))
        return success_response(message="Permissions updated successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)
