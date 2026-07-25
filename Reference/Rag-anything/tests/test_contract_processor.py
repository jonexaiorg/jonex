"""Contract tests ensuring RAGAnything public API stays compatible."""
import asyncio
import inspect

from raganything.base import DocStatus
from raganything.raganything import RAGAnything


class TestPublicAPISignatures:
    """Verify method signatures haven't changed."""

    def test_process_document_complete_is_async(self):
        meth = getattr(RAGAnything, "process_document_complete", None)
        assert meth is not None, "process_document_complete missing"
        assert asyncio.iscoroutinefunction(meth)

    def test_check_parser_installation_exists(self):
        assert hasattr(RAGAnything, "check_parser_installation")
        meth = getattr(RAGAnything, "check_parser_installation")
        assert callable(meth)

    def test_process_document_complete_params(self):
        sig = inspect.signature(RAGAnything.process_document_complete)
        params = list(sig.parameters.keys())
        assert "file_path" in params
        assert any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )

    def test_aquery_exists(self):
        assert hasattr(RAGAnything, "aquery")
        meth = getattr(RAGAnything, "aquery")
        assert asyncio.iscoroutinefunction(meth)

    def test_process_folder_complete_exists(self):
        assert hasattr(RAGAnything, "process_folder_complete")
        meth = getattr(RAGAnything, "process_folder_complete")
        assert asyncio.iscoroutinefunction(meth)


class TestDocStatusStateMachine:
    """Verify doc_status constants are unchanged."""

    def test_status_constants_unchanged(self):
        assert DocStatus.READY == "ready"
        assert DocStatus.HANDLING == "handling"
        assert DocStatus.PROCESSED == "processed"
        assert DocStatus.FAILED == "failed"


class TestCacheBehaviorContract:
    """Verify cache key determinism."""

    def test_deterministic_cache_key(self, tmp_path):
        from unittest.mock import MagicMock
        from raganything.cache import ParseCacheManager

        cfg = MagicMock()
        cfg.parser = "mineru"
        cfg.parse_method = "auto"

        f = tmp_path / "test.pdf"
        f.write_text("content")

        k1 = ParseCacheManager.generate_cache_key(f, parse_method=cfg.parse_method, config=cfg)
        k2 = ParseCacheManager.generate_cache_key(f, parse_method=cfg.parse_method, config=cfg)
        assert k1 == k2
