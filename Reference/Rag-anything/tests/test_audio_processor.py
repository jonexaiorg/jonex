"""Unit tests for AsrModalProcessor audio processing."""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from raganything.modalprocessors import (
    AsrModalProcessor,
    AUDIO_ENTITY_TYPE_ENUM,
    _sha256,
    _asr_config_hash,
)


def _make_config(**overrides):
    """Minimal config with audio defaults."""
    cfg = MagicMock()
    cfg.max_parallel_asr = 1
    cfg.audio_asr_timeout = 30
    cfg.audio_chunk_token_size = 600
    cfg.audio_summarize_batch_size = 8
    cfg.audio_summarize_max_batches = 20
    cfg.min_asr_confidence = 0.0
    cfg.parser_output_dir = tempfile.gettempdir()
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def _make_asr_func():
    def asr(path):
        return {
            "transcript": "Hello world. This is a test.",
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Hello world.", "confidence": 0.95},
                {"start": 1.0, "end": 2.5, "text": "This is a test.", "confidence": 0.90},
            ],
            "language": "en",
            "duration": 2.5,
        }
    asr.asr_identity = "test:mock"
    asr.asr_model = "mock"
    return asr


def _make_proc(asr_func=None, config=None, tokenizer=None, modal_caption_func=None):
    """Create AsrModalProcessor with asdict patched."""
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

    with patch("raganything.modalprocessors.asdict", return_value={}):
        return AsrModalProcessor(
            lightrag,
            modal_caption_func or AsyncMock(),
            asr_func or _make_asr_func(),
            config=config or _make_config(),
            tokenizer=tokenizer,
        )


class TestEstimateTokens:
    def test_with_tokenizer(self):
        tok = MagicMock()
        tok.encode.return_value = list(range(50))
        proc = _make_proc(tokenizer=tok)
        assert proc._estimate_tokens("hello world") == 50

    def test_fallback_cjk_safe(self):
        proc = _make_proc(tokenizer=None)
        text = "你好世界，这是一个测试。"
        result = proc._estimate_tokens(text)
        assert result == max(1, -(-len(text) // 3))

    def test_fallback_empty(self):
        proc = _make_proc(tokenizer=None)
        assert proc._estimate_tokens("") == 1


class TestAsrConfigHash:
    def test_with_identity(self):
        def f(): pass
        f.asr_identity = "whisper:base"
        assert len(_asr_config_hash(f)) == 8

    def test_without_identity(self):
        def f(): pass
        assert len(_asr_config_hash(f)) == 8

    def test_different_identity_different_hash(self):
        def f(): pass
        f.asr_identity = "whisper:base"
        def g(): pass
        g.asr_identity = "whisper:large"
        assert _asr_config_hash(f) != _asr_config_hash(g)


class TestSegmentWithOverlap:
    def test_basic_no_overlap(self):
        config = _make_config(audio_chunk_token_size=600)
        proc = _make_proc(config=config)
        asr_result = {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Hello.", "confidence": 0.95},
                {"start": 1.0, "end": 2.0, "text": "World.", "confidence": 0.90},
            ],
            "duration": 2.0,
        }
        chunks = proc._segment_with_overlap(asr_result)
        assert len(chunks) == 1
        assert chunks[0]["start_time"] == 0.0
        assert chunks[0]["end_time"] == 2.0
        assert chunks[0]["source_segment_indices"] == [0, 1]

    def test_empty_segments_returns_dummy(self):
        proc = _make_proc()
        asr_result = {
            "segments": [{"start": 0.0, "end": 5.0, "text": "", "confidence": 0.0}],
            "duration": 5.0,
        }
        chunks = proc._segment_with_overlap(asr_result)
        assert len(chunks) == 1
        assert chunks[0]["end_time"] == 5.0

    def test_low_confidence_marked(self):
        config = _make_config(min_asr_confidence=0.5)
        proc = _make_proc(config=config)
        asr_result = {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Clear.", "confidence": 0.9},
                {"start": 1.0, "end": 2.0, "text": "Noisy.", "confidence": 0.1},
            ],
            "duration": 2.0,
        }
        chunks = proc._segment_with_overlap(asr_result)
        assert len(chunks) == 1
        assert chunks[0]["has_low_confidence"] is True

    def test_overlap_when_split(self):
        tok = MagicMock()
        tok.encode.return_value = list(range(500))
        config = _make_config(audio_chunk_token_size=400)
        proc = _make_proc(config=config, tokenizer=tok)
        asr_result = {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "A" * 100, "confidence": 1.0},
                {"start": 1.0, "end": 2.0, "text": "B" * 100, "confidence": 1.0},
                {"start": 2.0, "end": 3.0, "text": "C" * 100, "confidence": 1.0},
            ],
            "duration": 3.0,
        }
        chunks = proc._segment_with_overlap(asr_result)
        assert len(chunks) >= 2
        # Overlap: chunk0's last seg == chunk1's first seg
        assert chunks[0]["source_segment_indices"][-1] == chunks[1]["source_segment_indices"][0]


class TestProcessorRouting:
    def test_audio_routes_to_audio(self):
        from raganything.utils import get_processor_for_type
        proc = {"audio": "audio_proc", "generic": "gen_proc"}
        assert get_processor_for_type(proc, "audio") == "audio_proc"

    def test_unknown_routes_to_generic(self):
        from raganything.utils import get_processor_for_type
        proc = {"generic": "gen_proc"}
        assert get_processor_for_type(proc, "video") == "gen_proc"

    def test_audio_key_without_processor_falls_back(self):
        from raganything.utils import get_processor_for_type
        proc = {"generic": "gen_proc"}
        assert get_processor_for_type(proc, "audio") == "gen_proc"


class TestEntityTypeEnum:
    def test_known_types(self):
        assert "meeting" in AUDIO_ENTITY_TYPE_ENUM
        assert "lecture" in AUDIO_ENTITY_TYPE_ENUM
        assert "podcast" in AUDIO_ENTITY_TYPE_ENUM
        assert "unknown" in AUDIO_ENTITY_TYPE_ENUM

    def test_oov_not_in_enum(self):
        assert "brainstorm" not in AUDIO_ENTITY_TYPE_ENUM


class TestGenerateDescriptionOnly:
    @pytest.mark.asyncio
    async def test_empty_transcript_skips(self):
        proc = _make_proc()
        async def fake_load(path):
            return {"transcript": "", "segments": [], "language": "en", "duration": 0}
        proc._load_or_transcribe = fake_load

        desc, entity = await proc.generate_description_only(
            {"type": "audio", "audio_path": "/fake/empty.mp3", "file_name": "empty.mp3"},
            "audio",
        )
        assert desc == ""
        assert entity["entity_type"] == "unknown"
        assert entity["chunk_count"] == 0

    @pytest.mark.asyncio
    async def test_missing_audio_path_raises(self):
        proc = _make_proc()
        with pytest.raises(ValueError, match="No audio_path"):
            await proc.generate_description_only({"type": "audio"}, "audio")


class TestSha256:
    def test_deterministic(self):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        f.write(b"hello world")
        f.close()
        h = _sha256(f.name)
        assert len(h) == 64
        assert _sha256(f.name) == h
        os.unlink(f.name)
