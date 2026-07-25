"""Tests for ParseCacheManager."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.parser = "mineru"
    cfg.parse_method = "auto"
    return cfg


@pytest.fixture
def mock_kv():
    kv = AsyncMock()
    kv.get_by_id = AsyncMock(return_value=None)
    kv.upsert = AsyncMock()
    kv.index_done_callback = AsyncMock()
    return kv


@pytest.fixture
def cache_manager(mock_kv, mock_config):
    from raganything.cache import ParseCacheManager

    return ParseCacheManager(mock_kv, mock_config)


class TestGenerateCacheKey:
    def test_deterministic_key(self, tmp_path, mock_config):
        from raganything.cache import ParseCacheManager

        f = tmp_path / "doc.pdf"
        f.write_text("content")

        k1 = ParseCacheManager.generate_cache_key(f, config=mock_config)
        k2 = ParseCacheManager.generate_cache_key(f, config=mock_config)
        assert k1 == k2

    def test_different_method_different_key(self, tmp_path, mock_config):
        from raganything.cache import ParseCacheManager

        f = tmp_path / "doc.pdf"
        f.write_text("content")

        k1 = ParseCacheManager.generate_cache_key(f, "auto", mock_config)
        k2 = ParseCacheManager.generate_cache_key(f, "ocr", mock_config)
        assert k1 != k2

    def test_different_file_different_key(self, tmp_path, mock_config):
        from raganything.cache import ParseCacheManager

        f1 = tmp_path / "a.pdf"
        f1.write_text("aaa")
        f2 = tmp_path / "b.pdf"
        f2.write_text("bbb")

        k1 = ParseCacheManager.generate_cache_key(f1, config=mock_config)
        k2 = ParseCacheManager.generate_cache_key(f2, config=mock_config)
        assert k1 != k2

    def test_relevant_kwargs_affect_key(self, tmp_path, mock_config):
        from raganything.cache import ParseCacheManager

        f = tmp_path / "doc.pdf"
        f.write_text("content")

        k1 = ParseCacheManager.generate_cache_key(f, "auto", mock_config, lang="en")
        k2 = ParseCacheManager.generate_cache_key(f, "auto", mock_config, lang="zh")
        assert k1 != k2


class TestGetCachedResult:
    @pytest.mark.asyncio
    async def test_miss_when_no_cache(self, cache_manager, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_text("data")
        result = await cache_manager.get_cached_result("some-key", f)
        assert result is None

    @pytest.mark.asyncio
    async def test_stale_mtime_returns_none(self, cache_manager, mock_kv, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_text("data")
        mock_kv.get_by_id = AsyncMock(
            return_value={
                "mtime": time.time() + 9999,  # future mtime
                "parse_config": {"parser": "mineru", "parse_method": "auto"},
                "content_list": [{"type": "text", "text": "hello"}],
                "doc_id": "doc-abc",
            }
        )
        result = await cache_manager.get_cached_result("key", f)
        assert result is None

    @pytest.mark.asyncio
    async def test_hit_returns_content(self, cache_manager, mock_kv, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_text("data")
        mock_kv.get_by_id = AsyncMock(
            return_value={
                "mtime": f.stat().st_mtime,
                "parse_config": {"parser": "mineru", "parse_method": "auto"},
                "content_list": [{"type": "text", "text": "hello"}],
                "doc_id": "doc-abc",
            }
        )
        result = await cache_manager.get_cached_result("key", f)
        assert result is not None
        content_list, doc_id = result
        assert content_list == [{"type": "text", "text": "hello"}]
        assert doc_id == "doc-abc"

    @pytest.mark.asyncio
    async def test_config_change_invalidates(self, cache_manager, mock_kv, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_text("data")
        mock_kv.get_by_id = AsyncMock(
            return_value={
                "mtime": f.stat().st_mtime,
                "parse_config": {"parser": "mineru", "parse_method": "ocr"},
                "content_list": [{"type": "text", "text": "hello"}],
                "doc_id": "doc-abc",
            }
        )
        result = await cache_manager.get_cached_result("key", f, parse_method="auto")
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_content_returns_none(self, cache_manager, mock_kv, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_text("data")
        mock_kv.get_by_id = AsyncMock(
            return_value={
                "mtime": f.stat().st_mtime,
                "parse_config": {"parser": "mineru", "parse_method": "auto"},
            }
        )
        result = await cache_manager.get_cached_result("key", f)
        assert result is None


class TestStoreCachedResult:
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, cache_manager, mock_kv, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_text("data")
        await cache_manager.store_cached_result(
            "my-key",
            [{"type": "text", "text": "hello"}],
            "doc-abc",
            f,
        )
        assert mock_kv.upsert.called
        call_args = mock_kv.upsert.call_args[0][0]
        assert "my-key" in call_args
        assert call_args["my-key"]["doc_id"] == "doc-abc"
        assert call_args["my-key"]["cache_version"] == "1.0"
        assert mock_kv.index_done_callback.called

    @pytest.mark.asyncio
    async def test_no_op_when_cache_none(self, tmp_path):
        from raganything.cache import ParseCacheManager

        mgr = ParseCacheManager(None, MagicMock())
        f = tmp_path / "doc.pdf"
        f.write_text("data")
        await mgr.store_cached_result("k", [], "", f)
        # Should not raise

    @pytest.mark.asyncio
    async def test_error_logged_on_failure(self, cache_manager, mock_kv, tmp_path, caplog):
        mock_kv.upsert = AsyncMock(side_effect=Exception("KV error"))
        f = tmp_path / "doc.pdf"
        f.write_text("data")
        await cache_manager.store_cached_result("k", [], "id", f)
        assert "Error writing parse cache" in caplog.text
