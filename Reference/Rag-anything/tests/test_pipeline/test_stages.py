"""Tests for individual pipeline stages."""
import ssl
import urllib.error
from unittest.mock import MagicMock

import pytest

from raganything.pipeline.base import PipelineContext, PipelineServices
from raganything.pipeline.stages import (
    FileValidateStage,
    _is_transient_parse_error,
)


@pytest.fixture
def ctx():
    return PipelineContext(file_path="/nonexistent/file.pdf", file_name="file.pdf")


@pytest.fixture
def services():
    return PipelineServices(
        config=MagicMock(),
        lightrag=MagicMock(),
        doc_parser=MagicMock(),
        logger=MagicMock(),
    )


@pytest.mark.asyncio
async def test_file_validate_missing_file(ctx, services):
    stage = FileValidateStage()
    result = await stage.execute(ctx, services)
    assert result.error is not None
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_file_validate_exists(ctx, services, tmp_path):
    f = tmp_path / "test.pdf"
    f.write_text("content")
    ctx.file_path = str(f)
    stage = FileValidateStage()
    result = await stage.execute(ctx, services)
    assert result.error is None


# ── #4 _is_transient_parse_error ────────────────────────────────────


class TestIsTransientParseError:
    """[jonex] #4: transient error detection for parse retry."""

    def test_ssl_error_is_transient(self):
        assert _is_transient_parse_error(ssl.SSLError("unexpected eof")) is True

    def test_urlerror_is_transient(self):
        assert _is_transient_parse_error(urllib.error.URLError("timed out")) is True

    def test_timeout_error_is_transient(self):
        assert _is_transient_parse_error(TimeoutError("connection timed out")) is True

    def test_connection_error_is_transient(self):
        assert _is_transient_parse_error(ConnectionError("connection reset")) is True

    def test_value_error_is_not_transient(self):
        assert _is_transient_parse_error(ValueError("unsupported format")) is False

    def test_key_error_is_not_transient(self):
        assert _is_transient_parse_error(KeyError("missing field")) is False

    def test_transient_marker_in_message(self):
        # Exception type is not in the known set, but message contains a marker
        exc = RuntimeError("failed to download mineru result: timeout")
        assert _is_transient_parse_error(exc) is True

    def test_transient_marker_connection_reset(self):
        exc = OSError("connection reset by peer")
        assert _is_transient_parse_error(exc) is True

    def test_transient_marker_max_retries(self):
        exc = RuntimeError("max retries exceeded with url: /api/parse")
        assert _is_transient_parse_error(exc) is True

    def test_hard_failure_message_not_matched(self):
        exc = RuntimeError("unsupported file format PDF/A-3")
        assert _is_transient_parse_error(exc) is False

    def test_chained_exception_transient(self):
        """Transient exception as __cause__ should be detected."""
        inner = ssl.SSLError("unexpected eof while reading")
        outer = RuntimeError("parse failed")
        outer.__cause__ = inner
        assert _is_transient_parse_error(outer) is True

    def test_chained_exception_hard_failure(self):
        """Non-transient __cause__ should not be treated as transient."""
        inner = ValueError("corrupt content")
        outer = RuntimeError("parse failed")
        outer.__cause__ = inner
        assert _is_transient_parse_error(outer) is False
