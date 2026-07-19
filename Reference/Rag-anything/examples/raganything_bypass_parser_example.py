#!/usr/bin/env python
"""
Example script demonstrating how to skip MinerU parsing and directly insert
already-parsed content into RAGAnything.

Use this when you have already run MinerU to parse a document and the
content_list.json is available in the output directory. This bypasses the
parser step and proceeds directly to text insertion, multimodal processing,
and querying.

Usage:
    uv run python examples/raganything_bypass_parser_example.py \\
        --parsed-dir "./output/MyDoc_abc1234567/MyDoc/hybrid_auto" \\
        --file-path "/abs/path/to/MyDoc.pdf"

The --parsed-dir should point to the directory containing the
*_content_list.json file produced by MinerU.
"""

import os
import sys
import json
import argparse
import asyncio
import logging
import logging.config
from functools import partial
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc, logger, set_verbose_debug
from raganything import RAGAnything, RAGAnythingConfig
from raganything.asset_urls import attach_public_media_urls

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=False)


def configure_logging():
    log_dir = os.getenv("LOG_DIR", os.getcwd())
    log_file_path = os.path.abspath(
        os.path.join(log_dir, "raganything_bypass_parser_example.log")
    )

    print(f"\nRAGAnything bypass-parser example log file: {log_file_path}\n")
    os.makedirs(os.path.dirname(log_dir), exist_ok=True)

    log_max_bytes = int(os.getenv("LOG_MAX_BYTES", 10485760))
    log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", 5))

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": "%(levelname)s: %(message)s"},
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "file": {
                    "formatter": "detailed",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": log_file_path,
                    "maxBytes": log_max_bytes,
                    "backupCount": log_backup_count,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "lightrag": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    )

    logger.setLevel(logging.INFO)
    set_verbose_debug(os.getenv("VERBOSE", "false").lower() == "true")


def find_content_list_json(parsed_dir: Path) -> Path:
    """Find the content_list.json file in the parsed directory.

    MinerU outputs files named like: {stem}_content_list.json
    We prefer the v1 format; v2 has a different schema.
    """
    candidates = list(parsed_dir.glob("*_content_list.json"))
    # Exclude v2 files — they use a different format
    v1_candidates = [c for c in candidates if "_content_list_v2" not in c.name]

    if v1_candidates:
        return v1_candidates[0]
    if candidates:
        return candidates[0]
    raise FileNotFoundError(
        f"No *_content_list.json found in {parsed_dir}"
    )


def load_and_fix_content_list(json_path: Path, images_base_dir: Path) -> list:
    """Load content_list and fix relative image paths to absolute paths.

    Replicates the post-processing done by MineruParser._read_output_files().
    """
    with open(json_path, "r", encoding="utf-8") as f:
        content_list = json.load(f)

    # Normalize MinerU 1.x → 2.0 field name aliases
    _FIELD_ALIASES = {
        "img_caption": "image_caption",
        "img_footnote": "image_footnote",
    }
    for item in content_list:
        if not isinstance(item, dict):
            continue
        for old_name, new_name in _FIELD_ALIASES.items():
            if old_name in item and new_name not in item:
                item[new_name] = item[old_name]
            elif new_name in item and old_name not in item:
                item[old_name] = item[new_name]

    # Fix relative image paths → absolute
    resolved_base = images_base_dir.resolve()
    for item in content_list:
        if not isinstance(item, dict):
            continue
        for field_name in ["img_path", "table_img_path", "equation_img_path"]:
            if field_name in item and item[field_name]:
                img_path = item[field_name]
                absolute_img_path = (images_base_dir / img_path).resolve()
                if not absolute_img_path.is_relative_to(resolved_base):
                    logger.warning(
                        f"Skipping path outside base dir: {img_path}"
                    )
                    item[field_name] = ""
                    continue
                item[field_name] = str(absolute_img_path)

    # Attach public media URLs for each item (matching parser post-processing)
    for item in content_list:
        if isinstance(item, dict):
            attach_public_media_urls(item)

    return content_list


async def process_bypass_parser(
    parsed_dir: str,
    file_path: str,
    api_key: str,
    base_url: str = None,
    working_dir: str = None,
):
    """
    Insert already-parsed MinerU content into RAGAnything and run queries.

    Args:
        parsed_dir: Directory containing MinerU's *_content_list.json
        file_path: Original document path (used as citation reference)
        api_key: API key
        base_url: Optional base URL for API
        working_dir: Working directory for RAG storage
    """
    try:
        parsed_dir = Path(parsed_dir).resolve()
        file_path_ref = Path(file_path)

        if not parsed_dir.is_dir():
            raise FileNotFoundError(f"Parsed directory not found: {parsed_dir}")

        # Find and load the content_list
        json_path = find_content_list_json(parsed_dir)
        logger.info(f"Loading content list from: {json_path}")
        content_list = load_and_fix_content_list(json_path, parsed_dir)
        logger.info(
            f"Loaded {len(content_list)} content blocks from parsed output"
        )

        # Count by type
        type_counts = {}
        for item in content_list:
            if isinstance(item, dict):
                t = item.get("type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
        logger.info(f"Content types: {type_counts}")

        # Configuration
        config = RAGAnythingConfig(
            working_dir=working_dir or "./rag_storage_bypass",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
            display_content_stats=True,
        )

        # Vision/VLM binding: separate host/api_key from LLM
        vision_base_url = os.getenv("VISION_BINDING_HOST") or base_url
        vision_api_key = os.getenv("VISION_BINDING_API_KEY") or api_key

        # Model functions
        llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        vision_model = os.getenv("VISION_MODEL", "gpt-4o")

        def llm_model_func(
            prompt, system_prompt=None, history_messages=[], **kwargs
        ):
            return openai_complete_if_cache(
                llm_model,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=api_key,
                base_url=base_url,
                **kwargs,
            )

        def vision_model_func(
            prompt,
            system_prompt=None,
            history_messages=[],
            image_data=None,
            messages=None,
            **kwargs,
        ):
            if messages:
                return openai_complete_if_cache(
                    vision_model,
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=messages,
                    api_key=vision_api_key,
                    base_url=vision_base_url,
                    **kwargs,
                )
            elif image_data:
                return openai_complete_if_cache(
                    vision_model,
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=[
                        {"role": "system", "content": system_prompt}
                        if system_prompt
                        else None,
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    },
                                },
                            ],
                        }
                        if image_data
                        else {"role": "user", "content": prompt},
                    ],
                    api_key=vision_api_key,
                    base_url=vision_base_url,
                    **kwargs,
                )
            else:
                return llm_model_func(
                    prompt, system_prompt, history_messages, **kwargs
                )

        # Embedding function — uses EMBEDDING_BINDING_HOST if set, else falls back to LLM_BINDING_HOST
        embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))
        embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        embedding_base_url = os.getenv("EMBEDDING_BINDING_HOST") or base_url
        embedding_api_key = os.getenv("EMBEDDING_BINDING_API_KEY") or api_key
        embedding_func = EmbeddingFunc(
            embedding_dim=embedding_dim,
            max_token_size=8192,
            func=partial(
                openai_embed.func,
                model=embedding_model,
                api_key=embedding_api_key,
                base_url=embedding_base_url,
            ),
        )

        # Initialize RAGAnything
        rag = RAGAnything(
            config=config,
            llm_model_func=llm_model_func,
            vision_model_func=vision_model_func,
            embedding_func=embedding_func,
        )

        # Insert content list (this is the key step — skips MinerU parsing)
        logger.info("Inserting content list into RAGAnything (bypassing parser)...")
        await rag.insert_content_list(
            content_list=content_list,
            file_path=str(file_path_ref),
        )
        logger.info("Content list insertion complete!")

        # Queries
        logger.info("\nQuerying processed document:")
        text_queries = [
            "What is the main content of the document?",
            "What are the key topics discussed?",
        ]

        for query in text_queries:
            logger.info(f"\n[Text Query]: {query}")
            result = await rag.aquery(query, mode="hybrid")
            logger.info(f"Answer: {result}")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback

        logger.error(traceback.format_exc())


def main():
    parser = argparse.ArgumentParser(
        description="Bypass MinerU parsing and insert already-parsed content"
    )
    parser.add_argument(
        "--parsed-dir",
        required=True,
        help="Path to MinerU output directory containing *_content_list.json",
    )
    parser.add_argument(
        "--file-path",
        required=True,
        help="Path to the original document (for citation reference)",
    )
    parser.add_argument(
        "--working_dir",
        "-w",
        default="./rag_storage_bypass",
        help="Working directory path (default: ./rag_storage_bypass to avoid "
        "conflicts with the main example's ./rag_storage)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("LLM_BINDING_API_KEY"),
        help="API key (defaults to LLM_BINDING_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("LLM_BINDING_HOST"),
        help="Optional base URL for API",
    )

    args = parser.parse_args()

    if not args.api_key:
        logger.error("Error: API key is required")
        logger.error("Set LLM_BINDING_API_KEY env var or use --api-key option")
        return

    asyncio.run(
        process_bypass_parser(
            parsed_dir=args.parsed_dir,
            file_path=args.file_path,
            api_key=args.api_key,
            base_url=args.base_url,
            working_dir=args.working_dir,
        )
    )


if __name__ == "__main__":
    configure_logging()

    print("RAGAnything Bypass Parser Example")
    print("=" * 40)
    print("Inserting pre-parsed MinerU content (skipping parser step)")
    print("=" * 40)

    main()
