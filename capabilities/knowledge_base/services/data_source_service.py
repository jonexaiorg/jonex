#!/usr/bin/python3


import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import text

from jonex_core.common.crypto import (
    decode_ingest_key,
    encrypt_secret,
    generate_ingest_key,
    hash_ingest_key,
    verify_ingest_key,
)
from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import (
    InvalidApiKeyError,
    InvalidParameterError,
    ResourceNotFoundError,
)
from jonex_core.common.object_storage import get_object_storage
from jonex_core.common.tenant import require_tenant

from ..models.data_source import KnowledgeDataSource
from ..repository.data_source_repository import KnowledgeDataSourceRepository
from ..repository.document_repository import KnowledgeDocumentRepository
from .document_service import DocumentService
from .ingestion import get_ingestion_adapter

logger = logging.getLogger(__name__)

_VALID_ACCESS_TYPES = {"api", "api_push", "storage", "file"}


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name or "unnamed")


class DataSourceService:
    def __init__(self) -> None:
        self._docs = DocumentService()


    def _encrypt_config(self, access_type: str, cfg: dict) -> dict:
        cfg = dict(cfg or {})
        if access_type == "api":
            auth = dict(cfg.get("auth") or {})
            if auth.get("token"):
                auth["token_ref"] = encrypt_secret(auth.pop("token"))
            cfg["auth"] = auth
        elif access_type == "storage":
            if cfg.get("credential"):
                cfg["credential_ref"] = encrypt_secret(cfg.pop("credential"))
        return cfg


    async def list_sources(self, tenant_id: str, kb_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            items = await repo.list_by_kb(tenant_id, kb_id)
            total = await repo.count_by_kb(tenant_id, kb_id)

            type_count = await KnowledgeDocumentRepository(session).count_by_source_type(tenant_id, kb_id)
        result_items = []
        for i in items:
            d = i.to_dict()
            d["document_count"] = type_count.get(i.access_type, 0)
            result_items.append(d)
        return {"items": result_items, "total": total}

    async def get_source(self, tenant_id: str, ds_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            ds = await repo.get_required(ds_id, tenant_id)
            type_count = await KnowledgeDocumentRepository(session).count_by_source_type(
                tenant_id, ds.knowledge_base_id
            )
            data = ds.to_dict()
            data["document_count"] = type_count.get(ds.access_type, 0)
            return data

    async def create_source(self, tenant_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        access_type = data.get("access_type")
        if access_type not in _VALID_ACCESS_TYPES:
            raise InvalidParameterError(message=f"Invalid access_type: {access_type}")
        cfg = self._encrypt_config(access_type, data.get("config_json") or {})

        ds_id = str(uuid4())
        kb_id = data["knowledge_base_id"]
        plain: Optional[str] = None
        if access_type == "api_push":
            plain = generate_ingest_key(tenant_id=tenant_id, kb_id=kb_id, ds_id=ds_id)
            cfg["ingest_key_hash"] = hash_ingest_key(plain)
            cfg.setdefault("allowed_ext", ["pdf","doc","docx","ppt","pptx","xls","xlsx","txt","md","jpg","jpeg","png","gif","bmp","tiff","tif","webp","mp3","wav","flac","aac","m4a","ogg","wma","opus","amr","mp4","avi","mov","mkv","flv","wmv","webm","m4v","mpg","mpeg","3gp"])
            cfg.setdefault("max_file_mb", 50)

        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            ds = await repo.create(
                KnowledgeDataSource(
                    id=ds_id,
                    tenant_id=tenant_id,
                    knowledge_base_id=kb_id,
                    access_method_id=data.get("access_method_id"),
                    access_type=access_type,
                    name=data["name"],
                    config_json=cfg,
                    sync_mode=data.get("sync_mode", "manual"),
                    cron_expr=data.get("cron_expr"),
                    status="active",
                )
            )
            ds_id = ds.id
            result = ds.to_dict()
            await session.commit()

        await self._recalc_kb_stats(tenant_id, kb_id, ds_id)
        if access_type == "api_push" and plain:
            result["ingest_key"] = plain
            result["ingest_url"] = self._ingest_url(ds_id)
        return result

    async def update_source(self, tenant_id: str, ds_id: str, data: dict) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            ds = await repo.get_required(ds_id, tenant_id)
            if data.get("name") is not None:
                ds.name = data["name"]
            if data.get("sync_mode") is not None:
                ds.sync_mode = data["sync_mode"]
            if data.get("cron_expr") is not None:
                ds.cron_expr = data["cron_expr"]
            if data.get("status") is not None:
                ds.status = data["status"]
            if data.get("config_json") is not None:
                merged = {**(ds.config_json or {}), **self._encrypt_config(ds.access_type, data["config_json"])}
                ds.config_json = merged
            await session.flush()
            result = ds.to_dict()
            await session.commit()
        return result

    async def delete_source(self, tenant_id: str, ds_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        kb_id: str = ""
        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            ds = await repo.get_required(ds_id, tenant_id)
            kb_id = ds.knowledge_base_id
            await repo.delete_soft(ds, tenant_id)
            await session.commit()
        if kb_id:
            await self._recalc_kb_stats(tenant_id, kb_id, ds_id)
        return {"deleted": True}


    async def test_source(self, tenant_id: str, ds_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        ds = await self._load(tenant_id, ds_id)
        if ds.access_type == "api_push":
            return {"ok": True, "message": "入站推送无需测试连接"}
        adapter = get_ingestion_adapter(ds.access_type)
        return await adapter.test_connection(ds.config_json or {})


    async def sync_source(self, tenant_id: str, ds_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        ds = await self._load(tenant_id, ds_id)
        if ds.access_type not in {"api", "storage"}:
            raise InvalidParameterError(message=f"{ds.access_type} 不支持立即同步")

        await self._set_sync_status(tenant_id, ds_id, "running", None)
        adapter = get_ingestion_adapter(ds.access_type)
        cfg = ds.config_json or {}
        kb_id = ds.knowledge_base_id
        access_type = ds.access_type
        created, failed, errors = 0, 0, []
        try:


            files = await adapter.list_remote_files(cfg, since=None)
            for rf in files:
                try:
                    if await self._is_ingested(tenant_id, kb_id, ds_id, rf.external_id):
                        continue
                    data, mime = await adapter.fetch_bytes(cfg, rf)
                    await self._land_and_ingest(
                        tenant_id, kb_id, ds_id, access_type, rf.name, data, mime,
                        external_id=rf.external_id,
                    )
                    created += 1
                except Exception as fe:
                    failed += 1
                    errors.append(f"{rf.name}: {fe}")
                    logger.warning("Failed to synchronize individual data source file ds=%s file=%s err=%s", ds_id, rf.name, fe)
            status = "success" if created or not failed else "failed"
            msg = "; ".join(errors[:5]) if errors else None
            await self._bump_after_sync(tenant_id, ds_id, ds.knowledge_base_id, status, msg)
            return {"created": created, "failed": failed, "message": msg}
        except Exception as e:
            await self._set_sync_status(tenant_id, ds_id, "failed", str(e))
            raise


    async def reset_ingest_key(self, tenant_id: str, ds_id: str) -> dict:
        tenant_id = require_tenant(tenant_id)
        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            ds = await repo.get_required(ds_id, tenant_id)
            if ds.access_type != "api_push":
                raise InvalidParameterError(message="Only API push data sources support Key reset")
            plain = generate_ingest_key(tenant_id=tenant_id, kb_id=ds.knowledge_base_id, ds_id=ds_id)
            cfg = dict(ds.config_json or {})
            cfg["ingest_key_hash"] = hash_ingest_key(plain)
            ds.config_json = cfg
            await session.flush()
            result = ds.to_dict()
            await session.commit()
        result["ingest_key"] = plain
        result["ingest_url"] = self._ingest_url(ds_id)
        return result


    async def ingest_push(
        self, ds_id: str, ingest_key: str, *,
        storage_key: str, file_name: str, mime_type: Optional[str] = None,
        file_size: int = 0, external_id: Optional[str] = None,
    ) -> dict:

        key_info = decode_ingest_key(ingest_key)
        if key_info and key_info.get("ds_id") and key_info["ds_id"] != ds_id:
            raise InvalidApiKeyError(message="ingest key does not match the data source")

        async with get_db_session() as session:
            ds = await session.get(KnowledgeDataSource, ds_id)
            if ds is None or ds.is_deleted or ds.access_type != "api_push":
                raise ResourceNotFoundError(message="Data source not found")
            tenant_id = ds.tenant_id
            kb_id = ds.knowledge_base_id
            cfg = dict(ds.config_json or {})


            if key_info:
                if key_info.get("tenant_id") and key_info["tenant_id"] != tenant_id:
                    raise InvalidApiKeyError(message="ingest key tenant mismatch")
                if key_info.get("kb_id") and key_info["kb_id"] != kb_id:
                    raise InvalidApiKeyError(message="ingest key knowledge base mismatch")

        if not verify_ingest_key(ingest_key, cfg.get("ingest_key_hash", "")):
            raise InvalidApiKeyError(message="Invalid ingest key")
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        allow = {e.lower() for e in (cfg.get("allowed_ext") or [])}
        if allow and ext not in allow:
            raise InvalidParameterError(message=f"File type not allowed: {ext}")
        max_mb = cfg.get("max_file_mb", 50)
        if file_size and file_size > max_mb * 1024 * 1024:
            raise InvalidParameterError(message=f"File exceeds the {max_mb}MB limit")

        doc = await self._docs.upload_document(tenant_id, {
            "file_name": file_name,
            "file_path": storage_key,
            "file_size": file_size,
            "mime_type": mime_type,
            "knowledge_base_id": kb_id,
            "storage_backend": os.getenv("OBJECT_STORAGE_BACKEND", "local"),
            "storage_key": storage_key,
            "metadata": {"data_source_id": ds_id, "source": "api_push", "external_id": external_id},
        })
        await self._bump_after_sync(tenant_id, ds_id, kb_id, "success", None)
        return {"document_id": doc.get("id"), "status": doc.get("status")}


    async def _load(self, tenant_id: str, ds_id: str) -> KnowledgeDataSource:
        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            return await repo.get_required(ds_id, tenant_id)

    def _ingest_url(self, ds_id: str) -> str:
        base = os.getenv("PUBLIC_API_BASE", "").rstrip("/")
        return f"{base}/api/v1/knowledge-base/ingest/{ds_id}"

    async def _land_and_ingest(
        self, tenant_id, kb_id, ds_id, access_type, file_name, data, mime, *, external_id,
    ):
        doc_id = str(uuid4())
        prefix = os.getenv("COS_KEY_PREFIX", "jonex")
        storage_key = f"{prefix}/kb/{tenant_id}/{kb_id}/{doc_id}/{doc_id}_{_safe_name(file_name)}"
        await get_object_storage().put_bytes(storage_key, data, content_type=mime)
        await self._docs.upload_document(tenant_id, {
            "file_name": file_name,
            "file_path": storage_key,
            "file_size": len(data),
            "mime_type": mime,
            "knowledge_base_id": kb_id,
            "doc_id": doc_id,
            "storage_backend": os.getenv("OBJECT_STORAGE_BACKEND", "local"),
            "storage_key": storage_key,
            "metadata": {"data_source_id": ds_id, "source": access_type, "external_id": external_id},
        })

    async def _is_ingested(self, tenant_id, kb_id, ds_id, external_id) -> bool:


        async with get_db_session() as session:
            row = (await session.execute(text(
                """
                SELECT 1 FROM knowledge_base.knowledge_documents
                WHERE tenant_id=:t AND knowledge_base_id=:kb
                  AND extra_metadata->>'data_source_id' = :ds
                  AND extra_metadata->>'external_id' = :ext
                LIMIT 1
                """
            ), {"t": tenant_id, "kb": kb_id, "ds": ds_id, "ext": external_id or ""})).first()
        return row is not None

    async def _recalc_kb_stats(self, tenant_id: str, kb_id: str, ds_id: str) -> None:

        async with get_db_session() as session:

            await session.execute(text("""
                UPDATE knowledge_base.knowledge_data_sources ds
                   SET document_count = sub.cnt
                  FROM (
                    SELECT d.extra_metadata->>'data_source_id' AS ds_id,
                           COUNT(*) AS cnt
                      FROM knowledge_base.knowledge_documents d
                     WHERE d.is_deleted = 0
                       AND d.tenant_id = :t
                       AND d.extra_metadata->>'data_source_id' IS NOT NULL
                     GROUP BY d.extra_metadata->>'data_source_id'
                  ) sub
                 WHERE ds.id = sub.ds_id
                   AND ds.tenant_id = :t
            """), {"t": tenant_id})


            await session.execute(text("""
                UPDATE knowledge_base.knowledge_info ki
                   SET document_count = (
                         SELECT COUNT(*)
                           FROM knowledge_base.knowledge_documents d
                          WHERE d.knowledge_base_id = ki.id
                            AND d.is_deleted = 0
                            AND d.tenant_id = ki.tenant_id
                       ),
                       data_source_types = (
                         SELECT COALESCE(
                           jsonb_agg(DISTINCT ds.access_type) FILTER (WHERE ds.access_type IS NOT NULL),
                           '[]'::jsonb
                         )
                           FROM knowledge_base.knowledge_data_sources ds
                          WHERE ds.knowledge_base_id = ki.id
                            AND ds.is_deleted = 0
                            AND ds.status = 'active'
                            AND ds.tenant_id = ki.tenant_id
                       )
                 WHERE ki.id = :kb AND ki.tenant_id = :t
            """), {"kb": kb_id, "t": tenant_id})

            await session.commit()
        logger.debug("_recalc_kb_stats kb=%s ds=%s done", kb_id, ds_id)

    async def _set_sync_status(self, tenant_id, ds_id, status, message):
        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            ds = await repo.get_required(ds_id, tenant_id)
            ds.last_sync_status = status
            ds.last_sync_message = message
            if status == "running":
                ds.last_sync_at = datetime.now(timezone.utc)
            await session.commit()

    async def _bump_after_sync(self, tenant_id, ds_id, kb_id, status, message):

        async with get_db_session() as session:
            repo = KnowledgeDataSourceRepository(session)
            ds = await repo.get_required(ds_id, tenant_id)
            ds.last_sync_status = status
            ds.last_sync_message = message
            ds.last_sync_at = datetime.now(timezone.utc)
            await session.commit()

        await self._recalc_kb_stats(tenant_id, kb_id, ds_id)


__all__ = ["DataSourceService"]
