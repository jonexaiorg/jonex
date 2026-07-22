#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Knowledge base API route (thin access layer)

Authentication uses router-level require_auth_header (Authorization: Bearer).
tenant_id is extracted from the Bearer token (token format jonex_test_{tenant_id}).
"""

import os
import uuid
from pathlib import Path
from typing import Optional

import jwt
from fastapi import APIRouter, Body, Depends, File, Form, Query, Request, UploadFile

from jonex_core.common import (
    CapabilityInvokeError,
    InvalidParameterError,
    get_config,
    get_logger,
    success_response,
)
from api_gateway.deps import require_auth_header

logger = get_logger("api_knowledge_base")

router = APIRouter(dependencies=[Depends(require_auth_header)])


# ==================== Tool functions ====================
def _extract_tenant(request: Request) -> str:
    """Extract tenant_id from Authorization: Bearer <token>

    Token format: Bearer jonex_test_{tenant_id} -> tenant_id
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        if token.startswith("jonex_test_"):
            return token.replace("jonex_test_", "") or "default"
    return "default_tenant"


def _extract_user_id(request: Request) -> str | None:
    """Extract user ID from JWT token (sub field)

    Parse the JWT in Authorization: Bearer <token> and return the sub field as user_id.
    Returns None if decoding fails (e.g. test token jonex_test_xxx); Sidecar will fall back to extraction.
    """
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


def _save_to_storage(file: UploadFile, tenant_id: str, content: bytes) -> str:
    """File persistence: write to atomic-rag shared inputs volume"""
    base_dir = Path(os.getenv("KB_INPUT_DIR", "/app/inputs"))
    tenant_dir = base_dir / tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)

    safe_name = file.filename or "unnamed"
    dest = tenant_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"
    dest.write_bytes(content)
    return str(dest)


# ==================== Sidecar invocation tool ====================
async def _call_kb_capability(
    request: Request,
    action: str,
    payload: dict,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    Invoke knowledge base capability via Sidecar

    Args:
        request: FastAPI Request object
        action: Capability operation type
        payload: Capability invocation parameters
        tenant_id: Tenant ID (auto-extracted from request headers if not provided)
        user_id: User ID (auto-extracted from request headers if not provided)
    """
    import httpx

    config = get_config()
    sidecar_url = config.SIDECAR_URL
    request_id = getattr(request.state, "request_id", "")
    tenant_id = tenant_id or _extract_tenant(request)
    user_id = user_id or _extract_user_id(request)

    sidecar_payload: dict = {
        "capability_id": "business.knowledge_base.v1",
        "payload": {
            "action": action,
            "data": payload,
        },
        "tenant_id": tenant_id,
    }
    if user_id:
        sidecar_payload["user_id"] = user_id

    logger.info(f"Invoke Sidecar: action={action}, tenant={tenant_id}, sidecar={sidecar_url}")

    headers = {
        "X-API-Key": "jonex_test_gateway",
        "X-Request-ID": request_id,
        "X-Tenant-ID": tenant_id,
    }

    try:
        timeout = float(os.getenv("GATEWAY_SIDECAR_TIMEOUT", "120"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{sidecar_url}/invoke",
                json=sidecar_payload,
                headers=headers,
            )
            result = response.json()

            if response.status_code != 200 or not result.get("success", False):
                # Extract root cause error, avoid exposing nested chain to users
                raw_msg = result.get("message", "") or ""
                # Trim nested prefixes: e.g. "Execution failed: RAG ingestion submission failed: Server error '500..." -> "RAG service returned 500"
                friendly = raw_msg
                if "RAG ingestion submission failed" in raw_msg:
                    friendly = f"RAG parsing service error"
                elif "Capability service unavailable" in raw_msg:
                    friendly = f"RAG parsing service not ready"
                elif "Capability service not configured" in raw_msg:
                    friendly = f"RAG parsing service not configured"
                elif "Internal service authentication failed" in raw_msg:
                    friendly = f"Inter-service authentication failed"
                elif "Invalid token" in raw_msg or "MissingApiKeyError" in raw_msg:
                    friendly = f"Authentication failed"
                elif "Invocation timed out" in raw_msg:
                    friendly = f"RAG service invocation timed out"
                logger.error(
                    f"Sidecar invocation failed: action={action}, code={result.get('code')}, "
                    f"message={friendly}"
                )
                raise CapabilityInvokeError(
                    message=friendly,
                    details={"action": action, "status_code": response.status_code},
                )

            logger.info(f"Sidecar invocation succeeded: action={action}")
            return result.get("data", {})

    except httpx.TimeoutException:
        raise CapabilityInvokeError(message=f"RAG service invocation timed out")
    except CapabilityInvokeError:
        raise
    except Exception as e:
        logger.error(f"Sidecar invocation error: action={action}, error={e}")
        raise CapabilityInvokeError(
            message=f"RAG service unavailable",
            details={"action": action},
        )


# ==================== API Interface ====================
@router.get("/search/overview", summary="Knowledge search overview statistics")
async def get_search_overview(request: Request):
    """Get 4 summary card data for homepage"""
    tenant_id = _extract_tenant(request)
    result = await _call_kb_capability(request, "get_search_overview", {}, tenant_id)
    return success_response(data=result)


# ==================== Search history interface ====================

@router.get("/search/history", summary="Query search history")
async def list_search_history(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    """Query search history of current tenant and current user"""
    tenant_id = _extract_tenant(request)
    user_id = _extract_user_id(request)
    result = await _call_kb_capability(
        request,
        "list_search_history",
        {"user_id": user_id, "limit": limit, "offset": offset},
        tenant_id=tenant_id,
        user_id=user_id,
    )
    return success_response(data=result)


@router.post("/search/history", summary="Save search history")
async def save_search_history(request: Request, payload: dict = Body(...)):
    """Save a search history entry (called by frontend after streaming search completes)"""
    tenant_id = _extract_tenant(request)
    user_id = _extract_user_id(request)
    capability_payload = {
        "user_id": user_id,
        "query": payload.get("query"),
        "domain_id": payload.get("domainId") or payload.get("domain_id") or "all",
        "domain_name": payload.get("domain") or payload.get("domainName") or payload.get("domain_name"),
        "mode": payload.get("mode") or "hybrid",
        "top_k": payload.get("topK") or payload.get("top_k") or 5,
        "status": payload.get("status") or "done",
        "answer_preview": payload.get("answerPreview") or payload.get("answer_preview"),
        "reference_count": payload.get("referenceCount") or payload.get("reference_count") or 0,
        "result_count": payload.get("resultCount") or payload.get("result_count") or 0,
        "duration_ms": payload.get("durationMs") or payload.get("duration_ms"),
        "extra_metadata": payload.get("extraMetadata") or payload.get("extra_metadata") or {},
    }
    result = await _call_kb_capability(
        request, "save_search_history", capability_payload,
        tenant_id=tenant_id, user_id=user_id,
    )
    return success_response(data=result)


@router.delete("/search/history/{history_id}", summary="Delete single search history")
async def delete_search_history(request: Request, history_id: str):
    """Soft delete specified search history"""
    tenant_id = _extract_tenant(request)
    user_id = _extract_user_id(request)
    result = await _call_kb_capability(
        request,
        "delete_search_history",
        {"user_id": user_id, "history_id": history_id},
        tenant_id=tenant_id,
        user_id=user_id,
    )
    return success_response(data=result)


@router.delete("/search/history", summary="Clear search history")
async def clear_search_history(request: Request):
    """Clear all search history of current tenant and user (soft delete)"""
    tenant_id = _extract_tenant(request)
    user_id = _extract_user_id(request)
    result = await _call_kb_capability(
        request,
        "clear_search_history",
        {"user_id": user_id},
        tenant_id=tenant_id,
        user_id=user_id,
    )
    return success_response(data=result)


# ==================== Document interface ====================

@router.get("/documents", summary="List documents")
async def get_documents(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Status filter"),
):
    """List documents"""
    tenant_id = _extract_tenant(request)
    payload = {
        "status": status,
        "offset": (page - 1) * page_size,
        "limit": page_size,
    }
    result = await _call_kb_capability(request, "list", payload, tenant_id)
    return success_response(data=result)


@router.get("/documents/search", summary="Semantic search documents (RAG-based)")
@router.post("/documents/search", summary="Semantic search documents (RAG-based)")
async def search_documents(
    request: Request,
    query: str = Query(..., description="Query"),
    mode: str = Query("hybrid", description="Search mode: naive/local/global/hybrid"),
    top_k: int = Query(5, ge=1, le=50, description="Result count"),
):
    """Semantic search documents"""
    tenant_id = _extract_tenant(request)
    payload = {
        "query": query,
        "mode": mode,
        "top_k": top_k,
    }
    result = await _call_kb_capability(request, "query", payload, tenant_id)
    return success_response(data=result)


@router.get("/documents/search/enhanced", summary="Enhanced semantic search (RAG + ontology instances)")
async def search_documents_enhanced(
    request: Request,
    query: str = Query(..., description="Query"),
    kb_id: Optional[str] = Query(None, alias="knowledge_base_id", description="Knowledge base ID"),
    mode: str = Query("hybrid", description="Search mode: naive/local/global/hybrid"),
    top_k: int = Query(5, ge=1, le=50, description="Result count"),
):
    """RAG query + ontology instance enhancement, returns structured results"""
    tenant_id = _extract_tenant(request)
    payload = {
        "query": query,
        "mode": mode,
        "top_k": top_k,
        "knowledge_base_id": kb_id,
    }
    result = await _call_kb_capability(request, "query_with_ontology", payload, tenant_id)
    return success_response(data=result)


@router.get("/documents/search/stream", summary="Streaming semantic search documents (OpenAI-compatible streaming format)")
async def search_documents_stream(
    request: Request,
    query: str = Query(..., description="Query"),
    mode: str = Query("hybrid", description="Search mode: naive/local/global/hybrid"),
    top_k: int = Query(5, ge=1, le=50, description="Result count"),
    domain_id: Optional[str] = Query(None, description="Domain ID"),
):
    """Streaming semantic search, returns OpenAI-compatible SSE stream (delta format)"""
    from fastapi.responses import StreamingResponse
    import httpx
    import json
    import time
    import uuid
    import re

    config = get_config()
    sidecar_url = config.SIDECAR_URL
    tenant_id = _extract_tenant(request)
    stream_params = {"query": query, "mode": mode, "top_k": top_k}
    if domain_id and domain_id != "all":
        stream_params["domain_id"] = domain_id

    # Pre-compile regex: extract content from {"response":"..."} (avoid json.loads per-token parsing)
    _RESPONSE_RE = re.compile(r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"')

    async def _generate():
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())

        _base_choice = {"index": 0, "delta": {}, "finish_reason": None}
        _base_payload = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": "lightrag",
            "choices": [None],
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "GET",
                    f"{sidecar_url}/invoke/stream/rag",
                    params=stream_params,
                    headers={"X-API-Key": "jonex_test_gateway"},
                ) as resp:
                    resp.raise_for_status()

                    # After upstream connection succeeds, send the first chunk (role declaration)
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
                                refs_text = "\n".join(
                                    f"- {r.get('file_path', '')}" for r in data["references"]
                                )
                                choice = dict(_base_choice)
                                choice["delta"] = {"content": refs_text + "\n\n"}
                                _base_payload["choices"][0] = choice
                                yield f"data: {json.dumps(_base_payload, ensure_ascii=False)}\n\n"

            # Normal end
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
                "delta": {"content": f"Search service temporarily unavailable: {e}"},
                "finish_reason": "error",
            }
            _base_payload["choices"][0] = error_choice
            yield f"data: {json.dumps(_base_payload, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.get("/documents/{document_id}", summary="Get document detail (lazy reconciliation)")
async def get_document_detail(
    request: Request,
    document_id: str,
):
    """Get document detail (auto-trigger reconciliation in capability layer)"""
    tenant_id = _extract_tenant(request)
    payload = {"doc_id": document_id}
    result = await _call_kb_capability(request, "get", payload, tenant_id)
    return success_response(data=result)


@router.post("/documents/upload", summary="Upload document")
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="Uploaded file"),
    knowledge_base_id: Optional[str] = Form(None, description="Knowledge base ID"),
):
    """
    Upload document

    Flow: Gateway persists file → pass file_path to capability layer → capability layer writes DB + invokes RAG
    """
    if not file.filename:
        raise InvalidParameterError(message="Missing file name")

    tenant_id = _extract_tenant(request)
    content = await file.read()
    file_path = _save_to_storage(file, tenant_id, content)

    payload = {
        "file_name": file.filename,
        "file_path": file_path,
        "file_size": len(content),
        "mime_type": file.content_type,
    }
    if knowledge_base_id:
        payload["knowledge_base_id"] = knowledge_base_id
    result = await _call_kb_capability(request, "upload", payload, tenant_id)
    return success_response(data=result)


# ==================== Parse result（LightRAG storage reader） ====================

@router.get("/bases/{kb_id}/parse-result/summary", summary="Knowledge base parse result summary")
async def get_parse_result_summary(request: Request, kb_id: str):
    tenant_id = _extract_tenant(request)
    payload = {"knowledge_base_id": kb_id}
    result = await _call_kb_capability(request, "get_parse_result_summary", payload, tenant_id)
    return success_response(data=result)


@router.get("/bases/{kb_id}/parse-result/documents", summary="Knowledge base parse result documents")
async def get_parse_result_documents(
    request: Request,
    kb_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    tenant_id = _extract_tenant(request)
    payload = {
        "knowledge_base_id": kb_id,
        "page": page,
        "page_size": page_size,
    }
    if keyword:
        payload["keyword"] = keyword
    if status:
        payload["status"] = status
    result = await _call_kb_capability(request, "get_parse_result_documents", payload, tenant_id)
    return success_response(data=result)


@router.get("/bases/{kb_id}/parse-result/entities", summary="Knowledge base parse result entities")
async def get_parse_result_entities(
    request: Request,
    kb_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    file_path: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
):
    tenant_id = _extract_tenant(request)
    payload = {
        "knowledge_base_id": kb_id,
        "page": page,
        "page_size": page_size,
    }
    if keyword:
        payload["keyword"] = keyword
    if entity_type:
        payload["entity_type"] = entity_type
    if file_path:
        payload["file_path"] = file_path
    if document_id:
        payload["document_id"] = document_id
    result = await _call_kb_capability(request, "get_parse_result_entities", payload, tenant_id)
    return success_response(data=result)


@router.get("/bases/{kb_id}/parse-result/relationships", summary="Knowledge base parse result relationships")
async def get_parse_result_relationships(
    request: Request,
    kb_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    file_path: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    source_entity: Optional[str] = Query(None),
    target_entity: Optional[str] = Query(None),
):
    tenant_id = _extract_tenant(request)
    payload = {
        "knowledge_base_id": kb_id,
        "page": page,
        "page_size": page_size,
    }
    if keyword:
        payload["keyword"] = keyword
    if file_path:
        payload["file_path"] = file_path
    if document_id:
        payload["document_id"] = document_id
    if source_entity:
        payload["source_entity"] = source_entity
    if target_entity:
        payload["target_entity"] = target_entity
    result = await _call_kb_capability(request, "get_parse_result_relationships", payload, tenant_id)
    return success_response(data=result)


@router.get("/bases/{kb_id}/parse-result/graph-summary", summary="Knowledge base graph summary")
async def get_parse_result_graph_summary(request: Request, kb_id: str):
    tenant_id = _extract_tenant(request)
    payload = {"knowledge_base_id": kb_id}
    result = await _call_kb_capability(request, "get_parse_result_graph_summary", payload, tenant_id)
    return success_response(data=result)


@router.get("/bases/{kb_id}/parse-result/graph", summary="Knowledge base graph data")
async def get_parse_result_graph(
    request: Request,
    kb_id: str,
    limit: int = Query(200, ge=1, le=1000),
    keyword: Optional[str] = Query(None),
    file_path: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
):
    tenant_id = _extract_tenant(request)
    payload = {
        "knowledge_base_id": kb_id,
        "limit": limit,
    }
    if keyword:
        payload["keyword"] = keyword
    if file_path:
        payload["file_path"] = file_path
    if document_id:
        payload["document_id"] = document_id
    result = await _call_kb_capability(request, "get_parse_result_graph", payload, tenant_id)
    return success_response(data=result)


@router.get("/documents/{doc_id}/parse-result", summary="Single document parse result")
async def get_document_parse_result_route(request: Request, doc_id: str):
    tenant_id = _extract_tenant(request)
    payload = {"knowledge_base_id": doc_id}
    result = await _call_kb_capability(request, "get_document_parse_result", payload, tenant_id)
    return success_response(data=result)


@router.delete("/documents/{document_id}", summary="Delete document (soft delete)")
async def delete_document(
    request: Request,
    document_id: str,
):
    """Delete document (soft delete)"""
    tenant_id = _extract_tenant(request)
    payload = {"doc_id": document_id}
    result = await _call_kb_capability(request, "delete", payload, tenant_id)
    return success_response(data=result)


# ==================== QA interface (synonymous with search, for frontend compatibility) ====================
@router.post("/qa/ask", summary="Q&A query (RAG-based)")
async def qa_ask(
    request: Request,
    question: str = Body(..., embed=True, description="Question"),
    mode: str = Body("hybrid", embed=True, description="Search mode"),
    top_k: int = Body(5, embed=True, description="Search count"),
):
    """Q&A query"""
    tenant_id = _extract_tenant(request)
    payload = {
        "query": question,
        "mode": mode,
        "top_k": top_k,
    }
    result = await _call_kb_capability(request, "query", payload, tenant_id)
    return success_response(data=result)
