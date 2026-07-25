"""Unit tests for ChunkRepository Protocol and LightRAGChunkRepository."""

import asyncio
import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from lightrag.constants import GRAPH_FIELD_SEP
from lightrag.utils import compute_mdhash_id


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_chunk_entry(chunk_id, content, full_doc_id, chunk_order_index=0,
                      file_path="test.pdf", page_idx=0, tokens=None):
    """Build a dict matching what LightRAG text_chunks stores."""
    t = tokens or len(content) // 4
    return {
        "content": content,
        "full_doc_id": full_doc_id,
        "chunk_order_index": chunk_order_index,
        "file_path": file_path,
        "page_idx": page_idx,
        "tokens": t,
    }


def _make_mock_lightrag(chunks_dict=None, entity_data=None,
                         relation_data=None, doc_status=None):
    """Create a mock LightRAG instance with minimal storages."""
    mock = MagicMock()
    mock.tokenizer = MagicMock()
    mock.tokenizer.encode = lambda text: [0] * (len(text) // 4)

    # text_chunks — uses _data (JsonKVStorage compat)
    _chunks = chunks_dict or {}
    tc = MagicMock()
    tc._data = _chunks
    tc.get_by_id = MagicMock(side_effect=lambda cid: _chunks.get(cid))
    tc.upsert = AsyncMock()
    tc.delete = AsyncMock()
    tc.filter_keys = AsyncMock(return_value=set())
    tc.index_done_callback = AsyncMock()
    mock.text_chunks = tc

    # chunks_vdb
    cv = MagicMock()
    cv.upsert = AsyncMock()
    cv.delete = AsyncMock()
    cv.index_done_callback = AsyncMock()
    mock.chunks_vdb = cv

    # entity_chunks — uses _data (JsonKVStorage compat)
    _entity = entity_data or {}
    ec = MagicMock()
    ec._data = _entity
    ec.upsert = AsyncMock()
    ec.index_done_callback = AsyncMock()
    mock.entity_chunks = ec

    # relation_chunks — uses _data (JsonKVStorage compat)
    _relation = relation_data or {}
    rc = MagicMock()
    rc._data = _relation
    rc.upsert = AsyncMock()
    rc.index_done_callback = AsyncMock()
    mock.relation_chunks = rc

    # doc_status
    ds = MagicMock()
    ds.get_by_id = AsyncMock(return_value=doc_status)
    ds.upsert = AsyncMock()
    ds.index_done_callback = AsyncMock()
    mock.doc_status = ds

    return mock


async def _fake_embedding_func(texts):
    """Return deterministic fake vectors: len=768, all values=0.1."""
    return [[0.1] * 768 for _ in texts]


# ── Tests ────────────────────────────────────────────────────────────────


class TestGetByDocId:
    """Tests for ChunkRepository.get_by_doc_id()."""

    @pytest.mark.asyncio
    async def test_returns_sorted_by_chunk_order_index(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        chunks = {
            "chunk-a": _make_chunk_entry("chunk-a", "content a", "doc-1", chunk_order_index=2),
            "chunk-b": _make_chunk_entry("chunk-b", "content b", "doc-1", chunk_order_index=0),
            "chunk-c": _make_chunk_entry("chunk-c", "content c", "doc-1", chunk_order_index=1),
            "chunk-d": _make_chunk_entry("chunk-d", "content d", "doc-2", chunk_order_index=0),
        }
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.get_by_doc_id("doc-1")
        order_indices = [c["chunk_order_index"] for c in result]
        assert order_indices == [0, 1, 2]
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_doc(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        chunks = {"chunk-a": _make_chunk_entry("chunk-a", "x", "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.get_by_doc_id("doc-nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_storage(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        mock_lr = _make_mock_lightrag(chunks_dict={})
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.get_by_doc_id("doc-1")
        assert result == []


class TestGetChunk:
    """Tests for ChunkRepository.get_chunk()."""

    @pytest.mark.asyncio
    async def test_returns_chunk_with_id_key(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        chunks = {"chunk-x": _make_chunk_entry("chunk-x", "hello", "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.get_chunk("chunk-x")
        assert result is not None
        assert result["chunk_id"] == "chunk-x"
        assert result["content"] == "hello"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_chunk(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        mock_lr = _make_mock_lightrag(chunks_dict={})
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.get_chunk("chunk-nonexistent")
        assert result is None


class TestUpdateChunk:
    """Tests for ChunkRepository.update_chunk()."""

    @pytest.mark.asyncio
    async def test_content_changed_new_id_differs(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "original text content"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.update_chunk(
            old_id, "modified text content", _fake_embedding_func,
        )
        assert result.new_chunk_id != result.old_chunk_id
        assert result.doc_id == "doc-1"
        assert result.vector_updated is True

    @pytest.mark.asyncio
    async def test_preserves_metadata(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "some text"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {
            old_id: _make_chunk_entry(
                old_id, old_content, "doc-5", chunk_order_index=3,
                file_path="report.pdf", page_idx=2,
            )
        }
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.update_chunk(old_id, "updated text", _fake_embedding_func)

        # Verify the upserted chunk preserved metadata
        call_args = mock_lr.text_chunks.upsert.call_args[0][0]
        new_chunk = list(call_args.values())[0]
        assert new_chunk["full_doc_id"] == "doc-5"
        assert new_chunk["chunk_order_index"] == 3
        assert new_chunk["file_path"] == "report.pdf"
        assert new_chunk["page_idx"] == 2
        assert new_chunk["content"] == "updated text"
        assert new_chunk["tokens"] == len("updated text") // 4

    @pytest.mark.asyncio
    async def test_tokens_recalculated(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "short"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1", tokens=2)}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        new_content = "this is a much longer text that should produce more tokens"
        result = await repo.update_chunk(old_id, new_content, _fake_embedding_func)

        expected_tokens = len(new_content) // 4
        assert result.tokens == expected_tokens

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_chunk(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository
        from raganything.service.exceptions import ChunkNotFoundError

        mock_lr = _make_mock_lightrag(chunks_dict={})
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        with pytest.raises(ChunkNotFoundError):
            await repo.update_chunk("chunk-nonexistent", "new", _fake_embedding_func)

    @pytest.mark.asyncio
    async def test_unchanged_short_circuits(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        content = "same content"
        chunk_id = compute_mdhash_id(content, prefix="chunk-")
        chunks = {chunk_id: _make_chunk_entry(chunk_id, content, "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.update_chunk(chunk_id, content, _fake_embedding_func)

        assert result.old_chunk_id == result.new_chunk_id
        # No delete called (short-circuit)
        mock_lr.text_chunks.delete.assert_not_called()
        mock_lr.chunks_vdb.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_collision_cross_doc_raises(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository
        from raganything.service.exceptions import ChunkContentConflictError

        old_content = "doc1 original"
        other_content = "doc2 content that matches target"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        other_id = compute_mdhash_id(other_content, prefix="chunk-")

        chunks = {
            old_id: _make_chunk_entry(old_id, old_content, "doc-1"),
            other_id: _make_chunk_entry(other_id, other_content, "doc-2"),
        }
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        # Modify doc-1's chunk to have the same content as doc-2's chunk
        with pytest.raises(ChunkContentConflictError):
            await repo.update_chunk(old_id, other_content, _fake_embedding_func)

    @pytest.mark.asyncio
    async def test_same_content_same_doc_allowed(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        # Two chunks in the SAME doc happen to have identical content (edge case)
        content_a = "chunk a content"
        content_b = "duplicate content in same doc"
        id_a = compute_mdhash_id(content_a, prefix="chunk-")
        id_b = compute_mdhash_id(content_b, prefix="chunk-")

        chunks = {
            id_a: _make_chunk_entry(id_a, content_a, "doc-1", chunk_order_index=0),
            id_b: _make_chunk_entry(id_b, content_b, "doc-1", chunk_order_index=1),
        }
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        # Change chunk a to same content as chunk b (same doc → allowed)
        result = await repo.update_chunk(id_a, content_b, _fake_embedding_func)
        # Should succeed — new_chunk_id == id_b, but same doc, so it's fine
        assert result.new_chunk_id == id_b

    @pytest.mark.asyncio
    async def test_exceeds_token_limit_raises(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository, MAX_CHUNK_TOKENS
        from raganything.service.exceptions import ChunkContentTooLargeError

        old_content = "short"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}

        # tokenizer mock: return too many tokens
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        mock_lr.tokenizer.encode = lambda text: [0] * (MAX_CHUNK_TOKENS + 1)

        repo = LightRAGChunkRepository(lightrag=mock_lr)

        with pytest.raises(ChunkContentTooLargeError):
            await repo.update_chunk(old_id, "x" * 100000, _fake_embedding_func)

    @pytest.mark.asyncio
    async def test_optimistic_lock_hash_mismatch_raises(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository
        from raganything.service.exceptions import ContentHashMismatchError

        old_content = "current content"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        wrong_hash = "00000000000000000000000000000000"
        with pytest.raises(ContentHashMismatchError):
            await repo.update_chunk(
                old_id, "new stuff", _fake_embedding_func,
                expected_content_hash=wrong_hash,
            )

    @pytest.mark.asyncio
    async def test_optimistic_lock_correct_hash_succeeds(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "current content"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        correct_hash = compute_mdhash_id(old_content, prefix="")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.update_chunk(
            old_id, "new content", _fake_embedding_func,
            expected_content_hash=correct_hash,
        )
        assert result.vector_updated is True


class TestUpdateChunkVdbFailure:
    """Tests for vdb failure rollback behaviour."""

    @pytest.mark.asyncio
    async def test_vdb_failure_rolls_back_text_chunks(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "original text"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        # Make chunks_vdb.upsert fail
        mock_lr.chunks_vdb.upsert = AsyncMock(side_effect=RuntimeError("vdb down"))

        repo = LightRAGChunkRepository(lightrag=mock_lr)
        result = await repo.update_chunk(old_id, "new text", _fake_embedding_func)

        assert result.vector_updated is False
        # Old chunk NOT deleted from text_chunks
        text_delete_calls = [
            c for c in mock_lr.text_chunks.delete.call_args_list
        ]
        deleted_ids = []
        for args, _kwargs in text_delete_calls:
            deleted_ids.extend(args[0])
        # Only new_chunk_id is deleted (rollback), old_id is preserved
        assert old_id not in deleted_ids


class TestRewriteChunkReferences:
    """Tests for _rewrite_chunk_references with GRAPH_FIELD_SEP handling."""

    @pytest.mark.asyncio
    async def test_rewrites_entity_source_id_sep_separated(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "test content"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")

        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}
        # entity source_id uses <SEP> delimiter
        entity_data = {
            "entity-1": {
                "source_id": GRAPH_FIELD_SEP.join([old_id, "chunk-other"]),
            },
            "entity-2": {
                "source_id": old_id,  # single chunk ID, no separator
            },
            "entity-3": {
                "source_id": "chunk-other-only",  # unrelated
            },
        }
        doc_status = {
            "status": "PROCESSED",
            "chunks_list": [old_id, "chunk-other"],
        }
        mock_lr = _make_mock_lightrag(
            chunks_dict=chunks, entity_data=entity_data, doc_status=doc_status,
        )
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.update_chunk(old_id, "new text", _fake_embedding_func)
        new_id = result.new_chunk_id

        # Check entity_chunks upsert was called with updated source_ids
        ec_upsert_call = mock_lr.entity_chunks.upsert.call_args
        if ec_upsert_call:
            updated = ec_upsert_call[0][0]
            # entity-1: old_id was part of a multi-chunk source_id
            if "entity-1" in updated:
                new_source = updated["entity-1"]["source_id"]
                assert "chunk-other" in new_source  # other chunk preserved
                assert new_id in new_source          # old_id replaced
                assert old_id not in new_source

            # entity-2: old_id was the sole source_id
            if "entity-2" in updated:
                assert updated["entity-2"]["source_id"] == new_id

        assert result.affected_entities >= 1

    @pytest.mark.asyncio
    async def test_rewrites_doc_status_chunks_list(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "doc content"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}
        doc_status = {"status": "PROCESSED", "chunks_list": [old_id, "chunk-other"]}
        mock_lr = _make_mock_lightrag(
            chunks_dict=chunks, doc_status=doc_status,
        )
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        result = await repo.update_chunk(old_id, "updated content", _fake_embedding_func)

        # Check doc_status was upserted with replaced chunk_id
        ds_upsert_call = mock_lr.doc_status.upsert.call_args
        if ds_upsert_call:
            updated_ds = ds_upsert_call[0][0].get("doc-1", {})
            new_list = updated_ds.get("chunks_list", [])
            assert result.new_chunk_id in new_list
            assert old_id not in new_list
            assert "chunk-other" in new_list  # unchanged

    @pytest.mark.asyncio
    async def test_does_not_rewrite_full_docs(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "content"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        # Add a full_docs mock to verify it's never touched
        mock_lr.full_docs = MagicMock()
        mock_lr.full_docs.upsert = AsyncMock()
        mock_lr.full_docs.get_by_id = AsyncMock()

        repo = LightRAGChunkRepository(lightrag=mock_lr)
        await repo.update_chunk(old_id, "new content", _fake_embedding_func)

        # full_docs must remain untouched
        mock_lr.full_docs.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_index_done_callbacks_invoked(self):
        from raganything.service.chunk_repository import LightRAGChunkRepository

        old_content = "test"
        old_id = compute_mdhash_id(old_content, prefix="chunk-")
        chunks = {old_id: _make_chunk_entry(old_id, old_content, "doc-1")}
        mock_lr = _make_mock_lightrag(chunks_dict=chunks)
        repo = LightRAGChunkRepository(lightrag=mock_lr)

        await repo.update_chunk(old_id, "new content", _fake_embedding_func)

        # text_chunks callbacks: upsert + delete each trigger index_done_callback
        assert mock_lr.text_chunks.index_done_callback.call_count >= 2
        # chunks_vdb callbacks: upsert + delete
        assert mock_lr.chunks_vdb.index_done_callback.call_count >= 2
