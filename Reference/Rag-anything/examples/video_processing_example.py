#!/usr/bin/env python
"""
Video processing example for RAG-Anything — COS + TokenHub VLM + token control.

Only the first 10 keyframes call real VLM; subsequent frames get mocked
descriptions to save tokens/cost while still testing the full pipeline.

Usage:
    # With COS + TokenHub VLM (from .env):
    uv run python examples/video_processing_example.py "C:/work/项目文件/DataAI/dataset/DM_20260526140158_001.mp4"

    # With OpenAI-compatible VLM (supports base64, no COS needed):
    ENABLE_VIDEO_PROCESSING=1 uv run python examples/video_processing_example.py video.mp4
"""

import argparse
import asyncio
import base64
import os
import sys
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=False)

from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc, logger
from raganything import RAGAnything, RAGAnythingConfig

# ── Token control ───────────────────────────────────────
MAX_REAL_VLM_FRAMES = 10  # only first N keyframes call real VLM API
MOCK_VLM_DESC = "(mock) A keyframe from the video segment."
# ─────────────────────────────────────────────────────────


def _build_vlm_func(api_key, base_url, max_frames=10):
    """Build a proxy VLM function that throttles real calls after max_frames.

    - Real call: upload frame to COS → TokenHub VLM via URL
    - Mock call: return placeholder string (saves tokens)
    - If no COS configured: use base64 for OpenAI-compatible VLMs
    """
    vision_host = os.getenv("VISION_BINDING_HOST") or base_url
    vision_key = os.getenv("VISION_BINDING_API_KEY") or api_key
    vision_model = os.getenv("VISION_MODEL", "gpt-4o")

    if vision_model.upper() == "YT-VITA":
        vision_model = "youtu-vita"

    call_count = [0]
    cos_host = [None]
    vlm_base_url = vision_host.rstrip("/") + "/v1"

    async def _vlm_func(image_path: str, prompt: str) -> str:
        call_count[0] += 1
        idx = call_count[0]

        if idx > max_frames:
            logger.info(
                f"VLM frame {idx}: exceeding limit ({max_frames}), "
                f"returning mock description")
            return MOCK_VLM_DESC

        # Determine image source: URL or local?
        if image_path.startswith(("http://", "https://")):
            image_url = image_path
        elif _has_cos_config():
            # Upload to COS for TokenHub (URL-required VLM)
            if cos_host[0] is None:
                cos_host[0] = _create_cos_host()
            prep = await cos_host[0].prepare_urls(
                [{"frame_path": image_path, "frame_time": 0.0}],
                "video_example",
            )
            if prep.transport_available and prep.frames[0].get("upload", {}).get("url"):
                image_url = prep.frames[0]["upload"]["url"]
                logger.debug(f"VLM frame {idx}: COS URL ready")
            else:
                logger.warning(
                    f"VLM frame {idx}: COS upload failed ({prep.fatal_error}), "
                    f"returning mock")
                return MOCK_VLM_DESC
        else:
            # Base64 path (OpenAI-compatible VLM)
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            image_url = f"data:image/jpeg;base64,{b64}"

        # Call VLM with retry + empty-content protection
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                result = await openai_complete_if_cache(
                    vision_model,
                    None,
                    system_prompt=None,
                    history_messages=[],
                    base_url=vlm_base_url,
                    api_key=vision_key,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url",
                             "image_url": {"url": image_url}},
                        ],
                    }],
                )
                # Guard against empty content from VLM
                if result and result.strip():
                    logger.info(f"VLM frame {idx}: got {len(result)} chars")
                    return result
                else:
                    logger.warning(
                        f"VLM frame {idx}: empty content received"
                        + (f" (attempt {attempt+1})" if attempt > 0 else ""))
                    if attempt < max_retries:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        return MOCK_VLM_DESC
            except Exception as e:
                err_msg = str(e)
                # 502/503/upstream error: retry; other: fail immediately
                retryable = any(x in err_msg for x in (
                    "502", "503", "model engine error",
                    "upstream_error", "empty content",
                ))
                if retryable and attempt < max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        f"VLM frame {idx}: retryable error (attempt {attempt+1}), "
                        f"waiting {wait}s: {err_msg[:120]}")
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        f"VLM frame {idx}: VLM failed: {err_msg[:200]}")
                    return MOCK_VLM_DESC

    _vlm_func.vlm_model = vision_model
    return _vlm_func


def _has_cos_config():
    return bool(
        os.getenv("COS_BUCKET") and os.getenv("COS_APPID")
        and os.getenv("COS_SECRET_ID")
    )


def _create_cos_host():
    from raganything.image_transport import CosImageHost

    return CosImageHost(
        bucket=os.getenv("COS_BUCKET"),
        appid=os.getenv("COS_APPID"),
        region=os.getenv("COS_REGION", "ap-guangzhou"),
        secret_id=os.getenv("COS_SECRET_ID", ""),
        secret_key=os.getenv("COS_SECRET_KEY", ""),
        key_prefix=os.getenv("COS_KEY_PREFIX", "rag_anything/video"),
        max_concurrent=int(os.getenv("COS_MAX_CONCURRENT", "5")),
    )


async def process_video(file_path: str, api_key: str, base_url: str = None,
                       max_vlm_frames: int = 10):
    """Full pipeline. vlm_max_frames controls real VLM calls per processing pass.
    Beyond this limit, frames get mock descriptions to save tokens.
    """
    config = RAGAnythingConfig(
        working_dir="./rag_storage_video",
        enable_video_processing=True,
        enable_audio_processing=True,   # video needs ASR for audio track
        video_keyframe_interval=10,
        video_max_frames=30,
        video_chunk_token_size=600,
        video_summarize_batch_size=8,
        video_summarize_max_batches=20,
        max_parallel_vlm=2,
        vlm_timeout=120,
    )

    llm_model = os.getenv("LLM_MODEL", "deepseek-chat")

    def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs):
        return openai_complete_if_cache(
            llm_model,
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    vlm_func = _build_vlm_func(api_key, base_url, max_frames=max_vlm_frames)

    embedding_dim = int(os.getenv("EMBEDDING_DIM", "1024"))
    embedding_model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    embedding_base_url = os.getenv("EMBEDDING_BINDING_HOST") or base_url
    embedding_api_key = os.getenv("EMBEDDING_BINDING_API_KEY") or api_key

    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,
        func=partial(
            openai_embed.func,
            model=embedding_model_name,
            api_key=embedding_api_key,
            base_url=embedding_base_url,
        ),
    )

    rag = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        vlm_model_func=vlm_func,
        embedding_func=embedding_func,
    )

    logger.info(f"Video:  {Path(file_path).name}")
    logger.info(f"Config: video_max_frames={config.video_max_frames}, "
                f"interval={config.video_keyframe_interval}s")
    logger.info(f"VLM:    real calls ≤ {max_vlm_frames} frames, "
                f"model={getattr(vlm_func, 'vlm_model', '?')}")
    logger.info(f"COS:    {'enabled' if _has_cos_config() else 'disabled (base64 mode)'}")

    with rag:
        logger.info(f"Processing video...")
        await rag.process_document_complete(file_path)

        logger.info("\n" + "=" * 60)
        logger.info("Queries:")
        logger.info("=" * 60)

        queries = [
            "What is the main content of this video?",
            "What are the key scenes or topics shown?",
        ]
        for q in queries:
            logger.info(f"\n[Query]: {q}")
            result = await rag.aquery(q, mode="hybrid")
            logger.info(f"Answer: {result}")


def main():
    parser = argparse.ArgumentParser(
        description="RAG-Anything Video Processing Example (with token control)")
    parser.add_argument(
        "file_path",
        nargs="?",
        default="C:/work/项目文件/DataAI/dataset/DM_20260526140158_001.mp4",
        help="Path to video file",
    )
    parser.add_argument(
        "--api-key", default=os.getenv("LLM_BINDING_API_KEY"))
    parser.add_argument(
        "--base-url", default=os.getenv("LLM_BINDING_HOST"))
    parser.add_argument(
        "--max-vlm-frames", type=int, default=None,
        help=f"Max real VLM calls (default: {MAX_REAL_VLM_FRAMES})")
    parser.add_argument(
        "--mock-only", action="store_true",
        help="Mock ALL VLM calls (zero token cost, for pipeline testing)")

    args = parser.parse_args()

    if not args.api_key:
        logger.error("LLM_BINDING_API_KEY required. Set in .env or use --api-key")
        return

    # Set limit based on CLI args
    limit = args.max_vlm_frames if args.max_vlm_frames is not None else MAX_REAL_VLM_FRAMES
    if args.mock_only:
        limit = 0
        logger.info("--mock-only: all VLM calls mocked (zero tokens)")
    else:
        logger.info(f"Real VLM limit: {limit} frames")

    video_path = Path(args.file_path)
    if not video_path.exists():
        logger.error(f"Video file not found: {args.file_path}")
        return

    asyncio.run(process_video(str(video_path), args.api_key, args.base_url,
                              max_vlm_frames=limit))


if __name__ == "__main__":
    main()
