"""Chunk storage abstraction for read/write operations.

Defines ChunkRepository Protocol and LightRAGChunkRepository
as the primary (and currently only) implementation.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from lightrag.constants import GRAPH_FIELD_SEP
from lightrag.utils import compute_mdhash_id

from .exceptions import (
    ChunkContentConflictError,
    ChunkContentTooLargeError,
    ChunkNotFoundError,
    ContentHashMismatchError,
)
from .models import UpdateChunkResult

MAX_CHUNK_TOKENS = 8000  # aligned with embedding model token limit


@runtime_checkable
class ChunkRepository(Protocol):
    """Storage-agnostic interface for chunk read/write operations.

    Decouples chunk modification logic from LightRAG internals,
    enabling future backend swaps (Milvus, Qdrant, etc.).
    """

    async def get_by_doc_id(self, doc_id: str) -> list[dict]:
        """Return all chunks for a doc_id, sorted by chunk_order_index."""
        ...

    async def get_chunk(self, chunk_id: str) -> dict | None:
        """Return a single chunk by chunk_id, or None."""
        ...

    async def update_chunk(
        self,
        chunk_id: str,
        new_content: str,
        embedding_func,
        *,
        expected_content_hash: str | None = None,
    ) -> UpdateChunkResult:
        """
        Modify a chunk's content and re-vectorize.

        Steps: validate → hash check → short-circuit → collision check →
               build new chunk → embed → upsert-new-then-delete-old →
               rewrite references.
        """
        ...


@dataclass
class LightRAGChunkRepository:
    """ChunkRepository implementation backed by LightRAG internal storages.

    Uses per-doc_id asyncio.Lock for concurrency safety.
    Write order: upsert new → delete old (rollback on vdb failure).
    """

    lightrag: Any
    _locks: dict[str, asyncio.Lock] = field(default_factory=dict)
    _locks_guard: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def _get_lock(self, doc_id: str) -> asyncio.Lock:
        """Acquire or create a per-doc_id lock.

        Document-level granularity prevents concurrent modifications
        from overwriting each other's doc_status.chunks_list updates.
        """
        async with self._locks_guard:
            if doc_id not in self._locks:
                self._locks[doc_id] = asyncio.Lock()
            return self._locks[doc_id]

    # ── Read methods ────────────────────────────────────────────────

    async def get_by_doc_id(self, doc_id: str) -> list[dict]:
        """Scan all text_chunks filtering by full_doc_id.

        Uses _data directly because JsonKVStorage does not expose get_all().
        """
        all_chunks = getattr(self.lightrag.text_chunks, "_data", {}) or {}
        doc_chunks = [
            {**v, "chunk_id": k}
            for k, v in all_chunks.items()
            if isinstance(v, dict) and v.get("full_doc_id") == doc_id
        ]
        doc_chunks.sort(key=lambda c: c.get("chunk_order_index", 0))
        return doc_chunks

    async def get_chunk(self, chunk_id: str) -> dict | None:
        """Look up a single chunk by ID.

        Uses _data directly because JsonKVStorage does not expose get_by_id().
        """
        all_chunks = getattr(self.lightrag.text_chunks, "_data", {}) or {}
        chunk = all_chunks.get(chunk_id)
        if chunk:
            chunk = dict(chunk)
            chunk["chunk_id"] = chunk_id
        return chunk

    # ── Write method ────────────────────────────────────────────────

    async def update_chunk(
        self,
        chunk_id: str,
        new_content: str,
        embedding_func,
        *,
        expected_content_hash: str | None = None,
    ) -> UpdateChunkResult:
        """Public entry point — acquires per-doc_id lock."""
        old = await self.get_chunk(chunk_id)
        if not old:
            raise ChunkNotFoundError(chunk_id)
        doc_id = old["full_doc_id"]

        async with await self._get_lock(doc_id):
            return await self._update_chunk_locked(
                chunk_id, old, new_content, embedding_func,
                expected_content_hash=expected_content_hash,
            )

    async def _update_chunk_locked(
        self,
        chunk_id: str,
        old: dict,
        new_content: str,
        embedding_func,
        *,
        expected_content_hash: str | None = None,
    ) -> UpdateChunkResult:
        """Core update logic — runs under per-doc_id lock."""

        # 0. Token length check
        tokens = len(self.lightrag.tokenizer.encode(new_content))
        if tokens > MAX_CHUNK_TOKENS:
            raise ChunkContentTooLargeError(chunk_id, tokens, MAX_CHUNK_TOKENS)

        # 1. Optimistic lock check
        if expected_content_hash is not None:
            old_hash = compute_mdhash_id(old["content"], prefix="")
            if old_hash != expected_content_hash:
                raise ContentHashMismatchError(chunk_id)

        # 2. Short-circuit: content unchanged
        new_chunk_id = compute_mdhash_id(new_content, prefix="chunk-")
        if new_chunk_id == chunk_id:
            return UpdateChunkResult(
                old_chunk_id=chunk_id, new_chunk_id=chunk_id,
                doc_id=old["full_doc_id"], tokens=old["tokens"],
                content_length=len(new_content),
                updated_at=datetime.now(timezone.utc).isoformat(),
                vector_updated=True,
            )

        # 3. Collision check
        existing = await self.get_chunk(new_chunk_id)
        if existing and existing.get("full_doc_id") != old["full_doc_id"]:
            raise ChunkContentConflictError(
                new_chunk_id,
                f"content collides with chunk in doc {existing['full_doc_id']}",
            )

        # 4. Build new chunk (preserve all metadata)
        new_chunk = {**old, "content": new_content, "tokens": tokens}
        new_chunk.pop("chunk_id", None)

        # 5. Embed
        new_vector = await embedding_func([new_content])
        vdb_data = {new_chunk_id: {**new_chunk, "vector": new_vector[0]}}

        # ── 6. Core write: upsert new → delete old ──
        # 6a. Write new data first
        await self.lightrag.text_chunks.upsert({new_chunk_id: new_chunk})
        await self.lightrag.text_chunks.index_done_callback()

        partial_failure = None
        vector_updated = True
        try:
            await self.lightrag.chunks_vdb.upsert(vdb_data)
            await self.lightrag.chunks_vdb.index_done_callback()
        except Exception as e:
            partial_failure = str(e)
            vector_updated = False

        # 6b. Delete old data — ONLY when ALL stores succeeded
        if vector_updated:
            await self.lightrag.text_chunks.delete([chunk_id])
            await self.lightrag.text_chunks.index_done_callback()
            await self.lightrag.chunks_vdb.delete([chunk_id])
            await self.lightrag.chunks_vdb.index_done_callback()
        else:
            # vdb failed → rollback new text_chunks, keep old data intact
            await self.lightrag.text_chunks.delete([new_chunk_id])
            await self.lightrag.text_chunks.index_done_callback()

        # 7. Rewrite id references (only on full success)
        affected = 0
        if vector_updated:
            affected = await self._rewrite_chunk_references(
                old_chunk_id=chunk_id,
                new_chunk_id=new_chunk_id,
                doc_id=old["full_doc_id"],
            )

        return UpdateChunkResult(
            old_chunk_id=chunk_id,
            new_chunk_id=new_chunk_id,
            doc_id=old["full_doc_id"],
            tokens=tokens,
            content_length=len(new_content),
            updated_at=datetime.now(timezone.utc).isoformat(),
            vector_updated=vector_updated,
            partial_failure=partial_failure,
            affected_entities=affected,
        )

    # ── Reference rewriting ─────────────────────────────────────────

    async def _rewrite_chunk_references(
        self, old_chunk_id: str, new_chunk_id: str, doc_id: str
    ) -> int:
        """Rewrites all storage records that reference old_chunk_id.

        LightRAG stores source_id as a GRAPH_FIELD_SEP ("<SEP>") delimited
        string (e.g. "chunk-1<SEP>chunk-2<SEP>chunk-3") because entities
        are extracted from multiple chunks.  We must split→replace→join
        rather than doing a simple == comparison.
        """
        count = 0

        # entity_chunks
        entity_data = getattr(self.lightrag.entity_chunks, "_data", {}) or {}
        updated_entities = {}
        for ek, ev in entity_data.items():
            if not isinstance(ev, dict) or not ev.get("source_id"):
                continue
            source_ids = ev["source_id"].split(GRAPH_FIELD_SEP)
            if old_chunk_id in source_ids:
                new_ids = [
                    new_chunk_id if cid == old_chunk_id else cid
                    for cid in source_ids
                ]
                ev["source_id"] = GRAPH_FIELD_SEP.join(new_ids)
                updated_entities[ek] = ev
                count += 1
        if updated_entities:
            await self.lightrag.entity_chunks.upsert(updated_entities)
            await self.lightrag.entity_chunks.index_done_callback()

        # relation_chunks
        relation_data = getattr(self.lightrag.relation_chunks, "_data", {}) or {}
        updated_relations = {}
        for rk, rv in relation_data.items():
            if not isinstance(rv, dict) or not rv.get("source_id"):
                continue
            source_ids = rv["source_id"].split(GRAPH_FIELD_SEP)
            if old_chunk_id in source_ids:
                new_ids = [
                    new_chunk_id if cid == old_chunk_id else cid
                    for cid in source_ids
                ]
                rv["source_id"] = GRAPH_FIELD_SEP.join(new_ids)
                updated_relations[rk] = rv
                count += 1
        if updated_relations:
            await self.lightrag.relation_chunks.upsert(updated_relations)
            await self.lightrag.relation_chunks.index_done_callback()

        # doc_status.chunks_list (plain list, no delimiter)
        doc_status = await self.lightrag.doc_status.get_by_id(doc_id)
        if doc_status and isinstance(doc_status, dict):
            chunks_list = doc_status.get("chunks_list", [])
            if old_chunk_id in chunks_list:
                new_list = [
                    new_chunk_id if cid == old_chunk_id else cid
                    for cid in chunks_list
                ]
                doc_status["chunks_list"] = new_list
                await self.lightrag.doc_status.upsert({doc_id: doc_status})
                await self.lightrag.doc_status.index_done_callback()
                count += 1

        return count
