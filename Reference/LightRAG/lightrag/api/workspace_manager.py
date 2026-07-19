"""
[yuexi] WorkspaceRAGManager — per-workspace lazy-loaded LightRAG instance registry.

Extracted from lightrag_server.py to enable workspace-aware multi-tenancy
in query/document/graph/Ollama endpoints. When RAG_WORKSPACE_ISOLATION is
enabled, each LIGHTRAG-WORKSPACE header value maps to a separate LightRAG
instance (with isolated KV/vector/graph/doc_status storage). When disabled,
all requests share the default instance (current behaviour).

All changes tagged with # [yuexi] for easy identification when merging
upstream LightRAG updates.
"""

import os
import re
import asyncio
from collections import OrderedDict, defaultdict
from typing import Optional

from fastapi import Request
from lightrag.utils import logger


def get_workspace_from_request(request: Request) -> Optional[str]:
    """
    [yuexi] Extract workspace from HTTP request header.

    Checks the custom 'LIGHTRAG-WORKSPACE' header first. If absent and the
    WEBUI_WORKSPACE_SWITCHER debug flag is enabled, falls back to the
    'lightrag_workspace' cookie (set by the injected WebUI switcher). If both
    are absent/empty, returns None (caller falls back to the default workspace).

    NOTE: the cookie fallback is a DEBUG-ONLY surface that bypasses the
    platform tenant/permission checks (Gateway -> Sidecar). It is gated behind
    WEBUI_WORKSPACE_SWITCHER (default off) and must never be enabled in
    production with port 9621 exposed.

    Args:
        request: FastAPI Request object

    Returns:
        Sanitized workspace string, or None if no source present.
    """
    workspace = request.headers.get("LIGHTRAG-WORKSPACE", "").strip()

    # [yuexi] Debug-only cookie fallback for the WebUI workspace switcher.
    if not workspace and os.getenv(
        "WEBUI_WORKSPACE_SWITCHER", "false"
    ).strip().lower() == "true":
        workspace = (request.cookies.get("lightrag_workspace") or "").strip()

    if not workspace:
        return None

    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", workspace)
    if sanitized != workspace:
        logger.warning(
            f"Workspace header '{workspace}' contains invalid characters. "
            f"Sanitized to '{sanitized}'."
        )
        workspace = sanitized

    return workspace


class WorkspaceRAGManager:
    """
    [yuexi] Lazy-loading registry of LightRAG instances keyed by workspace.

    Responsibilities:
    - Maintains workspace(str) -> LightRAG cache (OrderedDict)
    - get(workspace): returns cached instance or creates new one via factory
    - Per-workspace asyncio.Lock to avoid double-init races on first access
    - LRU eviction when cache exceeds max_size; default instance is pinned
    - RAG_WORKSPACE_ISOLATION=false → always returns default (feature toggle)

    Usage::

        manager = WorkspaceRAGManager(build_rag, default_workspace="", max_size=64)
        await manager.init_default()
        app.state.rag_manager = manager

        # In route handlers:
        rag = await manager.get(get_workspace_from_request(request))
    """

    def __init__(
        self,
        build_rag,
        default_workspace: str = "",
        max_size: int = 64,
        isolation_enabled: bool = True,
    ):
        self._build = build_rag
        self._default_ws = default_workspace or ""
        self._cache: OrderedDict[str, object] = OrderedDict()
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._max = max(1, max_size)
        self._isolation_enabled = isolation_enabled
        self._default = None
        # [yuexi] Guards cache structure mutations (move_to_end / __setitem__ /
        # pop) to prevent _evict_if_needed from finalizing an instance that a
        # concurrent get() just promoted to MRU. Residual narrow race: a
        # long-running query on workspace X may still hold a reference after X
        # is evicted by a later eviction cycle. This requires cache to be full
        # AND X to become LRU during that query — negligible in practice.
        self._eviction_lock = asyncio.Lock()

    @property
    def isolation_enabled(self) -> bool:
        return self._isolation_enabled

    async def init_default(self):
        """[yuexi] Create and initialize the default (pinned) LightRAG instance."""
        self._default = self._build(self._default_ws)
        await self._default.initialize_storages()
        await self._default.check_and_migrate_data()

    def get_default(self):
        """[yuexi] Return the default LightRAG instance (call init_default first)."""
        return self._default

    async def get(self, workspace: Optional[str]):
        """
        [yuexi] Get or create a LightRAG instance for the given workspace.

        When isolation is disabled, always returns the default instance.
        When workspace is None/empty or equals the default workspace,
        returns the default instance.
        """
        if not self._isolation_enabled:
            return self._default

        ws = (workspace or "").strip()
        if not ws or ws == self._default_ws:
            return self._default

        async with self._locks[ws]:
            inst = self._cache.get(ws)
            if inst is not None:
                async with self._eviction_lock:
                    self._cache.move_to_end(ws)
                return inst

            inst = self._build(ws)
            await inst.initialize_storages()
            async with self._eviction_lock:
                self._cache[ws] = inst

        # [yuexi] Evict OUTSIDE the per-ws lock to avoid lock nesting deadlock.
        # Eviction needs to acquire _locks[oldest_ws] to finalize storages safely,
        # and holding self._locks[ws] while acquiring another lock is a deadlock risk.
        await self._evict_if_needed(keep=ws)
        return inst

    async def _evict_if_needed(self, keep: str):
        """[yuexi] Evict LRU instances if cache exceeds max size.

        Cache structure reads and mutations are guarded by _eviction_lock to
        prevent racing with concurrent get() move_to_end / __setitem__.
        finalize_storages() runs outside _eviction_lock to avoid blocking
        other get() calls.
        """
        while True:
            async with self._eviction_lock:
                if len(self._cache) <= self._max:
                    break
                oldest_ws = next(iter(self._cache))
                if oldest_ws == keep:
                    if len(self._cache) <= 1:
                        break
                    items = list(self._cache.items())
                    oldest_ws = items[1][0]

                inst = self._cache.pop(oldest_ws, None)

            if inst is None:
                break

            async with self._locks[oldest_ws]:
                try:
                    await inst.finalize_storages()
                except Exception as e:
                    logger.error(
                        f"Error finalizing evicted workspace '{oldest_ws}': {e}"
                    )
            # [yuexi] Clean up the lock for this workspace so _locks doesn't
            # grow without bound over the server lifetime.
            self._locks.pop(oldest_ws, None)

    async def finalize_all(self):
        """[yuexi] Finalize all cached and default instances (shutdown)."""
        for ws, inst in list(self._cache.items()):
            try:
                await inst.finalize_storages()
            except Exception as e:
                logger.error(f"Error finalizing workspace '{ws}': {e}")
        self._cache.clear()
        self._locks.clear()
        if self._default:
            try:
                await self._default.finalize_storages()
            except Exception as e:
                logger.error(f"Error finalizing default instance: {e}")
