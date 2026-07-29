-- ============================================================
-- 触发单 KB 本体重抽（Phase C 存量回填）
-- ============================================================
-- 原理：knowledge-base-service 的 30s reconcile 循环会自动扫描
--   ontology_status IN ('pending','failed','extracting') 的文档并重抽。
--   本脚本把目标 KB 的"已解析(ready)"文档置回 pending 并清零重试计数，
--   循环将在 ≤30s 内接手，调用 atomic-rag 重新抽取（带新代码的 description + 边）。
--
-- 用法（在 deploy/ 目录）：
--   1) 改下方 \set 的 tenant / kb 两个值
--   2) docker exec -i jonex-postgres psql -U jonex -d jonex < scripts/trigger_kb_ontology_reextract.sql
--   2 win命令) Get-Content scripts\trigger_kb_ontology_reextract.sql -Raw | docker exec -i jonex-postgres psql -U jonex -d jonex 
--
-- 安全：强制按 tenant_id + knowledge_base_id 限定，只动 ready 且未软删的文档。
-- ============================================================

\set tenant '1'
\set kb     '1'

-- ① 预检：将影响多少文档
SELECT ontology_status, count(*)
FROM knowledge_base.knowledge_documents
WHERE tenant_id = :'tenant'
  AND knowledge_base_id = :'kb'
  AND status = 'ready'
  AND is_deleted = 0
GROUP BY ontology_status;

-- ② 触发重抽
UPDATE knowledge_base.knowledge_documents
SET ontology_status    = 'pending',
    ontology_retry_count = 0,
    ontology_error     = NULL,
    rag_task_id        = NULL,   -- 关键：清掉旧入库任务，否则 reconcile 会用旧缓存结果回写，不触发新抽取
    updated_at         = now()
WHERE tenant_id = :'tenant'
  AND knowledge_base_id = :'kb'
  AND status = 'ready'
  AND is_deleted = 0;

-- ③ 复核：置位后的状态分布
SELECT ontology_status, count(*)
FROM knowledge_base.knowledge_documents
WHERE tenant_id = :'tenant'
  AND knowledge_base_id = :'kb'
  AND is_deleted = 0
GROUP BY ontology_status;
