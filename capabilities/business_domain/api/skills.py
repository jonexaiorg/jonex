
from fastapi import APIRouter, Query, Request

from jonex_core.common.response import success_response, error_response
from jonex_core.common.exceptions import JonexException
from jonex_core.common.tenant import extract_tenant_id

from ..services import SkillService

router = APIRouter()
_service = SkillService()


@router.get("/skills")
async def list_skills(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    keyword: str | None = Query(None),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list(tenant_id, offset, limit, category, keyword)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.get("/skills/mcp-tools")
async def list_enabled_mcp_tools(request: Request):

    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list_enabled_mcp_tools(tenant_id)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.get(tenant_id, skill_id)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/skills/{skill_id}/enable")
async def enable_skill(skill_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.enable(tenant_id, skill_id)
        return success_response(data=result, message="Skill enabled successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/skills/{skill_id}/disable")
async def disable_skill(skill_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.disable(tenant_id, skill_id)
        return success_response(data=result, message="Skill disabled successfully")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)