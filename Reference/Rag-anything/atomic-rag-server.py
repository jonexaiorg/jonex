#!/usr/bin/env python3
"""
atomic-rag FastAPI 服务 — raganything 解析 + LightRAG Server 索引

端点:
  POST /process        异步提交文档解析 + 入库
  GET  /status/{task_id}  查询任务状态
  POST /query          检索（透传 lightrag）
  GET  /health          健康检查

视频处理链路:
  视频 → parse_video(元数据) → ffmpeg 提取音频 → whisper 转写 → 推送文本到 LightRAG
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
import types
import uuid
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("atomic-rag-server")

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
LIGHTRAG_API_URL: str = os.getenv("LIGHTRAG_API_URL", "http://lightrag:9621")
LIGHTRAG_API_KEY: str = os.getenv("LIGHTRAG_API_KEY", "")
LIGHTRAG_API_TIMEOUT: float = float(os.getenv("LIGHTRAG_API_TIMEOUT", "300"))
RAG_WEBHOOK_URL: str = os.getenv("RAG_WEBHOOK_URL", "")
RAG_PARSER: str = os.getenv("RAG_PARSER", "mineru")
RAG_WORKER_NUM: int = int(os.getenv("RAG_WORKER_NUM", "2"))

# ASR 模型（首次加载会下载，后续缓存）
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")

# MPS（腾讯云媒体处理）视频智能分析配置（可选）
MPS_ENABLED: bool = os.getenv("MPS_ENABLED", "false").lower() == "true"
MPS_SECRET_ID: str = os.getenv("MPS_SECRET_ID", "")
MPS_SECRET_KEY: str = os.getenv("MPS_SECRET_KEY", "")
MPS_COS_BUCKET: str = os.getenv("MPS_COS_BUCKET", "")
MPS_COS_REGION: str = os.getenv("MPS_COS_REGION") or os.getenv("MPS_REGION", "")

VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp",
}
AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".wma", ".aac", ".opus", ".amr",
}

# 租户 ID 安全处理
_TENANT_SAFE_RE = re.compile(r"[^A-Za-z0-9_\-]")


def _safe_tenant(tenant_id: str) -> str:
    return _TENANT_SAFE_RE.sub("_", tenant_id) if tenant_id else "default"


# ---------------------------------------------------------------------------
# LightRAG Server HTTP 客户端
# ---------------------------------------------------------------------------
class LightRAGClient:
    """LightRAG Server REST API 薄客户端"""

    def __init__(self) -> None:
        self.base_url = LIGHTRAG_API_URL.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def startup(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": LIGHTRAG_API_KEY},
            timeout=LIGHTRAG_API_TIMEOUT,
        )
        for _ in range(120):
            try:
                resp = await self._client.get("/health")
                if resp.status_code == 200:
                    logger.info(f"LightRAG Server 就绪: {self.base_url}")
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1)
        raise RuntimeError(f"LightRAG Server 启动超时: {self.base_url}")

    async def shutdown(self) -> None:
        if self._client:
            await self._client.aclose()

    async def upload_text(self, text: str, workspace: str, metadata: dict) -> dict:
        resp = await self._client.post(
            "/documents/text",
            json={"text": text, "file_source": metadata.get("source_file", "unknown")},
        )
        resp.raise_for_status()
        return resp.json()

    async def query(
        self, query: str, workspace: str, mode: str = "hybrid", top_k: int = 5
    ) -> str:
        resp = await self._client.post(
            "/query",
            json={"query": query, "mode": mode, "top_k": top_k},
        )
        resp.raise_for_status()
        return resp.json().get("response", "")

    async def delete_doc(self, doc_id: str) -> bool:
        """从 LightRAG 删除文档"""
        resp = await self._client.request(
            "DELETE",
            "/documents/delete_document",
            json={"doc_ids": [doc_id]},
        )
        return resp.status_code == 200


# ---------------------------------------------------------------------------
# 视频处理: ffmpeg 提取音频 + whisper 转写
# ---------------------------------------------------------------------------
_whisper_model_cache: dict[str, object] = {}


def _get_whisper_model(model_name: str = "base"):
    """懒加载 whisper 模型，避免重复加载"""
    if model_name not in _whisper_model_cache:
        import whisper

        logger.info(f"加载 Whisper 模型: {model_name}...")
        _whisper_model_cache[model_name] = whisper.load_model(model_name)
        logger.info(f"Whisper 模型 {model_name} 就绪")
    return _whisper_model_cache[model_name]


def _extract_audio(video_path: str, output_dir: str) -> str | None:
    """用 ffmpeg 从视频提取音频到 wav"""
    audio_path = os.path.join(output_dir, f"{Path(video_path).stem}_audio.wav")
    os.makedirs(output_dir, exist_ok=True)

    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
        logger.info(f"音频缓存命中: {audio_path}")
        return audio_path

    cmd = [
        "ffmpeg", "-y", "-v", "quiet",
        "-i", video_path,
        "-vn",               # 不要视频
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", "16000",       # 16kHz
        "-ac", "1",           # 单声道
        audio_path,
    ]
    try:
        subprocess.run(cmd, check=True, timeout=300)
        logger.info(f"音频提取完成: {audio_path}")
        return audio_path
    except subprocess.CalledProcessError as e:
        logger.warning(f"视频无音轨或 ffmpeg 失败: {e}")
        return None
    except Exception as e:
        logger.warning(f"音频提取异常: {e}")
        return None


def _transcribe_audio(audio_path: str, model_name: str = "base") -> dict:
    """whisper 转写音频"""
    model = _get_whisper_model(model_name)
    import whisper as _whisper

    result = model.transcribe(
        audio_path,
        language=None,           # 自动检测语言
        task="transcribe",
        verbose=False,
    )
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg.get("start", 0),
            "end": seg.get("end", 0),
            "text": seg.get("text", "").strip(),
        })
    return {
        "text": result.get("text", "").strip(),
        "language": result.get("language", "unknown"),
        "segments": segments,
    }


# ---------------------------------------------------------------------------
# MPS 视频智能分析（可选）
# ---------------------------------------------------------------------------
_mps_backend_cache: dict[str, object] = {}


def _get_mps_backend() -> object | None:
    """懒加载 MPSVideoBackend，返回 None 表示配置不完整。"""
    if not MPS_ENABLED:
        return None
    if not all([MPS_SECRET_ID, MPS_SECRET_KEY, MPS_COS_BUCKET, MPS_COS_REGION]):
        logger.warning("MPS 配置不完整，跳过视频智能分析")
        return None
    cache_key = f"{MPS_SECRET_ID}:{MPS_COS_BUCKET}"
    if cache_key not in _mps_backend_cache:
        try:
            from raganything.video_analysis.backends.mps import MPSVideoBackend

            cfg = types.SimpleNamespace(
                mps_secret_id=MPS_SECRET_ID,
                mps_secret_key=MPS_SECRET_KEY,
                mps_cos_bucket=MPS_COS_BUCKET,
                mps_cos_region=MPS_COS_REGION,
            )
            _mps_backend_cache[cache_key] = MPSVideoBackend(cfg)
            logger.info("MPS 视频分析后端就绪")
        except Exception as e:
            logger.error(f"MPS 后端初始化失败: {e}")
            _mps_backend_cache[cache_key] = None
    return _mps_backend_cache.get(cache_key)


async def _run_mps_analysis(video_cos_url: str) -> list[dict]:
    """调用 MPS 分析视频，返回格式化的 text chunk 列表。

    Returns:
        每个 chunk 是 {"type": "text", "text": str} 格式，
        可直接追加到 content_list。
    """
    backend = _get_mps_backend()
    if backend is None:
        return []

    result = await backend.analyze_video(video_path=video_cos_url)
    chunks: list[dict] = []
    file_name = Path(video_cos_url).name

    # Chunk 1: 全局摘要
    if result.summary:
        chunks.append({
            "type": "text",
            "text": (
                f"[MPS 视频分析] {file_name}\n"
                f"分析方式: {result.analysis_method}\n\n"
                f"【视频摘要】\n{result.summary}\n"
            ),
        })

    # Chunk 2+: 每个 scene 一个独立 chunk（带时间轴）
    scenes = result.scenes or []
    for i, scene in enumerate(scenes):
        desc = scene.get("description", "")
        start = scene.get("start_time", 0)
        end = scene.get("end_time", 0)

        # 时间格式化成 MM:SS
        def _fmt(sec: float) -> str:
            m, s = divmod(int(sec), 60)
            return f"{m:02d}:{s:02d}"

        scene_lines = [f"[MPS 视频场景 {i+1}/{len(scenes)}]"]
        scene_lines.append(f"时间: {_fmt(start)} - {_fmt(end)}")
        if scene.get("name"):
            scene_lines.append(f"名称: {scene['name']}")
        if scene.get("structure_type"):
            scene_lines.append(f"类型: {scene['structure_type']}")
        if desc:
            scene_lines.append(f"\n描述: {desc}")

        chunks.append({
            "type": "text",
            "text": "\n".join(scene_lines),
        })

    logger.info(
        f"MPS 分析完成: {len(scenes)} scenes, "
        f"{len(chunks)} text chunks 已生成"
    )
    return chunks


# ---------------------------------------------------------------------------
# 任务管理
# ---------------------------------------------------------------------------
class TaskManager:
    """内存任务状态 + 异步 worker 队列"""

    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._parser = None
        self._lightrag: Optional[LightRAGClient] = None

    @property
    def lightrag(self) -> LightRAGClient:
        assert self._lightrag is not None
        return self._lightrag

    async def startup(self) -> None:
        self._lightrag = LightRAGClient()
        await self._lightrag.startup()

        from raganything.parser import get_parser

        parser_name = RAG_PARSER.lower()
        self._parser = get_parser(parser_name)
        if not self._parser.check_installation():
            logger.warning(f"解析器 {parser_name} 未完整安装，可能解析失败")
        logger.info(f"解析器就绪: {parser_name}")

        for i in range(RAG_WORKER_NUM):
            asyncio.create_task(self._worker(i))

    async def shutdown(self) -> None:
        if self._lightrag:
            await self._lightrag.shutdown()

    def create_task(
        self,
        file_path: str | None = None,
        tenant_id: str = "default",
        output_dir: str | None = None,
        mps_video_url: str | None = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "file_path": file_path,
            "mps_video_url": mps_video_url,
            "output_dir": output_dir or os.getenv("OUTPUT_DIR", "/app/output"),
            "status": "pending",
            "progress": 0.0,
            "doc_ids": [],
            "error": None,
        }
        self._tasks[task_id] = task
        self._queue.put_nowait(task)
        source = mps_video_url or file_path or "unknown"
        logger.info(f"任务入队: task_id={task_id} source={source}")
        return task_id

    def get_status(self, task_id: str, tenant_id: str) -> dict:
        task = self._tasks.get(task_id)
        if not task:
            return {"task_id": task_id, "status": "not_found"}
        if task["tenant_id"] != tenant_id:
            raise PermissionError("租户隔离: 无权查看此任务")
        return {
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
            "error": task["error"],
            "doc_ids": task.get("doc_ids", []),
        }

    async def _worker(self, worker_id: int) -> None:
        logger.info(f"Worker {worker_id} 启动")
        while True:
            task = await self._queue.get()
            task_id = task["task_id"]
            try:
                task["status"] = "processing"
                task["progress"] = 0.05

                file_path = task.get("file_path")
                mps_url = task.get("mps_video_url")

                # ── 阶段1: 本地文件解析（file_path 有值时才执行） ──
                content_list: list[dict] = []

                if file_path:
                    ext = os.path.splitext(file_path)[1].lower()
                    is_video = ext in VIDEO_EXTENSIONS
                    is_audio = ext in AUDIO_EXTENSIONS

                    if is_video:
                        content_list = await asyncio.to_thread(
                            self._parser.parse_video,
                            video_path=file_path,
                            output_dir=task["output_dir"],
                        )
                        logger.info(f"task={task_id} 视频元数据: {file_path}")
                    elif is_audio:
                        content_list = await asyncio.to_thread(
                            self._parser.parse_audio,
                            audio_path=file_path,
                            output_dir=task["output_dir"],
                        )
                        logger.info(f"task={task_id} 音频元数据: {file_path}")
                    else:
                        content_list = await asyncio.to_thread(
                            self._parser.parse_document,
                            file_path=file_path,
                            output_dir=task["output_dir"],
                        )
                    logger.info(f"task={task_id} 解析完成: {len(content_list)} blocks")
                    task["progress"] = 0.3

                # ── 阶段2: 音频转写（仅本地视频/音频文件） ──
                if file_path:
                    ext = os.path.splitext(file_path)[1].lower()
                    is_video = ext in VIDEO_EXTENSIONS
                    is_audio = ext in AUDIO_EXTENSIONS

                    if is_video:
                        audio_path = await asyncio.to_thread(
                            _extract_audio, file_path, task["output_dir"]
                        )
                        if audio_path:
                            task["progress"] = 0.4
                            asr_result = await asyncio.to_thread(
                                _transcribe_audio, audio_path, WHISPER_MODEL
                            )
                            transcript = asr_result.get("text", "")
                            if transcript:
                                content_list.append({
                                    "type": "text",
                                    "text": f"[视频转写] 语言: {asr_result.get('language', 'unknown')}\n\n{transcript}",
                                })
                                logger.info(
                                    f"task={task_id} ASR 完成: lang={asr_result.get('language')}, "
                                    f"{len(transcript)} chars"
                                )
                            task["progress"] = 0.5
                        else:
                            logger.info(f"task={task_id} 视频无音轨或音频提取失败")

                    elif is_audio:
                        task["progress"] = 0.4
                        asr_result = await asyncio.to_thread(
                            _transcribe_audio, file_path, WHISPER_MODEL
                        )
                        transcript = asr_result.get("text", "")
                        if transcript:
                            content_list.append({
                                "type": "text",
                                "text": f"[音频转写] 语言: {asr_result.get('language', 'unknown')}\n\n{transcript}",
                            })
                            logger.info(
                                f"task={task_id} ASR 完成: lang={asr_result.get('language')}, "
                                f"{len(transcript)} chars"
                            )
                        task["progress"] = 0.5

                # ── MPS 视频智能分析（mps_video_url 有值 + MPS_ENABLED 时执行） ──
                if mps_url and MPS_ENABLED:
                    try:
                        task["progress"] = 0.55
                        mps_chunks = await _run_mps_analysis(mps_url)
                        content_list.extend(mps_chunks)
                        logger.info(
                            f"task={task_id} MPS 分析完成: "
                            f"{len(mps_chunks)} chunks"
                        )
                    except Exception as e:
                        logger.warning(
                            f"task={task_id} MPS 分析失败（非致命）: {e}"
                        )
                    task["progress"] = 0.6

                # ── 阶段3: 推文本到 LightRAG ──
                workspace = f"tenant_{_safe_tenant(task['tenant_id'])}"
                doc_ids: list[str] = []

                for idx, chunk in enumerate(content_list):
                    if chunk.get("type") != "text":
                        continue
                    text = chunk.get("text", "")
                    if not text.strip():
                        continue
                    result = await self.lightrag.upload_text(
                        text=text,
                        workspace=workspace,
                        metadata={
                            "source_file": task["file_path"],
                            "tenant_id": task["tenant_id"],
                            "chunk_index": idx,
                            "task_id": task_id,
                        },
                    )
                    if "doc_id" in result:
                        doc_ids.append(result["doc_id"])

                task["doc_ids"] = doc_ids
                task["status"] = "completed"
                task["progress"] = 1.0
                logger.info(f"task={task_id} 完成: {len(doc_ids)} chunks 已入库")

                await _send_webhook(task_id, task["tenant_id"], "completed", doc_ids)

            except Exception as e:
                task["status"] = "failed"
                task["error"] = str(e)
                logger.exception(f"task={task_id} 失败: {e}")
                await _send_webhook(task_id, task["tenant_id"], "failed", [], str(e))
            finally:
                self._queue.task_done()


# ---------------------------------------------------------------------------
# Webhook 回调
# ---------------------------------------------------------------------------
async def _send_webhook(
    task_id: str,
    tenant_id: str,
    status: str,
    doc_ids: list[str],
    error: str | None = None,
) -> None:
    if not RAG_WEBHOOK_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                RAG_WEBHOOK_URL,
                json={
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "status": status,
                    "doc_ids": doc_ids,
                    "error": error,
                },
            )
            logger.debug(f"Webhook 回调: task_id={task_id} status={status}")
    except httpx.HTTPError as e:
        logger.warning(f"Webhook 回调失败（非致命）: {e}")


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
_task_manager: TaskManager = TaskManager()

app = FastAPI(title="atomic-rag", version="1.0.0")


@app.on_event("startup")
async def _on_startup() -> None:
    await _task_manager.startup()


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    await _task_manager.shutdown()


# ---- 请求模型 ----
class ProcessRequest(BaseModel):
    file_path: str | None = None  # 本地文件路径（与 mps_video_url 至少传一个）
    tenant_id: str = "default"
    output_dir: str | None = None
    mps_video_url: str | None = None  # MPS 视频分析的 COS URL（可选）


class QueryRequest(BaseModel):
    query: str
    tenant_id: str = "default"
    mode: str = "hybrid"
    top_k: int = 5


# ---- 端点 ----
@app.get("/health")
async def health():
    return {"status": "healthy", "parser": RAG_PARSER}


@app.post("/process")
async def process(req: ProcessRequest):
    if not req.file_path and not req.mps_video_url:
        raise HTTPException(400, "file_path 和 mps_video_url 至少传一个")
    task_id = _task_manager.create_task(
        file_path=req.file_path,
        tenant_id=req.tenant_id,
        output_dir=req.output_dir,
        mps_video_url=req.mps_video_url,
    )
    return {"task_id": task_id, "status": "pending", "file_path": req.file_path}


@app.get("/status/{task_id}")
async def task_status(task_id: str, tenant_id: str = "default"):
    try:
        return _task_manager.get_status(task_id, tenant_id)
    except PermissionError as e:
        raise HTTPException(403, str(e))


@app.post("/query")
async def query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(400, "query 不能为空")
    workspace = f"tenant_{_safe_tenant(req.tenant_id)}"
    answer = await _task_manager.lightrag.query(
        query=req.query,
        workspace=workspace,
        mode=req.mode,
        top_k=req.top_k,
    )
    return {"query": req.query, "answer": answer}


# ---- 统一能力调用入口（兼容 Sidecar 代理协议） ----
class InvokeRequest(BaseModel):
    capability_id: str = ""
    payload: dict = {}
    tenant_id: str = "default"
    user_id: str | None = None
    request_id: str | None = None


@app.post("/invoke")
async def invoke(req: InvokeRequest):
    """统一能力调用入口，接受 Sidecar 代理的请求并分派"""
    action = req.payload.get("action")
    params = req.payload
    tenant_id = req.tenant_id

    try:
        if action == "insert":
            file_path = params.get("file_path", "") or None
            mps_video_url = params.get("mps_video_url", "") or None
            if not file_path and not mps_video_url:
                raise HTTPException(400, "file_path 和 mps_video_url 至少传一个")
            task_id = _task_manager.create_task(
                file_path=file_path,
                tenant_id=tenant_id,
                output_dir=params.get("output_dir"),
                mps_video_url=mps_video_url,
            )
            return {
                "request_id": req.request_id or "",
                "success": True,
                "code": 0,
                "message": "success",
                "data": {
                    "task_id": task_id,
                    "status": "pending",
                    "file_path": file_path,
                    "tenant_id": tenant_id,
                },
            }

        elif action == "query":
            query_text = params.get("query", "")
            mode = params.get("mode", "hybrid")
            top_k = int(params.get("top_k", 5))
            if not query_text.strip():
                raise HTTPException(400, "query 不能为空")
            workspace = f"tenant_{_safe_tenant(tenant_id)}"
            answer = await _task_manager.lightrag.query(
                query=query_text,
                workspace=workspace,
                mode=mode,
                top_k=top_k,
            )
            return {
                "request_id": req.request_id or "",
                "success": True,
                "code": 0,
                "message": "success",
                "data": {"answer": answer},
            }

        elif action == "delete":
            doc_id = params.get("doc_id", "")
            if not doc_id:
                raise HTTPException(400, "doc_id 不能为空")
            success = await _task_manager.lightrag.delete_doc(doc_id=doc_id)
            return {
                "request_id": req.request_id or "",
                "success": True,
                "code": 0,
                "message": "success",
                "data": {"success": success},
            }

        elif action == "get_task_status":
            task_id = params.get("task_id", "")
            if not task_id:
                raise HTTPException(400, "task_id 不能为空")
            status = _task_manager.get_status(task_id, tenant_id)
            # 兼容 KnowledgeBaseService 预期的 lightrag_doc_ids 字段名
            status["lightrag_doc_ids"] = status.pop("doc_ids", [])
            return {
                "request_id": req.request_id or "",
                "success": True,
                "code": 0,
                "message": "success",
                "data": status,
            }

        else:
            return {
                "request_id": req.request_id or "",
                "success": False,
                "code": 400,
                "message": f"不支持的 action: {action}",
                "data": None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"调用失败: {e}")
        return {
            "request_id": req.request_id or "",
            "success": False,
            "code": 500,
            "message": str(e),
            "data": None,
        }


# ---- 主入口 ----
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
