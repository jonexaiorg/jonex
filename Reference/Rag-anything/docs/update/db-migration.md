# DB Migration — content_summary 列扩容

**日期**: 2026-07-15  
**相关**: `update_chunk` 链路修复 — 方案 A  
**影响**: PostgreSQL `LIGHTRAG_DOC_STATUS` 表

---

## 背景

LightRAG 在存储文档处理状态时，`content_summary` 列被限制为 `varchar(255)`，导致存储的 chunk 内容被截断。客户端无法从截断内容计算准确的 KV 存储层 `chunk_id`，导致 `update_chunk` 永远 404。

修复方案：将列扩容至 `varchar(4096)`，使完整 chunk 内容可被存储和读取。

---

## Migration SQL

**文件**: `deploy/postgres/migrations/008_extend_doc_status_summary.sql`

```sql
-- 008_extend_doc_status_summary.sql
-- 扩容 content_summary 列以支持完整 chunk 内容（从 255 → 4096 字符）
ALTER TABLE LIGHTRAG_DOC_STATUS
  ALTER COLUMN content_summary TYPE varchar(4096);
```

---

## 执行方式

### 方式 1：容器内直连（推荐）

```bash
docker exec jonex-postgres psql -U jonex -d jonex \
  -c "ALTER TABLE LIGHTRAG_DOC_STATUS ALTER COLUMN content_summary TYPE varchar(4096);"
```

**前提**: LightRAG 使用 PostgreSQL doc_status 存储（`LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage`），且表已创建。

> **注意**: 如果 LightRAG 使用 JSON 文件存储（`JsonDocStatusStorage`），则不需要此 migration。当前部署中 LightRAG 使用 JSON 存储，此 migration 为 PG 模式预留。

### 方式 2：挂载 migration 目录（自动执行）

将 SQL 文件放入 `deploy/postgres/migrations/` 目录，PostgreSQL 容器启动时会自动执行 `.sql` 文件（如果 compose 配置了 migration volume）。

### 方式 3：Docker compose exec

```bash
cd deploy
docker compose exec -T postgres psql -U jonex -d jonex < postgres/migrations/008_extend_doc_status_summary.sql
```

---

## 验证

```bash
docker exec jonex-postgres psql -U jonex -d jonex -c "
  SELECT column_name, character_maximum_length
  FROM information_schema.columns
  WHERE table_name = 'lightrag_doc_status' AND column_name = 'content_summary';
"
```

预期输出：
```
  column_name    | character_maximum_length
-----------------+--------------------------
 content_summary |                     4096
```

如果表不存在：
```
ERROR:  relation "lightrag_doc_status" does not exist
```
→ LightRAG 未使用 PostgreSQL doc_status 存储，无需执行。

---

## 回滚

如需回退到原宽度：

```sql
ALTER TABLE LIGHTRAG_DOC_STATUS
  ALTER COLUMN content_summary TYPE varchar(255);
```

> **警告**: 回滚会截断已有数据中超过 255 字符的部分。
