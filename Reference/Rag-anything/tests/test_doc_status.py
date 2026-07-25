"""Tests for DocStatusManager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from raganything.base import DocStatus


@pytest.fixture
def mock_lightrag():
    lr = MagicMock()
    lr.doc_status = AsyncMock()
    lr.doc_status.get_by_id = AsyncMock(return_value=None)
    lr.doc_status.upsert = AsyncMock()
    lr.doc_status.index_done_callback = AsyncMock()
    return lr


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.use_full_path = False
    return cfg


@pytest.fixture
def manager(mock_lightrag, mock_config):
    from raganything.doc_status import DocStatusManager

    return DocStatusManager(mock_lightrag, mock_config)


class TestEnsureRecord:
    @pytest.mark.asyncio
    async def test_creates_new_when_not_found(self, manager, mock_lightrag):
        await manager.ensure_record("doc-1", "/path/file.pdf")
        assert mock_lightrag.doc_status.upsert.called
        call_key = list(mock_lightrag.doc_status.upsert.call_args[0][0].keys())[0]
        assert call_key == "doc-1"

    @pytest.mark.asyncio
    async def test_returns_existing(self, manager, mock_lightrag):
        existing = {"doc_id": "doc-1", "status": "ready", "file_path": "file.pdf"}
        mock_lightrag.doc_status.get_by_id = AsyncMock(return_value=existing)
        result = await manager.ensure_record("doc-1", "/path/file.pdf")
        assert result == existing
        # upsert should not be called
        mock_lightrag.doc_status.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_includes_scheme_name_when_given(self, manager, mock_lightrag):
        await manager.ensure_record(
            "doc-1", "/path/file.pdf", scheme_name="test-scheme"
        )
        payload = mock_lightrag.doc_status.upsert.call_args[0][0]["doc-1"]
        assert payload["scheme_name"] == "test-scheme"

    @pytest.mark.asyncio
    async def test_default_status(self, manager, mock_lightrag):
        await manager.ensure_record("doc-1", "/path/file.pdf")
        payload = mock_lightrag.doc_status.upsert.call_args[0][0]["doc-1"]
        assert payload["status"] == DocStatus.READY

    @pytest.mark.asyncio
    async def test_custom_status(self, manager, mock_lightrag):
        await manager.ensure_record(
            "doc-1", "/path/file.pdf", status=DocStatus.PROCESSING
        )
        payload = mock_lightrag.doc_status.upsert.call_args[0][0]["doc-1"]
        assert payload["status"] == DocStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_creates_timestamp(self, manager, mock_lightrag):
        await manager.ensure_record("doc-1", "/path/file.pdf")
        payload = mock_lightrag.doc_status.upsert.call_args[0][0]["doc-1"]
        assert "created_at" in payload
        assert "updated_at" in payload
        assert payload["created_at"] == payload["updated_at"]


class TestUpsert:
    @pytest.mark.asyncio
    async def test_merges_updates(self, manager, mock_lightrag):
        mock_lightrag.doc_status.get_by_id = AsyncMock(
            return_value={
                "status": "ready",
                "content": "original",
                "file_path": "file.pdf",
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
            }
        )
        result = await manager.upsert("doc-1", "/path/file.pdf", content="updated")
        assert result["content"] == "updated"
        assert result["status"] == "ready"  # unchanged

    @pytest.mark.asyncio
    async def test_updates_timestamp(self, manager, mock_lightrag):
        mock_lightrag.doc_status.get_by_id = AsyncMock(
            return_value={
                "status": "ready",
                "file_path": "file.pdf",
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
            }
        )
        from raganything.doc_status import current_doc_status_timestamp

        result = await manager.upsert("doc-1", "/path/file.pdf")
        assert result["updated_at"] == current_doc_status_timestamp()

    @pytest.mark.asyncio
    async def test_ensures_record_if_missing(self, manager, mock_lightrag):
        mock_lightrag.doc_status.get_by_id = AsyncMock(return_value=None)
        result = await manager.upsert("doc-1", "/path/file.pdf", content="new")
        assert result["content"] == "new"
        assert mock_lightrag.doc_status.upsert.called

    @pytest.mark.asyncio
    async def test_index_callback_called(self, manager, mock_lightrag):
        await manager.upsert("doc-1", "/path/file.pdf")
        assert mock_lightrag.doc_status.index_done_callback.called


class TestCurrentDocStatusTimestamp:
    def test_stable_format(self):
        from raganything.doc_status import current_doc_status_timestamp

        ts = current_doc_status_timestamp()
        assert ts.endswith("+00:00")
        assert "T" in ts


class TestGetFileReference:
    def test_use_full_path(self, mock_lightrag, mock_config):
        mock_config.use_full_path = True
        from raganything.doc_status import DocStatusManager

        mgr = DocStatusManager(mock_lightrag, mock_config)
        assert mgr._get_file_reference("/a/b/file.pdf") == "/a/b/file.pdf"

    def test_basename(self, mock_lightrag, mock_config):
        mock_config.use_full_path = False
        from raganything.doc_status import DocStatusManager

        mgr = DocStatusManager(mock_lightrag, mock_config)
        assert mgr._get_file_reference("/a/b/file.pdf") == "file.pdf"
