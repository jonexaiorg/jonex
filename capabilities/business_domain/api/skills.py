"""
业务领域 — AI Skill MCP 化 API 路由

外部接口：
  GET  /skills              — 技能列表
  GET  /skills/{skill_id}   — 技能详情
  POST /skills/{skill_id}/enable   — 启用
  POST /skills/{skill_id}/disable  — 停用

内部 AI 编排接口：
  GET  /skills/mcp-tools    — 租户已启用 MCP 工具定义
"""
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
    """内部 AI 编排接口：返回当前租户已启用 Skill 的 MCP 工具定义"""
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
        return success_response(data=result, message="技能已启用")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/skills/{skill_id}/disable")
async def disable_skill(skill_id: str, request: Request):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.disable(tenant_id, skill_id)
        return success_response(data=result, message="技能已停用")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)