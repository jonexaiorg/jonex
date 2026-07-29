"""
Utility functions for RAGAnything

Contains helper functions for content separation, text insertion, and other utilities
"""

import base64
import inspect
from typing import Dict, List, Any, Tuple
from pathlib import Path
from lightrag.utils import logger


def normalize_caption_list(value: Any) -> List[str]:
    """Return captions and footnotes as a clean list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def get_table_body(item: Dict[str, Any]) -> Any:
    """Read table content across common content-list alias fields."""
    if item.get("table_body") not in (None, ""):
        return item.get("table_body")
    if item.get("table_data") not in (None, ""):
        return item.get("table_data")
    return item.get("text", "")


def format_table_body(table_body: Any) -> str:
    """Serialize table content for prompts and chunks without dropping aliases.

    Strings are passed through unchanged. List-of-lists (the common
    ``table_data`` shape from non-MinerU parsers) are rendered as a simple
    Markdown table so the LLM sees structured rows instead of a Python repr.
    Other shapes fall back to a newline-joined string of ``str(...)`` items.
    """
    if isinstance(table_body, str):
        return table_body
    if isinstance(table_body, list):
        if not table_body:
            return ""
        if all(isinstance(row, (list, tuple)) for row in table_body):
            rendered_rows = [
                "| " + " | ".join(str(cell) for cell in row) + " |"
                for row in table_body
            ]
            if len(rendered_rows) >= 1:
                column_count = max(len(row) for row in table_body)
                separator = "| " + " | ".join(["---"] * column_count) + " |"
                rendered_rows.insert(1, separator)
            return "\n".join(rendered_rows)
        return "\n".join(str(row) for row in table_body)
    return str(table_body)


def get_equation_text_and_format(item: Dict[str, Any]) -> Tuple[str, str]:
    """Read equation content while preserving LaTeX aliases from content lists.

    Field priority follows MinerU first (``text`` + ``text_format``), then
    falls back to ``latex`` and ``equation`` aliases used by other parsers.
    The textual description is intentionally NOT concatenated into the
    equation body: the ``equation_chunk`` template has a separate
    ``enhanced_caption`` slot for that.
    """
    text = str(item.get("text", "") or "").strip()
    latex = str(item.get("latex", "") or "").strip()
    equation = str(item.get("equation", "") or "").strip()
    equation_format = str(item.get("text_format", "") or "").strip()

    if text:
        equation_text = text
    elif latex:
        equation_text = latex
        if not equation_format:
            equation_format = "latex"
    elif equation:
        equation_text = equation
    else:
        equation_text = ""

    return equation_text, equation_format


def separate_content(
    content_list: List[Dict[str, Any]],
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Separate text content and multimodal content

    For each text block, computes positional metadata:
      - page_idx:   page number from parser (0-based)
      - text_idx:   position index in content_list
      - line_start: starting line in the concatenated full text (1-based)
      - line_end:   ending line in the concatenated full text (1-based)

    Args:
        content_list: Content list from MinerU parsing

    Returns:
        (text_content, multimodal_items): Pure text content and multimodal items list.
        The last element of multimodal_items is a sentinel ``{"_text_meta": [...]}``
        carrying per-block metadata for downstream use.
    """
    text_parts = []
    text_meta_list: List[Dict[str, Any]] = []
    multimodal_items = []
    line_cursor = 1  # 1-based document-level line counter

    for index, item in enumerate(content_list):
        content_type = item.get("type", "text")

        if content_type == "text":
            # Text content — preserve positional metadata
            text = item.get("text", "")
            if text.strip():
                lines_in_block = text.count("\n") + 1
                text_parts.append(text)
                # Record per-block metadata for downstream chunk tracking
                text_meta_list.append({
                    "content": text,
                    "page_idx": item.get("page_idx", 0),
                    "text_idx": index,  # original position in content_list
                    "line_start": line_cursor,
                    "line_end": line_cursor + lines_in_block - 1,
                })
                # Advance cursor: this block's lines + 1 for the "\n\n" join
                # separator between blocks (adds one empty line)
                line_cursor += lines_in_block + 1
        else:
            # Multimodal content (image, table, equation, etc.)
            multimodal_item = dict(item)
            multimodal_item.setdefault("_content_list_index", index)
            multimodal_items.append(multimodal_item)

    # Merge all text content for backward-compatible full-text reference
    text_content = "\n\n".join(text_parts)

    # Attach metadata list to the return value for callers that need it.
    # Stored as an attribute on the string is not Pythonic, so we return
    # the metadata list separately via a sentinel key in multimodal_items.
    # Backward-compatible callers only use text_content and multimodal_items.
    multimodal_items.append({"_text_meta": text_meta_list})

    logger.info("Content separation complete:")
    logger.info(f"  - Text content length: {len(text_content)} characters")
    logger.info(f"  - Text blocks: {len(text_meta_list)}")
    logger.info(f"  - Multimodal items count: {len(multimodal_items) - 1}")

    # Count multimodal types
    modal_types = {}
    for item in multimodal_items:
        modal_type = item.get("type", "unknown")
        modal_types[modal_type] = modal_types.get(modal_type, 0) + 1

    if modal_types:
        logger.info(f"  - Multimodal type distribution: {modal_types}")

    return text_content, multimodal_items


def extract_text_metadata(multimodal_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract text block metadata hidden in multimodal_items by separate_content.

    Returns:
        List of dicts with keys: content, page_idx, text_idx
    """
    for item in multimodal_items:
        if "_text_meta" in item:
            return item["_text_meta"]
    return []


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode image file to base64 string

    Args:
        image_path: Path to the image file

    Returns:
        str: Base64 encoded string, empty string if encoding fails
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string
    except Exception as e:
        logger.error(f"Failed to encode image {image_path}: {e}")
        return ""


def validate_image_file(image_path: str, max_size_mb: int = 50) -> bool:
    """
    Validate if a file is a valid image file

    Args:
        image_path: Path to the image file
        max_size_mb: Maximum file size in MB

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        path = Path(image_path)

        logger.debug(f"Validating image path: {image_path}")
        logger.debug(f"Resolved path object: {path}")
        logger.debug(f"Path exists check: {path.exists()}")

        # Check if file exists and is not a symlink (for security)
        if not path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return False

        if path.is_symlink():
            logger.warning(f"Blocking symlink for security: {image_path}")
            return False

        # Check file extension
        image_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".tiff",
            ".tif",
        ]

        path_lower = str(path).lower()
        has_valid_extension = any(path_lower.endswith(ext) for ext in image_extensions)
        logger.debug(
            f"File extension check - path: {path_lower}, valid: {has_valid_extension}"
        )

        if not has_valid_extension:
            logger.warning(f"File does not appear to be an image: {image_path}")
            return False

        # Check file size
        file_size = path.stat().st_size
        max_size = max_size_mb * 1024 * 1024
        logger.debug(
            f"File size check - size: {file_size} bytes, max: {max_size} bytes"
        )

        if file_size > max_size:
            logger.warning(f"Image file too large ({file_size} bytes): {image_path}")
            return False

        logger.debug(f"Image validation successful: {image_path}")
        return True

    except Exception as e:
        logger.error(f"Error validating image file {image_path}: {e}")
        return False


async def insert_text_content(
    lightrag,
    input: str | list[str] | list[dict],
    file_paths: str | list[str] | None = None,
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
    ids: str | list[str] | None = None,
):
    """
    Insert text content into LightRAG with optional per-chunk metadata.

    When *input* is a ``list[dict]``, each dict must have a ``"content"`` key.
    Extra keys (``page_idx``, ``text_idx``, etc.) are forwarded as chunk metadata
    via ``lightrag.ainsert_custom_chunks``, bypassing LightRAG's internal
    token-based splitting.  This preserves positional information through the
    ingestion pipeline.

    When *input* is a plain ``str`` or ``list[str]``, behaviour is identical to
    the previous implementation (delegates to ``lightrag.ainsert``).

    Args:
        lightrag: LightRAG instance.
        input: Text to insert — plain string(s) or pre-chunked metadata dicts.
        file_paths: File path(s) for reference citation.
        split_by_character: Character to split on (plain-text mode only).
        split_by_character_only: Split by character only (plain-text mode only).
        ids: Document ID(s).
    """
    logger.info("Starting text content insertion into LightRAG...")

    # ── Metadata-aware path: list[dict] → ainsert_custom_chunks ─────
    if isinstance(input, list) and len(input) > 0 and isinstance(input[0], dict):
        # Build full text from all chunks for document storage
        full_text = "\n\n".join(
            item.get("content", "") if isinstance(item, dict) else str(item)
            for item in input
        )
        # Normalize file_paths to a single string for the doc entry
        fp = file_paths
        if isinstance(fp, list):
            fp = fp[0] if fp else ""
        fp = fp or ""

        doc_id = None
        if ids:
            doc_id = ids if isinstance(ids, str) else ids[0] if ids else None

        await lightrag.ainsert_custom_chunks(
            full_text=full_text,
            text_chunks=input,
            doc_id=doc_id,
            file_path=fp,
        )
        logger.info(
            f"Text content insertion complete "
            f"({len(input)} chunks with metadata)"
        )
        return

    # ── Plain-text path: str | list[str] → ainsert (backward compat) ─
    await lightrag.ainsert(
        input=input,
        file_paths=file_paths,
        split_by_character=split_by_character,
        split_by_character_only=split_by_character_only,
        ids=ids,
    )

    logger.info("Text content insertion complete")


async def insert_text_content_with_multimodal_content(
    lightrag,
    input: str | list[str],
    multimodal_content: list[dict[str, any]] | None = None,
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
    ids: str | list[str] | None = None,
    file_paths: str | list[str] | None = None,
    scheme_name: str | None = None,
):
    """
    Insert pure text content into LightRAG

    Args:
        lightrag: LightRAG instance
        input: Single document string or list of document strings
        multimodal_content: Multimodal content list (optional)
        split_by_character: if split_by_character is not None, split the string by character, if chunk longer than
        chunk_token_size, it will be split again by token size.
        split_by_character_only: if split_by_character_only is True, split the string by character only, when
        split_by_character is None, this parameter is ignored.
        ids: single string of the document ID or list of unique document IDs, if not provided, MD5 hash IDs will be generated
        file_paths: single string of the file path or list of file paths, used for citation
        scheme_name: scheme name (optional)
    """
    logger.info("Starting text content insertion into LightRAG...")

    insert_kwargs = {
        "input": input,
        "file_paths": file_paths,
        "split_by_character": split_by_character,
        "split_by_character_only": split_by_character_only,
        "ids": ids,
    }

    try:
        insert_signature = inspect.signature(lightrag.ainsert)
        supported_params = insert_signature.parameters
        accepts_any_kwargs = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in supported_params.values()
        )
    except (TypeError, ValueError):
        supported_params = {}
        accepts_any_kwargs = True

    if multimodal_content is not None and (
        accepts_any_kwargs or "multimodal_content" in supported_params
    ):
        insert_kwargs["multimodal_content"] = multimodal_content
    elif multimodal_content is not None:
        logger.warning(
            "LightRAG ainsert() does not accept multimodal_content; "
            "retrying with text-only insertion so doc_status is still created"
        )

    if scheme_name is not None and (
        accepts_any_kwargs or "scheme_name" in supported_params
    ):
        insert_kwargs["scheme_name"] = scheme_name
    elif scheme_name is not None:
        logger.warning(
            "LightRAG ainsert() does not accept scheme_name; "
            "continuing without it for compatibility"
        )

    await lightrag.ainsert(**insert_kwargs)

    logger.info("Text content insertion complete")


_PROCESSOR_KEY_MAP: Dict[str, str] = {
    "image": "image",
    "table": "table",
    "equation": "equation",
    "audio": "audio",
    "video": "video",
}


def get_processor_for_type(modal_processors: Dict[str, Any], content_type: str):
    """
    Get appropriate processor based on content type using registry.

    Args:
        modal_processors: Dictionary of available processors
        content_type: Content type

    Returns:
        Corresponding processor instance
    """
    key = _PROCESSOR_KEY_MAP.get(content_type)
    if key:
        proc = modal_processors.get(key)
        if proc is not None:
            return proc
    return modal_processors.get("generic")


def get_processor_supports(proc_type: str) -> List[str]:
    """Get processor supported features"""
    supports_map = {
        "image": [
            "Image content analysis",
            "Visual understanding",
            "Image description generation",
            "Image entity extraction",
        ],
        "table": [
            "Table structure analysis",
            "Data statistics",
            "Trend identification",
            "Table entity extraction",
        ],
        "equation": [
            "Mathematical formula parsing",
            "Variable identification",
            "Formula meaning explanation",
            "Formula entity extraction",
        ],
        "audio": [
            "Audio transcription via ASR",
            "Transcript segment chunking",
            "Audio content summarization",
            "Audio entity extraction with time metadata",
        ],
        "generic": [
            "General content analysis",
            "Structured processing",
            "Entity extraction",
        ],
    }
    return supports_map.get(proc_type, ["Basic processing"])


# ── Parser kwarg filtering ───────────────────────────────────────────

_PARSER_KWARG_KEYS = frozenset({
    "lang", "device", "start_page", "end_page",
    "formula", "table", "backend", "source",
})


def filter_parser_kwargs(kwargs):
    """Return only kwargs that are relevant parser configuration keys."""
    return {k: v for k, v in kwargs.items() if k in _PARSER_KWARG_KEYS}
