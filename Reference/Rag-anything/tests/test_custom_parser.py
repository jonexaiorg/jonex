"""Tests for the custom parser plugin system (addresses #151)."""

import json

import pytest

from raganything.parser import (
    MineruOnlineParser,
    MineruSelfHostParser,
    Parser,
    get_parser,
    register_parser,
    unregister_parser,
    list_parsers,
    get_supported_parsers,
    _CUSTOM_PARSERS,
    SUPPORTED_PARSERS,
)


class DummyParser(Parser):
    """Minimal custom parser for testing."""

    def check_installation(self) -> bool:
        return True

    def parse_document(self, file_path, output_dir="./output", method="auto", **kw):
        return [{"type": "text", "text": "dummy parsed content", "page_idx": 0}]

    def parse_pdf(self, pdf_path, output_dir="./output", method="auto", **kw):
        return self.parse_document(
            file_path=pdf_path, output_dir=output_dir, method=method, **kw
        )


class AnotherParser(Parser):
    """Another custom parser for testing."""

    def check_installation(self) -> bool:
        return False

    def parse_document(self, file_path, output_dir="./output", method="auto", **kw):
        return [{"type": "text", "text": "another parsed", "page_idx": 0}]


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure a clean custom parser registry for every test."""
    _CUSTOM_PARSERS.clear()
    yield
    _CUSTOM_PARSERS.clear()


class TestRegisterParser:
    def test_register_and_get(self):
        register_parser("dummy", DummyParser)
        parser = get_parser("dummy")
        assert isinstance(parser, DummyParser)

    def test_register_case_insensitive(self):
        register_parser("  Dummy  ", DummyParser)
        parser = get_parser("dummy")
        assert isinstance(parser, DummyParser)

    def test_register_rejects_non_parser_subclass(self):
        with pytest.raises(TypeError, match="subclass of Parser"):
            register_parser("bad", dict)

    def test_register_rejects_builtin_name(self):
        for name in ("mineru", "mineru_online", "mineru_selfhost", "docling", "paddleocr"):
            with pytest.raises(ValueError, match="Cannot override built-in"):
                register_parser(name, DummyParser)

    def test_register_overwrites_same_custom_name(self):
        register_parser("custom", DummyParser)
        register_parser("custom", AnotherParser)
        parser = get_parser("custom")
        assert isinstance(parser, AnotherParser)


class TestParserNameValidation:
    def test_register_rejects_non_string_name(self):
        with pytest.raises(TypeError, match="non-empty string"):
            register_parser(123, DummyParser)  # type: ignore[arg-type]

    def test_register_rejects_blank_name(self):
        with pytest.raises(ValueError, match="non-empty string"):
            register_parser("   ", DummyParser)

    def test_unregister_rejects_non_string_name(self):
        with pytest.raises(TypeError, match="non-empty string"):
            unregister_parser(None)  # type: ignore[arg-type]

    def test_unregister_rejects_blank_name(self):
        with pytest.raises(ValueError, match="non-empty string"):
            unregister_parser("   ")


class TestUnregisterParser:
    def test_unregister_existing(self):
        register_parser("dummy", DummyParser)
        unregister_parser("dummy")
        with pytest.raises(ValueError, match="Unsupported parser type"):
            get_parser("dummy")

    def test_unregister_nonexistent(self):
        with pytest.raises(KeyError, match="No custom parser"):
            unregister_parser("nonexistent")


class TestListParsers:
    def test_list_builtin_only(self):
        result = list_parsers()
        assert "mineru" in result
        assert "mineru_online" in result
        assert "mineru_selfhost" in result
        assert "docling" in result
        assert "paddleocr" in result
        assert len(result) == 5

    def test_list_includes_custom(self):
        register_parser("dummy", DummyParser)
        result = list_parsers()
        assert "dummy" in result
        assert result["dummy"] == "DummyParser"
        assert len(result) == 6


class TestGetSupportedParsers:
    def test_builtin_only(self):
        supported = get_supported_parsers()
        assert set(SUPPORTED_PARSERS).issubset(set(supported))

    def test_includes_custom(self):
        register_parser("dummy", DummyParser)
        supported = get_supported_parsers()
        assert "dummy" in supported


class TestGetParserFallback:
    def test_builtin_parsers_still_work(self):
        """Ensure built-in parsers are unaffected by the plugin system."""
        for name in SUPPORTED_PARSERS:
            parser = get_parser(name)
            assert isinstance(parser, Parser)

    def test_unknown_parser_raises(self):
        with pytest.raises(ValueError, match="Unsupported parser type"):
            get_parser("totally-unknown")

    def test_custom_parser_content(self):
        register_parser("dummy", DummyParser)
        parser = get_parser("dummy")
        content = parser.parse_document("fake.pdf")
        assert content == [
            {"type": "text", "text": "dummy parsed content", "page_idx": 0}
        ]


class TestMineruOnlineParser:
    def test_get_parser(self, monkeypatch):
        monkeypatch.setenv("MINERU_API_TOKEN", "token")
        parser = get_parser("mineru_online")
        assert isinstance(parser, MineruOnlineParser)
        assert parser.check_installation() is True

    def test_check_installation_requires_token(self, monkeypatch):
        monkeypatch.delenv("MINERU_API_TOKEN", raising=False)
        parser = MineruOnlineParser()
        assert parser.check_installation() is False

    def test_read_any_output_files_normalizes_paths(self, tmp_path):
        output_dir = tmp_path / "result" / "nested"
        image_dir = output_dir / "images"
        image_dir.mkdir(parents=True)
        (image_dir / "fig.png").write_bytes(b"fake")
        (output_dir / "paper.md").write_text("# Paper", encoding="utf-8")
        (output_dir / "paper_content_list.json").write_text(
            json.dumps(
                [
                    {
                        "type": "image",
                        "img_path": "images/fig.png",
                        "img_caption": ["caption"],
                        "page_idx": 0,
                    }
                ]
            ),
            encoding="utf-8",
        )

        content, markdown = MineruOnlineParser._read_any_output_files(
            tmp_path / "result", "paper"
        )

        assert markdown == "# Paper"
        assert content[0]["image_caption"] == ["caption"]
        assert "img_footnote" not in content[0]
        assert content[0]["img_path"] == str((image_dir / "fig.png").resolve())


class TestMineruSelfHostParser:
    def test_get_parser(self):
        parser = get_parser("mineru_selfhost")
        assert isinstance(parser, MineruSelfHostParser)

    def test_in_supported_and_list(self):
        assert "mineru_selfhost" in get_supported_parsers()
        assert list_parsers()["mineru_selfhost"] == "MineruSelfHostParser"

    def test_base_url_from_env(self, monkeypatch):
        monkeypatch.setenv("MINERU_SELFHOST_BASE_URL", "http://svc:9000/")
        monkeypatch.setenv("MINERU_SELFHOST_BACKEND", "hybrid-engine")
        parser = MineruSelfHostParser()
        assert parser.base_url == "http://svc:9000"  # 尾部斜杠被去除
        assert parser.backend == "hybrid-engine"

    def test_ascii_safe_filename(self):
        f = MineruSelfHostParser._ascii_safe_filename
        assert f("resume.pdf") == "resume.pdf"
        # 全中文 stem -> 兜底 upload，保留扩展名
        assert f("张帅.pdf") == "upload.pdf"
        # 混合 -> 非法字符替换为 _
        assert f("a b#c.PDF") == "a_b_c.PDF"
        # 无扩展名且全非法 -> upload
        assert f("中文") == "upload"

    def test_build_content_list_from_json_string(self, monkeypatch, tmp_path):
        """content_list 为 JSON 字符串时正确解析 + 别名归一化 + 无图清空路径。"""
        monkeypatch.delenv("MINERU_SELFHOST_RETURN_IMAGES", raising=False)
        parser = MineruSelfHostParser()
        result_item = {
            "md_content": "# T",
            "content_list": json.dumps(
                [
                    {"type": "text", "text": "hello", "page_idx": 0},
                    {
                        "type": "image",
                        "img_path": "images/fig.png",
                        "img_caption": ["cap"],
                        "page_idx": 1,
                    },
                ]
            ),
        }
        content = parser._build_content_list(result_item, tmp_path)
        assert content[0]["text"] == "hello"
        # 别名双向补齐
        assert content[1]["image_caption"] == ["cap"]
        # return_images=false：图片本地路径清空，下游降级
        assert content[1]["img_path"] == ""

    def test_build_content_list_accepts_native_list(self, tmp_path):
        parser = MineruSelfHostParser()
        result_item = {"content_list": [{"type": "text", "text": "x", "page_idx": 0}]}
        content = parser._build_content_list(result_item, tmp_path)
        assert content == [{"type": "text", "text": "x", "page_idx": 0}]

    def test_fetch_result_item_prefers_stem_then_first(self, monkeypatch):
        parser = MineruSelfHostParser()
        # 精确命中 stem
        monkeypatch.setattr(
            parser, "_get_json", lambda *a, **k: {"results": {"paper": {"content_list": "[]"}, "other": {}}}
        )
        assert parser._fetch_result_item("t", "paper") == {"content_list": "[]"}
        # stem 不在 -> 取首条兜底（单文件场景）
        monkeypatch.setattr(
            parser, "_get_json", lambda *a, **k: {"results": {"onlyone": {"k": 1}}}
        )
        assert parser._fetch_result_item("t", "missing") == {"k": 1}


class TestCliIntegration:
    def test_cli_accepts_custom_parser_name(self, monkeypatch, tmp_path):
        """Ensure CLI argument parsing does not reject custom parser names."""
        import sys
        from raganything import parser as parser_module

        class DummyCliParser(Parser):
            def check_installation(self) -> bool:
                return True

            def parse_document(
                self, file_path, output_dir="./output", method="auto", **kwargs
            ):
                # Do not touch the filesystem; just return a dummy result.
                return [{"type": "text", "text": "ok", "page_idx": 0}]

        def fake_get_parser(name: str) -> Parser:
            assert name == "custom-cli"
            return DummyCliParser()

        monkeypatch.setattr(parser_module, "get_parser", fake_get_parser)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "raganything-parser",
                str(tmp_path / "dummy.pdf"),
                "--parser",
                "custom-cli",
            ],
        )

        # If argparse still enforced choices, this would raise SystemExit
        # before our fake_get_parser is even called.
        exit_code = parser_module.main()
        assert exit_code == 0
