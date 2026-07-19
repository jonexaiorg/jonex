
from fastapi import APIRouter, Query, Request

from jonex_core.common.exceptions import InvalidParameterError, JonexException
from jonex_core.common.response import error_response, success_response
from jonex_core.common.tenant import extract_tenant_id

from ..services import AdapterService

router = APIRouter()
_service = AdapterService()

VALID_ADAPTER_TYPES = {"dingtalk", "wechat_work", "feishu"}


def _validate_create_update(body: dict, *, require_name: bool = True) -> None:
    if require_name and not body.get("name"):
        raise InvalidParameterError(message="Adapter name must not be empty", details={"field": "name"})
    adapter_type = body.get("adapter_type")
    if adapter_type and adapter_type not in VALID_ADAPTER_TYPES:
        raise InvalidParameterError(
            message=f"Unsupported adapter type: {adapter_type}. Must be one of: {', '.join(sorted(VALID_ADAPTER_TYPES))}",
            details={"field": "adapter_type", "allowed": sorted(VALID_ADAPTER_TYPES)},
        )


@router.get("/adapters")
async def list_adapters(
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


@router.post("/adapters")
async def create_adapter(request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    _validate_create_update(body, require_name=True)
    try:
        result = await _service.create(tenant_id, body)
        return success_response(data=result, message="Adapter created successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.patch("/adapters/{adapter_id}")
async def update_adapter(adapter_id: str, request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    _validate_create_update(body, require_name=False)
    try:
        result = await _service.update(adapter_id, tenant_id, body)
        return success_response(data=result, message="Adapter updated successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/adapters/{adapter_id}/connect")
async def connect_adapter(adapter_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.connect(adapter_id, tenant_id)
        return success_response(data=result, message="Adapter connected successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/adapters/{adapter_id}/disconnect")
async def disconnect_adapter(adapter_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.disconnect(adapter_id, tenant_id)
        return success_response(data=result, message="Adapter disconnected successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)