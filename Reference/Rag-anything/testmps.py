"""
MPS 视频分析后端 — 单独测试脚本

直接加载 video_analysis 模块，不经过 raganything/__init__.py，
避免依赖 dotenv 等 RAG-Anything 环境依赖。

使用方法（PowerShell）:
  $env:MPS_SECRET_ID="AKIDxxxx"
  $env:MPS_SECRET_KEY="lLirnxxxx"
  $env:MPS_COS_BUCKET="material-understand-1322124992"
  $env:MPS_COS_REGION="ap-guangzhou"
  $env:MPS_TEST_VIDEO_URL="https://material-understand-1322124992.cos.ap-guangzhou.myqcloud.com/demo/xxxx/shipin_xxxx.mp4"
  $env:MPS_PROMPT_CATEGORY="mps_hotel_room_inspection"
  python testmps.py

结果会自动保存到 output/mps_result_YYYYMMDD_HHMMSS.json
"""

import asyncio
import importlib.util
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


def _load_module(name, filepath):
    """Load a Python file as a module without triggering package __init__."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_mock_config():
    """Read MPS config from environment variables."""

    class MockConfig:
        mps_secret_id = os.environ.get("MPS_SECRET_ID", "")
        mps_secret_key = os.environ.get("MPS_SECRET_KEY", "")
        mps_region = os.environ.get("MPS_REGION", "ap-guangzhou")
        mps_cos_bucket = os.environ.get("MPS_COS_BUCKET", "")
        mps_cos_region = os.environ.get("MPS_COS_REGION", "ap-guangzhou")
        mps_definition = int(os.environ.get("MPS_DEFINITION", "33"))
        mps_timeout = int(os.environ.get("MPS_TIMEOUT", "600"))
        mps_poll_interval = int(os.environ.get("MPS_POLL_INTERVAL", "3"))
        mps_max_retries = int(os.environ.get("MPS_MAX_RETRIES", "3"))
        mps_prompt_category = os.environ.get(
            "MPS_PROMPT_CATEGORY", "mps_hotel_room_inspection"
        )
        mps_tag_library = "{}"

    return MockConfig()


async def main():
    base = Path(__file__).resolve().parent / "raganything" / "video_analysis"

    # ── 1. 加载 video_analysis 模块（绕过 raganything/__init__.py）──
    print("=" * 72)
    print("  MPS 视频分析测试脚本")
    print("=" * 72)
    print()

    va_mod = _load_module("raganything.video_analysis", base / "__init__.py")
    _load_module(  # 加载 backend（触发 @register）
        "raganything.video_analysis.backends.mps",
        base / "backends" / "mps.py",
    )

    # ── 2. 检查环境变量 ─────────────────────────────────────────────────
    config = load_mock_config()
    required = ["MPS_SECRET_ID", "MPS_SECRET_KEY", "MPS_COS_BUCKET"]
    missing = [k for k in required if not getattr(config, k.lower())]
    if missing:
        print(f"错误: 缺少必要环境变量: {', '.join(missing)}")
        sys.exit(1)

    print(f"[CONFIG] SecretId:      {config.mps_secret_id[:8]}...{config.mps_secret_id[-4:]}")
    print(f"[CONFIG] COS Bucket:    {config.mps_cos_bucket}")
    print(f"[CONFIG] COS Region:    {config.mps_cos_region}")
    print(f"[CONFIG] 超时:          {config.mps_timeout}s")
    print(f"[CONFIG] 轮询间隔:      {config.mps_poll_interval}s")
    print(f"[CONFIG] 最大重试:      {config.mps_max_retries}")
    print(f"[CONFIG] 提示词类别:    {config.mps_prompt_category}")
    print()

    # ── 3. 初始化 MPS 后端 ──────────────────────────────────────────────
    backend_cls = va_mod.get_video_analysis_backend("mps")
    print(f"[INIT] 找到后端: {backend_cls.__name__}")

    issues = backend_cls.validate_config(config)
    if issues:
        print("[FAIL] 配置验证失败:")
        for i in issues:
            print(f"       [{i.level}] {i.field}: {i.message}")
        sys.exit(1)
    print("[INIT] 配置验证通过")

    start_time = time.monotonic()
    backend = backend_cls(config)
    print(f"[INIT] 后端初始化完成 ({time.monotonic() - start_time:.1f}s)")
    print(f"[INIT] 提示词长度: {len(backend._default_prompt)} 字符")
    print()

    # ── 4. 提交分析任务 ─────────────────────────────────────────────────
    video_url = os.environ.get(
        "MPS_TEST_VIDEO_URL",
        "https://material-understand-1322124992.cos.ap-guangzhou.myqcloud.com/"
        "demo/fe0b64cc-a870-4d37-b31c-747d22ff9cb0/shipin_20260608104341_1781495839.mp4",
    )

    print(f"[VIDEO] 视频地址:")
    print(f"        {video_url}")
    print()

    # 提取 object_key + 构建 prompt（复用后端内部方法）
    object_key = backend._extract_cos_key(video_url)
    analysis_prompt = backend._default_prompt

    # 初始化客户端 + 提交任务
    print(f"[SUBMIT] 正在提交到 MPS ...")
    print(f"[SUBMIT] ObjectKey: {object_key}")
    backend._ensure_client()
    task_start = time.monotonic()
    task_id = backend._submit_task(object_key, analysis_prompt)
    task_duration = time.monotonic() - task_start
    print(f"[SUBMIT] 完成! 耗时 {task_duration:.1f}s")
    print(f"[TASK]   TaskId: {task_id}")
    print()

    # ── 5. 轮询结果（自定义详细日志）─────────────────────────────────
    from tencentcloud.mps.v20190612 import models

    poll_interval = config.mps_poll_interval
    timeout = config.mps_timeout
    max_retries = config.mps_max_retries
    deadline = asyncio.get_event_loop().time() + timeout
    retry_count = 0
    poll_count = 0
    raw_result = None

    print(f"[POLL] 开始轮询（间隔 {poll_interval}s, 超时 {timeout}s）...")
    print(f"[POLL] {'─' * 72}")
    print(f"  {'轮次':>5} │ {'耗时':>7} │ {'状态'}")

    while True:
        if asyncio.get_event_loop().time() > deadline:
            print(f"\n[FAIL] 超时! 任务 {task_id} 在 {timeout}s 内未完成")
            sys.exit(1)

        try:
            detail_request = models.DescribeTaskDetailRequest()
            detail_request.TaskId = task_id
            response = backend._client.DescribeTaskDetail(detail_request)
        except Exception as exc:
            retry_count += 1
            elapsed = time.monotonic() - task_start
            if retry_count > max_retries:
                print(f"\n[FAIL] DescribeTaskDetail 重试 {max_retries} 次后失败: {exc}")
                sys.exit(1)
            print(f"  {f'{poll_count + 1}':>5} │ {elapsed:>6.1f}s │ RETRY {retry_count}/{max_retries}: {exc}")
            await asyncio.sleep(poll_interval)
            continue

        retry_count = 0
        poll_count += 1
        elapsed = time.monotonic() - task_start

        # 检查 task type
        if response.TaskType != "WorkflowTask":
            print(f"  {poll_count:>5} │ {elapsed:>6.1f}s │ 异常类型: {response.TaskType}")
            raise ValueError(f"Unexpected MPS task type: {response.TaskType}")

        status = response.Status
        workflow_task = response.WorkflowTask

        # 提取 VideoComprehension 结果集
        ai_results = workflow_task.AiAnalysisResultSet or []
        filtered = [r for r in ai_results if r.Type == "VideoComprehension"]

        if not filtered:
            if status == "FINISH":
                print(f"\n[FAIL] 任务完成但无 VideoComprehension 结果: {workflow_task.Message}")
                sys.exit(1)
            # 仍在处理中
            print(f"  {poll_count:>5} │ {elapsed:>6.1f}s │ {status:<10}")
            await asyncio.sleep(poll_interval)
            continue

        vc_task = filtered[0].VideoComprehensionTask

        if vc_task.Status == "FAIL":
            print(f"  {poll_count:>5} │ {elapsed:>6.1f}s │ FAIL (错误: {vc_task.Message})")
            print(f"\n[FAIL] MPS VideoComprehension 失败: {vc_task.Message}")
            sys.exit(1)

        # 获取进度
        progress = getattr(vc_task, "Progress", None)

        if vc_task.Status == "SUCCESS" and vc_task.Output:
            raw_result = vc_task.Output.VideoComprehensionAnalysisResult
            if raw_result:
                print(f"  {poll_count:>5} │ {elapsed:>6.1f}s │ SUCCESS (进度 100%)")
                print(f"[POLL] {'─' * 72}")
                print(f"[POLL] 完成! 轮询 {poll_count} 次, 总耗时 {elapsed:.1f}s")
                print()
                break

        # 仍在运行，显示进度
        progress_str = f"{progress}%" if progress is not None else "N/A"
        print(f"  {poll_count:>5} │ {elapsed:>6.1f}s │ {status:<10} 进度 {progress_str}")
        await asyncio.sleep(poll_interval)

    # ── 6. 解析结果 ─────────────────────────────────────────────────────
    print(f"[PARSE] 正在解析 MPS 返回的 JSON 结果 ...")
    parse_start = time.monotonic()
    result = backend._parse_result(raw_result)
    parse_duration = time.monotonic() - parse_start
    print(f"[PARSE] 解析完成 ({parse_duration:.3f}s)")
    print()

    # ── 7. 控制台输出概要 ──────────────────────────────────────────────
    total_duration = time.monotonic() - task_start

    print("=" * 72)
    print("  分析结果概要")
    print("=" * 72)
    print(f"  分析方法:     {result.analysis_method}")
    print(f"  任务耗时:     {total_duration:.1f}s")
    print(f"  轮询次数:     {poll_count}")
    print(f"  TaskId:       {task_id}")
    print()

    # 摘要
    if result.summary:
        print(f"  ┌─ 摘要 ──────────────────────────────────────────────────")
        for line in result.summary.split("\n"):
            print(f"  │ {line}")
        print(f"  └─────────────────────────────────────────────────────────")
        print()

    # scenes
    scenes = result.scenes
    if scenes:
        print(f"  scenes: {len(scenes)} 个分镜")
        print(f"  ┌{'─' * 68}┐")
        for i, scene in enumerate(scenes):
            desc = scene.get("description", "") or str(scene)
            name = scene.get("name", "")
            num = scene.get("number", i + 1)
            st = scene.get("structure_type", "")
            label = f"  │ [{num}] {name}"
            if st:
                label += f" ({st})"
            print(label[:68])
            # 描述换行缩进
            for line in desc.split("\n"):
                for chunk in [line[j:j+120] for j in range(0, max(len(line), 1), 120)]:
                    print(f"  │     {chunk}")
            if i < len(scenes) - 1:
                print(f"  │{' ' * 68}│")
        print(f"  └{'─' * 68}┘")
        print()
    else:
        print(f"  scenes: 无")
        print()

    # tags
    tags = result.tags
    if tags:
        print(f"  tags: {len(tags)} 个标签")
        for tag in tags[:15]:
            name = tag.get("name", tag.get("tag", str(tag)))
            cat = tag.get("category", "N/A")
            conf = tag.get("confidence", "")
            conf_str = f" (confidence: {conf})" if conf else ""
            print(f"    - {name} [{cat}]{conf_str}")
        if len(tags) > 15:
            print(f"    ... 还有 {len(tags) - 15} 个 tag")
        print()
    else:
        print(f"  tags: 无")
        print()

    # raw_json 大小
    raw_len = len(result.raw_json)
    print(f"  raw_json: {raw_len:,} 字符")
    print()

    # ── 8. 保存完整结果到 JSON 文件 ─────────────────────────────────────
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"mps_result_{timestamp}.json"

    # 尝试解析 raw_json 为结构化对象
    raw_parsed = None
    if raw_result:
        try:
            raw_parsed = json.loads(result.raw_json if result.raw_json else raw_result)
        except json.JSONDecodeError:
            # 尝试清理后解析
            import re
            cleaned = result.raw_json.strip()
            m = re.search(r"```json\s*\n(.*?)\n```", cleaned, re.DOTALL)
            if m:
                try:
                    raw_parsed = json.loads(m.group(1).strip())
                except json.JSONDecodeError:
                    pass
            if not raw_parsed:
                m = re.search(r"(\{.*\})", cleaned, re.DOTALL)
                if m:
                    try:
                        raw_parsed = json.loads(m.group(1).strip())
                    except json.JSONDecodeError:
                        pass

    output = {
        "meta": {
            "export_time": datetime.now().isoformat(),
            "analysis_method": "mps",
            "prompt_category": config.mps_prompt_category,
            "video_url": video_url,
            "object_key": object_key,
            "task_id": task_id,
            "duration_seconds": round(total_duration, 1),
            "poll_count": poll_count,
        },
        "config": {
            "mps_secret_id": f"{config.mps_secret_id[:8]}...{config.mps_secret_id[-4:]}",
            "mps_cos_bucket": config.mps_cos_bucket,
            "mps_cos_region": config.mps_cos_region,
            "mps_definition": config.mps_definition,
            "mps_timeout": config.mps_timeout,
            "mps_poll_interval": config.mps_poll_interval,
            "mps_prompt_category": config.mps_prompt_category,
        },
        "summary": result.summary,
        "scenes": scenes,
        "tags": tags,
        "metadata": result.metadata,
        "raw_json": raw_result,
        "raw_parsed": raw_parsed,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[SAVE] 结果已保存到:")
    print(f"       {output_path.resolve()}")
    print()

    # ── 9. 输出原始 JSON 预览 ──────────────────────────────────────────
    print(f"[RAW] 原始 JSON（前 500 字符）:")
    print(f"      ┌{'─' * 60}┐")
    preview = raw_result.strip()[:500]
    for line in preview.split("\n")[:15]:
        print(f"      │ {line[:58]}")
    if len(raw_result.strip()) > 500:
        print(f"      │ ...")
    print(f"      └{'─' * 60}┘")
    print()

    print("[DONE] 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
