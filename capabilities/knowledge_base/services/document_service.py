"""Document application service for Knowledge Base."""

import logging
import os
from typing import Any, Optional

from sqlalchemy import and_, delete, or_, select

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common.audit import schedule_emit
from jonex_core.common.audit_enums import ResourceType
from jonex_core.common.database import get_db_session
from jonex_core.common.file_source_util import parse_file_source
from jonex_core.common.exceptions import (
    InvalidParameterError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from jonex_core.common.i18n import translate
from jonex_core.common.neo4j_client import get_neo4j_driver
from jonex_core.common.object_storage import build_object_key, get_object_storage, get_object_storage_for
from jonex_core.common.tenant import require_tenant

from ..models import DocStatus, DocumentTag, KnowledgeDocument, OntologyStatus
from ..models.data_source import KnowledgeDataSource
from ..repository import FolderRepository, KnowledgeDocumentRepository, OntologyGraphRepository
from ..dtos import DocumentListRequest, DocumentScopeRequest, DocumentUploadRequest, SetDocumentFolderRequest

logger = logging.getLogger(__name__)


# [jonex] 线性状态（phase）→ SQLAlchemy 谓词。单一事实来源，供 list_documents 与
# documents_stats 复用。与前端 deriveDocPhase / 设计文档 §4.1 表一致。
_PHASE_PREDICATE = {
    "pending_parse":   lambda: KnowledgeDocument.status == DocStatus.PENDING.value,
    "parsing":         lambda: KnowledgeDocument.status == DocStatus.PARSING.value,
    "ingesting":       lambda: KnowledgeDocument.status == DocStatus.INGESTING.value,
    "parse_failed":    lambda: KnowledgeDocument.status == DocStatus.FAILED.value,
    "pending_compile": lambda: and_(
        KnowledgeDocument.status == DocStatus.READY.value,
        KnowledgeDocument.ontology_status == OntologyStatus.PENDING.value,
    ),
    "compiling": lambda: and_(
        KnowledgeDocument.status == DocStatus.READY.value,
        KnowledgeDocument.ontology_status == OntologyStatus.EXTRACTING.value,
    ),
    "compiled": lambda: and_(
        KnowledgeDocument.status == DocStatus.READY.value,
        KnowledgeDocument.ontology_status == OntologyStatus.READY.value,
    ),
    "compile_failed": lambda: and_(
        KnowledgeDocument.status == DocStatus.READY.value,
        KnowledgeDocument.ontology_status == OntologyStatus.FAILED.value,
    ),
}


def _phase_condition(phases: Optional[list[str]]):
    """多值 phase → OR-of-AND 谓词；无有效 phase 返回 None。"""
    if not phases:
        return None
    preds = [_PHASE_PREDICATE[p]() for p in phases if p in _PHASE_PREDICATE]
    if not preds:
        return None
    return or_(*preds) if len(preds) > 1 else preds[0]


def _file_ext(file_name: str) -> str:
    """取文件名的小写扩展名（不含点），无扩展名返回空串。例：'a.MP4' → 'mp4'。"""
    return os.path.splitext(file_name or "")[1].lower().lstrip(".")


def _normalize_parser_exts(file_types: Any) -> set[str]:
    """把 parser_configs.file_types 归一为小写扩展名集合（不含点）。

    值可能是 list（JSONB 已反序列化）或 JSON 字符串；元素如 'MP4' / '.mp4' → 'mp4'。
    """
    raw = file_types
    if raw is None:
        return set()
    if isinstance(raw, str):
        import json
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return set()
    if not isinstance(raw, list):
        return set()
    return {str(v).strip().lower().lstrip(".") for v in raw if str(v).strip()}


def _payload(model_or_dict: Any) -> dict[str, Any]:
    if isinstance(model_or_dict, dict):
        return model_or_dict
    if hasattr(model_or_dict, "model_dump"):
        return model_or_dict.model_dump(exclude_none=True)
    return model_or_dict.dict(exclude_none=True)


def _audit_user_id(user_id: Optional[str]) -> Optional[int]:
    """安全的将 invoke 链路中的字符串 user_id 转为 int"""
    if user_id and user_id.isdigit():
        return int(user_id)
    return None


class DocumentService:
    """Tenant-scoped document metadata and RAG ingestion orchestration."""

    # 手动上传归属的数据源接入类型
    _FILE_ACCESS_TYPE = "file"

    async def _require_file_data_source_id(self, tenant_id: str, kb_id: str) -> str:
        """返回该 KB 的「文件上传」(file) 数据源 id；不存在则报错。

        手动上传要求知识库已配置 file 数据源（通过数据源管理创建）。上传服务只做
        归属，不在上传时隐式创建数据源——能调用上传即意味着该数据源应已存在。
        """
        async with get_db_session() as session:
            ds = (
                await session.execute(
                    select(KnowledgeDataSource)
                    .where(
                        KnowledgeDataSource.tenant_id == tenant_id,
                        KnowledgeDataSource.knowledge_base_id == kb_id,
                        KnowledgeDataSource.access_type == self._FILE_ACCESS_TYPE,
                        KnowledgeDataSource.is_deleted == 0,
                    )
                    .limit(1)
                )
            ).scalar_one_or_none()
        if ds is None:
            raise ResourceNotFoundError(
                message=translate("err.kb.no_file_datasource", fallback="该知识库未配置「文件上传」数据源，请先在数据源设置中添加后再上传")  ,  # 原消息
                details={"knowledge_base_id": kb_id, "access_type": self._FILE_ACCESS_TYPE},
            )
        return ds.id

    async def _resolve_parser_preset(self, tenant_id: str, kb_id: str, file_name: str) -> tuple[str, Optional[str]]:
        """按文件后缀在该 KB 已配置的解析器中定位，返回 active 的 parser_config_id
        （= raganything preset name）。

        解析逻辑：文件后缀 → 命中"某个已选中解析器声明的 file_types"。KB 每个
        parser_type 类目选一个解析器（knowledge_parser_settings），解析器的 file_types
        （business_domain.parser_configs）是"后缀 → 解析器"的唯一事实来源，无需任何
        扩展名词表映射。

        严格模式：定位不到有效解析器 → 抛 InvalidParameterError。调用方据此把文档标记为
        解析失败、保留记录、不推送到 atomic-rag。

        触发报错的情形：
          - 文件无扩展名；
          - 该 KB 没有任何 active 解析设置绑定的 active 解析器的 file_types 覆盖该后缀。
        """
        from sqlalchemy import text as _sql_text

        ext = _file_ext(file_name)
        if not ext:
            raise InvalidParameterError(
                message=translate("err.doc.no_extension", params={"file_name": file_name}, fallback=f"文件缺少扩展名，无法定位解析器：{file_name}")  ,  # 原消息
                details={"file_name": file_name, "knowledge_base_id": kb_id},
            )

        async with get_db_session() as session:
            # 该 KB 的 active 解析设置 join 其选中的 active 解析器，取出 file_types
            rows = (
                await session.execute(
                    _sql_text(
                        "SELECT pc.id AS parser_config_id, pc.file_types AS file_types, "
                        "       ps.prompt_config_id AS prompt_config_id "
                        "FROM knowledge_base.knowledge_parser_settings ps "
                        "JOIN business_domain.parser_configs pc "
                        "  ON pc.id = ps.parser_config_id "
                        " AND pc.tenant_id = ps.tenant_id "
                        " AND pc.is_deleted = 0 "
                        " AND pc.status = 'active' "
                        "WHERE ps.tenant_id = :tid "
                        "  AND ps.knowledge_base_id = :kb "
                        "  AND ps.is_deleted = 0 "
                        "  AND ps.status = 'active' "
                        "  AND ps.parser_config_id IS NOT NULL"
                    ),
                    {"tid": tenant_id, "kb": kb_id},
                )
            ).fetchall()

        for row in rows:
            if ext in _normalize_parser_exts(row.file_types):
                # 返回 (parser_config_id, prompt_config_id)；后者用于解析时下发 prompt_ids
                return row.parser_config_id, row.prompt_config_id

        raise InvalidParameterError(
            message=translate("err.kb.no_parser_for_ext", params={"ext": ext}, fallback=f"该知识库未配置支持「.{ext}」文件的解析器，请先在解析设置中配置后再上传")  ,  # 原消息
            details={"knowledge_base_id": kb_id, "file_ext": ext, "file_name": file_name},
        )

    async def upload_document(self, tenant_id: str, request: DocumentUploadRequest | dict, *, user_id: Optional[str] = None, username: Optional[str] = None, ip: Optional[str] = None) -> dict:
        tenant_id = require_tenant(tenant_id)
        data = _payload(request)
        req = DocumentUploadRequest(**data)
        metadata = dict(req.metadata or {})

        # 统一来源标记：未显式归属（即手动上传，同步/推送路径已自带 data_source_id）时，
        # 归属到该 KB 已存在的 file 数据源；不存在则报错，不隐式创建。
        if not metadata.get("data_source_id"):
            metadata["data_source_id"] = await self._require_file_data_source_id(tenant_id, req.knowledge_base_id)
            metadata.setdefault("source", self._FILE_ACCESS_TYPE)
        # 冗余真实列：文档来源方式（file / api / storage / api_push），文档数统计按此列分组
        data_source_type = metadata.get("source")

        storage_key = req.storage_key or req.file_path
        storage_backend = req.storage_backend
        # 未显式指定存储后端时，从环境变量自动推断
        if storage_backend == "local" and os.getenv("OBJECT_STORAGE_BACKEND", "local") == "cos":
            storage_backend = "cos"

        # file_path 由存储后端统一推导（下游 atomic-rag 解析用）：
        #  - 对象存储后端（cos 等）：通过 storage_key 下载，file_path 仅作标识 → 用 storage_key；
        #  - local 后端：解析需可直接读取的绝对路径，由对象存储后端把 key 解析为共享卷绝对路径。
        if storage_backend == "cos":
            file_path = req.file_path or storage_key
        else:
            file_path = get_object_storage().fs_path(storage_key) or req.file_path or storage_key

        doc_id = req.doc_id or None  # 预生成 doc_id（COS 直传模式），None 则自动 UUID
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.create(
                KnowledgeDocument(
                    id=doc_id,
                    tenant_id=tenant_id,
                    file_name=req.file_name,
                    file_path=file_path,
                    file_size=req.file_size,
                    mime_type=req.mime_type,
                    knowledge_base_id=req.knowledge_base_id,
                    storage_backend=storage_backend,
                    storage_key=storage_key,
                    status=DocStatus.PARSING.value,
                    ontology_status=OntologyStatus.PENDING.value,
                    folder_id=req.folder_id,
                    extra_metadata=metadata,
                    data_source_type=data_source_type,
                )
            )
            doc_id = doc.id
            doc_dict = doc.to_dict()

        uid = _audit_user_id(user_id)
        schedule_emit({
            "tenant_id": tenant_id,
            "user_id": uid,
            "username": username,
            "ip": ip,
            "log_type": "OPERATION",
            "action": "document.upload",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": ResourceType.DOCUMENT.value,
            "resource_id": str(doc_id),
            "request_params": {"file_name": req.file_name, "knowledge_base_id": req.knowledge_base_id},
        })
        schedule_emit({
            "tenant_id": tenant_id,
            "user_id": uid,
            "username": username,
            "ip": ip,
            "log_type": "TASK",
            "action": "document.parse",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": ResourceType.DOCUMENT.value,
            "resource_id": str(doc_id),
        })

        # COS 后端：确认对象已存在后再入队解析，避免竞态（D9）
        if storage_backend == "cos":
            exists = await get_object_storage().head_object(storage_key)
            if not exists:
                raise ResourceNotFoundError(
                    message=translate("err.cos.object_not_found", params={"storage_key": storage_key}, fallback=f"COS 对象不存在或上传未完成: {storage_key}")  ,  # 原消息
                    details={"storage_key": storage_key},
                )

        # Ensure compiled schema exists for this KB (non-blocking)
        schema = None
        schema_version = 0
        try:
            from .ontology_compiler import OntologyCompiler
            compiler = OntologyCompiler()
            schema = await compiler.get_compiled_schema(tenant_id, req.knowledge_base_id, auto_compile=True)
            if schema is None:
                logger.warning("No compiled schema available for KB %s after auto-compile", req.knowledge_base_id)
            else:
                schema_version = int(schema.get("schema_version", 0) or 0)
        except Exception as exc:
            logger.warning("Failed to ensure compiled schema for KB %s: %s", req.knowledge_base_id, exc)

        try:
            # 按文件类型解析该 KB 配置的解析器 preset。解析不到（类型不支持 / 未配置 /
            # 解析器非 active）会抛 InvalidParameterError，落入下方 except：文档标记为
            # 解析失败、保留记录、不推送到 atomic-rag。
            preset, prompt_config_id = await self._resolve_parser_preset(
                tenant_id, req.knowledge_base_id, req.file_name
            )
            # [jonex] 主解析提示词下发：该类目关联了 prompt 配置则带上 prompt_ids
            prompt_ids = [prompt_config_id] if prompt_config_id else []

            rag_result = await get_rag_client().insert(
                file_path=file_path,
                tenant_id=tenant_id,
                knowledge_base_id=req.knowledge_base_id,
                document_id=doc_id,
                ontology_schema=schema,           # [jonex] push compiled schema 到抽取链路
                storage_backend=storage_backend,  # P3: COS 本地后端
                storage_key=storage_key,
                preset=preset,                    # KB 按文件类型选择的解析器（v2 preset 链路）
                prompt_ids=prompt_ids,            # KB 主解析提示词
                schema_version=schema_version,    # [jonex] P1-E：供对账写图前 fencing
            )
        except Exception as exc:
            logger.exception("Knowledge document ingestion failed: %s", doc_id)
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                doc = await repo.get_required(doc_id, tenant_id)
                await repo.set_status(doc, DocStatus.FAILED, error_message=str(exc))
                doc_dict = doc.to_dict()
            schedule_emit({
                "tenant_id": tenant_id,
                "user_id": uid,
                "username": username,
                "ip": ip,
                "log_type": "TASK",
                "action": "document.parse_failed",
                "outcome": "FAILED",
                "service_name": "knowledge_base",
                "resource": ResourceType.DOCUMENT.value,
                "resource_id": str(doc_id),
                "error_message": str(exc)[:1000],
            })
            return doc_dict

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(doc_id, tenant_id)
            status = DocStatus.READY if not rag_result.get("task_id") else DocStatus.PARSING
            await repo.set_status(
                doc,
                status,
                rag_task_id=rag_result.get("task_id"),
                rag_doc_ids=rag_result.get("doc_ids") or rag_result.get("document_ids") or [],
            )
            # [jonex] P1-E：记录本文档应归类到的目标 schema 版本
            if schema_version:
                doc.ontology_target_schema_version = schema_version
            doc.extra_metadata = {**(doc.extra_metadata or {}), "rag_result": rag_result}
            doc_dict = doc.to_dict()

        if status == DocStatus.READY:
            schedule_emit({
                "tenant_id": tenant_id,
                "user_id": uid,
                "username": username,
                "ip": ip,
                "log_type": "TASK",
                "action": "document.parse_done",
                "outcome": "SUCCESS",
                "service_name": "knowledge_base",
                "resource": ResourceType.DOCUMENT.value,
                "resource_id": str(doc_id),
            })

        return doc_dict

    async def generate_upload_url(
        self, tenant_id: str, kb_id: str, file_name: str, content_type: str | None = None,
    ) -> dict:
        """生成 COS 预签名 PUT URL 和 storage_key（D9）。

        前端/网关直传字节到 COS（不经 Sidecar 透传），
        然后再调 upload_document 传 storage_key 确认。
        """
        from uuid import uuid4

        tenant_id = require_tenant(tenant_id)
        doc_id = str(uuid4())
        storage_key = build_object_key(tenant_id, kb_id, doc_id, file_name)

        storage = get_object_storage()
        try:
            upload_url = await storage.presigned_put_url(storage_key, expires=300)
        except Exception:
            # local 后端不支持预签名 PUT 时降级
            upload_url = None

        return {
            "doc_id": doc_id,
            "storage_key": storage_key,
            "upload_url": upload_url,
            "storage_backend": os.getenv("OBJECT_STORAGE_BACKEND", "local"),
        }

    async def get_raw_location(self, tenant_id: str, document_id: str) -> dict:
        """获取文档原文位置信息（校验租户归属后返回）。

        统一 raw 入口：
        - 对象存储后端（cos）：返回 presigned_url，gateway 302 直跳（天然支持 Range/流式）；
        - local 后端：presigned_url 为空，返回 storage_key，gateway 用 FileResponse
          从共享卷流式返回（支持 Range，音视频可拖动/边下边播，不经 Sidecar 传字节）。
        """
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
        # 按文档自身的 storage_backend 选后端（混合数据时不能用全局 env 单例）
        backend = (doc.storage_backend or "local").strip().lower()
        presigned = ""
        if backend == "cos":
            presigned = await get_object_storage_for("cos").presigned_url(doc.storage_key, tenant_id)
        return {
            "storage_backend": backend,
            "storage_key": doc.storage_key,
            "mime_type": doc.mime_type or "application/octet-stream",
            "file_name": doc.file_name,
            "presigned_url": presigned or "",
        }

    async def get_raw_url(self, tenant_id: str, document_id: str) -> str:
        """获取文档原文的预签名 URL（校验租户归属后签名）。

        用于 GET /documents/{id}/raw 端点（302 重定向）。
        """
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
        storage = get_object_storage()
        return await storage.presigned_url(doc.storage_key, tenant_id)

    async def get_raw_content(self, tenant_id: str, document_id: str) -> dict:
        """获取文档原文的字节内容（本地回退，无预签名 URL 时使用）。

        返回 base64 编码的内容 + 元信息，供 gateway 代理文件下载。
        """
        import base64
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
        storage = get_object_storage()
        raw = await storage.get_bytes(doc.storage_key)
        return {
            "content": base64.b64encode(raw).decode("ascii"),
            "mime_type": doc.mime_type or "application/octet-stream",
            "file_name": doc.file_name,
        }

    async def get_document_chunks(self, tenant_id: str, document_id: str) -> dict:
        """按文档 id 查看 chunk 列表（含时间轴/页码等位置元数据）。

        校验租户归属后取文档所属 KB，经 RAGClient 调 atomic-rag v2 的 get_doc_chunks
        （→ LightRAGAdapterV2.get_doc_chunks → action `get_doc_chunks`）。
        doc_id 即 KB knowledge_documents.id，与 file_source 的 doc= 锚点一致。

        对每个 chunk 解析 file_path（file_source 字符串），提取 time_start/time_end
        （视频/音频时间轴）、page_no、char_start/end 等位置元数据，供前端渲染
        时间段标签和定位播放。
        """
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
        result = await get_rag_client().get_doc_chunks(
            document_id=document_id,
            knowledge_base_id=doc.knowledge_base_id,
            tenant_id=tenant_id,
        )
        # 对每个 chunk 解析 file_path，提取位置元数据（time_start/time_end 等）
        chunks = result.get("chunks") or []
        enriched = []
        for c in chunks:
            fp = c.get("file_path", "")
            parsed = parse_file_source(fp) if fp else {}
            enriched.append({
                **c,
                "time_start": parsed.get("time_start"),
                "time_end": parsed.get("time_end"),
                "page_no": parsed.get("page_no"),
                "char_start": parsed.get("char_start"),
                "char_end": parsed.get("char_end"),
                "chunk_index": parsed.get("chunk_index"),
            })
        return {
            "doc_id": result.get("doc_id", document_id),
            "total": len(enriched),
            "chunks": enriched,
        }

    async def get_chunk(self, tenant_id: str, document_id: str, chunk_id: str) -> dict:
        """按 chunk_id 精确直查单片内容（直连 LightRAG text_chunks，不拉整篇列表）。

        校验 doc 租户归属后，按 chunk_id 直查；再用 chunk 的 file_path `doc=` 锚点校验其确实
        归属于 document_id（防跨文档串取）。未命中抛 ResourceNotFoundError。只认 chunk_id。
        """
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)  # 租户+归属校验
        chunk = await get_rag_client().get_chunk_by_id(
            chunk_id=chunk_id,
            knowledge_base_id=doc.knowledge_base_id,
            tenant_id=tenant_id,
        )
        if not chunk:
            raise ResourceNotFoundError(
                message=translate("err.kb.chunk_not_found", params={"chunk_id": chunk_id},
                                  fallback=f"未找到 chunk: {chunk_id}"),
            )
        # 归属校验：chunk 的 file_path doc= 锚点须等于 document_id，避免跨文档串取
        parsed = parse_file_source(chunk.get("file_path", "")) or {}
        if parsed.get("doc_id") and parsed["doc_id"] != document_id:
            raise ResourceNotFoundError(
                message=translate("err.kb.chunk_not_found", params={"chunk_id": chunk_id},
                                  fallback=f"未找到 chunk: {chunk_id}"),
            )
        # 去除入库时注入的命名空间隔离标记 <!--yx:HASH-->，与 references 文本口径一致，不泄露给前端
        import re
        content = re.sub(
            r"\s*<!--yx:[0-9a-f]+-->\s*", "", chunk.get("content") or "",
        ).strip()
        return {
            "doc_id": document_id,
            "kb_id": doc.knowledge_base_id,
            "file_name": doc.file_name,
            "chunk_id": chunk.get("chunk_id") or chunk_id,
            "chunk_index": chunk.get("chunk_order_index"),
            "content": content,
            "page_idx": chunk.get("page_idx"),
            "line_start": chunk.get("line_start"),
            "line_end": chunk.get("line_end"),
        }

    async def reparse_document(
        self, tenant_id: str, document_id: str, *,
        user_id: Optional[str] = None, username: Optional[str] = None, ip: Optional[str] = None,
    ) -> dict:
        """按文档 id 重新解析（force_reparse）。

        复用文档已存的 storage_key / storage_backend / 所属 KB，重新走"按文件类型选 preset
        + 推送 compiled ontology schema"链路，经 atomic-rag `retry` action 强制重解析。
        与上传一致：preset 解析不到 → 文档标记解析失败、保留记录、不推送。
        """
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
            # [jonex] P0-I 互斥：正在解析/清理中（PARSING/PENDING）或删除中的文档拒绝重复 reparse，
            # 避免两个 reparse 并发用不同 old_ids 快照互删、旧代次覆盖新代次。
            if doc.status in (DocStatus.PARSING.value, DocStatus.PENDING.value, DocStatus.INGESTING.value):
                raise ResourceConflictError(message=translate("err.doc.parsing_or_cleaning", fallback="文档正在解析/入库中，请等待完成后再重新解析")  )  # 原消息)
            if doc.status == DocStatus.DELETING.value:
                raise ResourceConflictError(message=translate("err.doc.deleting_cannot_reparse", fallback="文档正在删除中，无法重新解析")  )  # 原消息)
            kb_id = doc.knowledge_base_id
            file_path = doc.file_path
            storage_key = doc.storage_key
            storage_backend = (doc.storage_backend or "local").strip().lower()
            file_name = doc.file_name
            # reparse 走严格全量替换：快照旧 rag_doc_ids（权威 old_ids 之一，另一半由 atomic-rag 现查）
            old_rag_doc_ids = list(doc.rag_doc_ids or [])
            # [jonex] P0-I：原子递增 reparse 代次；重置状态（reparse 期间 ontology 置 PENDING，
            # 代次变化会 fencing 掉在途 ontology-only 结果，实现 reparse↔ontology-only 互斥）
            new_generation = (doc.content_generation or 0) + 1
            doc.content_generation = new_generation
            doc.status = DocStatus.PARSING.value
            doc.ontology_status = OntologyStatus.PENDING.value
            doc.error_message = None
            await session.flush()
            doc_dict = doc.to_dict()

        uid = _audit_user_id(user_id)
        schedule_emit({
            "tenant_id": tenant_id,
            "user_id": uid,
            "username": username,
            "ip": ip,
            "log_type": "TASK",
            "action": "document.reparse",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": ResourceType.DOCUMENT.value,
            "resource_id": str(document_id),
        })

        # COS 后端：确认对象仍存在
        if storage_backend == "cos":
            exists = await get_object_storage().head_object(storage_key)
            if not exists:
                raise ResourceNotFoundError(
                    message=translate("err.cos.object_deleted", params={"storage_key": storage_key}, fallback=f"COS 对象不存在或已被删除: {storage_key}")  ,  # 原消息
                    details={"storage_key": storage_key},
                )

        # 确保 KB 编译 schema 存在（非阻塞）
        schema = None
        schema_version = 0
        try:
            from .ontology_compiler import OntologyCompiler
            schema = await OntologyCompiler().get_compiled_schema(tenant_id, kb_id, auto_compile=True)
            if schema:
                schema_version = int(schema.get("schema_version", 0) or 0)
        except Exception as exc:
            logger.warning("Failed to ensure compiled schema for KB %s: %s", kb_id, exc)

        try:
            preset, prompt_config_id = await self._resolve_parser_preset(tenant_id, kb_id, file_name)
            # [jonex] 主解析提示词下发：重解析同样带上当前配置
            prompt_ids = [prompt_config_id] if prompt_config_id else []
            rag_result = await get_rag_client().retry(
                file_path=file_path,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                document_id=document_id,
                ontology_schema=schema,
                storage_backend=storage_backend,
                storage_key=storage_key,
                preset=preset,
                prompt_ids=prompt_ids,
                # [jonex] 阶段4：严格全量替换 + 代次 fencing
                execution_mode="reparse_strict",
                strict_push=True,
                content_generation=new_generation,
                schema_version=schema_version,
                old_rag_doc_ids=old_rag_doc_ids,
            )
        except Exception as exc:
            logger.exception("Knowledge document reparse failed: %s", document_id)
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                doc = await repo.get_required(document_id, tenant_id)
                await repo.set_status(doc, DocStatus.FAILED, error_message=str(exc))
                doc_dict = doc.to_dict()
            schedule_emit({
                "tenant_id": tenant_id,
                "user_id": uid,
                "username": username,
                "ip": ip,
                "log_type": "TASK",
                "action": "document.parse_failed",
                "outcome": "FAILED",
                "service_name": "knowledge_base",
                "resource": ResourceType.DOCUMENT.value,
                "resource_id": str(document_id),
                "error_message": str(exc)[:1000],
            })
            return doc_dict

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
            status = DocStatus.READY if not rag_result.get("task_id") else DocStatus.PARSING
            await repo.set_status(
                doc,
                status,
                rag_task_id=rag_result.get("task_id"),
                rag_doc_ids=rag_result.get("doc_ids") or rag_result.get("document_ids") or [],
            )
            # [jonex] P1-E：reparse 也写目标 schema 版本
            if schema_version:
                doc.ontology_target_schema_version = schema_version
            doc.extra_metadata = {**(doc.extra_metadata or {}), "rag_result": rag_result}
            doc_dict = doc.to_dict()
        return doc_dict

    async def list_documents(self, tenant_id: str, request: DocumentListRequest | dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = DocumentListRequest(**_payload(request))
        offset = (req.page - 1) * req.page_size

        conditions = []
        phase_cond = _phase_condition(req.phase)
        if phase_cond is not None:
            # phase 优先：线性状态多选，翻译为 (status, ontology_status) 谓词
            conditions.append(phase_cond)
        else:
            if req.status:
                conditions.append(KnowledgeDocument.status == req.status)
            if req.ontology_status:
                conditions.append(KnowledgeDocument.ontology_status == req.ontology_status)
        if req.keyword:
            pattern = f"%{req.keyword}%"
            conditions.append(
                or_(
                    KnowledgeDocument.file_name.ilike(pattern),
                    KnowledgeDocument.file_path.ilike(pattern),
                )
            )
        if req.folder_id:
            conditions.append(KnowledgeDocument.folder_id == req.folder_id)
        conditions.append(KnowledgeDocument.knowledge_base_id == req.knowledge_base_id)

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            items = await repo.list_all(
                tenant_id=tenant_id,
                offset=offset,
                limit=req.page_size,
                extra_conditions=conditions,
            )
            total = await repo.count(tenant_id=tenant_id, extra_conditions=conditions)

        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        }

    async def documents_stats(self, tenant_id: str, request: DocumentScopeRequest | dict) -> dict:
        """按线性状态口径统计某 KB 文档数（互斥四桶，设计 §5）。

        返回 processing / completed / compile_failed / parse_failed 四个**互斥**桶，
        total = 四桶之和（恒等可对账，deleting/deleted 不计入）。与列表徽章/筛选同源。
        count 由 BaseRepository 统一加租户 + is_deleted=0。
        """
        tenant_id = require_tenant(tenant_id)
        req = DocumentScopeRequest(**_payload(request))
        base = [KnowledgeDocument.knowledge_base_id == req.knowledge_base_id]

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)

            async def _count(extra: list) -> int:
                return await repo.count(tenant_id=tenant_id, extra_conditions=base + extra)

            # 互斥四桶（相加 = total）：每个文档恰好落进一桶，避免嵌套指标的对账困惑。
            # 处理中：待解析/解析中/入库中/待编译/编译中（还在跑）
            processing = await _count([
                or_(
                    KnowledgeDocument.status.in_([
                        DocStatus.PENDING.value,
                        DocStatus.PARSING.value,
                        DocStatus.INGESTING.value,
                    ]),
                    and_(
                        KnowledgeDocument.status == DocStatus.READY.value,
                        KnowledgeDocument.ontology_status.in_([
                            OntologyStatus.PENDING.value,
                            OntologyStatus.EXTRACTING.value,
                        ]),
                    ),
                )
            ])
            # 已完成：解析+图谱都就绪
            completed = await _count([
                and_(
                    KnowledgeDocument.status == DocStatus.READY.value,
                    KnowledgeDocument.ontology_status == OntologyStatus.READY.value,
                )
            ])
            # 编译失败：可搜索但图谱未建成
            compile_failed = await _count([
                and_(
                    KnowledgeDocument.status == DocStatus.READY.value,
                    KnowledgeDocument.ontology_status == OntologyStatus.FAILED.value,
                )
            ])
            # 解析失败：不可用
            parse_failed = await _count([KnowledgeDocument.status == DocStatus.FAILED.value])

        # total 定义为四桶之和，恒等可对账（deleting/deleted 不计入）。
        total = processing + completed + compile_failed + parse_failed
        return {
            "total": total,
            "processing": processing,
            "completed": completed,
            "compile_failed": compile_failed,
            "parse_failed": parse_failed,
        }

    async def get_document(
        self,
        tenant_id: str,
        document_id: str,
        request: DocumentScopeRequest | dict,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = DocumentScopeRequest(**_payload(request))
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_by_id(document_id, tenant_id)
            if doc is None or doc.knowledge_base_id != req.knowledge_base_id:
                raise ResourceNotFoundError(message=translate("err.doc.not_found", fallback="知识文档不存在")  )  # 原消息)
            return doc.to_dict()

    async def delete_document(
        self,
        tenant_id: str,
        document_id: str,
        request: DocumentScopeRequest | dict,
        *,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> dict:
        tenant_id = require_tenant(tenant_id)
        req = DocumentScopeRequest(**_payload(request))
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_by_id(document_id, tenant_id)
            if doc is None or doc.knowledge_base_id != req.knowledge_base_id:
                raise ResourceNotFoundError(message=translate("err.doc.not_found", fallback="知识文档不存在")  )  # 原消息)
            if doc.status == DocStatus.DELETING.value:
                raise ResourceConflictError(message=translate("err.doc.deleting_in_progress", fallback="知识文档正在删除中")  )  # 原消息)
            if doc.status in (DocStatus.PENDING.value, DocStatus.PARSING.value, DocStatus.INGESTING.value):
                raise ResourceConflictError(message=translate("err.doc.parsing_cannot_delete", fallback="知识文档正在解析/入库中，请等待完成后再删除")  )  # 原消息)
            await repo.set_status(doc, DocStatus.DELETING)
            rag_doc_ids = list(doc.rag_doc_ids or [])
            kb_id = doc.knowledge_base_id or ""
            file_name = doc.file_name or ""
            storage_key = doc.storage_key
            storage_backend = doc.storage_backend

        # rag_doc_ids 可能为空（insert 不返回 doc_ids，对账未及时补充时），
        # 此时从 LightRAG 存储反查，确保已入库的内容能被清理。
        if not rag_doc_ids and file_name and kb_id:
            rag_doc_ids = await self._lookup_rag_doc_ids(
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                file_name=file_name,
                document_id=document_id,
            )

        if rag_doc_ids:
            logger.info(
                "Deleting %d LightRAG documents for doc %s: %s",
                len(rag_doc_ids), document_id, rag_doc_ids[:10],
            )
        else:
            logger.warning(
                "No LightRAG doc_ids found for document %s (file_name=%s), "
                "LightRAG cleanup will be skipped",
                document_id, file_name,
            )

        for rag_doc_id in rag_doc_ids:
            try:
                await get_rag_client().delete(
                    rag_doc_id, tenant_id=tenant_id, knowledge_base_id=kb_id
                )
            except Exception:
                logger.warning("Failed to delete RAG document %s", rag_doc_id, exc_info=True)

        # 清理 Neo4j 本体图谱中该文档关联的实体节点和关系
        try:
            gdao = OntologyGraphRepository(get_neo4j_driver())
            await gdao.delete_by_document(tenant_id, document_id)
        except Exception:
            logger.warning("Neo4j cleanup failed for document %s", document_id, exc_info=True)

        # 清理对象存储中的原始上传文件（COS / Local）
        if storage_key:
            try:
                storage = get_object_storage_for(storage_backend) if storage_backend else get_object_storage()
                await storage.delete(storage_key)
                logger.info("Deleted storage file %s for doc %s", storage_key, document_id)
            except Exception:
                logger.warning("Failed to delete storage file for document %s", document_id, exc_info=True)

        async with get_db_session() as session:
            # 显式清理文档-标签关联（软删除不触发外键 CASCADE）
            try:
                await session.execute(
                    delete(DocumentTag).where(DocumentTag.document_id == document_id)
                )
            except Exception:
                logger.warning("Failed to clean document_tags for doc %s", document_id, exc_info=True)

            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
            await repo.set_status(doc, DocStatus.DELETED)
            await repo.delete_soft(doc, tenant_id)

        schedule_emit({
            "tenant_id": tenant_id,
            "user_id": _audit_user_id(user_id),
            "username": username,
            "ip": ip,
            "log_type": "OPERATION",
            "action": "document.delete",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": ResourceType.DOCUMENT.value,
            "resource_id": str(document_id),
        })

        return {"id": document_id, "deleted": True}

    async def set_document_folder(
        self, tenant_id: str, document_id: str, req: SetDocumentFolderRequest | dict
    ) -> dict:
        """设置或清除文档的文件夹归属。

        如果 folder_id 非空，校验文件夹属于同一个 knowledge_base_id；
        如果 folder_id 为 None，清除文档的文件夹归属。
        """
        tenant_id = require_tenant(tenant_id)
        data = _payload(req)
        folder_id = data.get("folder_id")
        knowledge_base_id = data.get("knowledge_base_id")

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_by_id(document_id, tenant_id)
            if doc is None or doc.knowledge_base_id != knowledge_base_id:
                raise ResourceNotFoundError(message=translate("err.doc.not_found", fallback="知识文档不存在")  )  # 原消息)

            if folder_id:
                # 校验文件夹存在且属于同一个 knowledge_base_id
                folder_repo = FolderRepository(session)
                folder = await folder_repo.get_required(folder_id, tenant_id)
                if folder.knowledge_base_id != knowledge_base_id:
                    raise ResourceNotFoundError(
                        message=translate("err.folder.not_belong_to_kb", fallback="文件夹不属于该知识库")  ,  # 原消息
                        details={"folder_id": folder_id, "knowledge_base_id": knowledge_base_id},
                    )

            doc.folder_id = folder_id
            await session.commit()
            return doc.to_dict()

    async def _lookup_rag_doc_ids(
        self,
        *,
        tenant_id: str,
        knowledge_base_id: str,
        file_name: str,
        document_id: str,
    ) -> list[str]:
        """从 LightRAG 存储反查文档的实际 doc_ids。

        用于 rag_doc_ids 为空时的兜底（insert 不返回 doc_ids，对账可能未及时补充）。
        优先通过 file_path 中的 doc=<id> 匹配，再降级到 file_name 匹配。
        """
        import re

        try:
            result = await get_rag_client().get_storage_documents(
                knowledge_base_id=knowledge_base_id,
                tenant_id=tenant_id,
                keyword=file_name,
                page=1,
                page_size=500,
            )
        except Exception as e:
            logger.warning(
                "Storage lookup failed for doc %s during delete: %s", document_id, e
            )
            return []

        items = result.get("items", [])
        total = result.get("total", len(items))
        if total > len(items):
            logger.warning(
                "Storage fallback during delete: total %d exceeds page size for doc %s",
                total, document_id,
            )

        matched = []
        for item in items:
            fp = item.get("file_path") or ""
            m = re.search(r'doc=([a-f0-9-]+)\|', fp)
            if m and m.group(1) == document_id:
                matched.append(item)
        if not matched:
            matched = [
                item for item in items
                if (
                    item.get("file_name") == file_name
                    or (item.get("file_name") or "").endswith("_" + file_name)
                )
            ]

        if not matched:
            logger.info(
                "Storage fallback miss during delete: doc_id=%s, file_name=%s, total=%d",
                document_id, file_name, len(items),
            )
            return []

        rag_doc_ids = [item["id"] for item in matched if item.get("id")]
        logger.info(
            "Storage fallback hit during delete: doc_id=%s, found %d LightRAG doc_ids",
            document_id, len(rag_doc_ids),
        )
        return rag_doc_ids


__all__ = ["DocumentService"]
