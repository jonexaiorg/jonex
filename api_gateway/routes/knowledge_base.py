#!/usr/bin/python3



import os
import re
import uuid
from typing import Any, Optional
from uuid import uuid4

import httpx
import jwt
from fastapi import APIRouter, Body, Depends, File, Form, Header, Query, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse

from api_gateway.deps import require_auth_header
from jonex_core.common.crypto import generate_view_token, verify_view_token
from jonex_core.common.object_storage import build_object_key, get_object_storage, get_object_storage_for
from capabilities.knowledge_base.dtos import (
    DocumentParseResultRequest,
    DocumentScopeRequest,
    FolderCreateRequest,
    FolderUpdateRequest,
    OntologyGraphRequest,
    OntologyInstanceListRequest,
    OntologyNeighborRequest,
    OntologyRelationListRequest,
    OntologyRetryRequest,
    OntologySearchRequest,
    OntologyStatsRequest,
    ParseResultDocumentListRequest,
    ParseResultEntityListRequest,
    ParseResultGraphRequest,
    ParseResultRelationshipListRequest,
    ParseResultScopeRequest,
    ReferenceResolveRequest,
    SearchHistoryCreateRequest,
    SearchHistoryDeleteRequest,
    SearchRequest,
    SetDocumentFolderRequest,
)
from jonex_core.common import CapabilityInvokeError, InvalidApiKeyError, InvalidParameterError, get_exception_class
from jonex_core.common import get_config, get_logger, success_response
from jonex_core.common.file_source_util import parse_file_source
from jonex_core.common.tenant import extract_tenant_id

logger = get_logger("api_knowledge_base")

router = APIRouter(dependencies=[Depends(require_auth_header)])


_TEXT_MIME_PREFIXES = ("text/",)
_TEXT_MIME_EXACT = {
    "application/json",
    "application/xml",
    "application/javascript",
    "application/x-yaml",
    "application/yaml",
}


def _media_type_with_charset(mime: str | None) -> str:

    mime = (mime or "application/octet-stream").strip()
    if "charset=" in mime.lower():
        return mime
    base = mime.split(";", 1)[0].strip().lower()
    if base.startswith(_TEXT_MIME_PREFIXES) or base in _TEXT_MIME_EXACT:
        return f"{mime}; charset=utf-8"
    return mime



_EXECUTABLE_MIME = {"text/html", "application/xhtml+xml", "image/svg+xml"}


def _safe_inline_media_type(mime: str | None) -> str:

    base = (mime or "").split(";", 1)[0].strip().lower()
    if base in _EXECUTABLE_MIME:
        return "text/plain; charset=utf-8"
    return _media_type_with_charset(mime)



def _extract_user_id(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    config = get_config()
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        return payload.get("sub") or None
    except jwt.PyJWTError:
        return None


async def _call_kb_capability(
    request: Request,
    action: str,
    payload: dict[str, Any],
    *,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> dict:
    config = get_config()
    tenant_id = tenant_id or extract_tenant_id(request)
    request_id = getattr(request.state, "request_id", "")
    resolved_user_id = user_id or _extract_user_id(request)

    sidecar_payload: dict[str, Any] = {
        "capability_id": "business.knowledge_base.v1",
        "payload": {"action": action, "data": payload},
        "tenant_id": tenant_id,
    }
    if resolved_user_id:
        sidecar_payload["user_id"] = resolved_user_id

    headers = {
        "X-API-Key": config.SIDECAR_API_KEY,
        "X-Request-ID": request_id,
        "X-Tenant-ID": tenant_id,
        "X-Forwarded-For": request.client.host if request.client else "",
    }

    try:
        timeout = float(os.getenv("GATEWAY_SIDECAR_TIMEOUT", "120"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{config.SIDECAR_URL}/invoke",
                json=sidecar_payload,
                headers=headers,
            )
        result = response.json()
        if response.status_code != 200 or not result.get("success", False):
            message = result.get("message") or "Knowledge base capability call failed"
            code = int(result.get("code") or CapabilityInvokeError.code)
            exception_cls = get_exception_class(code)
            raise exception_cls(message=message, details={"action": action})
        return result.get("data") or {}
    except httpx.TimeoutException:
        raise CapabilityInvokeError(message="Knowledge base capability call timed out", details={"action": action})
    except CapabilityInvokeError:
        raise
    except Exception as exc:
        if hasattr(exc, "code") and hasattr(exc, "status_code"):
            raise
        logger.error("Knowledge Base capability call failed: action=%s error=%s", action, exc)
        raise CapabilityInvokeError(message="Knowledge base capability is unavailable", details={"action": action})


@router.post("/documents/upload", summary="上传知识文档")
async def upload_document(
    request: Request,
    file: UploadFile = File(None, description="上传的文件（COS 直传模式可不传）"),
    knowledge_base_id: str = Form(..., min_length=1, max_length=128, description="知识库 ID"),
    storage_key: Optional[str] = Form(None, description="COS 预上传后的对象键（COS 直传模式）"),
    storage_backend: Optional[str] = Form(None, description="存储后端，cos 或 local"),
    doc_id: Optional[str] = Form(None, description="文档 ID（COS 直传模式，与 generate-upload-url 返回一致）"),
    file_name: Optional[str] = Form(None, description="文件名（COS 直传模式必传）"),
    mime_type: Optional[str] = Form(None, description="文件 MIME 类型"),
    folder_id: Optional[str] = Form(None, description="文件夹 ID（归属到指定文件夹）"),
    metadata: Optional[str] = Form(None, description="额外元数据（JSON 字符串）"),
):

    tenant_id = extract_tenant_id(request)

    payload: dict[str, Any] = {
        "knowledge_base_id": knowledge_base_id,
    }
    if folder_id:
        payload["folder_id"] = folder_id

    if storage_key:

        if doc_id:
            payload["doc_id"] = doc_id
        payload["file_name"] = file_name or storage_key.rsplit("/", 1)[-1]
        payload["file_path"] = storage_key
        payload["storage_key"] = storage_key
        payload["storage_backend"] = storage_backend or "cos"
        if mime_type:
            payload["mime_type"] = mime_type
    else:

        if file is None:
            raise InvalidParameterError(message="Traditional upload mode requires a file; for direct COS uploads, provide storage_key")
        content = await file.read()
        if not content:
            raise InvalidParameterError(message="The uploaded file must not be empty")

        backend = os.getenv("OBJECT_STORAGE_BACKEND", "local").strip().lower()
        doc_id = str(uuid4())
        new_key = build_object_key(tenant_id, knowledge_base_id, doc_id, file.filename)
        await get_object_storage().put_bytes(
            new_key, content, content_type=_media_type_with_charset(file.content_type)
        )

        payload["doc_id"] = doc_id
        payload["file_name"] = file.filename or "unnamed"
        payload["mime_type"] = file.content_type
        payload["file_size"] = len(content)
        payload["storage_key"] = new_key
        payload["storage_backend"] = backend


        logger.info("Gateway uploaded file: backend=%s key=%s (%d bytes)", backend, new_key, len(content))

    if metadata:
        payload["metadata"] = {"raw": metadata}

    result = await _call_kb_capability(request, "upload_document", payload)
    return success_response(data=result)


@router.post("/documents/generate-upload-url", summary="生成预签名上传 URL（COS 直传）")
async def generate_upload_url(
    request: Request,
    knowledge_base_id: str = Body(..., min_length=1, max_length=128),
    file_name: str = Body(..., min_length=1, max_length=512),
    content_type: Optional[str] = Body(None, max_length=128),
):

    result = await _call_kb_capability(
        request,
        "generate_upload_url",
        {"knowledge_base_id": knowledge_base_id, "file_name": file_name, "content_type": content_type},
    )
    return success_response(data=result)


@router.get("/documents/{document_id}/view-ticket", summary="签发原文短时查看票据（音视频/PDF/图片直连）")
async def get_view_ticket(request: Request, document_id: str):

    tenant_id = extract_tenant_id(request)
    ttl = int(os.getenv("RAW_VIEW_TOKEN_TTL", "300"))
    token = generate_view_token(tenant_id, document_id, ttl)
    return success_response(
        data={
            "url": f"/api/v1/knowledge-base/documents/{document_id}/raw?token={token}",
            "expires_in": ttl,
        }
    )


@router.get("/documents", summary="查询知识文档列表")
async def list_documents(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    status: Optional[str] = Query(None, description="文档状态过滤"),
    ontology_status: Optional[str] = Query(None, description="本体状态过滤"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    folder_id: Optional[str] = Query(None, description="文件夹筛选（仅返回该文件夹下的文档，不传为全部文档）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):

    payload: dict[str, Any] = {
        "knowledge_base_id": knowledge_base_id,
        "status": status,
        "ontology_status": ontology_status,
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
    }
    if folder_id:
        payload["folder_id"] = folder_id
    result = await _call_kb_capability(request, "list_documents", payload)
    return success_response(data=result)


@router.get("/documents/{document_id}", summary="获取知识文档详情")
async def get_document(
    request: Request,
    document_id: str,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = DocumentScopeRequest(knowledge_base_id=knowledge_base_id)
    result = await _call_kb_capability(
        request,
        "get_document",
        {"document_id": document_id, **_schema_payload(payload)},
    )
    return success_response(data=result)


@router.delete("/documents/{document_id}", summary="删除知识文档")
async def delete_document(
    request: Request,
    document_id: str,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = DocumentScopeRequest(knowledge_base_id=knowledge_base_id)
    result = await _call_kb_capability(
        request,
        "delete_document",
        {"document_id": document_id, **_schema_payload(payload)},
    )
    return success_response(data=result)


@router.put("/documents/{document_id}/folder", summary="设置或清除文档所属文件夹")
async def set_document_folder(
    request: Request,
    document_id: str,
    body: SetDocumentFolderRequest,
):

    result = await _call_kb_capability(
        request,
        "set_document_folder",
        {"document_id": document_id, **_schema_payload(body)},
    )
    return success_response(data=result)





@router.get("/knowledge-base/folders", summary="列出知识库文件夹")
async def list_folders(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    result = await _call_kb_capability(
        request,
        "list_folders",
        {"knowledge_base_id": knowledge_base_id},
    )
    return success_response(data=result)


@router.post("/knowledge-base/folders", summary="创建文件夹")
async def create_folder(request: Request, body: FolderCreateRequest):

    result = await _call_kb_capability(request, "create_folder", _schema_payload(body))
    return success_response(data=result, message="Folder created successfully")


@router.patch("/knowledge-base/folders/{folder_id}", summary="重命名文件夹")
async def rename_folder(
    request: Request,
    folder_id: str,
    body: FolderUpdateRequest,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = {"folder_id": folder_id, "knowledge_base_id": knowledge_base_id, **_schema_payload(body)}
    result = await _call_kb_capability(request, "rename_folder", payload)
    return success_response(data=result, message="Folder renamed successfully")


@router.delete("/knowledge-base/folders/{folder_id}", summary="删除文件夹")
async def delete_folder(
    request: Request,
    folder_id: str,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    result = await _call_kb_capability(
        request,
        "delete_folder",
        {"folder_id": folder_id, "knowledge_base_id": knowledge_base_id},
    )
    return success_response(data=result, message="Folder deleted successfully")


def _schema_payload(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


@router.post("/search", summary="知识库语义检索")
async def search(request: Request, payload: SearchRequest):

    result = await _call_kb_capability(
        request,
        "search",
        _schema_payload(payload),
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.post("/search/enhanced", summary="知识库增强检索")
async def search_enhanced(request: Request, payload: SearchRequest):

    result = await _call_kb_capability(
        request,
        "search_enhanced",
        _schema_payload(payload),
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.post("/search/ontology", summary="本体优先检索（Ontology → RAG fallback，多 KB）")
async def search_ontology(request: Request, payload: OntologySearchRequest):

    result = await _call_kb_capability(
        request,
        "query_with_ontology",
        _schema_payload(payload),
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.post("/qa/ask", summary="问答查询（基于 RAG）")
async def qa_ask(
    request: Request,
    question: str = Body(..., embed=True, description="问题内容"),
    mode: str = Body("hybrid", embed=True, description="检索模式: naive/local/global/hybrid"),
    top_k: int = Body(5, embed=True, description="返回结果数量"),
):

    result = await _call_kb_capability(
        request,
        "search",
        {"query": question, "mode": mode, "top_k": top_k, "knowledge_base_id": ""},
    )
    return success_response(data=result)


@router.get("/documents/search/stream", summary="流式语义搜索（OpenAI 兼容 SSE）")
async def search_documents_stream(
    request: Request,
    query: str = Query(..., description="查询问题"),
    mode: str = Query("hybrid", description="检索模式: naive/local/global/hybrid/mix/bypass"),
    top_k: int = Query(5, ge=1, le=50, description="返回结果数量"),
    domain_id: str | None = Query(None, description="领域 ID"),
    knowledge_base_id: str = Query("", description="知识库 ID（按知识库隔离检索；空表示沿用默认行为）"),
):

    from fastapi.responses import StreamingResponse
    import httpx, json, time, uuid, re

    config = get_config()
    sidecar_url = config.SIDECAR_URL
    tenant_id = extract_tenant_id(request)
    request_id = getattr(request.state, "request_id", "")
    stream_params = {"query": query, "mode": mode, "top_k": top_k}
    if domain_id and domain_id != "all":
        stream_params["domain_id"] = domain_id

    if knowledge_base_id:
        stream_params["knowledge_base_id"] = knowledge_base_id

    _RESPONSE_RE = re.compile(r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"')

    async def _generate():
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())
        _base_choice = {"index": 0, "delta": {}, "finish_reason": None}
        _base_payload = {
            "id": chunk_id, "object": "chat.completion.chunk",
            "created": created, "model": "lightrag", "choices": [None],
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "GET",
                    f"{sidecar_url}/invoke/stream/rag",
                    params=stream_params,
                    headers={
                        "X-API-Key": config.SIDECAR_API_KEY,
                        "X-Request-ID": request_id,
                        "X-Tenant-ID": tenant_id,
                    },
                ) as resp:
                    resp.raise_for_status()
                    choice0 = dict(_base_choice)
                    choice0["delta"] = {"role": "assistant", "content": ""}
                    _base_payload["choices"][0] = choice0
                    yield f"data: {json.dumps(_base_payload, ensure_ascii=False)}\n\n"

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        m = _RESPONSE_RE.search(line)
                        if m:
                            content = json.loads('"' + m.group(1) + '"')
                            choice = dict(_base_choice)
                            choice["delta"] = {"content": content}
                            _base_payload["choices"][0] = choice
                            yield f"data: {json.dumps(_base_payload, ensure_ascii=False)}\n\n"
                            continue
                        if '"references"' in line:
                            try:
                                data = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if data.get("references"):

                                refs_text = "\n".join(f"- {r.get('file_path', '')}" for r in data["references"])
                                choice = dict(_base_choice)
                                choice["delta"] = {"content": refs_text + "\n\n"}
                                _base_payload["choices"][0] = choice
                                yield f"data: {json.dumps(_base_payload, ensure_ascii=False)}\n\n"


                                if os.getenv("STREAM_REF_STRUCTURED", "").lower() in ("1", "true", "yes"):
                                    parsed = [
                                        parse_file_source(r.get("file_path", ""))
                                        for r in data["references"]
                                    ]
                                    parsed = [p for p in parsed if p.get("doc_id")]
                                    if parsed:
                                        ref_payload = dict(_base_payload)
                                        ref_payload["object"] = "references"
                                        ref_payload["references"] = parsed
                                        if "choices" in ref_payload:
                                            del ref_payload["choices"]
                                        yield f"data: {json.dumps(ref_payload, ensure_ascii=False)}\n\n"

            choice = dict(_base_choice)
            choice["delta"] = {}
            choice["finish_reason"] = "stop"
            _base_payload["choices"][0] = choice
            yield f"data: {json.dumps(_base_payload, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.warning(f"Streaming search interrupted: query={query[:50]}, error={e}")
            error_choice = {
                "index": 0,
                "delta": {"content": f"Retrieval service is temporarily unavailable: {e}"},
                "finish_reason": "error",
            }
            _base_payload["choices"][0] = error_choice
            yield f"data: {json.dumps(_base_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.post("/documents/references/resolve", summary="引用富化/预签名")
async def resolve_references(request: Request, payload: ReferenceResolveRequest):

    ref_dicts = [r.dict() for r in payload.refs] if payload.refs else None
    doc_ids = payload.doc_ids or None
    result = await _call_kb_capability(
        request,
        "resolve_references",
        {"refs": ref_dicts, "doc_ids": doc_ids},
    )
    return success_response(data=result)


@router.get("/search/overview", summary="知识检索概览")
async def get_search_overview(
    request: Request,
    knowledge_base_id: str = Query("", min_length=0, max_length=128, description="知识库 ID（空表示全局）"),
):

    result = await _call_kb_capability(
        request,
        "get_search_overview",
        {"knowledge_base_id": knowledge_base_id},
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.get("/search/history", summary="查询检索历史（全局可不传 kb_id）")
async def list_search_history(
    request: Request,
    knowledge_base_id: str = Query("", min_length=0, max_length=128, description="知识库 ID（空表示全局）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):

    result = await _call_kb_capability(
        request,
        "list_search_history",
        {
            "knowledge_base_id": knowledge_base_id,
            "page": page,
            "page_size": page_size,
        },
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.post("/search/history", summary="保存检索历史")
async def save_search_history(request: Request, payload: SearchHistoryCreateRequest):

    result = await _call_kb_capability(
        request,
        "save_search_history",
        _schema_payload(payload),
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.delete("/search/history/{history_id}", summary="删除检索历史")
async def delete_search_history(
    request: Request,
    history_id: str,
    knowledge_base_id: str = Query("", min_length=0, max_length=128, description="知识库 ID"),
):

    payload = SearchHistoryDeleteRequest(knowledge_base_id=knowledge_base_id)
    result = await _call_kb_capability(
        request,
        "delete_search_history",
        {"history_id": history_id, **_schema_payload(payload)},
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.delete("/search/history", summary="清空检索历史")
async def clear_search_history(
    request: Request,
    knowledge_base_id: str = Query("", min_length=0, max_length=128, description="知识库 ID"),
):

    result = await _call_kb_capability(
        request,
        "clear_search_history",
        {"knowledge_base_id": knowledge_base_id},
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)







@router.post("/search/feedback", summary="提交搜索结果反馈")
async def submit_search_feedback(request: Request, payload: dict = Body(...)):

    result = await _call_kb_capability(
        request,
        "submit_search_feedback",
        payload,
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.delete("/search/feedback", summary="取消搜索结果反馈")
async def cancel_search_feedback(request: Request, payload: dict = Body(...)):

    result = await _call_kb_capability(
        request,
        "cancel_search_feedback",
        payload,
        user_id=_extract_user_id(request),
    )
    return success_response(data=result)


@router.get("/search/feedback", summary="查询知识库的反馈记录列表")
async def list_search_feedback(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    feedback_type: str = Query(None, regex="^(like|dislike)?$", description="反馈类型过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页条数"),
):

    result = await _call_kb_capability(
        request,
        "list_search_feedback",
        {
            "knowledge_base_id": knowledge_base_id,
            "feedback_type": feedback_type,
            "page": page,
            "page_size": page_size,
        },
    )
    return success_response(data=result)


@router.post("/search/feedback/toggle-adopt", summary="切换反馈采纳状态")
async def toggle_search_feedback_adopt(request: Request, payload: dict = Body(...)):

    result = await _call_kb_capability(
        request,
        "toggle_search_feedback_adopted",
        payload,
    )
    return success_response(data=result)


@router.get("/search/feedback/stats", summary="获取知识库的反馈统计")
async def get_search_feedback_stats(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    result = await _call_kb_capability(
        request,
        "get_search_feedback_stats",
        {"knowledge_base_id": knowledge_base_id},
    )
    return success_response(data=result)


@router.get("/parse-results/summary", summary="解析结果概要")
async def get_parse_result_summary(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = ParseResultScopeRequest(knowledge_base_id=knowledge_base_id)
    result = await _call_kb_capability(
        request,
        "get_parse_result_summary",
        _schema_payload(payload),
    )
    return success_response(data=result)


@router.get("/parse-results/documents", summary="解析文档列表")
async def get_parse_result_documents(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态过滤"),
):

    payload = ParseResultDocumentListRequest(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
    )
    result = await _call_kb_capability(
        request,
        "get_parse_result_documents",
        _schema_payload(payload),
    )
    return success_response(data=result)


@router.get("/parse-results/entities", summary="解析实体列表")
async def get_parse_result_entities(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    file_path: Optional[str] = Query(None, description="来源文件路径"),
    document_id: Optional[str] = Query(None, description="文档 ID"),
):

    payload = ParseResultEntityListRequest(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        entity_type=entity_type,
        file_path=file_path,
        document_id=document_id,
    )
    result = await _call_kb_capability(
        request,
        "get_parse_result_entities",
        _schema_payload(payload),
    )
    return success_response(data=result)


@router.get("/parse-results/relationships", summary="解析关系列表")
async def get_parse_result_relationships(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    file_path: Optional[str] = Query(None, description="来源文件路径"),
    document_id: Optional[str] = Query(None, description="文档 ID"),
    source_entity: Optional[str] = Query(None, description="源实体名称"),
    target_entity: Optional[str] = Query(None, description="目标实体名称"),
):

    payload = ParseResultRelationshipListRequest(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        file_path=file_path,
        document_id=document_id,
        source_entity=source_entity,
        target_entity=target_entity,
    )
    result = await _call_kb_capability(
        request,
        "get_parse_result_relationships",
        _schema_payload(payload),
    )
    return success_response(data=result)


@router.get("/parse-results/graph-summary", summary="解析图谱概要")
async def get_parse_result_graph_summary(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = ParseResultScopeRequest(knowledge_base_id=knowledge_base_id)
    result = await _call_kb_capability(
        request,
        "get_parse_result_graph_summary",
        _schema_payload(payload),
    )
    return success_response(data=result)


@router.get("/parse-results/graph", summary="解析图谱")
async def get_parse_result_graph(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    file_path: Optional[str] = Query(None, description="来源文件路径"),
    document_id: Optional[str] = Query(None, description="文档 ID"),
    limit: int = Query(200, ge=1, le=1000, description="返回节点数量上限"),
):

    payload = ParseResultGraphRequest(
        knowledge_base_id=knowledge_base_id,
        keyword=keyword,
        file_path=file_path,
        document_id=document_id,
        limit=limit,
    )
    result = await _call_kb_capability(
        request,
        "get_parse_result_graph",
        _schema_payload(payload),
    )
    return success_response(data=result)


@router.get("/documents/{document_id}/parse-result", summary="获取单文档解析结果")
async def get_document_parse_result(
    request: Request,
    document_id: str,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = DocumentParseResultRequest(
        document_id=document_id,
        knowledge_base_id=knowledge_base_id,
    )
    result = await _call_kb_capability(
        request,
        "get_document_parse_result",
        _schema_payload(payload),
    )
    return success_response(data=result)


@router.post("/documents/{document_id}/retry-ontology", summary="重试本体抽取")
async def retry_ontology_extract(
    request: Request,
    document_id: str,
    payload: OntologyRetryRequest = Body(...),
):

    result = await _call_kb_capability(
        request,
        "retry_ontology_extract",
        {
            "document_id": document_id,
            "knowledge_base_id": payload.knowledge_base_id,
        },
    )
    return success_response(data=result)






@router.get("/knowledge-info", summary="知识库列表")
async def list_knowledge_info(
    request: Request,
    space_id: Optional[str] = Query(None, description="所属空间 ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页条数"),
):
    result = await _call_kb_capability(request, "list_knowledge_info", {
        "space_id": space_id, "status": status, "keyword": keyword,
        "offset": offset, "limit": limit,
    })
    return success_response(data=result)


@router.post("/knowledge-info", summary="创建知识库")
async def create_knowledge_info(request: Request, payload: dict = Body(...)):
    result = await _call_kb_capability(request, "create_knowledge_info", payload)
    return success_response(data=result)


@router.get("/knowledge-info/{kb_id}", summary="知识库详情")
async def get_knowledge_info(request: Request, kb_id: str):
    result = await _call_kb_capability(request, "get_knowledge_info", {"kb_id": kb_id})
    return success_response(data=result)


@router.patch("/knowledge-info/{kb_id}", summary="更新知识库")
async def update_knowledge_info(request: Request, kb_id: str, payload: dict = Body(...)):
    payload["kb_id"] = kb_id
    result = await _call_kb_capability(request, "update_knowledge_info", payload)
    return success_response(data=result)


@router.delete("/knowledge-info/{kb_id}", summary="删除知识库")
async def delete_knowledge_info(request: Request, kb_id: str):
    result = await _call_kb_capability(request, "delete_knowledge_info", {"kb_id": kb_id})
    return success_response(data=result)






@router.get("/spaces", summary="获取领域空间列表")
async def list_spaces(
    request: Request,
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页条数"),
):

    result = await _call_kb_capability(request, "list_spaces", {"offset": offset, "limit": limit})
    return success_response(data=result)


@router.post("/spaces", summary="创建领域空间")
async def create_space(request: Request, payload: dict = Body(...)):

    result = await _call_kb_capability(request, "create_space", payload)
    return success_response(data=result)


@router.get("/spaces/{space_id}", summary="获取领域空间详情")
async def get_space(request: Request, space_id: str):

    result = await _call_kb_capability(request, "get_space", {"space_id": space_id})
    return success_response(data=result)


@router.patch("/spaces/{space_id}", summary="更新领域空间")
async def update_space(request: Request, space_id: str, payload: dict = Body(...)):

    payload["space_id"] = space_id
    result = await _call_kb_capability(request, "update_space", payload)
    return success_response(data=result)


@router.delete("/spaces/{space_id}", summary="删除领域空间")
async def delete_space(request: Request, space_id: str):

    result = await _call_kb_capability(request, "delete_space", {"space_id": space_id})
    return success_response(data=result)


@router.get("/spaces/{space_id}/permissions", summary="获取领域空间权限")
async def get_space_permissions(request: Request, space_id: str):

    result = await _call_kb_capability(request, "get_space_permissions", {"space_id": space_id})
    return success_response(data=result)


@router.put("/spaces/{space_id}/permissions", summary="设置领域空间权限")
async def set_space_permissions(request: Request, space_id: str, payload: dict = Body(...)):

    payload["space_id"] = space_id
    result = await _call_kb_capability(request, "set_space_permissions", payload)
    return success_response(data=result)






@router.get("/services", summary="获取领域服务列表")
async def list_services(
    request: Request,
    space_id: Optional[str] = Query(None, description="所属空间 ID"),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页条数"),
):

    result = await _call_kb_capability(request, "list_services", {"space_id": space_id, "offset": offset, "limit": limit})
    return success_response(data=result)


@router.post("/services", summary="创建领域服务")
async def create_service(request: Request, payload: dict = Body(...)):

    result = await _call_kb_capability(request, "create_service", payload)
    return success_response(data=result)


@router.get("/services/{service_id}", summary="获取领域服务详情")
async def get_service(request: Request, service_id: str):

    result = await _call_kb_capability(request, "get_service", {"service_id": service_id})
    return success_response(data=result)


@router.patch("/services/{service_id}", summary="更新领域服务")
async def update_service(request: Request, service_id: str, payload: dict = Body(...)):

    payload["service_id"] = service_id
    result = await _call_kb_capability(request, "update_service", payload)
    return success_response(data=result)


@router.delete("/services/{service_id}", summary="删除领域服务")
async def delete_service(request: Request, service_id: str):

    result = await _call_kb_capability(request, "delete_service", {"service_id": service_id})
    return success_response(data=result)


@router.get("/services/{service_id}/permissions", summary="获取领域服务权限")
async def get_service_permissions(request: Request, service_id: str):

    result = await _call_kb_capability(request, "get_service_permissions", {"service_id": service_id})
    return success_response(data=result)


@router.put("/services/{service_id}/permissions", summary="设置领域服务权限")
async def set_service_permissions(request: Request, service_id: str, payload: dict = Body(...)):

    payload["service_id"] = service_id
    result = await _call_kb_capability(request, "set_service_permissions", payload)
    return success_response(data=result)


@router.get("/services/{service_id}/api-keys", summary="获取 API Key 列表")
async def list_api_keys(request: Request, service_id: str):

    result = await _call_kb_capability(request, "list_service_api_keys", {"service_id": service_id})
    return success_response(data=result)


@router.post("/services/{service_id}/api-keys", summary="创建 API Key")
async def create_api_key(request: Request, service_id: str, payload: dict = Body(...)):

    payload["service_id"] = service_id
    result = await _call_kb_capability(request, "create_service_api_key", payload)
    return success_response(data=result)


@router.delete("/services/{service_id}/api-keys/{key_id}", summary="删除 API Key")
async def delete_api_key(request: Request, service_id: str, key_id: str):

    result = await _call_kb_capability(request, "delete_service_api_key", {"service_id": service_id, "key_id": key_id})
    return success_response(data=result)


@router.post("/services/{service_id}/api-keys/rotate", summary="轮换服务 API Key")
async def rotate_api_key(request: Request, service_id: str):

    result = await _call_kb_capability(request, "rotate_service_api_key", {"service_id": service_id})
    return success_response(data=result)


@router.get("/services/{service_id}/configs", summary="获取服务配置")
async def get_service_configs(request: Request, service_id: str):

    result = await _call_kb_capability(request, "get_service_configs", {"service_id": service_id})
    return success_response(data=result)


@router.put("/services/{service_id}/configs", summary="更新服务配置")
async def update_service_configs(request: Request, service_id: str, payload: dict = Body(...)):

    payload["service_id"] = service_id
    result = await _call_kb_capability(request, "update_service_configs", payload)
    return success_response(data=result)


@router.get("/services/{service_id}/search", summary="搜索领域服务")
async def search_service(
    request: Request,
    service_id: str,
    query: str = Query(..., description="搜索关键词"),
):

    result = await _call_kb_capability(request, "search_service", {"service_id": service_id, "query": query})
    return success_response(data=result)






@router.get("/ontology/editor-state", summary="获取本体编译编辑状态")
async def get_ontology_editor_state(
    request: Request,
    knowledge_base_id: str = Query(..., description="知识库 ID"),
):

    result = await _call_kb_capability(request, "get_editor_state", {"knowledge_base_id": knowledge_base_id})
    return success_response(data=result)


@router.get("/ontology/compiled-schema", summary="获取本体编译 schema")
async def get_ontology_compiled_schema(
    request: Request,
    knowledge_base_id: str = Query(..., description="知识库 ID"),
):

    result = await _call_kb_capability(request, "get_compiled_schema", {"knowledge_base_id": knowledge_base_id})
    return success_response(data=result)


@router.put("/ontology/compiled-schema", summary="保存本体编译 schema")
async def save_ontology_compiled_schema(request: Request, payload: dict = Body(...)):

    result = await _call_kb_capability(request, "save_compiled_schema", payload)
    return success_response(data=result)


@router.post("/ontology/compiled-schema/reseed", summary="从模板重新生成编译 schema")
async def reseed_ontology_compiled_schema(request: Request, payload: dict = Body(...)):

    result = await _call_kb_capability(request, "reseed_compiled_schema", payload)
    return success_response(data=result)






@router.get("/ontology/synonyms", summary="同义词组列表")
async def list_synonyms(
    request: Request,
    knowledge_base_id: str = Query(..., description="知识库 ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):

    result = await _call_kb_capability(
        request,
        "list_synonyms",
        {"knowledge_base_id": knowledge_base_id, "page": page, "page_size": page_size},
    )
    return success_response(data=result)


@router.post("/ontology/synonyms", summary="新建同义词组")
async def create_synonym(request: Request, payload: dict = Body(...)):
    result = await _call_kb_capability(request, "create_synonym", payload)
    return success_response(data=result)


@router.patch("/ontology/synonyms/{synonym_id}", summary="更新同义词组")
async def update_synonym(request: Request, synonym_id: str, payload: dict = Body(...)):
    payload["synonym_id"] = synonym_id
    result = await _call_kb_capability(request, "update_synonym", payload)
    return success_response(data=result)


@router.delete("/ontology/synonyms/{synonym_id}", summary="删除同义词组")
async def delete_synonym(request: Request, synonym_id: str):
    result = await _call_kb_capability(request, "delete_synonym", {"synonym_id": synonym_id})
    return success_response(data=result)


@router.post("/ontology/synonyms/import", summary="批量导入同义词")
async def import_synonyms(request: Request, payload: dict = Body(...)):
    result = await _call_kb_capability(request, "import_synonyms", payload)
    return success_response(data=result)


@router.get("/ontology/statistics", summary="本体 kb 维度统计")
async def get_ontology_statistics(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = OntologyStatsRequest(knowledge_base_id=knowledge_base_id)
    result = await _call_kb_capability(request, "get_ontology_statistics", _schema_payload(payload))
    return success_response(data=result)


@router.get("/ontology/instances", summary="本体实例列表（kb 维度）")
async def list_ontology_instances(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索（子串匹配）"),
):

    payload = OntologyInstanceListRequest(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size,
        entity_type=entity_type,
        keyword=keyword,
    )
    result = await _call_kb_capability(request, "list_ontology_instances", _schema_payload(payload))
    return success_response(data=result)


@router.get("/ontology/relations", summary="本体关系列表（kb 维度）")
async def list_ontology_relations(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    relation_type: Optional[str] = Query(None, description="关系类型过滤"),
    source_name: Optional[str] = Query(None, description="源实体名称过滤"),
    target_name: Optional[str] = Query(None, description="目标实体名称过滤"),
    source_type: Optional[str] = Query(None, description="源实体类型精确过滤"),
    target_type: Optional[str] = Query(None, description="目标实体类型精确过滤"),
):

    payload = OntologyRelationListRequest(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size,
        relation_type=relation_type,
        source_name=source_name,
        target_name=target_name,
        source_type=source_type,
        target_type=target_type,
    )
    result = await _call_kb_capability(request, "list_ontology_relations", _schema_payload(payload))
    return success_response(data=result)


@router.get("/ontology/entity-types", summary="本体实体类型列表（含实例数）")
async def list_ontology_entity_types(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = OntologyStatsRequest(knowledge_base_id=knowledge_base_id)
    result = await _call_kb_capability(request, "list_ontology_entity_types", _schema_payload(payload))
    return success_response(data=result)


@router.get("/ontology/relation-types", summary="本体关系类型列表（含实例数）")
async def list_ontology_relation_types(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):

    payload = OntologyStatsRequest(knowledge_base_id=knowledge_base_id)
    result = await _call_kb_capability(request, "list_ontology_relation_types", _schema_payload(payload))
    return success_response(data=result)


@router.get("/ontology/graph", summary="本体图谱数据（nodes + edges + 统计）")
async def get_ontology_graph(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    limit: int = Query(500, ge=1, le=2000, description="节点数量上限（按连接度取 top-N）"),
    entity_types: Optional[list[str]] = Query(None, description="按实体类型过滤，可重复传参"),
):

    payload = OntologyGraphRequest(
        knowledge_base_id=knowledge_base_id,
        limit=limit,
        entity_types=entity_types,
    )
    result = await _call_kb_capability(request, "get_ontology_graph", _schema_payload(payload))
    return success_response(data=result)


@router.get("/ontology/neighbors", summary="实体一跳邻居展开（nodes + edges）")
async def expand_ontology_neighbors(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
    entity_type: str = Query(..., min_length=1, max_length=128, description="实体类型"),
    canonical_name: str = Query(..., min_length=1, max_length=512, description="实体规范名"),
    limit: int = Query(50, ge=1, le=200, description="邻居数量上限"),
):

    payload = OntologyNeighborRequest(
        knowledge_base_id=knowledge_base_id,
        entity_type=entity_type,
        canonical_name=canonical_name,
        limit=limit,
    )
    result = await _call_kb_capability(request, "expand_ontology_neighbors", _schema_payload(payload))
    return success_response(data=result)






@router.get("/data-sources", summary="数据源列表")
async def list_data_sources(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):
    result = await _call_kb_capability(request, "list_data_sources", {"knowledge_base_id": knowledge_base_id})
    return success_response(data=result)


@router.post("/data-sources", summary="创建数据源")
async def create_data_source(request: Request, payload: dict = Body(...)):
    result = await _call_kb_capability(request, "create_data_source", payload)
    return success_response(data=result)


@router.get("/data-sources/{ds_id}", summary="数据源详情")
async def get_data_source(request: Request, ds_id: str):
    result = await _call_kb_capability(request, "get_data_source", {"ds_id": ds_id})
    return success_response(data=result)


@router.patch("/data-sources/{ds_id}", summary="更新数据源")
async def update_data_source(request: Request, ds_id: str, payload: dict = Body(...)):
    payload["ds_id"] = ds_id
    result = await _call_kb_capability(request, "update_data_source", payload)
    return success_response(data=result)


@router.delete("/data-sources/{ds_id}", summary="删除数据源")
async def delete_data_source(request: Request, ds_id: str):
    result = await _call_kb_capability(request, "delete_data_source", {"ds_id": ds_id})
    return success_response(data=result)


@router.post("/data-sources/{ds_id}/test", summary="测试连接")
async def test_data_source(request: Request, ds_id: str):
    result = await _call_kb_capability(request, "test_data_source", {"ds_id": ds_id})
    return success_response(data=result)


@router.post("/data-sources/{ds_id}/sync", summary="立即同步")
async def sync_data_source(request: Request, ds_id: str):
    result = await _call_kb_capability(request, "sync_data_source", {"ds_id": ds_id})
    return success_response(data=result)


@router.post("/data-sources/{ds_id}/reset-ingest-key", summary="重置入站推送 Key")
async def reset_ingest_key(request: Request, ds_id: str):
    result = await _call_kb_capability(request, "reset_ingest_key", {"ds_id": ds_id})
    return success_response(data=result)






@router.get("/parser-settings", summary="解析引擎设置列表")
async def list_parser_settings(
    request: Request,
    knowledge_base_id: str = Query(..., min_length=1, max_length=128, description="知识库 ID"),
):
    result = await _call_kb_capability(request, "list_parser_settings", {"knowledge_base_id": knowledge_base_id})
    return success_response(data=result)


@router.post("/parser-settings", summary="创建解析引擎设置")
async def create_parser_setting(request: Request, payload: dict = Body(...)):
    result = await _call_kb_capability(request, "create_parser_setting", payload)
    return success_response(data=result)


@router.patch("/parser-settings/{setting_id}", summary="更新解析引擎设置")
async def update_parser_setting(request: Request, setting_id: str, payload: dict = Body(...)):
    payload["setting_id"] = setting_id
    result = await _call_kb_capability(request, "update_parser_setting", payload)
    return success_response(data=result)


@router.delete("/parser-settings/{setting_id}", summary="删除解析引擎设置")
async def delete_parser_setting(request: Request, setting_id: str):
    result = await _call_kb_capability(request, "delete_parser_setting", {"setting_id": setting_id})
    return success_response(data=result)






ingest_router = APIRouter()


async def _call_kb_capability_ingest(
    ds_id: str,
    ingest_key: str,
    *,
    storage_key: str,
    file_name: str,
    mime_type: Optional[str],
    file_size: int,
    external_id: Optional[str],
) -> dict:

    from jonex_core.common.crypto import decode_ingest_key
    key_info = decode_ingest_key(ingest_key) or {}

    if key_info.get("ds_id") and key_info["ds_id"] != ds_id:
        raise InvalidApiKeyError(message="ingest key does not match the data source")
    tenant_id = key_info.get("tenant_id")
    if not tenant_id:
        raise InvalidApiKeyError(message="Invalid ingest key")
    config = get_config()
    sidecar_payload = {
        "capability_id": "business.knowledge_base.v1",
        "tenant_id": tenant_id,
        "payload": {
            "action": "ingest_push",
            "data": {
                "ds_id": ds_id,
                "ingest_key": ingest_key,
                "storage_key": storage_key,
                "file_name": file_name,
                "mime_type": mime_type,
                "file_size": file_size,
                "external_id": external_id,
            },
        },
    }
    headers = {"X-API-Key": config.SIDECAR_API_KEY}
    timeout = float(os.getenv("GATEWAY_SIDECAR_TIMEOUT", "120"))
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{config.SIDECAR_URL}/invoke", json=sidecar_payload, headers=headers)
    result = resp.json()
    if resp.status_code != 200 or not result.get("success", False):
        code = int(result.get("code") or CapabilityInvokeError.code)
        raise get_exception_class(code)(message=result.get("message") or "推送入库失败")
    return result.get("data") or {}


@ingest_router.post("/ingest/{ds_id}", summary="外部推送文档入库（API 开放）")
async def ingest_push(
    request: Request,
    ds_id: str,
    file: UploadFile = File(...),
    x_ingest_key: str = Header(..., alias="X-Ingest-Key"),
    external_id: Optional[str] = Form(None),
):
    content = await file.read()
    if not content:
        raise InvalidParameterError(message="The uploaded file must not be empty")
    file_name = file.filename or "unnamed"
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", file_name)
    doc_id = str(uuid4())
    prefix = os.getenv("COS_KEY_PREFIX", "jonex")

    storage_key = f"{prefix}/ingest/{ds_id}/{doc_id}/{doc_id}_{safe}"
    await get_object_storage().put_bytes(storage_key, content, content_type=file.content_type)

    result = await _call_kb_capability_ingest(
        ds_id,
        x_ingest_key,
        storage_key=storage_key,
        file_name=file_name,
        mime_type=file.content_type,
        file_size=len(content),
        external_id=external_id,
    )
    return success_response(data=result)


@ingest_router.get("/documents/{document_id}/raw", summary="原文查看（token 或 JWT 鉴权；302 / 本地流式 / 同源代理）")
async def get_raw_document(
    request: Request,
    document_id: str,
    token: Optional[str] = Query(None, description="短时查看 token（音视频/PDF/图片直连用）"),
    proxy: bool = Query(False, description="同源代理模式：COS 后端由网关流式透传字节，规避跨域 CSP/X-Frame-Options（PDF/文本 iframe 用）"),
):

    if token:
        info = verify_view_token(token)
        if not info or info.get("doc_id") != document_id:
            raise InvalidApiKeyError(message="查看票据无效或已过期")
        tenant_id = info["tenant_id"]
    else:

        tenant_id = extract_tenant_id(request)

    loc = await _call_kb_capability(
        request, "get_raw_location", {"document_id": document_id}, tenant_id=tenant_id
    )
    presigned = loc.get("presigned_url")
    if presigned:
        if proxy:


            range_header = request.headers.get("range")
            upstream_headers = {"Range": range_header} if range_header else {}
            client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=None), follow_redirects=True)
            upstream = await client.send(
                client.build_request("GET", presigned, headers=upstream_headers),
                stream=True,
            )
            resp_headers = {
                "Content-Disposition": "inline",
                "X-Content-Type-Options": "nosniff",
                "Accept-Ranges": upstream.headers.get("accept-ranges", "bytes"),
            }
            if "content-range" in upstream.headers:
                resp_headers["Content-Range"] = upstream.headers["content-range"]
            if "content-length" in upstream.headers:
                resp_headers["Content-Length"] = upstream.headers["content-length"]

            async def _stream_upstream():
                try:
                    async for chunk in upstream.aiter_bytes():
                        yield chunk
                finally:
                    await upstream.aclose()
                    await client.aclose()

            return StreamingResponse(
                _stream_upstream(),
                status_code=upstream.status_code,
                media_type=_safe_inline_media_type(loc.get("mime_type")),
                headers=resp_headers,
            )

        return RedirectResponse(url=presigned, status_code=302)


    storage_key = loc.get("storage_key")
    backend = (loc.get("storage_backend") or "local").strip().lower()
    fs_path = get_object_storage_for(backend).fs_path(storage_key) if storage_key else None
    if not fs_path or not os.path.exists(fs_path):
        raise InvalidParameterError(message="文档原文不存在或不可访问")
    return FileResponse(
        path=fs_path,
        media_type=_safe_inline_media_type(loc.get("mime_type")),
        filename=loc.get("file_name") or None,
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )
