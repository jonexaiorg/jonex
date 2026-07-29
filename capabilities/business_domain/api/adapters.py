"""
业务领域 — 生态适配器 API 路由
"""
from fastapi import APIRouter, Query, Request

from jonex_core.common.exceptions import InvalidParameterError, JonexException
from jonex_core.common.i18n import translate
from jonex_core.common.response import error_response, success_response
from jonex_core.common.tenant import extract_tenant_id

from ..services import AdapterService

router = APIRouter()
_service = AdapterService()

VALID_ADAPTER_TYPES = {"dingtalk", "wechat_work", "feishu"}


def _validate_create_update(body: dict, *, require_name: bool = True) -> None:
    if require_name and not body.get("name"):
        raise InvalidParameterError(message=translate("err.adapter.name_required", fallback="适配器名称不能为空"), details={"field": "name"})  # 原消息
    adapter_type = body.get("adapter_type")
    if adapter_type and adapter_type not in VALID_ADAPTER_TYPES:
        raise InvalidParameterError(
            message=translate("err.adapter.unsupported_type", params={"adapter_type": adapter_type, "valid": ', '.join(sorted(VALID_ADAPTER_TYPES))}, fallback=f"不支持的适配器类型: {adapter_type}，必须是 {', '.join(sorted(VALID_ADAPTER_TYPES))} 之一"),  # 原消息
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
        return success_response(data=result, message="适配器已创建")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.patch("/adapters/{adapter_id}")
async def update_adapter(adapter_id: str, request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    _validate_create_update(body, require_name=False)
    try:
        result = await _service.update(adapter_id, tenant_id, body)
        return success_response(data=result, message="适配器已更新")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/adapters/{adapter_id}/connect")
async def connect_adapter(adapter_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.connect(adapter_id, tenant_id)
        return success_response(data=result, message="适配器已连接")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/adapters/{adapter_id}/disconnect")
async def disconnect_adapter(adapter_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.disconnect(adapter_id, tenant_id)
        return success_response(data=result, message="适配器已断开")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)