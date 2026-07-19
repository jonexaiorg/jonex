#!/usr/bin/env python
"""
Audio processing example for RAG-Anything.

Usage:
    # Local Whisper (default):
    ASR_BINDING=whisper ASR_MODEL=large-v3 uv run python examples/audio_processing_example.py meeting.mp3

    # OpenAI-compatible API:
    ASR_BINDING=openai_compatible ASR_API_KEY=sk-xxx ASR_BASE_URL=https://api.openai.com/v1 \\
        uv run python examples/audio_processing_example.py meeting.mp3

    # Legacy mode (manual asr_model_func, uncomment whisper_asr block below):
    uv run python examples/audio_processing_example.py meeting.mp3
"""

import argparse
import asyncio
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


# ── ASR function (singleton model) ──
# Set asr_identity + asr_model for cache invalidation when switching models.
#
# NOTE: The config-driven ASR backend (ASR_BINDING env var) is the default.
# Uncomment this block only for legacy manual asr_model_func usage (when
# ASR_BINDING is not set):

# _model = None
#
# def _get_whisper_model():
#     global _model
#     if _model is None:
#         import whisper
#         _model = whisper.load_model("base")
#     return _model
#
# def whisper_asr(audio_path: str) -> dict:
#     """Synchronous ASR — Processor wraps in asyncio.to_thread."""
#     model = _get_whisper_model()
#     result = model.transcribe(audio_path)
#     segments = result.get("segments", [])
#     return {
#         "transcript": result["text"],
#         "segments": [
#             {"start": s["start"], "end": s["end"], "text": s["text"].strip(), "confidence": None}
#             for s in segments
#         ],
#         "language": result.get("language", "unknown"),
#         "duration": segments[-1]["end"] if segments else 0,
#     }
#
# whisper_asr.asr_identity = "whisper:base"
# whisper_asr.asr_model = "base"


async def process_audio(file_path: str, api_key: str, base_url: str = None, asr_model_func=None):
    config = RAGAnythingConfig(
        working_dir="./rag_storage",
        enable_audio_processing=True,
        max_parallel_asr=1,
        audio_asr_timeout=600,
        audio_chunk_token_size=600,
        min_asr_confidence=0.0,
        audio_summarize_batch_size=8,
        audio_summarize_max_batches=20,
    )

    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")

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
        asr_model_func=asr_model_func,  # None -> auto-select from ASR_BINDING
        embedding_func=embedding_func,
    )

    # Use context manager for automatic cleanup
    with rag:
        logger.info(f"Processing audio: {file_path}")
        await rag.process_document_complete(file_path)

        logger.info("\nQuerying processed audio:")
        queries = [
            "What is the main topic of this audio?",
            "What were the key decisions or action items?",
        ]
        for q in queries:
            logger.info(f"\n[Query]: {q}")
            result = await rag.aquery(q, mode="hybrid")
            logger.info(f"Answer: {result}")


def main():
    parser = argparse.ArgumentParser(description="RAG-Anything Audio Processing Example")
    parser.add_argument("file_path", help="Path to audio file (.mp3, .wav, etc.)")
    parser.add_argument("--api-key", default=os.getenv("LLM_BINDING_API_KEY"))
    parser.add_argument("--base-url", default=os.getenv("LLM_BINDING_HOST"))

    args = parser.parse_args()
    if not args.api_key:
        logger.error("API key required. Set LLM_BINDING_API_KEY in .env or use --api-key")
        return

    asyncio.run(process_audio(args.file_path, args.api_key, args.base_url))


if __name__ == "__main__":
    main()
