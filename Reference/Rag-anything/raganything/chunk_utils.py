"""Chunk formatting utilities extracted from ProcessorMixin.

These are pure functions usable by both pipeline stages and the
backward-compatibility ProcessorMixin forwarding layer.
"""

import logging
from typing import Any, Dict

from raganything.prompt import PROMPTS
from raganything.utils import (
    format_table_body,
    get_equation_text_and_format,
    get_table_body,
    normalize_caption_list,
)

logger = logging.getLogger(__name__)


def sample_frames(frames: list, max_frames: int = 5) -> list:
    """Uniform sample frames to avoid head-of-segment bias."""
    if len(frames) <= max_frames:
        return frames
    indices = [int(i * (len(frames) - 1) / (max_frames - 1)) for i in range(max_frames)]
    return [frames[i] for i in indices]


def apply_chunk_template(
    content_type: str,
    original_item: Dict[str, Any],
    description: str,
) -> str:
    """Apply the appropriate chunk template based on content type.

    Extracted from ProcessorMixin._apply_chunk_template.
    """
    try:
        if content_type == "image":
            image_path = original_item.get("img_path", "")
            captions = normalize_caption_list(
                original_item.get(
                    "image_caption", original_item.get("img_caption", [])
                )
            )
            footnotes = normalize_caption_list(
                original_item.get(
                    "image_footnote", original_item.get("img_footnote", [])
                )
            )

            return PROMPTS["image_chunk"].format(
                image_path=image_path,
                captions=", ".join(captions) if captions else "None",
                footnotes=", ".join(footnotes) if footnotes else "None",
                enhanced_caption=description,
            )

        elif content_type == "table":
            table_img_path = original_item.get("img_path", "")
            table_caption = normalize_caption_list(
                original_item.get("table_caption", [])
            )
            table_body = format_table_body(get_table_body(original_item))
            table_footnote = normalize_caption_list(
                original_item.get("table_footnote", [])
            )

            return PROMPTS["table_chunk"].format(
                table_img_path=table_img_path,
                table_caption=", ".join(table_caption) if table_caption else "None",
                table_body=table_body,
                table_footnote=", ".join(table_footnote)
                if table_footnote
                else "None",
                enhanced_caption=description,
            )

        elif content_type == "equation":
            equation_text, equation_format = get_equation_text_and_format(
                original_item
            )

            return PROMPTS["equation_chunk"].format(
                equation_text=equation_text,
                equation_format=equation_format,
                enhanced_caption=description,
            )

        elif content_type == "audio":
            return PROMPTS["audio_chunk"].format(
                start_time=original_item.get("asr_start_time", 0.0),
                end_time=original_item.get("asr_end_time", 0.0),
                file_name=original_item.get("file_name", "Unknown"),
                segment_index=original_item.get("asr_segment_index", 0),
                total_segments=original_item.get("asr_total_segments", 1),
                language=original_item.get("asr_language", "unknown"),
                relative_position=original_item.get("asr_relative_position", 0.0),
                transcript=original_item.get("asr_transcript", ""),
            )

        elif content_type == "video":
            frame_descriptions = original_item.get("frame_descriptions", "")
            return PROMPTS["video_chunk"].format(
                start_time=original_item.get("asr_start_time", 0.0),
                end_time=original_item.get("asr_end_time", 0.0),
                file_name=original_item.get("file_name", "Unknown"),
                segment_index=original_item.get("asr_segment_index", 0),
                total_segments=original_item.get("asr_total_segments", 1),
                language=original_item.get("asr_language", "unknown"),
                frame_count=original_item.get("frame_count", 0),
                frame_descriptions=frame_descriptions if frame_descriptions.strip() else "(no visual context)",
                transcript=original_item.get("asr_transcript", ""),
            )

        else:  # generic or unknown types
            content = str(original_item.get("content", original_item))

            return PROMPTS["generic_chunk"].format(
                content_type=content_type.title(),
                content=content,
                enhanced_caption=description,
            )

    except Exception as e:
        logger.warning(
            f"Error applying chunk template for {content_type}: {e}"
        )
        return description
