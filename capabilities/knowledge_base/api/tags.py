"""
知识库 — 标签 API 路由
"""
from fastapi import APIRouter, Query, Request

from jonex_core.common.response import success_response
from jonex_core.common.tenant import extract_tenant_id

from ..services import TagService

router = APIRouter()
_service = TagService()


@router.get("/knowledge-base/tags")
async def list_tags(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128),
):
    """获取知识库标签列表"""
    tenant_id = extract_tenant_id(request)
    result = await _service.list_tags(tenant_id, knowledge_base_id)
    return success_response(data=result)


@router.post("/knowledge-base/tags")
async def create_tag(request: Request):
    """创建知识库标签"""
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    result = await _service.create_tag(tenant_id, body)
    return success_response(data=result, message="标签已创建")


@router.patch("/knowledge-base/tags/{tag_id}")
async def update_tag(
    tag_id: str,
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128),
):
    """更新知识库标签（名称/颜色）"""
    body = await request.json()
    tenant_id = extract_tenant_id(request)
    result = await _service.update_tag(tenant_id, tag_id, knowledge_base_id, body)
    return success_response(data=result, message="标签已更新")


@router.delete("/knowledge-base/tags/{tag_id}")
async def delete_tag(
    tag_id: str,
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128),
):
    """删除知识库标签"""
    tenant_id = extract_tenant_id(request)
    await _service.delete_tag(tenant_id, tag_id, knowledge_base_id)
    return success_response(message="标签已删除")
