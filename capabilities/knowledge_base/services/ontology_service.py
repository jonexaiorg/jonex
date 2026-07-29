"""Ontology extraction service for Knowledge Base."""

import logging

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common.database import get_db_session
from jonex_core.common.exceptions import InvalidParameterError, ResourceNotFoundError
from jonex_core.common.i18n import translate
from jonex_core.common.tenant import require_tenant

from ..models import OntologyStatus
from ..repository import KnowledgeDocumentRepository

logger = logging.getLogger(__name__)


class OntologyService:
    async def retry_extract(
        self,
        tenant_id: str,
        document_id: str,
        knowledge_base_id: str,
    ) -> dict:
        """手动重抽本体（ontology-only）。

        [jonex] P0-B：统一走「领取 → 提交 → 拿到有效 task_id → EXTRACTING + retry_count++」协议：
        - 不再凭 queued 就置 READY（会导致对账不再扫、新结果永不落 Neo4j）；
        - 提交成功才写回新 `rag_task_id`、置 EXTRACTING、++retry，由对账 EXTRACTING 分支收尾；
        - 提交失败 / 未拿到 task_id：不改状态、不 ++retry，不遗留无 rag_task_id 的 EXTRACTING。
        """
        tenant_id = require_tenant(tenant_id)

        # ontology-only 必须携带 compiled schema，否则 atomic-rag 无法归类
        schema = None
        schema_version = 0
        try:
            from .ontology_compiler import OntologyCompiler
            schema = await OntologyCompiler().get_compiled_schema(
                tenant_id, knowledge_base_id, auto_compile=True,
            )
            if schema:
                schema_version = int(schema.get("schema_version", 0) or 0)
        except Exception as e:
            logger.warning("Compiled schema check failed for doc %s: %s", document_id, e)

        if schema is None:
            raise InvalidParameterError(
                message=translate("err.ontology.no_compiled_schema", fallback="该知识库无可用 compiled schema，请先编译本体 schema 后再重试")  ,  # 原消息
                details={"knowledge_base_id": knowledge_base_id, "document_id": document_id},
            )

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_by_id(document_id, tenant_id)
            if doc is None or doc.knowledge_base_id != knowledge_base_id:
                raise ResourceNotFoundError(message=translate("err.doc.not_found", fallback="知识文档不存在")  )  # 原消息)
            file_path = doc.file_path
            # 携带当前代次，供对账写图前 fencing（reparse 后代次变化则本结果作废）
            content_generation = int(getattr(doc, "content_generation", 0) or 0)

        # 提交 ontology-only 任务（不在此处 ++retry / 置 EXTRACTING）
        try:
            result = await get_rag_client().retry_ontology_extract(
                document_id=document_id,
                knowledge_base_id=knowledge_base_id,
                tenant_id=tenant_id,
                file_path=file_path,
                ontology_schema=schema,
                schema_version=schema_version,
                content_generation=content_generation,
            )
        except Exception as e:
            logger.warning("Ontology retry submit failed for doc %s: %s", document_id, e)
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                doc = await repo.get_required(document_id, tenant_id)
                return doc.to_dict()

        task_id = (result or {}).get("task_id", "")
        if not task_id:
            logger.warning("Ontology retry did not return task_id for doc %s", document_id)
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                doc = await repo.get_required(document_id, tenant_id)
                return doc.to_dict()

        # 提交成功：写回新 rag_task_id + EXTRACTING + ++retry，由对账收尾后才 READY
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            doc = await repo.get_required(document_id, tenant_id)
            await repo.set_ontology_status(doc, OntologyStatus.EXTRACTING, increment_retry=True)
            await repo.set_status(doc, doc.status, rag_task_id=task_id)
            doc.extra_metadata = {**(doc.extra_metadata or {}), "ontology_retry_task_id": task_id}
            await session.commit()
            return doc.to_dict()

    async def reextract_kb_documents(
        self,
        tenant_id: str,
        knowledge_base_id: str,
        *,
        document_ids: list[str] | None = None,
        only_outdated: bool = False,
        only_ready: bool = True,
    ) -> dict:
        """KB 级「按新 schema 重抽本体」（C→B 联动，走对账被动）。

        [jonex] 阶段2：只做状态重置（置 PENDING + 重置计数 + 写目标 schema 版本）；
        实际重抽交给 30s 对账 reconcile_ontology 逐个 ontology-only 跑（不重解析文件）。
        返回 {matched, reset, skipped, schema_version}。
        """
        tenant_id = require_tenant(tenant_id)

        schema = None
        schema_version = 0
        try:
            from .ontology_compiler import OntologyCompiler
            schema = await OntologyCompiler().get_compiled_schema(
                tenant_id, knowledge_base_id, auto_compile=True,
            )
            if schema:
                schema_version = int(schema.get("schema_version", 0) or 0)
        except Exception as e:
            logger.warning("Compiled schema check failed for KB %s: %s", knowledge_base_id, e)

        if schema is None:
            raise InvalidParameterError(
                message=translate("err.ontology.no_compiled_schema", fallback="该知识库无可用 compiled schema，请先编译本体 schema 后再重试")  ,  # 原消息
                details={"knowledge_base_id": knowledge_base_id},
            )

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            stats = await repo.reset_ontology_for_kb(
                tenant_id, knowledge_base_id,
                document_ids=document_ids,
                only_ready=only_ready,
                only_outdated=only_outdated,
                target_schema_version=schema_version,
            )
            await session.commit()

        return {**stats, "schema_version": schema_version}


__all__ = ["OntologyService"]
