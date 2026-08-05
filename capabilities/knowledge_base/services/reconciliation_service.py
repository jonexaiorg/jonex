"""Internal Knowledge Base reconciliation service.

Follows the same core logic as the previous flat-file architecture:
- Per-doc task status polling with completed/failed/not_found handling
- LightRAG storage fallback (`_verify_via_storage`) when task state is lost
- Ontology retry with max 3 attempts
- Neo4j ontology write before PG status update (consistency design)
- Compiled schema check before ontology retry (Phase 4.2)
"""

import logging
import os
import time
from datetime import datetime

from jonex_core.capability.atomic.rag.client import get_rag_client
from jonex_core.common.audit import schedule_emit
from jonex_core.common.audit_enums import ResourceType
from jonex_core.common.database import get_db_session
from jonex_core.common.neo4j_client import get_neo4j_driver

from ..models import DocStatus, OntologyStatus
from ..repository import KnowledgeDocumentRepository, OntologyGraphRepository

logger = logging.getLogger(__name__)


# [jonex] §11 v2 stage key 白名单：过滤未知阶段、避免噪音泄露到聚合字段
_V2_STAGE_KEYS = frozenset({
    "created", "queued", "parse", "text_insert", "multimodal",
    "push_chunks", "ontology_extract", "pipeline_done",
})

# [jonex] P1-1：created/queued 是排队等待，不算入 worker 端到端耗时
_QUEUE_KEYS = frozenset({"created", "queued"})


def _normalize_stage_timings(raw):
    """归一 worker 分阶段耗时，兼容两种形态：
    - v1：dict，含 `worker_total_ms` + 各阶段键
    - v2：list[{stage,label,started_at,ended_at,elapsed_seconds}]
    返回 (worker_total_ms: int|None, per_stage_ms: dict)。
    v2 list 形态仅取白名单内 stage key，其余静默跳过。
    """
    if isinstance(raw, dict):
        total = raw.get("worker_total_ms")
        per = {k: v for k, v in raw.items() if k != "worker_total_ms"}
        return total, per
    if isinstance(raw, list):
        per: dict = {}
        total_s = 0.0
        for s in raw:
            if not isinstance(s, dict):
                continue
            stage = s.get("stage") or "unknown"
            # [jonex] §11 白名单过滤
            if stage not in _V2_STAGE_KEYS:
                continue
            try:
                secs = float(s.get("elapsed_seconds") or 0)
            except (TypeError, ValueError):
                secs = 0.0
            per[f"{stage}_ms"] = int(secs * 1000)
            # [jonex] P1-1：created/queued 是排队，不算入 worker 端到端
            if stage not in _QUEUE_KEYS:
                total_s += secs
        return (int(total_s * 1000) if raw else None), per
    return None, {}


def _detect_pipeline_version(raw) -> str | None:
    """从 stage_timings 形态推断 pipeline 版本。
    - list → v2 (raganything pipeline)
    - dict → v1 (lightrag_adapter legacy)
    - None/empty → None
    """
    if isinstance(raw, list):
        return "v2"
    if isinstance(raw, dict):
        return "v1"
    return None

MAX_ONTOLOGY_RETRIES = 3


class ReconciliationService:
    """Background-only cross-tenant scans. Do not use from request handlers."""

    # ── public entry points (called by the 30s loop) ───────────

    async def reconcile_documents(self, limit: int = 50) -> dict:
        """Scan PARSING + INGESTING docs and reconcile each one."""
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            docs = await repo.list_by_status_for_reconciliation(
                [DocStatus.PARSING, DocStatus.INGESTING], limit=limit,
            )

        updated, failed, skipped = 0, 0, 0
        for doc in docs:
            try:
                result = await self._reconcile_one(doc)
                if result == "updated":
                    updated += 1
                elif result == "skipped":
                    skipped += 1
            except Exception:
                failed += 1
                logger.warning("Failed to reconcile document %s", doc.id, exc_info=True)

        return {"checked": len(docs), "updated": updated, "skipped": skipped, "failed": failed}

    async def reconcile_ontology(self, limit: int = 50) -> dict:
        """Scan ontology pending/failed docs and retry extraction.

        [jonex] P1-F：最大在途 ontology task 数限流（ONTOLOGY_MAX_INFLIGHT，默认 100）——
        在途（EXTRACTING）过多时本轮少领/不领，避免打满上游 LLM。SKIP LOCKED 领取避免多实例重复。
        """
        max_inflight = int(os.getenv("ONTOLOGY_MAX_INFLIGHT", "100"))
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            inflight = await repo.count_by_ontology_status([OntologyStatus.EXTRACTING])
            # 预留额度：本轮最多新领 (max_inflight - inflight) 个 PENDING/FAILED；
            # EXTRACTING 文档仍需扫描以轮询收尾，故 fetch limit 不缩减，仅在提交新任务时受限。
            effective_limit = limit
            docs = await repo.list_by_ontology_status_for_reconciliation(
                [OntologyStatus.PENDING, OntologyStatus.FAILED, OntologyStatus.EXTRACTING],
                limit=effective_limit,
                skip_locked=True,
            )

        budget = max(0, max_inflight - inflight)  # 本轮可新提交的 ontology-only 任务数
        queued = 0
        for doc in docs:
            try:
                # EXTRACTING 文档只做轮询收尾（不占用新提交预算）；
                # PENDING/FAILED 需要新提交，受 budget 限制。
                is_new_submit = doc.ontology_status != OntologyStatus.EXTRACTING.value
                if is_new_submit and budget <= 0:
                    continue
                if await self._retry_ontology_one(doc):
                    if is_new_submit:
                        budget -= 1
                    queued += 1
            except Exception:
                logger.warning("Ontology retry failed for doc %s", doc.id, exc_info=True)

        return {"checked": len(docs), "queued": queued, "inflight": inflight}

    async def patrol_parsing_timeout(self, limit: int = 50) -> dict:
        """扫描 PARSING/INGESTING 超时的文档并处置。

        [jonex] R1 探活优化：
        - SOFT 超时（RAG_TASK_SOFT_TIMEOUT_SEC，默认 3600s）到点先探活，任务仍在处理/排队
          则继续等待，绝不无脑重推；
        - HARD 超时（RAG_TASK_HARD_TIMEOUT_SEC，默认 21600s=6h）兜底，超限即使 alive 也判死；
        - 探测失败不即判死（RAG_TASK_PROBE_FAIL_MAX，默认 3 次连续失败才判 dead）；
        - INGESTING 文档绝不 re-insert（已过 P1/P2，重推会丢弃进度并加重 LightRAG 负载）；
        - INGESTING 失败不动 parsing_retry_count（该字段语义仅代表 P1/P2 解析重试）。
        集成在 _reconcile_loop() 30 秒循环中，不额外引入 APScheduler。
        """
        SOFT = int(os.getenv("RAG_TASK_SOFT_TIMEOUT_SEC", "3600"))
        HARD = int(os.getenv("RAG_TASK_HARD_TIMEOUT_SEC", "21600"))
        PROBE_FAIL_MAX = int(os.getenv("RAG_TASK_PROBE_FAIL_MAX", "3"))

        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            docs = await repo.list_by_status_for_reconciliation(
                [DocStatus.PARSING, DocStatus.INGESTING], limit=limit,
            )

        now = datetime.now()  # [jonex] P0-2: naive 本地时间，与 DB 写入口径一致
        timed_out = 0
        retried = 0
        exhausted = 0
        waiting = 0

        for doc in docs:
            updated_at = doc.updated_at
            if updated_at is None:
                continue
            if updated_at.tzinfo is not None:
                # [jonex] P0-2: aware 归一到 naive 本地，避免 aware_utc - naive TypeError
                updated_at = updated_at.astimezone().replace(tzinfo=None)
            elapsed_seconds = (now - updated_at).total_seconds()
            if elapsed_seconds < SOFT:
                continue

            timed_out += 1

            meta = dict(doc.extra_metadata or {})
            retry_count = meta.get("parsing_retry_count", 0)

            # ── R1-E 探活：查任务真实状态 ──
            alive = False
            rag_status = ""
            current_step = ""
            probe_failures = meta.get("consecutive_probe_failures", 0)

            if doc.rag_task_id:
                try:
                    st = await get_rag_client().get_task_status(
                        task_id=doc.rag_task_id, tenant_id=doc.tenant_id,
                    )
                    rag_status = st.get("status") or st.get("state") or ""
                    current_step = st.get("current_step") or ""
                    alive = rag_status in ("pending", "queued", "processing", "running", "extracting")
                    # 探测成功 → 清零失败计数
                    if probe_failures > 0:
                        meta["consecutive_probe_failures"] = 0
                except Exception as exc:
                    logger.warning("Patrol probe get_task_status failed doc=%s: %s", doc.id, exc)
                    probe_failures += 1
                    meta["consecutive_probe_failures"] = probe_failures
                    if probe_failures < PROBE_FAIL_MAX:
                        # 单次探测失败 → 保守跳过本轮，不判死
                        waiting += 1
                        logger.info(
                            "Patrol→probe failed, skip this round: doc_id=%s waited=%.0fmin failures=%d/%d",
                            doc.id, elapsed_seconds / 60, probe_failures, PROBE_FAIL_MAX,
                        )
                        async with get_db_session() as session:
                            repo_s = KnowledgeDocumentRepository(session)
                            doc.extra_metadata = meta
                            session.add(doc)
                            await session.commit()
                        continue
                    # 连续失败达上限 → 判 dead
                    alive = False
            else:
                alive = False

            # ── 未到硬上限且任务还活着 → 只是排队/慢，继续等 ──
            if alive and elapsed_seconds < HARD:
                # [jonex] R5-a：processing + cleanup 卡死兜底 —— 不再等 6h HARD，
                # 按删除量动态超时判死（与 _handle_failed 同口径），覆盖 patrol
                # 对 processing 态盲区。reparse 进入 cleanup 后任务 status 为
                # processing，旧 patrol 只看 alive 就继续等 → 永久卡 ingesting。
                if current_step == "cleanup":
                    stuck_timeout = self._cleanup_stuck_timeout(st)
                    if elapsed_seconds >= stuck_timeout:
                        logger.error(
                            "Patrol PARSING+cleanup stuck→FAILED: doc_id=%s task_id=%s "
                            "waited=%.0fmin current_step=%s",
                            doc.id, doc.rag_task_id, elapsed_seconds / 60, current_step,
                        )
                        async with get_db_session() as session:
                            repo_s = KnowledgeDocumentRepository(session)
                            await repo_s.set_status(
                                doc, DocStatus.FAILED,
                                error_message=f"文档清理超时（cleanup 卡死 {elapsed_seconds/60:.0f} 分钟），请重试",
                            )
                        continue
                waiting += 1
                logger.info(
                    "Patrol→仍在处理/排队，继续等待: doc_id=%s waited=%.0fmin rag_status=%s current_step=%s",
                    doc.id, elapsed_seconds / 60, rag_status, current_step,
                )
                # 持久化可能已清零的 probe 计数
                if meta.get("consecutive_probe_failures", 0) == 0 and probe_failures > 0:
                    async with get_db_session() as session:
                        repo_s = KnowledgeDocumentRepository(session)
                        doc.extra_metadata = meta
                        session.add(doc)
                        await session.commit()
                continue

            # ── R1-C：INGESTING 绝不 re-insert ──
            is_ingesting = doc.status == "ingesting"  # forward-compatible with Batch 2-B
            if is_ingesting:
                # [jonex] 问题2：判死前探活。INGESTING 阶段 LightRAG 抽取可能
                # 极慢（3~18s/chunk × N千 chunk），健康任务在 HARD 内未完成
                # 是正常的。alive 且未超绝对上限则继续等待，避免误杀（如本例
                # 1878 chunk 文档在 6h HARD 时实际仍在正常入库）。
                INGESTING_CEIL = HARD * 2
                if alive and elapsed_seconds < INGESTING_CEIL:
                    waiting += 1
                    logger.info(
                        "Patrol→INGESTING 仍在入库，继续等待: doc_id=%s waited=%.0fmin "
                        "rag_status=%s current_step=%s",
                        doc.id, elapsed_seconds / 60, rag_status, current_step,
                    )
                    continue

                error_msg = (
                    f"知识入库超时（已 INGESTING {elapsed_seconds/60:.0f} 分钟），"
                    f"任务状态={rag_status or 'unknown'}"
                )
                if elapsed_seconds >= HARD:
                    logger.error(
                        "Patrol HARD timeout INGESTING→FAILED: doc_id=%s task_id=%s "
                        "waited=%.0fmin rag_status=%s current_step=%s",
                        doc.id, doc.rag_task_id, elapsed_seconds / 60, rag_status, current_step,
                    )
                async with get_db_session() as session:
                    repo_s = KnowledgeDocumentRepository(session)
                    await repo_s.set_status(doc, DocStatus.FAILED, error_message=error_msg)
                    # #6 计数隔离：INGESTING 失败用独立标记，不动 parsing_retry_count
                    meta["ingesting_failed"] = True
                    doc.extra_metadata = meta
                    session.add(doc)
                    await session.commit()
                logger.warning(
                    "Patrol INGESTING→FAILED (no re-insert): doc_id=%s waited=%.0fmin",
                    doc.id, elapsed_seconds / 60,
                )
                continue

            # ── PARSING：原有 FAILED + re-insert 路径 ──

            if retry_count >= 3:
                exhausted += 1
                if elapsed_seconds >= HARD:
                    logger.error(
                        "Patrol HARD timeout PARSING→FAILED(exhausted): doc_id=%s task_id=%s "
                        "waited=%.0fmin rag_status=%s current_step=%s retries=%d",
                        doc.id, doc.rag_task_id, elapsed_seconds / 60,
                        rag_status, current_step, retry_count,
                    )
                async with get_db_session() as session:
                    repo_s = KnowledgeDocumentRepository(session)
                    await repo_s.set_status(
                        doc, DocStatus.FAILED,
                        error_message=f"解析超时（已 PARSING {elapsed_seconds/60:.0f} 分钟），重试次数已用尽",
                    )
                logger.warning(
                    "Patrol timeout exhausted: doc_id=%s, waited=%.0fmin, retries=%d",
                    doc.id, elapsed_seconds / 60, retry_count,
                )
                continue

            # 决策 C：HARD 超限置 FAILED 时打 ERROR 告警日志
            if elapsed_seconds >= HARD:
                logger.error(
                    "Patrol HARD timeout PARSING→re-insert: doc_id=%s task_id=%s "
                    "waited=%.0fmin rag_status=%s current_step=%s retry=%d/3",
                    doc.id, doc.rag_task_id, elapsed_seconds / 60,
                    rag_status, current_step, retry_count + 1,
                )

            # Mark as FAILED first, then retry
            async with get_db_session() as session:
                repo_s = KnowledgeDocumentRepository(session)
                await repo_s.set_status(
                    doc, DocStatus.FAILED,
                    error_message=f"解析超时（已 PARSING {elapsed_seconds/60:.0f} 分钟），自动重试第 {retry_count + 1} 次",
                )

            # Re-submit to RAG
            try:
                from .ontology_compiler import OntologyCompiler
                schema = await OntologyCompiler().get_compiled_schema(
                    doc.tenant_id, doc.knowledge_base_id, auto_compile=True,
                )
            except Exception as exc:
                logger.warning(
                    "Patrol schema check failed for doc %s, proceeding: %s", doc.id, exc,
                )
                schema = None

            try:
                rag_result = await get_rag_client().insert(
                    file_path=doc.file_path,
                    tenant_id=doc.tenant_id,
                    knowledge_base_id=doc.knowledge_base_id,
                    document_id=doc.id,
                    ontology_schema=schema,
                    storage_backend=doc.storage_backend or "local",
                    storage_key=doc.storage_key,
                )

                new_status = DocStatus.READY if not rag_result.get("task_id") else DocStatus.PARSING

                async with get_db_session() as session:
                    repo_s = KnowledgeDocumentRepository(session)
                    await repo_s.set_status(
                        doc, new_status,
                        rag_task_id=rag_result.get("task_id"),
                        rag_doc_ids=rag_result.get("doc_ids") or rag_result.get("document_ids") or [],
                    )
                    meta["parsing_retry_count"] = retry_count + 1
                    doc.extra_metadata = meta
                    session.add(doc)
                    await session.commit()

                retried += 1
                logger.info(
                    "Patrol retry queued: doc_id=%s, retry=%d/%d, status=%s",
                    doc.id, meta["parsing_retry_count"], 3, new_status.value,
                )

            except Exception as exc:
                logger.warning(
                    "Patrol re-insert failed for doc %s, left as FAILED: %s", doc.id, exc,
                )

        return {
            "checked": len(docs),
            "timed_out": timed_out,
            "retried": retried,
            "exhausted": exhausted,
            "waiting": waiting,
        }

    # ── per-doc reconciliation ─────────────────────────────────

    async def _reconcile_one(self, doc) -> str:
        """Reconcile a single PARSING document. Returns 'updated' | 'skipped'."""
        if not doc.rag_task_id:
            return await self._handle_not_found(doc)

        try:
            status_info = await get_rag_client().get_task_status(
                task_id=doc.rag_task_id,
                tenant_id=doc.tenant_id,
            )
        except Exception as e:
            logger.warning("Reconcile query failed for doc %s: %s", doc.id, e)
            return "skipped"

        rag_status = status_info.get("status") or status_info.get("state", "")

        if rag_status == "completed":
            return await self._handle_completed(doc, status_info)
        elif rag_status == "failed":
            return await self._handle_failed(doc, status_info)
        elif rag_status == "not_found":
            return await self._handle_not_found(doc)
        else:
            # [jonex] 细粒度落库（设计 §9.5）：task 进入本体抽取（ontology_status=extracting）
            # ⟹ parse+push 已完成 ⟹ 文档已可搜索。把仍处于 PARSING 的文档提前落成
            # READY+EXTRACTING，使线性状态「编译中」在首次上传时真实可见。
            # 只提前置 EXTRACTING，绝不置 PENDING——否则 reconcile_ontology 会对 pending
            # 文档直接 claim+提交新的 ontology-only 重抽，与 insert 任务内抽取重复触发。
            # 收尾交给 reconcile_ontology 的 EXTRACTING 分支轮询同一 rag_task_id（insert 任务）。
            if (
                os.getenv("RECONCILE_REFLECT_COMPILING", "true").lower() in ("1", "true", "yes", "on")
                and doc.status in (DocStatus.PARSING.value, DocStatus.INGESTING.value)
                and status_info.get("ontology_status") == "extracting"
            ):
                # 代次 fencing：与 _handle_completed 一致，旧代次任务不提前置位
                task_gen = int(status_info.get("content_generation", 0) or 0)
                doc_gen = int(getattr(doc, "content_generation", 0) or 0)
                if task_gen < doc_gen:
                    logger.debug(
                        "Reconcile→skip reflect(stale gen): doc_id=%s task_gen=%s doc_gen=%s",
                        doc.id, task_gen, doc_gen,
                    )
                    return "skipped"
                doc_ids = status_info.get("lightrag_doc_ids") or status_info.get("doc_ids") or []
                async with get_db_session() as session:
                    repo = KnowledgeDocumentRepository(session)
                    # 保留 rag_task_id（仍指向 insert 任务）；仅更新 status + rag_doc_ids
                    await repo.set_status(doc, DocStatus.READY, rag_doc_ids=doc_ids)
                    await repo.set_ontology_status(doc, OntologyStatus.EXTRACTING)
                    await session.commit()
                logger.info(
                    "Reconcile→READY+EXTRACTING (compiling visible): doc_id=%s", doc.id,
                )
                return "updated"
            # ── [jonex] R1-B：INGESTING 判定（先判 READY 已不命中 → 回退判 INGESTING）──
            # #5 单轮合并：不命中 READY 才回退判 INGESTING，避免"先置 INGESTING 再等下一轮"
            if doc.status in (DocStatus.PARSING.value, DocStatus.INGESTING.value):
                current_step = status_info.get("current_step") or ""
                progress = status_info.get("progress", 0) or 0

                # 首选：push_chunks 阶段明确信号
                if current_step == "push_chunks":
                    async with get_db_session() as session:
                        repo = KnowledgeDocumentRepository(session)
                        await repo.set_status(doc, DocStatus.INGESTING)
                        await session.commit()
                    logger.info(
                        "Reconcile→INGESTING (push_chunks): doc_id=%s, progress=%s",
                        doc.id, progress,
                    )
                    return "updated"

                # 兜底：processing + progress>0 但 current_step 无法精确判定（已过解析）
                if rag_status == "processing" and progress > 0:
                    async with get_db_session() as session:
                        repo = KnowledgeDocumentRepository(session)
                        await repo.set_status(doc, DocStatus.INGESTING)
                        await session.commit()
                    logger.info(
                        "Reconcile→INGESTING (fallback, progress>0): doc_id=%s "
                        "rag_status=%s current_step=%s progress=%s",
                        doc.id, rag_status, current_step, progress,
                    )
                    return "updated"

            # processing / pending — keep current status
            logger.debug(
                "Reconcile→keep %s: doc_id=%s, rag_status=%s, progress=%s",
                doc.status, doc.id, rag_status, status_info.get("progress"),
            )
            return "skipped"

    async def _apply_synonyms(self, tenant_id: str, kb_id: str, ont_data: dict) -> dict:
        """[jonex] 写图前 KB 级同义词归一（效果 Y）。

        直查同义词表构建索引，对 ont_data 的 entities/relations 做归一 + 合并。
        受环境变量 ONTOLOGY_SYNONYM_MERGE_ENABLED（默认 true）总开关控制；
        任何异常降级返回原 ont_data，不阻塞写图。
        """
        if os.getenv("ONTOLOGY_SYNONYM_MERGE_ENABLED", "true").lower() not in ("1", "true", "yes", "on"):
            return ont_data
        try:
            from ..repository.ontology_synonym_repository import OntologySynonymRepository
            from .synonym_normalizer import build_synonym_index, normalize_ont_data

            async with get_db_session() as session:
                groups = await OntologySynonymRepository(session).list_all_by_kb(tenant_id, kb_id)
            index = build_synonym_index(groups)
            if not index:
                return ont_data
            before = len(ont_data.get("entities", []) or [])
            result = normalize_ont_data(ont_data, index)
            after = len(result.get("entities", []) or [])
            logger.info(
                "Synonym normalize: kb=%s groups=%d entities %d→%d",
                kb_id, len(groups), before, after,
            )
            return result
        except Exception as e:
            logger.warning("Synonym normalize skipped (degraded): kb=%s err=%s", kb_id, e)
            return ont_data

    async def _handle_completed(self, doc, status_info: dict, reconcile_source: str = "first") -> str:
        """Handle completed task: write Neo4j ontology (if any), then mark READY.

        reconcile_source: "first"（首次入库收尾）或 "ontology_retry"（本体重试收尾），
        用于区分 e2e_ready_ms 口径（重试路径含多轮等待，不可与首次比较）。
        """
        # [jonex] P0-I 代次 fencing：任务代次早于文档当前 content_generation → 整体作废，
        # 不改状态 / 不删数据 / 不覆盖 rag_doc_ids（交给最新代次任务收敛）。
        task_generation = int(status_info.get("content_generation", 0) or 0)
        doc_generation = int(getattr(doc, "content_generation", 0) or 0)
        if task_generation < doc_generation:
            logger.info(
                "Reconcile→skip(stale generation): doc_id=%s task_gen=%s doc_gen=%s",
                doc.id, task_generation, doc_generation,
            )
            return "skipped"

        ont_status = status_info.get("ontology_status", "pending")
        ont_data = status_info.get("ontology_data")
        ont_error = status_info.get("ontology_error")
        kb_id = (doc.knowledge_base_id or (doc.extra_metadata or {}).get("knowledge_base_id", ""))
        # worker 透传的分阶段耗时（见 docs/ingestion-timing-metrics-design.md §3.4 C）
        # 兼容 v1(dict) 与 v2(list) 两种 stage_timings 形态
        stage_timings_raw = status_info.get("stage_timings")
        worker_total_ms, worker_timings = _normalize_stage_timings(stage_timings_raw)
        pipeline_version = _detect_pipeline_version(stage_timings_raw)

        # [jonex] P1-E schema 版本 fencing：任务用的 schema 版本与文档目标版本不一致 → 丢弃
        # 本体结果（不 delete_by_document / 不 merge），文档本体保持 PENDING 等目标版本任务。
        task_schema_version = int(status_info.get("schema_version", 0) or 0)
        task_schema_hash = status_info.get("schema_hash") or None
        target_schema_version = getattr(doc, "ontology_target_schema_version", None)
        schema_fenced = bool(
            target_schema_version is not None
            and task_schema_version
            and task_schema_version != target_schema_version
        )
        if schema_fenced and ont_status == "completed" and ont_data:
            logger.info(
                "Ontology result fenced (stale schema): doc_id=%s task_ver=%s target_ver=%s",
                doc.id, task_schema_version, target_schema_version,
            )

        # Step 1: Neo4j ontology write (before PG, consistency design)
        neo4j_ok = True
        neo4j_write_ms = None
        if not schema_fenced and ont_status == "completed" and ont_data:
            _t_neo4j = time.perf_counter()
            try:
                gdao = OntologyGraphRepository(get_neo4j_driver())
                # 先清掉本文档此前写入的本体贡献，再重写。
                # 否则实体重新归类（entity_type 变化，如 unknown→Product）会因 MERGE 主键含
                # entity_type 而新建节点、旧节点残留，导致重复。
                await gdao.delete_by_document(doc.tenant_id, doc.id)
                # P1：本文档写入前清空端点解析缓存，避免命中上一文档/旧状态的解析结果
                gdao.reset_endpoint_cache()
                # [jonex] KB 级同义词归一（效果 Y：实体归并）——写图前把同义词组内不同表述
                # 归一到 canonical 并统一 entity_type，使 MERGE 主键相同的节点自然合并。
                # 直查 DB（强一致，正确性锚点）；失败降级不阻塞写图。
                ont_data = await self._apply_synonyms(doc.tenant_id, kb_id, ont_data)
                # 批量预取 embedding_hash，消除 merge_entity 循环内的 N+1 查询
                hash_cache = await gdao.get_embedding_hashes(doc.tenant_id, kb_id)
                for ent in ont_data.get("entities", []):
                    await gdao.merge_entity(doc.tenant_id, kb_id, doc.id, ent, hash_cache=hash_cache)
                for rel in ont_data.get("relations", []):
                    await gdao.merge_relation(doc.tenant_id, kb_id, doc.id, rel)
                neo4j_write_ms = int((time.perf_counter() - _t_neo4j) * 1000)
                logger.info(
                    "Ontology written: doc_id=%s, entities=%d, relations=%d",
                    doc.id,
                    len(ont_data.get("entities", [])),
                    len(ont_data.get("relations", [])),
                )
            except Exception as e:
                neo4j_write_ms = int((time.perf_counter() - _t_neo4j) * 1000)
                logger.error("Neo4j ontology write failed for doc %s: %s", doc.id, e)
                neo4j_ok = False

        # Step 2: PG status update
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            await repo.set_status(
                doc,
                DocStatus.READY,
                rag_doc_ids=status_info.get("lightrag_doc_ids") or status_info.get("doc_ids") or [],
            )

            if schema_fenced and ont_status == "completed":
                # 本体结果按目标版本作废：保持 PENDING 等目标版本任务重抽，不写 applied
                await repo.set_ontology_status(doc, OntologyStatus.PENDING)
            elif ont_status == "completed" and neo4j_ok:
                # [jonex] P1-E：写图成功后记录已应用的 schema 版本/hash
                await repo.set_ontology_status(
                    doc, OntologyStatus.READY,
                    applied_schema_version=(task_schema_version or None),
                    applied_schema_hash=task_schema_hash,
                )
            elif ont_status == "failed":
                await repo.set_ontology_status(doc, OntologyStatus.FAILED, error=ont_error or "本体抽取失败")
            elif not neo4j_ok:
                await repo.set_ontology_status(doc, OntologyStatus.FAILED, error="Neo4j 本体写入失败")

            await session.commit()

        # 端到端墙钟：created_at 为 naive UTC（TimestampMixin: default=datetime.utcnow），
        # 必须用 datetime.utcnow() 作差（详见设计文档 §3.1 #9）。
        e2e_ready_ms = None
        if doc.created_at is not None:
            e2e_ready_ms = int((datetime.utcnow() - doc.created_at).total_seconds() * 1000)

        logger.info("Reconcile→READY: doc_id=%s, chunks=%d", doc.id,
                     len(status_info.get("lightrag_doc_ids") or status_info.get("doc_ids") or []))
        logger.info(
            "reconcile_timing doc_id=%s source=%s pipeline_version=%s neo4j_write_ms=%s e2e_ready_ms=%s worker_total_ms=%s",
            doc.id,
            reconcile_source,
            pipeline_version or "unknown",
            neo4j_write_ms,
            e2e_ready_ms,
            worker_total_ms,
            extra={
                "event": "reconcile_timing",
                "tenant_id": doc.tenant_id,
                "knowledge_base_id": kb_id,
                "document_id": str(doc.id),
                "status": "ready",
                "reconcile_source": reconcile_source,
                "pipeline_version": pipeline_version,
                "neo4j_write_ms": neo4j_write_ms,
                "e2e_ready_ms": e2e_ready_ms,
                "worker_total_ms": worker_total_ms,
                **worker_timings,
            },
        )
        schedule_emit({
            "tenant_id": doc.tenant_id,
            "log_type": "TASK",
            "action": "document.parse_done",
            "outcome": "SUCCESS",
            "service_name": "knowledge_base",
            "resource": ResourceType.DOCUMENT.value,
            "resource_id": str(doc.id),
            "duration_ms": worker_total_ms,
            "request_params": {
                "reconcile_source": reconcile_source,
                "neo4j_write_ms": neo4j_write_ms,
                "e2e_ready_ms": e2e_ready_ms,
            },
        })
        return "updated"

    @staticmethod
    def _cleanup_stuck_timeout(status_info: dict) -> float:
        """[jonex] R5-a：cleanup 动态超时公式 = BASE + PER_DOC × cleanup_total，套 CEIL 上限。

        供 patrol（processing+cleanup 盲区）与 _handle_failed（failed+cleanup 已覆盖）
        共享同一口径。
        """
        base = int(os.getenv("RECONCILE_CLEANUP_BASE_SEC", "600"))
        per_doc = int(os.getenv("RECONCILE_CLEANUP_PER_DOC_SEC", "15"))
        ceil = int(os.getenv("RECONCILE_CLEANUP_CEIL_SEC", "21600"))
        cleanup_total = int(status_info.get("cleanup_total", 0) or 0)
        return min(ceil, base + per_doc * cleanup_total)

    async def _handle_failed(self, doc, status_info: dict) -> str:
        """Handle failed task. Try storage fallback first before finalizing failure."""
        # [jonex] P0-J：cleanup 进行中的任务对 storage fallback 免疫——保持 PARSING，
        # 不因 LightRAG 里仍有（旧）数据就恢复 READY，避免绕过未完成的清理。
        if status_info.get("current_step") == "cleanup":
            # [jonex] 3-A + R5-a：cleanup 不再无限期 skip，按删除量动态超时判死。
            stuck_timeout = self._cleanup_stuck_timeout(status_info)
            cleanup_total = int(status_info.get("cleanup_total", 0) or 0)
            pending = int(status_info.get("cleanup_pending_count", 0) or 0)

            # 计时基准：doc.updated_at（进入 cleanup 后对账 skip 不再刷新，可作卡死时长代理）
            now = datetime.now()  # [jonex] P0-2: naive 本地时间，与 DB 写入口径一致
            updated_at = doc.updated_at
            elapsed = 0.0
            if updated_at is not None:
                if updated_at.tzinfo is not None:
                    updated_at = updated_at.astimezone().replace(tzinfo=None)
                elapsed = (now - updated_at).total_seconds()

            if elapsed >= stuck_timeout:
                err = (
                    f"补偿清理未收敛（cleanup 卡死 {elapsed/60:.0f} 分钟，"
                    f"待删 {pending}/{cleanup_total}），请删除文档后重新上传"
                )
                async with get_db_session() as session:
                    repo = KnowledgeDocumentRepository(session)
                    await repo.set_status(doc, DocStatus.FAILED, error_message=err)
                    await session.commit()
                logger.warning(
                    "Reconcile→FAILED(cleanup stuck): doc_id=%s elapsed=%.0fmin "
                    "pending=%d/%d timeout=%ds",
                    doc.id, elapsed / 60, pending, cleanup_total, stuck_timeout,
                )
                return "updated"

            logger.info(
                "Reconcile→keep %s (cleanup in progress): doc_id=%s elapsed=%.0fmin "
                "pending=%d/%d timeout=%ds",
                doc.status, doc.id, elapsed / 60, pending, cleanup_total, stuck_timeout,
            )
            return "skipped"
        # 代次 fencing：旧代次任务的失败结果不改文档状态（交给最新代次收敛）
        task_generation = int(status_info.get("content_generation", 0) or 0)
        if task_generation < int(getattr(doc, "content_generation", 0) or 0):
            logger.info(
                "Reconcile→skip failed(stale generation): doc_id=%s task_gen=%s doc_gen=%s",
                doc.id, task_generation, getattr(doc, "content_generation", 0),
            )
            return "skipped"

        # If LightRAG has the data, recover to READY instead of FAILED
        rag_doc_ids = await self._verify_via_storage(doc)
        if rag_doc_ids:
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                await repo.set_status(doc, DocStatus.READY, rag_doc_ids=rag_doc_ids)
                await session.commit()
            logger.info("Reconcile→READY(via failed-task storage fallback): doc_id=%s", doc.id)
            return "updated"

        error_msg = status_info.get("error") or status_info.get("message") or "RAG 解析失败"
        worker_total_ms, _ = _normalize_stage_timings(status_info.get("stage_timings"))
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            await repo.set_status(doc, DocStatus.FAILED, error_message=error_msg)
            await session.commit()
        logger.info("Reconcile->FAILED: doc_id=%s, error=%s", doc.id, error_msg)
        schedule_emit({
            "tenant_id": doc.tenant_id,
            "log_type": "TASK",
            "action": "document.parse_failed",
            "outcome": "FAILED",
            "service_name": "knowledge_base",
            "resource": ResourceType.DOCUMENT.value,
            "resource_id": str(doc.id),
            "error_message": error_msg[:1000],
            "duration_ms": worker_total_ms,
        })
        return "updated"

    async def _handle_not_found(self, doc) -> str:
        """Task state lost (Redis expired / container restart). Try storage fallback."""
        _t_fallback = time.perf_counter()
        rag_doc_ids = await self._verify_via_storage(doc)
        storage_fallback_ms = int((time.perf_counter() - _t_fallback) * 1000)
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            if rag_doc_ids is not None:
                await repo.set_status(doc, DocStatus.READY, rag_doc_ids=rag_doc_ids)
                await session.commit()
                logger.info(
                    "Reconcile→READY(via storage fallback): doc_id=%s, chunks=%d",
                    doc.id, len(rag_doc_ids),
                )
                schedule_emit({
                    "tenant_id": doc.tenant_id,
                    "log_type": "TASK",
                    "action": "document.parse_recover",
                    "outcome": "SUCCESS",
                    "service_name": "knowledge_base",
                    "resource": ResourceType.DOCUMENT.value,
                    "resource_id": str(doc.id),
                    "duration_ms": storage_fallback_ms,
                })
            else:
                err = (
                    f"RAG 任务状态丢失（可能 atomic-rag 容器已重启），"
                    f"原 task_id={doc.rag_task_id}，请删除文档后重新上传"
                )
                await repo.set_status(doc, DocStatus.FAILED, error_message=err)
                await session.commit()
                logger.info("Reconcile→FAILED(task lost): doc_id=%s, task_id=%s", doc.id, doc.rag_task_id)
                schedule_emit({
                    "tenant_id": doc.tenant_id,
                    "log_type": "TASK",
                    "action": "document.parse_recover",
                    "outcome": "FAILED",
                    "service_name": "knowledge_base",
                    "resource": ResourceType.DOCUMENT.value,
                    "resource_id": str(doc.id),
                    "error_message": err[:1000],
                    "duration_ms": storage_fallback_ms,
                })
        return "updated"

    # ── ontology retry ─────────────────────────────────────────

    async def _retry_ontology_one(self, doc) -> bool:
        """Retry ontology extraction for a single doc. Returns True if a new task was queued."""
        kb_id = (doc.knowledge_base_id or (doc.extra_metadata or {}).get("knowledge_base_id", ""))

        # Step 0: Ensure compiled schema exists before retry (Phase 4.2)
        schema = None
        schema_version = 0
        try:
            from .ontology_compiler import OntologyCompiler
            schema = await OntologyCompiler().get_compiled_schema(doc.tenant_id, kb_id, auto_compile=True)
            if schema is None:
                logger.warning(
                    "Ontology retry skipped - no compiled schema for doc %s (KB %s)",
                    doc.id, kb_id,
                )
                return False
            schema_version = int(schema.get("schema_version", 0) or 0)
        except Exception as e:
            logger.warning("Compiled schema check failed for doc %s, proceeding anyway: %s", doc.id, e)
            if schema is None:
                return False

        # Check retry limit
        retry_count = doc.ontology_retry_count or 0
        if retry_count >= MAX_ONTOLOGY_RETRIES:
            logger.warning(
                "Ontology retry limit reached (%d/%d) for doc %s, marking failed",
                retry_count, MAX_ONTOLOGY_RETRIES, doc.id,
            )
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                await repo.set_ontology_status(
                    doc, OntologyStatus.FAILED,
                    error=f"本体重试次数已达上限 ({retry_count}/{MAX_ONTOLOGY_RETRIES})",
                )
                await session.commit()
            return False

        # 仅当文档已处于 EXTRACTING 时，才轮询既有任务并据其结果收尾。
        # EXTRACTING ⟹ 本对账循环此前已发起过一次 ontology-only 重抽，且彼时已把
        # rag_task_id 改写为该重抽任务，因此此处 rag_task_id 指向的是“重抽任务”，可安全收尾。
        #
        # 对 PENDING / FAILED 文档：rag_task_id 可能仍是最初的“入库任务”，其 Redis 缓存里
        # 带着旧的 ontology_data。若用它收尾，会把旧的（无描述 / 旧 schema）结果回写 Neo4j，
        # 且 retry_count 不增、永不触发新抽取（历史 bug）。故 PENDING/FAILED 一律跳过收尾，
        # 直接走下方“触发全新重抽”，不再依赖运维手动清空 rag_task_id。
        if doc.ontology_status == OntologyStatus.EXTRACTING.value and doc.rag_task_id:
            try:
                status_info = await get_rag_client().get_task_status(
                    task_id=doc.rag_task_id,
                    tenant_id=doc.tenant_id,
                )
                rag_status = status_info.get("status") or status_info.get("state", "")
                if rag_status in ("processing", "pending"):
                    logger.debug("Ontology retry task still running: doc_id=%s, task_id=%s", doc.id, doc.rag_task_id)
                    return False
                if rag_status == "completed":
                    ont_status = status_info.get("ontology_status")
                    if ont_status == "completed" and status_info.get("ontology_data"):
                        # 在途重抽任务已完成 — 收尾写入 Neo4j + 置 READY
                        await self._handle_completed(doc, status_info, reconcile_source="ontology_retry")
                        return True
                    # 已完成但无 ontology_data（例如无候选实体）
                    ont_error = status_info.get("ontology_error") or status_info.get("error") or "无候选实体"
                    if retry_count + 1 >= MAX_ONTOLOGY_RETRIES:
                        async with get_db_session() as session:
                            repo = KnowledgeDocumentRepository(session)
                            await repo.set_ontology_status(doc, OntologyStatus.FAILED, error=ont_error)
                            await session.commit()
                        logger.warning("Ontology retry exhausted for doc %s: %s", doc.id, ont_error)
                        return False
                    # 落空 → 继续往下触发新一轮重抽
            except Exception as e:
                logger.warning("Task status query failed for doc %s, skipping: %s", doc.id, e)
                return False

        # [jonex] P1-F 领取协议：CAS 领取（当前状态 → EXTRACTING 占位）→ 提交 atomic-rag →
        # 拿到 task_id 后写 rag_task_id + ++retry；提交失败回退 PENDING、不 ++retry。
        prev_status = doc.ontology_status
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            claimed = await repo.claim_ontology_for_retry(doc)
            await session.commit()
        if not claimed:
            # 其它实例已领取该文档 → 跳过（多实例只领一次）
            logger.debug("Ontology retry skipped (claimed by another instance): doc_id=%s", doc.id)
            return False

        # Trigger new ontology retry (ontology-only, 携带 schema + 版本 + 代次)
        try:
            result = await get_rag_client().retry_ontology_extract(
                document_id=doc.id,
                knowledge_base_id=kb_id,
                tenant_id=doc.tenant_id,
                file_path=doc.file_path,
                ontology_schema=schema,
                schema_version=schema_version,
                content_generation=int(getattr(doc, "content_generation", 0) or 0),
            )
        except Exception as e:
            logger.warning("Retry ontology extract failed for doc %s: %s", doc.id, e)
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                await repo.revert_ontology_status(doc, prev_status)
                await session.commit()
            return False

        retry_task_id = (result or {}).get("task_id", "")
        if not retry_task_id:
            logger.warning("Retry ontology did not return task_id for doc %s", doc.id)
            async with get_db_session() as session:
                repo = KnowledgeDocumentRepository(session)
                await repo.revert_ontology_status(doc, prev_status)
                await session.commit()
            return False

        # 提交成功：保持 EXTRACTING（已由 claim 置位），写 rag_task_id + ++retry
        async with get_db_session() as session:
            repo = KnowledgeDocumentRepository(session)
            await repo.set_ontology_status(doc, OntologyStatus.EXTRACTING, increment_retry=True)
            await repo.set_status(doc, doc.status, rag_task_id=retry_task_id)
            await session.commit()

        logger.info("Ontology retry queued: doc_id=%s, new_task_id=%s", doc.id, retry_task_id)
        return True

    # ── storage fallback ───────────────────────────────────────

    async def _verify_via_storage(self, doc) -> list[str] | None:
        """Confirm document existence via LightRAG storage reader.

        Used when atomic-rag task state is lost (Redis expired / container restarted)
        but the document may have been successfully ingested into LightRAG.

        Matching strategy: extract doc=<id> from LightRAG's file_path field and
        compare with doc.id.  This is more reliable than file_name matching
        because LightRAG prepends a UUID prefix and may change underscores
        (e.g. "年报" → "___").

        Returns:
            rag_doc_ids list if confirmed, None otherwise.
        """
        import re

        kb_id = (doc.knowledge_base_id or (doc.extra_metadata or {}).get("knowledge_base_id", ""))

        try:
            result = await get_rag_client().get_storage_documents(
                knowledge_base_id=kb_id,
                tenant_id=doc.tenant_id,
                keyword=doc.file_name,
                page=1,
                page_size=500,
            )
        except Exception as e:
            logger.warning("Storage lookup failed for doc %s: %s", doc.id, e)
            return None

        items = result.get("items", [])
        total = result.get("total", len(items))
        if total > len(items):
            logger.warning(
                "Storage fallback: total %d exceeds page size for doc %s, may miss rag_doc_ids",
                total, doc.id,
            )

        # Match by document_id in file_path (doc=<uuid>), then fall back to
        # file_name for backward compatibility.
        matched = []
        for item in items:
            fp = item.get("file_path") or ""
            m = re.search(r'doc=([a-f0-9-]+)\|', fp)
            if m and m.group(1) == doc.id:
                matched.append(item)
        if not matched:
            # Fallback: file_name match (legacy)
            matched = [
                item for item in items
                if (
                    item.get("file_name") == doc.file_name
                    or (item.get("file_name") or "").endswith("_" + doc.file_name)
                )
            ]

        if not matched:
            raw_items = [
                {
                    "file_name": i.get("file_name"),
                    "file_path": (i.get("file_path") or "")[:120],
                    "status": i.get("status"),
                }
                for i in items[:5]
            ]
            logger.info(
                "Storage fallback miss: doc_id=%s, file_name=%s, total=%d, sample(5)=%s",
                doc.id, doc.file_name, len(items), raw_items,
            )
            return None

        rag_doc_ids = [item["id"] for item in matched if item.get("id")]
        logger.info("Storage fallback hit: doc_id=%s, rag_doc_ids=%s", doc.id, rag_doc_ids)
        return rag_doc_ids


__all__ = ["ReconciliationService"]
