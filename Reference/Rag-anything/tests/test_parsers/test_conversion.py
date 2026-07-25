"""Tests for the conversion utilities."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from raganything.parsers.conversion import (
    _process_inline_markdown,
    convert_office_to_pdf,
    convert_text_to_pdf,
)


class TestProcessInlineMarkdown:
    """Pure function tests — no external dependencies needed."""

    def test_bold_double_asterisk(self):
        result = _process_inline_markdown("hello **world** test")
        assert "<b>world</b>" in result

    def test_bold_double_underscore(self):
        result = _process_inline_markdown("hello __world__ test")
        assert "<b>world</b>" in result

    def test_italic_single_asterisk(self):
        result = _process_inline_markdown("hello *world* test")
        assert "<i>world</i>" in result

    def test_italic_single_underscore(self):
        result = _process_inline_markdown("hello _world_ test")
        assert "<i>world</i>" in result

    def test_inline_code(self):
        result = _process_inline_markdown("use `code` here")
        assert 'font name="Courier"' in result
        assert "code" in result

    def test_link(self):
        result = _process_inline_markdown("[text](http://example.com)")
        assert 'href="http://example.com"' in result
        assert "text" in result

    def test_strikethrough(self):
        result = _process_inline_markdown("hello ~~world~~ test")
        assert "<strike>world</strike>" in result

    def test_html_escaping(self):
        result = _process_inline_markdown("a & b < c > d")
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result

    def test_empty_text(self):
        assert _process_inline_markdown("") == ""


class TestConvertOfficeToPdf:
    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            convert_office_to_pdf("/nonexistent/doc.docx")

    @patch("raganything.parsers.conversion.subprocess.run")
    def test_successful_conversion(self, mock_run, tmp_path):
        doc = tmp_path / "test.docx"
        doc.write_bytes(b"fake doc content")

        # Mock LibreOffice to succeed
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Mock generated PDF (separate path from doc to avoid file-lock issues)
        fake_pdf = Path(tmp_path / "generated" / "test.pdf")
        fake_pdf.parent.mkdir(parents=True)
        fake_pdf.write_bytes(b"a" * 200)

        with patch("raganything.parsers.conversion.Path.glob") as mock_glob:
            mock_glob.return_value = [fake_pdf]
            result = convert_office_to_pdf(str(doc), str(tmp_path))
            assert result.exists()
            assert result.name == "test.pdf"


class TestConvertTextToPdf:
    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            convert_text_to_pdf("/nonexistent/test.txt")

    def test_unsupported_format_raises(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("content")
        with pytest.raises(ValueError, match="Unsupported text format"):
            convert_text_to_pdf(str(f))

    def test_reportlab_not_installed(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")

        # Force ImportError on reportlab import
        import builtins
        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name.startswith("reportlab"):
                raise ImportError("reportlab not installed")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with pytest.raises(RuntimeError, match="reportlab is required"):
                convert_text_to_pdf(str(f), str(tmp_path))
