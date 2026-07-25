"""Tests for the Parser base class."""

from pathlib import Path

import pytest

from raganything.parsers.base import Parser


class _ConcreteParser(Parser):
    """Minimal concrete subclass for testing base class behavior."""

    def check_installation(self) -> bool:
        return True

    def parse_document(self, file_path, **kwargs):
        return [{"type": "text", "text": "test"}]


class TestParserFormatConstants:
    def test_office_formats(self):
        assert ".docx" in Parser.OFFICE_FORMATS
        assert ".pptx" in Parser.OFFICE_FORMATS
        assert ".xlsx" in Parser.OFFICE_FORMATS
        assert ".pdf" not in Parser.OFFICE_FORMATS

    def test_image_formats(self):
        assert ".png" in Parser.IMAGE_FORMATS
        assert ".jpg" in Parser.IMAGE_FORMATS
        assert ".jpeg" in Parser.IMAGE_FORMATS

    def test_audio_formats(self):
        assert ".mp3" in Parser.AUDIO_FORMATS
        assert ".wav" in Parser.AUDIO_FORMATS

    def test_video_formats(self):
        assert ".mp4" in Parser.VIDEO_FORMATS
        assert ".avi" in Parser.VIDEO_FORMATS
        assert ".mov" in Parser.VIDEO_FORMATS


class TestParserIsUrl:
    def test_valid_http_url(self):
        assert Parser._is_url("http://example.com/file.pdf")

    def test_valid_https_url(self):
        assert Parser._is_url("https://example.com/file.pdf")

    def test_invalid_local_path(self):
        assert not Parser._is_url("/local/path/file.pdf")

    def test_invalid_relative_path(self):
        assert not Parser._is_url("relative/path/file.pdf")

    def test_empty_string(self):
        assert not Parser._is_url("")


class TestParserUniqueOutputDir:
    def test_returns_path_with_hash(self, tmp_path):
        result = Parser._unique_output_dir(str(tmp_path), "/path/to/document.pdf")
        assert isinstance(result, Path)
        assert str(tmp_path) in str(result)
        assert "document" in str(result)

    def test_different_files_different_dirs(self, tmp_path):
        r1 = Parser._unique_output_dir(str(tmp_path), "/path/to/a.pdf")
        r2 = Parser._unique_output_dir(str(tmp_path), "/path/to/b.pdf")
        assert r1 != r2


class TestParserParseAudio:
    def test_existing_audio_file(self, tmp_path):
        parser = _ConcreteParser()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio content")

        result = parser.parse_audio(str(audio_file))
        assert len(result) == 1
        assert result[0]["type"] == "audio"
        assert "test.mp3" in result[0]["audio_path"]

    def test_nonexistent_audio_raises(self):
        parser = _ConcreteParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_audio("/nonexistent/audio.mp3")

    def test_unsupported_format_raises(self, tmp_path):
        parser = _ConcreteParser()
        f = tmp_path / "test.xyz"
        f.write_bytes(b"fake")
        with pytest.raises(ValueError, match="Unsupported audio format"):
            parser.parse_audio(str(f))


class TestParserParseVideo:
    def test_existing_video_file(self, tmp_path):
        parser = _ConcreteParser()
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video content")

        result = parser.parse_video(str(video_file))
        assert len(result) == 1
        assert result[0]["type"] == "video"
        assert "test.mp4" in result[0]["video_path"]

    def test_nonexistent_video_raises(self):
        parser = _ConcreteParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_video("/nonexistent/video.mp4")

    def test_unsupported_format_raises(self, tmp_path):
        parser = _ConcreteParser()
        f = tmp_path / "test.xyz"
        f.write_bytes(b"fake")
        with pytest.raises(ValueError, match="Unsupported video format"):
            parser.parse_video(str(f))


class TestParserCheckInstallation:
    def test_base_raises_not_implemented(self):
        # Parser base class raises NotImplementedError
        with pytest.raises(NotImplementedError):
            Parser().check_installation()

    def test_concrete_subclass_works(self):
        parser = _ConcreteParser()
        assert parser.check_installation() is True
