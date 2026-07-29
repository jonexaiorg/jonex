"""
提示词模板 API 路由（直连调试用）

生产环境通过 Gateway → Sidecar invoke 契约调用，此路由仅用于本地直连调试。
注册在 capability.register_routes 中，前缀 /api/v1。
"""
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
    """从 JWT 提取用户标识（粗粒度，仅用于直连调试时记录操作人）"""
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


# ── 列表 ──


@router.get("/prompt-templates")
async def list_prompt_templates(
    request: Request,
    scope: str | None = Query(None, description="system | domain"),
    category: str | None = Query(None, description="分类筛选"),
    keyword: str | None = Query(None, description="搜索关键词"),
    domain_space_id: str | None = Query(None, description="领域空间 ID（domain 模板按空间过滤）"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list_templates(
            tenant_id, scope=scope, category=category,
            keyword=keyword, domain_space_id=domain_space_id,
            offset=offset, limit=limit,
        )
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 详情 ──


@router.get("/prompt-templates/{template_id}")
async def get_prompt_template(
    template_id: str,
    request: Request,
    domain_space_id: str | None = Query(None, description="领域空间 ID（用于空间隔离校验）"),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.get_template(
            template_id, tenant_id, domain_space_id=domain_space_id,
        )
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 创建 ──


@router.post("/prompt-templates")
async def create_prompt_template(
    request: Request,
    payload: CreatePromptTemplateRequest = Body(...),
):
    tenant_id = extract_tenant_id(request)
    user_id = _extract_user_id(request)
    data = payload.dict(exclude_none=True)
    try:
        result = await _service.create_template(
            tenant_id, data, user_id=user_id,
            domain_space_id=data.get("domain_space_id"),
        )
        return success_response(data=result, message="提示词模板已创建")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 更新 ──


@router.patch("/prompt-templates/{template_id}")
async def update_prompt_template(
    template_id: str,
    request: Request,
    payload: UpdatePromptTemplateRequest = Body(...),
):
    tenant_id = extract_tenant_id(request)
    user_id = _extract_user_id(request)
    data = payload.dict(exclude_unset=True)
    try:
        result = await _service.update_template(
            template_id, tenant_id, data, user_id=user_id,
            domain_space_id=data.get("domain_space_id"),
        )
        return success_response(data=result, message="提示词模板已更新")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 删除 ──


@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(
    template_id: str,
    request: Request,
    domain_space_id: str | None = Query(None, description="领域空间 ID（用于空间隔离校验）"),
):
    tenant_id = extract_tenant_id(request)
    try:
        await _service.delete_template(template_id, tenant_id, domain_space_id=domain_space_id)
        return success_response(message="提示词模板已删除")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 复制 ──


@router.post("/prompt-templates/{template_id}/copy")
async def copy_prompt_template(template_id: str, request: Request, payload: dict = Body({})):
    tenant_id = extract_tenant_id(request)
    user_id = _extract_user_id(request)
    try:
        result = await _service.copy_template(
            template_id, tenant_id, user_id=user_id,
            domain_space_id=payload.get("domain_space_id"),
        )
        return success_response(data=result, message="提示词模板已复制")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 版本历史 ──


@router.get("/prompt-templates/{template_id}/versions")
async def list_versions(
    template_id: str,
    request: Request,
    domain_space_id: str | None = Query(None, description="领域空间 ID（用于空间隔离校验）"),
):
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.list_versions(template_id, tenant_id, domain_space_id=domain_space_id)
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


# ── 版本回滚 ──


@router.post("/prompt-templates/{template_id}/versions/rollback")
async def rollback_version(
    template_id: str,
    request: Request,
    payload: RollbackVersionRequest = Body(...),
    domain_space_id: str | None = Query(None, description="领域空间 ID（用于空间隔离校验）"),
):
    tenant_id = extract_tenant_id(request)
    user_id = _extract_user_id(request)
    try:
        result = await _service.rollback_version(
            template_id, tenant_id, payload.target_version, user_id=user_id,
            domain_space_id=domain_space_id,
        )
        return success_response(data=result, message=f"已回滚到版本 {payload.target_version}")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)
