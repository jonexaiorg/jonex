"""Unit tests for VideoModalProcessor video processing."""
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from raganything.video_processor import (
    VideoModalProcessor,
    VIDEO_ENTITY_TYPE_ENUM,
)


def _make_config(**overrides):
    """Minimal config with video defaults."""
    cfg = MagicMock()
    cfg.max_parallel_vlm = 1
    cfg.vlm_timeout = 30
    cfg.video_chunk_token_size = 600
    cfg.video_summarize_batch_size = 8
    cfg.video_summarize_max_batches = 20
    cfg.video_vlm_contextual_prompt = False
    cfg.vlm_force_time_interval = False
    cfg.parser_output_dir = tempfile.gettempdir()
    cfg.vlm_model_name = ""
    cfg.vlm_prompt_version = "v1"
    cfg.max_concurrent_video = 1
    cfg.video_cache_max_entries = 100
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def _make_vlm_func(description="Q2 Revenue Growth 32%. Meeting room."):
    async def vlm(image_path, prompt):
        return (
            f"===OCR===\n{description}\n"
            f"===SCENE===\nMeeting room with whiteboard"
        )
    return vlm


def _make_asr_backend():
    backend = MagicMock()
    backend.transcribe.return_value = {
        "transcript": "Hello world. This is a test.",
        "segments": [
            {"start": 0.0, "end": 1.0, "text": "Hello world.",
             "confidence": 0.95},
            {"start": 1.0, "end": 2.5, "text": "This is a test.",
             "confidence": 0.90},
        ],
        "language": "en",
        "duration": 2.5,
    }
    return backend


def _make_proc(vlm_func=None, asr_backend=None, config=None,
               tokenizer=None, modal_caption_func=None):
    """Create VideoModalProcessor with mocked dependencies."""
    lightrag = MagicMock()
    lightrag.tokenizer = tokenizer
    lightrag.text_chunks = MagicMock()
    lightrag.chunks_vdb = MagicMock()
    lightrag.entities_vdb = MagicMock()
    lightrag.relationships_vdb = MagicMock()
    lightrag.chunk_entity_relation_graph = MagicMock()
    lightrag.embedding_func = MagicMock()
    lightrag.llm_model_func = MagicMock()
    lightrag.llm_response_cache = MagicMock()
    lightrag.full_entities = MagicMock()
    lightrag.full_relations = MagicMock()
    lightrag.entity_chunks = MagicMock()
    lightrag.relation_chunks = MagicMock()
    lightrag.doc_status = MagicMock()

    with patch("raganything.modalprocessors.asdict", return_value={}):
        return VideoModalProcessor(
            lightrag=lightrag,
            modal_caption_func=modal_caption_func or AsyncMock(
                return_value="Test summary"),
            vlm_model_func=vlm_func or _make_vlm_func(),
            asr_backend=asr_backend or _make_asr_backend(),
            config=config or _make_config(),
            tokenizer=tokenizer,
        )


class TestVLMOutputParsing:
    """Tests for _parse_vlm_output method."""

    def test_parse_ocr_scene_separated(self):
        proc = _make_proc()
        raw = ("===OCR===\nQ2 Revenue Growth 32%\n"
               "===SCENE===\nMeeting room with whiteboard")
        result = proc._parse_vlm_output(raw)
        assert result is not None
        assert "Q2 Revenue Growth 32%" in result["ocr"]
        assert "Meeting room" in result["scene"]

    def test_parse_ocr_only_delimiter(self):
        proc = _make_proc()
        raw = "===OCR===\nDashboard showing metrics\n===SCENE===\n"
        result = proc._parse_vlm_output(raw)
        assert result is not None
        assert "Dashboard showing metrics" in result["ocr"]

    def test_parse_empty_input(self):
        proc = _make_proc()
        assert proc._parse_vlm_output("") is None

    def test_parse_unstructured_fallback(self):
        proc = _make_proc()
        raw = "1920x1080 display with charts"
        result = proc._parse_vlm_output(raw)
        assert result is not None
        assert "1920x1080" in result["ocr"]


class TestRetryTaxonomy:
    """Tests for _is_retryable_vlm_error."""

    def test_rate_limit_is_retryable(self):
        proc = _make_proc()
        assert proc._is_retryable_vlm_error(
            Exception("rate limit exceeded")) is True

    def test_500_is_retryable(self):
        proc = _make_proc()
        assert proc._is_retryable_vlm_error(
            Exception("500 internal server error")) is True

    def test_401_is_not_retryable(self):
        proc = _make_proc()
        assert proc._is_retryable_vlm_error(
            Exception("401 unauthorized")) is False

    def test_auth_error_is_not_retryable(self):
        proc = _make_proc()
        assert proc._is_retryable_vlm_error(
            Exception("invalid api key")) is False

    def test_timeout_is_retryable(self):
        proc = _make_proc()
        assert proc._is_retryable_vlm_error(
            Exception("connection timeout")) is True

    def test_unknown_is_retryable(self):
        proc = _make_proc()
        assert proc._is_retryable_vlm_error(
            Exception("some unknown error")) is True


class TestFrameOwnership:
    """Tests for _align_frames_to_segments."""

    def test_exclusive_ownership_basic(self):
        proc = _make_proc()
        segments = [
            {"start_time": 0.0, "end_time": 10.0, "frames": []},
            {"start_time": 8.0, "end_time": 18.0, "frames": []},
            {"start_time": 16.0, "end_time": 26.0, "frames": []},
        ]
        keyframes = [
            {"frame_time": 2.0},
            {"frame_time": 12.0},
            {"frame_time": 20.0},
        ]
        result = proc._align_frames_to_segments(segments, keyframes)
        assert len(result[0]["frames"]) == 1
        assert result[0]["frames"][0]["owner_segment"] == 0
        assert len(result[1]["frames"]) == 1
        assert result[1]["frames"][0]["owner_segment"] == 1
        assert len(result[2]["frames"]) == 1
        assert result[2]["frames"][0]["owner_segment"] == 2

    def test_boundary_frame_not_duplicated(self):
        proc = _make_proc()
        segments = [
            {"start_time": 0.0, "end_time": 10.0, "frames": []},
            {"start_time": 10.0, "end_time": 20.0, "frames": []},
        ]
        keyframes = [{"frame_time": 9.9}]
        result = proc._align_frames_to_segments(segments, keyframes)
        owned_count = sum(len(s["frames"]) for s in result)
        assert owned_count == 1

    def test_single_frame_one_segment(self):
        proc = _make_proc()
        segments = [{"start_time": 0.0, "end_time": 10.0, "frames": []}]
        keyframes = [{"frame_time": 5.0}]
        result = proc._align_frames_to_segments(segments, keyframes)
        assert len(result[0]["frames"]) == 1


class TestSegmentWithOverlap:
    """Tests for _segment_with_overlap."""

    def test_basic_chunking(self):
        proc = _make_proc(config=_make_config(video_chunk_token_size=5))
        asr = {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Hello"},
                {"start": 1.0, "end": 2.0, "text": "world"},
                {"start": 2.0, "end": 3.0, "text": "this"},
                {"start": 3.0, "end": 4.0, "text": "is"},
                {"start": 4.0, "end": 5.0, "text": "test"},
            ],
            "duration": 5.0,
        }
        result = proc._segment_with_overlap(asr)
        assert len(result) > 0
        for chunk in result:
            assert "text" in chunk
            assert "start_time" in chunk
            assert "end_time" in chunk
            assert "segment_index" in chunk

    def test_empty_segments(self):
        proc = _make_proc()
        asr = {"segments": [], "duration": 0.0}
        result = proc._segment_with_overlap(asr)
        assert result == []


class TestCondensation:
    """Tests for _condense_frame_descriptions."""

    @pytest.mark.asyncio
    async def test_ocr_used_as_condensed(self):
        proc = _make_proc()
        frames = [{
            "description": "Meeting room showing Q2 results",
            "ocr_text": "Q2 Revenue Growth 32%",
        }]
        result = await proc._condense_frame_descriptions(frames)
        assert "Q2 Revenue Growth" in result[0]["condensed"]

    @pytest.mark.asyncio
    async def test_ui_labels_filtered(self):
        proc = _make_proc()
        frames = [{
            "description": "Code editor",
            "ocr_text": "File\nEdit\nView\n12:34\n\nfunction main()",
        }]
        result = await proc._condense_frame_descriptions(frames)
        condensed = result[0]["condensed"]
        assert "File" not in condensed
        assert "Edit" not in condensed
        assert "function main" in condensed

    @pytest.mark.asyncio
    async def test_empty_description_skipped(self):
        proc = _make_proc()
        frames = [{"description": "", "ocr_text": ""}]
        result = await proc._condense_frame_descriptions(frames)
        # Should not crash, condensed stays absent
        assert result == frames


class TestEntityEnum:
    """Tests for VIDEO_ENTITY_TYPE_ENUM."""

    def test_entity_types(self):
        assert "meeting" in VIDEO_ENTITY_TYPE_ENUM
        assert "lecture" in VIDEO_ENTITY_TYPE_ENUM
        assert "unknown" in VIDEO_ENTITY_TYPE_ENUM
        assert len(VIDEO_ENTITY_TYPE_ENUM) == 12
