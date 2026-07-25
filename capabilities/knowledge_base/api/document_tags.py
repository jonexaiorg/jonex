"""
知识库 — 文档-标签关联 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Query, Request

from jonex_core.common.exceptions import JonexException
from jonex_core.common.response import error_response, success_response
from jonex_core.common.tenant import extract_tenant_id

from ..dtos.document_tag import AddDocumentTagRequest, SetDocumentTagsRequest
from ..services.document_tag_service import DocumentTagService

router = APIRouter()
_service = DocumentTagService()


@router.put("/documents/{document_id}/tags", summary="设置文档标签列表（全量替换）")
async def set_document_tags(
    document_id: str,
    request: Request,
    body: SetDocumentTagsRequest,
):
    """全量替换文档的标签列表 — 传入所有标签 ID，未传入的标签将被移除。"""
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.set_document_tags(
            tenant_id, document_id, body.knowledge_base_id, body.tag_ids,
        )
        return success_response(data=result, message="文档标签已更新")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.get("/documents/{document_id}/tags", summary="查询文档标签列表")
async def get_document_tags(
    document_id: str,
    request: Request,
    knowledge_base_id: Optional[str] = Query(None, min_length=1, max_length=128),
):
    """查询指定文档关联的所有标签。"""
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.get_document_tags(
            tenant_id, document_id, knowledge_base_id,
        )
        return success_response(data=result)
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.post("/documents/{document_id}/tags", summary="添加标签到文档")
async def add_document_tag(
    document_id: str,
    request: Request,
    body: AddDocumentTagRequest,
):
    """为文档添加一个标签（已存在则跳过，不报错）。"""
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.add_document_tag(
            tenant_id, document_id, body.knowledge_base_id, body.tag_id,
        )
        return success_response(data=result, message="标签已添加到文档")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)


@router.delete("/documents/{document_id}/tags/{tag_id}", summary="从文档移除标签")
async def remove_document_tag(
    document_id: str,
    tag_id: str,
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128),
):
    """从指定文档移除一个标签。"""
    tenant_id = extract_tenant_id(request)
    try:
        result = await _service.remove_document_tag(
            tenant_id, document_id, knowledge_base_id, tag_id,
        )
        return success_response(data=result, message="标签已从文档移除")
    except JonexException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code, details=e.details)
