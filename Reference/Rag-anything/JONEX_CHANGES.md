# RAG-Anything 悦溪（jonex）改动点清单

> 本文件记录悦溪平台对 vendored RAG-Anything（`Reference/Rag-anything/`）源码的改动点，
> 便于后续升级 RAG-Anything 时快速定位、重新 apply。**代码改动均以 `# [jonex]` 注释标记**，
> 可全局搜索 `[jonex]` 定位。约定与 `Reference/LightRAG/JONEX_CHANGES.md` 一致。

## 一、注释规范

- 单行改动：行尾加 `# [jonex]`。
- 代码块改动：块首 `# ── [jonex] <说明> ───`，块尾 `# ── [jonex] end ───`。
- 新增整类/整文件：类/文件头注释标明 `# [jonex] 悦溪新增`。

## 二、改动总览

| 分类 | 目的 |
|------|------|
| 解析器扩展 | 新增内网自建 MinerU（`mineru_selfhost`）解析器，去云化 + 去本地 GPU |
| 健壮性 | 多文件名/字段归一化去重与安全化 |
| 依赖分层 | 把 `mineru[core]` 从核心依赖降为 optional extra `local`，支撑 atomic-rag 镜像瘦身 |

> 说明：仓库中 `mineru_online`（mineru.net 云 API 解析器）、`raganything/asr/*`、
> `raganything/video_analysis/*`（含腾讯 MPS 后端）、`resilience`/`callbacks` 等模块亦为悦溪相关定制/新增，
> 本清单自「MinerU 内网自建接入」起开始系统记录；对应设计见
> `docs/mineru-selfhost-parser-execution-plan.md`。

---

## 三、解析器扩展（feature）

### (A) 新增 `MineruSelfHostParser`（内网 mineru-api 解析器）

| 文件 | 位置 | 说明 |
|------|------|------|
| `raganything/parser.py` | `class MineruSelfHostParser(MineruParser)` | `# ── [jonex] 悦溪新增：内网自建 MinerU (mineru-api) 解析器 ───` |

要点：
- 对接内网自建的 **MinerU 官方 `mineru-api`（FastAPI）** 服务（默认 `http://127.0.0.1:8000`；实际内网地址在 gitignored 的 `deploy/.env` 配），
  区别于 `MineruOnlineParser`（mineru.net 云 v4 签名上传契约）。
- 契约：`POST /tasks`（multipart 上传）→ 轮询 `GET /tasks/{id}`（`pending/processing/completed/failed`）
  → `GET /tasks/{id}/result`（`results.<stem>.content_list` 为 **JSON 字符串**）。
- 仅用标准库（`urllib` / `http.client`），**不依赖本地 mineru 包、不引入第三方 HTTP 库**。
- 复用父类 `MineruParser._FIELD_ALIASES` 做字段归一化；`return_images` 控制是否落盘图片并重写路径。
- 关键方法：`_post_multipart` / `_submit_task` / `_poll_task` / `_fetch_result_item`
  / `_build_content_list` / `_ascii_safe_filename` / `_dump_images`。

环境变量（parser 侧直接读 `os.environ`）：

| 变量 | 默认 | 说明 |
|------|------|------|
| `MINERU_SELFHOST_BASE_URL` | `http://127.0.0.1:8000` | 内网 mineru-api 地址（实际值在 `deploy/.env`） |
| `MINERU_SELFHOST_BACKEND` | `pipeline` | `pipeline` / `hybrid-engine` 等 |
| `MINERU_SELFHOST_LANG` | `ch` | pipeline/hybrid 后端 OCR 语言 |
| `MINERU_SELFHOST_POLL_INTERVAL` | `5` | 轮询间隔（秒） |
| `MINERU_SELFHOST_POLL_TIMEOUT` | `1800` | 轮询总超时（秒） |
| `MINERU_SELFHOST_RETURN_IMAGES` | `false` | 是否拉取解析图片并落盘 |

### (B) 解析器注册（`mineru_selfhost` 接入内置解析器）

| 文件 | 位置（均带 `# [jonex]`） | 说明 |
|------|------|------|
| `raganything/parser.py` | `_BUILTIN_NAMES` | 加入 `mineru_selfhost`（禁止被 `register_parser` 覆盖） |
| `raganything/parser.py` | `SUPPORTED_PARSERS` | 加入 `mineru_selfhost` |
| `raganything/parser.py` | `list_parsers()` 映射 dict | 加入 `"mineru_selfhost": "MineruSelfHostParser"` |
| `raganything/parser.py` | `get_parser()` 分支 | `if parser_name == "mineru_selfhost": return MineruSelfHostParser()` |
| `raganything/parser.py` | `get_parser` docstring / `main()` argparse help / 顶部 description | 文案补 `mineru_selfhost` |

### (C) `_FIELD_ALIASES` 提取为类常量（去重，健壮性）

| 文件 | 位置 | 说明 |
|------|------|------|
| `raganything/parser.py` | `MineruParser._FIELD_ALIASES`（类常量，`# [jonex]`） | 原为 `_read_output_files` / `_read_any_output_files` 内 2 处重复局部 dict |
| `raganything/parser.py` | `_read_output_files` / `_read_any_output_files` | 改为引用 `cls._FIELD_ALIASES` |

### (D) 中文/非 ASCII 文件名安全化（健壮性）

- `MineruSelfHostParser._ascii_safe_filename()`：上传 multipart 时把非 `[A-Za-z0-9._-]` 文件名字符
  替换为 `_`（保留扩展名，MinerU 只按扩展名判类型），避免中文文件名在 `filename="..."` 头里被服务端
  错误解码；单文件任务结果按 `results` 首条兜底匹配，不依赖文件名。

### (E) 单测

| 文件 | 说明 |
|------|------|
| `tests/test_custom_parser.py` | `list_parsers` 数量断言 4→5 / 5→6；`test_register_rejects_builtin_name` 元组补 `mineru_selfhost`；新增 `TestMineruSelfHostParser`（注册 / 环境变量 / `_ascii_safe_filename` / `_build_content_list` / `_fetch_result_item`，全离线） |

---

## 四、依赖分层（build）：`mineru[core]` 降为 optional extra `local`

目的：让 atomic-rag 镜像在 online/selfhost 模式下可去掉 mineru 及其重传递依赖。**三处元数据一致修改**，
保证无论 pip 采用 pyproject 还是 setup.py 都生效：

| 文件 | 改动 |
|------|------|
| `pyproject.toml` | `[project].dependencies` 移除 `mineru[core]`；`[project.optional-dependencies]` 新增 `local = ["mineru[core]"]`（`# [jonex]`） |
| `setup.py` | `extras_require` 新增 `"local": ["mineru[core]"]`（`# [jonex]`） |
| `requirements.txt` | 移除 `mineru[core]` 行，加 `NOTE(jonex)` 说明其移入 `local` extra |

安装约定（由 `deploy/docker/atomic-rag.Dockerfile` 的 `RAG_PROFILE` 控制，见下）：
- `full`：`pip install -e "/opt/raganything[all,local]"`（含本地 mineru CLI）。
- `slim`：`pip install -e "/opt/raganything[image,text]"`（online/selfhost，无 mineru）。

> 安全依据：全仓无任何 `import mineru`，本地解析走 `mineru` CLI 子进程；online/selfhost 从不调用本地 mineru。

---

## 五、平台侧配套改动（不在本目录，登记以便追溯）

| 文件 | 改动 |
|------|------|
| `jonex_core/capability/atomic/rag/lightrag_adapter.py` | 支持 `RAG_PARSER=mineru_selfhost`；记录 `self._parser_name`；CLI 专用 kwargs（backend/source）仅对 `RAG_PARSER=mineru` 注入；错误文案补三种模式 |
| `deploy/docker/atomic-rag.Dockerfile` | 新增 `ARG RAG_PROFILE=full`，第 2 层按 profile 条件安装 raganything（full=`[all,local]` / slim=`[image,text]`） |
| `deploy/docker/atomic-rag-requirements.txt` | 移除 `sentence-transformers`（全仓零引用；它与 whisper 是 torch 的唯二来源） |
| `deploy/docker-compose.yml` | `atomic-rag.build.args` 新增 `RAG_PROFILE: ${RAG_PROFILE:-full}` |
| `deploy/.env` / `deploy/.env.example` / `.env.local.example` | MinerU 段重构为三选一 + `MINERU_SELFHOST_*` + `RAG_PROFILE` 说明 |

详见 `docs/mineru-selfhost-parser-execution-plan.md`。

---

## 六、升级 RAG-Anything 时的重放清单

1. 全局搜索 `[jonex]` 定位 `raganything/parser.py` 内的：`MineruSelfHostParser` 整类、`_FIELD_ALIASES` 类常量、
   4 处注册点、docstring/CLI 文案。
2. 重放依赖分层：确认新版 `pyproject.toml` / `setup.py` / `requirements.txt` 是否仍把 `mineru[core]` 列为核心依赖；
   若是，重新降级到 `local` extra。
3. 跑 `tests/test_custom_parser.py` 校验解析器注册契约。
4. atomic-rag 侧按 `RAG_PROFILE=slim/full` 重建镜像并做 selfhost 端到端解析验证（见执行计划 §11）。


## 七、v2 LightRAG 关系响应契约归一化（fix）

| 文件 | 改动 |
|------|------|
| `raganything/service/http_lightrag_client.py` | `get_relationships()` 在 HTTP 客户端边界把 LightRAG 的 `src_id` / `tgt_id` 补齐为平台稳定契约 `source_entity` / `target_entity`，同时保留原字段，修复 v2 本体关系定型和 untyped fallback 均因端点字段缺失而得到 0 条关系的问题。 |
| `tests/test_service/test_http_lightrag_client.py` | 新增关系响应归一化回归测试，覆盖原始字段、已有规范字段及不修改上游响应对象。 |

升级重放：若新版 LightRAG 关系端点仍返回 `src_id` / `tgt_id`，保留该客户端边界映射；若上游已返回 `source_entity` / `target_entity`，当前兼容逻辑会优先使用规范字段。


## 八、v2 chunk 命名空间 token 注入回归修复（fix）

**现象**：v2 入库某文档后 LightRAG 图中该文档实体数为 0（`Task ... completed entities=0`），
本体阶段读不到候选实体 → `无候选实体` → 对账重试 3 次耗尽 → `ontology_status=FAILED`
（`reconciliation_service.py:481 Ontology retry limit reached (3/3)`）。

**根因**：v1 `LightRAGAdapter` 在 `upload_text` 前给每个 chunk 文本末尾注入
`<!--yx:{md5(tenant|kb|doc)[:8]}-->` 命名空间 token，使内容 hash 带上 (tenant, kb, doc)
隔离维度，避免 LightRAG 按 chunk 内容全局去重把跨文档/跨 KB 的相同文本合并（合并后只有首篇
文档抽到实体、其余文档图为空）。v2 迁移到 `PushChunksStage` 后**遗漏该 token**，
`_collect_text_chunks` / `_collect_multimodal_chunks` 上传的是原始文本；而消费侧
`task_manager.py` 本体抽取仍按 `<!--yx:[a-f0-9]{8}-->` 过滤该 token，证明契约期待其存在。

| 文件 | 改动 |
|------|------|
| `raganything/pipeline/stages.py` | 新增 `_inject_ns_token(text, tenant_id, kb_id, document_id)`；`_collect_text_chunks` 文本/表格 chunk 与 `_collect_multimodal_chunks` 的 summary/video_frame/audio_segment chunk 追加该 token 后再入队上传（对齐 v1）。新增 `import hashlib`。 |

**验证**：`py_compile stages.py` 通过；需重建 atomic-rag 镜像生效。存量已 `entities=0` 的文档
需删除后重新入库（或清 LightRAG 该文档 chunk + 抽取缓存）才能重跑抽取，仅重置 `ontology_status`
无效（图仍为空）。

升级重放：若新版仍走 `PushChunksStage`，保留 `_inject_ns_token` 注入；消费侧过滤正则与
`hexdigest()[:8]` 长度需保持一致。


## 九、v2 ⇄ v1 行为补齐 #4/#5/#6 (2026-07-16)

补齐 v2 HTTP 模式相对 v1 `lightrag_adapter.py` 缺失的三项健壮性/成本/检索正确性行为。
详见 `docs/atomic-rag-v2-v1-parity-fixes-execution-plan.md`。

### (A) #6 逐 chunk 严格确认 doc_id/track_id

区分 TIMEOUT 与硬失败，默认 `RAG_REQUIRE_DOC_IDS=true`（与 v1 对齐）。

| 文件 | 改动 |
|------|------|
| `raganything/pipeline/stages.py` | `PushChunksStage.__init__` 读取 `RAG_REQUIRE_DOC_IDS`（默认 true）；§4 track_status 轮询分类 terminal failed 为 `terminal_hard_failed`；§5 严格模式下硬失败/超时分别返回错误（`LightRAG 入库部分失败：X/Y` / `RAG_PUSH_TIMEOUT`）；ctx 写入 `total_chunk_count`/`failed_chunk_count`/`timeout_chunk_count` |
| `raganything/pipeline/base.py` | `PipelineContext` 新增 `total_chunk_count`/`failed_chunk_count`/`timeout_chunk_count`/`duplicated_chunk_count`/`total_pushed_count` |
| `raganything/service/task_manager.py` | `_execute_pipeline_http` 失败分支持久化 `ctx.collected_doc_ids`→`task.lightrag_doc_ids`；透传 `timeout_chunk_count`；`_resume_track_polling` 区分 terminal failed vs still_pending → `timeout_chunk_count` |
| `raganything/service/models.py` | `TaskInfo` 新增 `timeout_chunk_count`/`duplicated_chunk_count`/`total_pushed_count` |

### (B) #5 全 duplicated 幂等守卫（跳过本体抽取）

所有 chunk 内容重复 → 跳过本体抽取（省 LLM 成本），设 `ontology_status="completed"`。

| 文件 | 改动 |
|------|------|
| `raganything/pipeline/stages.py` | `PushChunksStage._push_one` 收集 `result.status == "duplicated"` 到 `duplicated_indices`；execute §5 计算 `duplicated_chunk_count`/`total_pushed_count` 写入 ctx |
| `raganything/service/task_manager.py` | `_execute_pipeline_http` 本体触发前检查 `all_duplicated`（`total_pushed>0 and duplicated==total_pushed`）→ 跳过 `_run_ontology_extraction`、置 `ontology_status="completed"` |

### (C) #4 parse 解析阶段瞬时错误自动重试

仅对瞬时网络/SSL 错误指数退避重试，硬失败快速返回。

| 文件 | 改动 |
|------|------|
| `raganything/pipeline/stages.py` | 新增 `_TRANSIENT_PARSE_ERROR_MARKERS` + `_is_transient_parse_error()` 辅助函数（对齐 v1）；`ParseStage.__init__` 读取 `RAG_PARSE_RETRY_MAX`（默认 3）/`RAG_PARSE_RETRY_BASE_SEC`（默认 2.0）；原有 try/except NotImplementedError 替换为 `_parse_with_retry()` 方法，primary/fallback 均套重试循环，每次重试前检查 `ctx.cancel_event` |

### 新增环境变量

| 变量 | 默认 | 作用 |
|------|------|------|
| `RAG_REQUIRE_DOC_IDS` | `true` | 严格要求逐 chunk 确认 doc_id |
| `RAG_PARSE_RETRY_MAX` | `3` | 解析瞬时错误最大重试次数（含首次） |
| `RAG_PARSE_RETRY_BASE_SEC` | `2.0` | 解析重试指数退避基数 |

升级重放：三处改动均以 `# [jonex]` 标记，集中在 `stages.py`/`base.py`/`task_manager.py`/`models.py`。


## 十、v2 batch_track_status pending 脏残留误判超时修复（2026-07-16）

**现象**：文档入库成功（collected_doc_ids 有值），但 PushChunksStage 报 `RAG_PUSH_TIMEOUT: 600.0s`，
而实际轮询几秒就退出了，并未等待 10 分钟。

**根因**：`batch_track_status` 的 `pending` dict 在循环外声明、循环内不清理。一个 chunk 第 1 轮
还在 `processing`（写进 `pending`），第 2 轮才 `completed`（写进 `terminal`）——但没有任何地方把它从
`pending` 里删掉。结果它同时留在 `terminal` 和 `pending`。`stages.py` §5 按 `pending_track_ids`
判超时，把已完成的 chunk 误判为 timed_out → 严格模式直接报 `RAG_PUSH_TIMEOUT`。

**修复**：终态 track 进 `terminal` 时同步从 `pending` 剔除（`pending.pop(tid, None)`），一行核心改动。

| 文件 | 改动 |
|------|------|
| `raganything/service/http_lightrag_client.py` | `batch_track_status` 轮询循环内 `terminal[tid] = result` 后追加 `pending.pop(tid, None)`（`# [jonex]`） |
| `tests/test_service/test_http_lightrag_client.py` | 新增 `TestBatchTrackStatusNoDirtyPending`：跑真实 `batch_track_status` 实现（mock `_poll_one_track`），验证 processing→completed 转换后 pending 不含已完成 track |

升级重放：若新版 `batch_track_status` 重构轮询逻辑，需确保终态 track 不会残留在 pending/未完成集合中。


## 十一、v2 batch_track_status 并发控制（2026-07-16）

**现象**：V2 `batch_track_status` 用 `asyncio.gather` 一次性并发所有 remaining track_ids，
大文档数百 chunk 时同时建立数百 HTTP 连接，无任何限流机制。V1 有 `RAG_TRACK_POLL_CONCURRENCY=8` 来控制。

**修复**：`HttpLightRagClient.__init__` 读取 `RAG_TRACK_POLL_CONCURRENCY`（默认 8），
`batch_track_status` 轮询循环内用 `asyncio.Semaphore` 包装 `_poll_one_track`，限制同时进行的
track_status 查询数。

| 文件 | 改动 |
|------|------|
| `raganything/service/http_lightrag_client.py` | `__init__` 新增 `self._track_poll_concurrency`；`batch_track_status` 用 semaphore 限流（`# [jonex]`） |

### 新增环境变量

| 变量 | 默认 | 作用 |
|------|------|------|
| `RAG_TRACK_POLL_CONCURRENCY` | `8` | track_status 轮询并发上限 |

升级重放：若新版 `batch_track_status` 重构轮询逻辑，保留 semaphore 限流避免连接风暴。


## 十二、parser.py 拆包后 CLI 顶部 description 文案补回（review, 2026-07-17）

**背景**：`MineruSelfHostParser` 原在单体 `raganything/parser.py`（commit `243dd4c`）实现，
后 `parser.py` 重构为 `raganything/parsers/` 包（`mineru.py` / `registry.py` / `__init__.py`）。
本次 review 逐方法比对拆包后实现与 `243dd4c` 原始实现，核心类、`_FIELD_ALIASES`、4 处注册点、
`__init__` 导出、`--parser` argparse help 均已完整保留，**仅顶部 `ArgumentParser(description=...)` 漏补**
（见上文 §三(B) 记录的「顶部 description」项，拆包时只补了 `--parser` help，遗漏了顶部 description）。

| 文件 | 位置 | 改动 |
|------|------|------|
| `raganything/parser.py` | `main()` 内 `argparse.ArgumentParser(description=...)` | description 由 `"...MinerU online, Docling, or PaddleOCR"` 补为 `"...MinerU online, MinerU self-host, Docling, or PaddleOCR"` |

纯 CLI 帮助文案，不影响运行时解析行为。`py_compile` `parser.py` / `parsers/{mineru,registry,__init__}.py` 全部通过。

升级重放：全局搜索 `[jonex]` 及本节，确认 `parser.py` 顶部 description 与 `--parser` help 两处文案都含 `mineru_selfhost` / `MinerU self-host`。


## 十三、P3 push_chunks 阶段信号 + VLM base64 caption 适配器（2026-07-23）

批次 2-A + 2-C：透出 P3 推送入图阶段信号供 kb-service 对账置 INGESTING；
修复图片 VLM 描述调用约定不匹配（base64 vs file://）。

详见 `docs/kb-doc-status-ingesting-and-patrol-plan.md` §4、§6、§12。

### (A) PushChunksStage 发 on_push_chunks_start → current_step="push_chunks"

| 文件 | 改动 |
|------|------|
| `raganything/pipeline/stages.py` | `PushChunksStage.execute` 起始 dispatch `on_push_chunks_start`（`# [jonex] Callback: push_chunks start`） |
| `raganything/callbacks.py` | `ProcessingCallback` 新增 `on_push_chunks_start` 空实现（`# [jonex] 批次 2-A`） |
| `raganything/service/task_manager.py` | `ProgressTrackingCallback` 新增 `on_push_chunks_start` 处理器：`current_step="push_chunks"`、`progress=0.92`（`# [jonex] 批次 2-A`） |

信号值定稿为 `"push_chunks"`，经 `get_task_status` 内存实时透出，kb-service 对账据此置 `DocStatus.INGESTING`。

### (B) VLM base64 caption 适配器

| 文件 | 改动 |
|------|------|
| `raganything/models/adapters.py` | 新增 `base64_caption_adapter(bound)`：签名 `(prompt, image_data=base64, system_prompt=...)` → `data:` image_url（`# [jonex] 批次 2-C`） |
| `raganything/models/__init__.py` | 导出 `base64_caption_adapter` |
| `raganything/service/model_factory.py` | `build_vlm()` 返回值从 `Callable` 改为 `dict {"func": ..., "bound": ...}` |
| `raganything/processor_builder.py` | `_create_image` 优先用 `_vlm_bound` + `base64_caption_adapter`，fallback 到原有 `_vlm_func` |
| `raganything/raganything.py` | 新增 `vlm_bound` 字段；`_init_processors_via_builder` 传递 `vlm_bound` 到 builder |
| `atomic-rag-server-v2.py` | 解构 `build_vlm()` 返回 dict，传 `vlm_bound` 到 `RAGAnything` |

升级重放：若新版 `PushChunksStage.execute` 重构，保留起始 dispatch `on_push_chunks_start`；
若新版 `build_vlm()` 签名变化，确认 `vlm_bound` 仍能从 `model_factory` 传递到 image processor factory。

### (C) 平台侧配套改动

| 文件 | 改动 |
|------|------|
| `jonex_core/capability/atomic/rag/lightrag_adapter_v2.py` | `_assemble_stack` 解构 `build_vlm()` 返回 dict，传 `vlm_bound` 到 `RAGAnything` |
| `atomic-rag-server-v2.py` | 同上，解构 `build_vlm()` 返回 dict，传 `vlm_bound` 到 `RAGAnything` |

## 十四、chunk_id 透传 + 单片直查（RAG fallback 召回明细 / 查看单个 Chunk）（2026-07-24）

> 关联设计：`docs/rag-fallback-recall-detail-and-chunk-lookup-plan.md`（§3.2、§9 P9~P11）。
> 关联 LightRAG 侧改动：`Reference/LightRAG/JONEX_CHANGES.md` §十。
> 生效前提：vendored 改动，须**重建 atomic-rag 镜像**。所有改动带 `# [jonex]` 标记。

### (A) chunk_id 透传（v2 生产检索路径）

**背景**：LightRAG references 透出 `chunk_ids` 后，recalls 的 `chunk_id` 仍恒 null。根因是 v2 生产路径
（REMOTE：kb-service → atomic-rag → raganything）组装 references 时丢弃了 `chunk_ids`（此前只改了
v1 `jonex_core/.../lightrag_adapter.py::LightRAGServerClient.query()`，生产不走）。

| 文件 | 位置 | 说明 |
|---|---|---|
| `raganything/service/task_manager.py` | `_query_via_http`（约 L692-716） | `parse_file_source` 组装 `refs` 的循环中透传 `chunk_ids`：`parsed["chunk_ids"]=chunk_ids; parsed["chunk_id"]=chunk_ids[0]`（本平台 file_source 按 chunk 唯一，取首个） |

### (B) 单片直查 `get_chunk`（按 chunk_id 直连 LightRAG text_chunks）

| 文件 | 位置 | 说明 |
|---|---|---|
| `raganything/service/http_lightrag_client.py` | `get_chunk_by_id` | 新增：`GET /documents/chunks/{chunk_id}`（带 workspace header），返回单片 chunk |
| `raganything/service/task_manager.py` | `get_chunk_by_id` | 新增：调 http_client；`httpx.HTTPStatusError` 404 → None |
| `atomic-rag-server-v2.py` | `@ActionRegistry.register("get_chunk")` | 新增 action handler `handle_get_chunk`；None → 40405 |

### (C) 既有缺陷 TODO：`get_document_chunks`（"查看文档 Chunk 列表"接口）

| 文件 | 位置 | 说明 |
|---|---|---|
| `raganything/service/task_manager.py` | `get_document_chunks` docstring | 打 `# [jonex][TODO]`：该实现对已入库文档恒返回空/结构不符（查 `/documents/paginated` 返回文档级 `{documents}` 而非 text_chunks，键名/层级不符 `{doc_id,total,chunks}` 契约，且 doc_id 语义不匹配——LightRAG 用 `doc-<md5>`、KB id 仅在 file_path 的 `doc=` 锚点）。修复方案见该 TODO 与计划 §9(P11)。单片直查已由 (B) 解决、不受影响 |

**平台侧配套**（不在本目录，登记以便追溯）：

| 文件 | 改动 |
|---|---|
| `jonex_core/capability/atomic/rag/client.py` | `RemoteRAGClient.get_chunk_by_id` 发 action `get_chunk`，40405→None |
| `jonex_core/capability/atomic/rag/lightrag_adapter.py` | v1 兼容路径 `LightRAGServerClient.query()` 解析 `chunk_ids`（生产不走） |
| `capabilities/knowledge_base/services/document_service.py` | `get_chunk` 改直查 `get_chunk_by_id`（不经 get_doc_chunks）+ `doc=` 锚点归属校验 + 清理 `<!--yx:...-->` 标记；`get_document_chunks` 补 TODO |
| `capabilities/knowledge_base/services/search_service.py` | `_rag_fallback_multi` recalls 明细带 `chunk_id`（来自透传） |

升级重放：(A) 保留 `_query_via_http` 的 chunk_ids 透传；(B) 保留 `get_chunk_by_id` 全链路 + action 注册；
(C) get_document_chunks 若重构，按 TODO 用 `doc=` 锚点枚举 text_chunks 返回契约结构。
