"""Tests for ModalProcessorBuilder."""

from unittest.mock import MagicMock, patch

import pytest

from raganything.config import RAGAnythingConfig
from raganything.processor_builder import ModalProcessorBuilder


@pytest.fixture
def mock_lightrag():
    lr = MagicMock()
    lr.tokenizer = MagicMock()
    return lr


@pytest.fixture
def full_config():
    return RAGAnythingConfig(
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
        enable_audio_processing=True,
        enable_video_processing=True,
    )


@pytest.fixture
def minimal_config():
    return RAGAnythingConfig(
        enable_image_processing=False,
        enable_table_processing=False,
        enable_equation_processing=False,
        enable_audio_processing=False,
        enable_video_processing=False,
    )


class TestBuilder:
    """Tests build_all behavior with mocked modal processors."""

    @patch("raganything.processor_builder.GenericModalProcessor")
    def test_build_all_creates_generic_always(self, mock_generic, mock_lightrag, minimal_config):
        builder = ModalProcessorBuilder(mock_lightrag, minimal_config, MagicMock())
        processors = builder.build_all()
        assert "generic" in processors
        mock_generic.assert_called_once()

    @patch("raganything.video_processor.VideoModalProcessor")
    @patch("raganything.modalprocessors.AsrModalProcessor")
    @patch("raganything.processor_builder.GenericModalProcessor")
    @patch("raganything.processor_builder.ImageModalProcessor")
    @patch("raganything.processor_builder.TableModalProcessor")
    @patch("raganything.processor_builder.EquationModalProcessor")
    def test_build_all_with_full_config(
        self, mock_eq, mock_table, mock_image, mock_generic,
        mock_asr, mock_video, mock_lightrag, full_config,
    ):
        builder = ModalProcessorBuilder(mock_lightrag, full_config, MagicMock())
        builder.with_asr_backend(MagicMock())
        processors = builder.build_all()
        assert "image" in processors
        assert "table" in processors
        assert "equation" in processors
        assert "audio" in processors
        assert "video" in processors
        assert "generic" in processors

    @patch("raganything.video_processor.VideoModalProcessor")
    @patch("raganything.processor_builder.GenericModalProcessor")
    @patch("raganything.processor_builder.ImageModalProcessor")
    @patch("raganything.processor_builder.TableModalProcessor")
    @patch("raganything.processor_builder.EquationModalProcessor")
    def test_build_all_without_asr_skips_audio(
        self, mock_eq, mock_table, mock_image, mock_generic,
        mock_video, mock_lightrag, full_config,
    ):
        builder = ModalProcessorBuilder(mock_lightrag, full_config, MagicMock())
        # No ASR backend set
        processors = builder.build_all()
        assert "audio" not in processors

    @patch("raganything.processor_builder.GenericModalProcessor")
    def test_build_all_minimal_config(self, mock_generic, mock_lightrag, minimal_config):
        builder = ModalProcessorBuilder(mock_lightrag, minimal_config, MagicMock())
        processors = builder.build_all()
        assert "image" not in processors
        assert "table" not in processors
        assert "equation" not in processors
        assert "generic" in processors
        mock_generic.assert_called_once()
