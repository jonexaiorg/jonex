"""
业务领域 — 引擎管理 API 路由
"""
from fastapi import APIRouter, Query, Request

from jonex_core.common.response import success_response, error_response
from jonex_core.common.exceptions import JonexException
from jonex_core.common.tenant import extract_tenant_id

from ..services import EngineService

router = APIRouter()
_service = EngineService()


# ── 数据接入方式 ──

@router.get("/access-methods")
async def list_access_methods(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list_access_methods(tenant_id, offset, limit)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/access-methods")
async def create_access_method(request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.create_access_method(tenant_id, body)
        return success_response(data=result, message="数据接入方式已创建")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.patch("/access-methods/{method_id}")
async def update_access_method(method_id: str, request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.update_access_method(method_id, tenant_id, body)
        return success_response(data=result, message="数据接入方式已更新")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 解析器配置 ──

@router.get("/parsers")
async def list_parsers(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list_parsers(tenant_id, offset, limit)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/parsers")
async def create_parser(request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.create_parser(tenant_id, body)
        return success_response(data=result, message="解析器已创建")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.patch("/parsers/{parser_id}")
async def update_parser(parser_id: str, request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.update_parser(parser_id, tenant_id, body)
        return success_response(data=result, message="解析器已更新")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 模型供应商 ──

@router.get("/providers")
async def list_providers(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list_providers(tenant_id, offset, limit)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/providers")
async def create_provider(request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.create_provider(tenant_id, body)
        return success_response(data=result, message="模型供应商已创建")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.patch("/providers/{provider_id}")
async def update_provider(provider_id: str, request: Request):
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.update_provider(provider_id, tenant_id, body)
        return success_response(data=result, message="模型供应商已更新")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/providers/{provider_id}/test")
async def test_provider(provider_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.test_provider(provider_id, tenant_id)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)
