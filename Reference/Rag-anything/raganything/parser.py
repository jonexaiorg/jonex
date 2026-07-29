# type: ignore
"""
⚠️  Deprecated import path — use :mod:`raganything.parsers` instead.

This module is a backward-compatibility shim that re-exports everything
from ``raganything.parsers``.  New code should import directly from
``raganything.parsers`` (e.g. ``from raganything.parsers import Parser``).

The shim also retains the standalone CLI entry point (``main()``, also
registered as ``raganything-parser`` console script).
"""

import argparse

# Re-export everything from the new parsers package.
from raganything.parsers import *  # noqa: F401, F403
from raganything.parsers.base import Parser  # noqa: F401
from raganything.parsers.registry import (  # noqa: F401
    _CUSTOM_PARSERS,
    _normalize_parser_name,
    get_parser,
    get_supported_parsers,
    list_parsers,
    register_parser,
    unregister_parser,
)
from raganything.parsers.mineru import MineruExecutionError  # noqa: F401

logger = __import__("logging").getLogger(__name__)


def main():
    """
    Main function to run the document parser from command line
    """
    parser = argparse.ArgumentParser(
        description="Parse documents using MinerU 2.0, MinerU online, MinerU self-host, Docling, or PaddleOCR"
    )
    parser.add_argument("file_path", help="Path to the document to parse")
    parser.add_argument("--output", "-o", help="Output directory path")
    parser.add_argument(
        "--method",
        "-m",
        choices=["auto", "txt", "ocr"],
        default="auto",
        help="Parsing method (auto, txt, ocr)",
    )
    parser.add_argument(
        "--lang",
        "-l",
        help="Document language for OCR optimization (e.g., ch, en, ja)",
    )
    parser.add_argument(
        "--backend",
        "-b",
        choices=[
            "pipeline",
            "hybrid-auto-engine",
            "hybrid-http-client",
            "vlm-auto-engine",
            "vlm-http-client",
        ],
        default="pipeline",
        help="Parsing backend",
    )
    parser.add_argument(
        "--device",
        "-d",
        help="Inference device (e.g., cpu, cuda, cuda:0, npu, mps)",
    )
    parser.add_argument(
        "--source",
        choices=["huggingface", "modelscope", "local"],
        default="huggingface",
        help="Model source",
    )
    parser.add_argument(
        "--no-formula",
        action="store_true",
        help="Disable formula parsing",
    )
    parser.add_argument(
        "--no-table",
        action="store_true",
        help="Disable table parsing",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Display content statistics"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check parser installation",
    )
    parser.add_argument(
        "--parser",
        default="mineru",
        help=(
            "Parser selection. Built-ins: mineru, mineru_online, mineru_selfhost, "
            "docling, paddleocr. "
            "Custom parsers registered via register_parser() in the same "
            "Python process are also accepted when you integrate RAGAnything "
            "as a library. The standalone CLI itself only sees parsers that "
            "have already been registered in this process."
        ),
    )
    parser.add_argument(
        "--vlm_url",
        help="When the backend is `vlm-http-client`, you need to specify the server_url",
    )

    args = parser.parse_args()

    if args.check:
        doc_parser = get_parser(args.parser)
        if doc_parser.check_installation():
            print(f"✅ {args.parser.title()} is properly installed")
            return 0
        else:
            print(f"❌ {args.parser.title()} installation check failed")
            return 1

    try:
        doc_parser = get_parser(args.parser)
        content_list = doc_parser.parse_document(
            file_path=args.file_path,
            method=args.method,
            output_dir=args.output,
            lang=args.lang,
            backend=args.backend,
            device=args.device,
            source=args.source,
            formula=not args.no_formula,
            table=not args.no_table,
            vlm_url=args.vlm_url,
        )

        print(f"✅ Successfully parsed: {args.file_path}")
        print(f"📊 Extracted {len(content_list)} content blocks")

        if args.stats:
            print("\n📈 Document Statistics:")
            print(f"Total content blocks: {len(content_list)}")
            content_types = {}
            for item in content_list:
                if isinstance(item, dict):
                    content_type = item.get("type", "unknown")
                    content_types[content_type] = content_types.get(content_type, 0) + 1
            if content_types:
                print("\n📋 Content Type Distribution:")
                for content_type, count in sorted(content_types.items()):
                    print(f"  • {content_type}: {count}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
