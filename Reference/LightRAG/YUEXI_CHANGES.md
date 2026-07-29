
## 2026-07-24 — 方案 C：MPS 视频分析 COS URL 链路修复

**问题**：v2 管线中 `_localize_input()` 将视频从 COS 下载到本地后，`storage_backend` 被改写为 `"local"`，但 `VideoModalProcessor` 在 `MPS_ENABLED=true` 时无条件选择 MPS 后端，导致 MPS 收到本地路径而无法提取 COS key，报 `MPSBackendError: Cannot extract COS key from URL`。

**修复**（方案 C：MPS 和本地 ffmpeg 两条独立路径）：

| 文件 | 改动 |
|---|---|
| `lightrag_adapter_v2.py` | 新增 MPS 辅助函数 `_MPS_ENABLED`、`_is_video_file()`、`_build_mps_cos_url()`；`_localize_input()` 在视频 COS 场景下保留 `mps_video_url` |
| `models.py` | `TaskInfo` 新增 `mps_video_url: str = ""`；`CreateTaskRequest` 新增 `mps_video_url: Optional[str] = None` |
| `task_manager.py` | `create_task()` 转发 `mps_video_url`；`_execute_task()` 注入 `PipelineContext.mps_video_url` |
| `pipeline/base.py` | `PipelineContext` 新增 `mps_video_url: str = ""` |
| `stages.py` | `MultimodalStage._process()` 将 `ctx.mps_video_url` 注入 video `modal_content` |
| `video_processor.py` | `generate_description_only()` 调用 MPS 时优先使用 `mps_video_url` |
| `atomic-rag-server-v2.py` | `handle_insert` / `handle_retry` 将 `mps_video_url` 传入 `CreateTaskRequest` |

**# [jonex] 标记**：所有 vendored 改动均带 `# [jonex] 方案 C` 注释。


## 2026-07-24 — MPS JSON 双层嵌套结构解析

**问题**：MPS 视频理解接口返回双层嵌套 JSON：
```json
{"box_2d": [0, 0, 1, 11], "body": "{\"scenes\":[...],\"tags\":[...]}"}
```
`scenes` / `tags` 嵌在 `body` 字段里（一个 JSON 字符串），原代码 `obj.get("scenes")` 始终拿不到数据。

**修复**（`mps.py:_parse_result()`）：解析外层 JSON 后，检测 `body` 字段是否为 JSON 字符串，是则二次 `json.loads(body)` 取出内层的 `scenes` / `tags`；否则回退原有逻辑。
