
from fastapi import APIRouter, Body, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.database import get_db
from jonex_core.common.response import success_response, error_response
from jonex_core.common.exceptions import JonexException
from jonex_core.common.tenant import extract_tenant_id

from ..dtos.prompt_template import (
    CreatePromptTemplateRequest,
    UpdatePromptTemplateRequest,
    RollbackVersionRequest,
)
from ..services.prompt_template_service import PromptTemplateService

router = APIRouter()
_service = PromptTemplateService()


def _extract_user_id(request: Request) -> str | None:

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        import jwt
        from jonex_core.common import get_config
        config = get_config()
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None





@router.get("/prompt-templates")
async def list_prompt_templates(
    request: Request,
    scope: str | None = Query(None, description="system | domain"),
    category: str | None = Query(None, description="分类筛选"),
    keyword: str | None = Query(None, description="搜索关键词"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list_templates(
            tenant_id, scope=scope, category=category,
            keyword=keyword, offset=offset, limit=limit,
        )
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)





@router.get("/prompt-templates/{template_id}")
async def get_prompt_template(template_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.get_template(template_id, tenant_id)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)





@router.post("/prompt-templates")
async def create_prompt_template(
    request: Request,
    payload: CreatePromptTemplateRequest = Body(...),
):
    tenant_id = extract_tenant_id(request)
    user_id = _extract_user_id(request)
    try:
        result = await _service.create_template(
            tenant_id, payload.dict(exclude_none=True), user_id=user_id,
        )
        return success_response(data=result, message="Prompt template created successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)





@router.patch("/prompt-templates/{template_id}")
async def update_prompt_template(
    template_id: str,
    request: Request,
    payload: UpdatePromptTemplateRequest = Body(...),
):
    tenant_id = extract_tenant_id(request)
    user_id = _extract_user_id(request)
    try:
        result = await _service.update_template(
            template_id, tenant_id, payload.dict(exclude_unset=True), user_id=user_id,
        )
        return success_response(data=result, message="Prompt template updated successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)





@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(template_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        await _service.delete_template(template_id, tenant_id)
        return success_response(message="Prompt template deleted successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)





@router.post("/prompt-templates/{template_id}/copy")
async def copy_prompt_template(template_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    user_id = _extract_user_id(request)
    try:
        result = await _service.copy_template(template_id, tenant_id, user_id=user_id)
        return success_response(data=result, message="Prompt template copied successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)





@router.get("/prompt-templates/{template_id}/versions")
async def list_versions(template_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list_versions(template_id, tenant_id)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)





@router.post("/prompt-templates/{template_id}/versions/rollback")
async def rollback_version(
    template_id: str,
    request: Request,
    payload: RollbackVersionRequest = Body(...),
):
    tenant_id = extract_tenant_id(request)
    user_id = _extract_user_id(request)
    try:
        result = await _service.rollback_version(
            template_id, tenant_id, payload.target_version, user_id=user_id,
        )
        return success_response(data=result, message=f"Rolled back to version {payload.target_version}")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)
