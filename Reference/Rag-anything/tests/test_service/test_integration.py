"""Integration tests for the RAGAnything Service API.

Tests the full HTTP layer through the FastAPI TestClient, with a
mocked RAGAnything backend via a stub TenantRAGCache.
"""

import asyncio
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from raganything.service.app import create_app
from raganything.service.task_manager import TaskManager
from raganything.service.config_resolver import ConfigResolver
from raganything.service.model_factory import ModelFactory
from raganything.service.models import TaskStatus, TERMINAL_STATES


# ── Test fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def test_file(tmp_path):
    """Create a real temp file for task creation."""
    f = tmp_path / "test_video.mp4"
    f.write_text("fake video content")
    return str(f)


@pytest.fixture
def profiles_dir(tmp_path):
    """Minimal profile directory for tests."""
    profiles = tmp_path / "config" / "profiles" / "dev"
    profiles.mkdir(parents=True)
    (profiles / "models.env").write_text(
        "qwen3-72b = ollama://http://localhost:11434/v1\n"
        "bge-m3 = ollama://?dim=1024\n"
    )
    (profiles / "secrets.env").write_text("ollama=not-needed\n")
    (profiles / "endpoints.toml").write_text(
        '[ollama]\ndefault_host = "http://localhost:11434/v1"\n'
    )
    return str(profiles.parent.parent)


@pytest.fixture
def presets_dir(tmp_path):
    """Presets directory."""
    presets = tmp_path / "config" / "presets"
    presets.mkdir(parents=True)
    return str(presets)


@pytest.fixture
def app_client(profiles_dir, presets_dir, tmp_path):
    """Create FastAPI TestClient with TaskManager + ConfigResolver."""
    base_dir = str(tmp_path / "rag_data")
    os.makedirs(base_dir, exist_ok=True)

    mf = ModelFactory(profiles_dir=os.path.join(profiles_dir, "..", "profiles"))
    # Actually, profiles_dir already points to config/ so profiles are at config/profiles/
    # Recalculate:
    config_dir = tmp_path / "config"
    mf = ModelFactory(profiles_dir=str(config_dir / "profiles"))

    tm = TaskManager(
        base_dir=base_dir,
        model_factory=mf,
        worker_count=1,
        queue_capacity=2,
    )
    cr = ConfigResolver(
        profiles_dir=str(config_dir / "profiles"),
        presets_dir=str(config_dir / "presets"),
    )
    tm.set_config_resolver(cr)

    app = create_app(tm, cr, title="Test RAGAnything Service")
    client = TestClient(app)
    return client


# ── Health ─────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_ok(self, app_client):
        resp = app_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_ready_when_accepting(self, app_client):
        resp = app_client.get("/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"

    def test_metrics(self, app_client):
        resp = app_client.get("/metrics")
        assert resp.status_code == 200
        body = resp.text
        assert "rag_tasks_total" in body
        assert "rag_queue_depth" in body
        assert "rag_slots_available" in body


# ── Tasks CRUD ─────────────────────────────────────────────────────────


class TestTasksAPI:
    def test_create_task_inline_mode(self, app_client, test_file):
        resp = app_client.post(
            "/api/v1/tasks",
            json={
                "mode": "inline",
                "file_path": test_file,
                "llm": "qwen3-72b",
                "embedding": "bge-m3",
                "modalities": ["video", "audio"],
            },
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["task_id"]
        assert data["status"] in ("created", "queued")
        assert data["tenant_id"] == "tenant_test"

    def test_create_task_preset_mode(self, app_client, test_file, presets_dir):
        # Create a preset first
        import yaml
        preset_path = os.path.join(presets_dir, "test_preset.yaml")
        os.makedirs(presets_dir, exist_ok=True)
        with open(preset_path, "w") as f:
            yaml.safe_dump({
                "description": "Test preset",
                "version": "1.0",
                "config": {
                    "llm": "qwen3-72b",
                    "embedding": "bge-m3",
                    "profile": "dev",
                    "modalities": ["video"],
                },
            }, f)

        resp = app_client.post(
            "/api/v1/tasks",
            json={
                "mode": "preset",
                "file_path": test_file,
                "preset": "test_preset",
            },
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["task_id"]

    def test_create_task_missing_tenant(self, app_client, test_file):
        resp = app_client.post(
            "/api/v1/tasks",
            json={"mode": "inline", "file_path": test_file},
        )
        assert resp.status_code == 400
        assert "tenant" in str(resp.json()["detail"]).lower()

    def test_get_task_not_found(self, app_client):
        resp = app_client.get(
            "/api/v1/tasks/nonexistent_id",
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code == 404
        assert "Task not found" in resp.json()["detail"]["message"]

    def test_get_task_found(self, app_client, test_file):
        # Create first
        create_resp = app_client.post(
            "/api/v1/tasks",
            json={"mode": "inline", "file_path": test_file},
            headers={"X-Tenant-ID": "tenant_test"},
        )
        task_id = create_resp.json()["data"]["task_id"]

        # Get it
        resp = app_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["task_id"] == task_id

    def test_list_tasks(self, app_client, test_file):
        # Create a few tasks
        for _ in range(3):
            app_client.post(
                "/api/v1/tasks",
                json={"mode": "inline", "file_path": test_file},
                headers={"X-Tenant-ID": "tenant_test"},
            )

        resp = app_client.get(
            "/api/v1/tasks",
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 3
        assert len(data["tasks"]) >= 3
        # Check pagination fields
        assert "page" in data
        assert "page_size" in data

    def test_list_tasks_filter_by_status(self, app_client, test_file):
        # Create tasks
        app_client.post(
            "/api/v1/tasks",
            json={"mode": "inline", "file_path": test_file},
            headers={"X-Tenant-ID": "tenant_test"},
        )

        resp = app_client.get(
            "/api/v1/tasks?status=created",
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code == 200

    def test_list_tasks_pagination(self, app_client, test_file):
        # Create 5 tasks
        for _ in range(5):
            app_client.post(
                "/api/v1/tasks",
                json={"mode": "inline", "file_path": test_file},
                headers={"X-Tenant-ID": "tenant_test"},
            )

        resp = app_client.get(
            "/api/v1/tasks?page=1&page_size=2",
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["tasks"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_cancel_task(self, app_client, test_file):
        # Create task
        create_resp = app_client.post(
            "/api/v1/tasks",
            json={"mode": "inline", "file_path": test_file},
            headers={"X-Tenant-ID": "tenant_test"},
        )
        task_id = create_resp.json()["data"]["task_id"]

        # Cancel it
        resp = app_client.delete(
            f"/api/v1/tasks/{task_id}",
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code in (200, 202)
        assert resp.json()["data"]["status"] == "cancelled"

    def test_cancel_nonexistent_task(self, app_client):
        resp = app_client.delete(
            "/api/v1/tasks/nonexistent",
            headers={"X-Tenant-ID": "tenant_test"},
        )
        assert resp.status_code == 404

    def test_tenant_isolation(self, app_client, test_file):
        """Tenant A should not see Tenant B's tasks."""
        # Create as tenant_a
        resp_a = app_client.post(
            "/api/v1/tasks",
            json={"mode": "inline", "file_path": test_file},
            headers={"X-Tenant-ID": "tenant_a"},
        )
        task_id = resp_a.json()["data"]["task_id"]

        # Try to get as tenant_b
        resp_b = app_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"X-Tenant-ID": "tenant_b"},
        )
        assert resp_b.status_code == 404

    def test_idempotency_key(self, app_client, test_file):
        """Same idempotency key should return existing task."""
        resp1 = app_client.post(
            "/api/v1/tasks",
            json={"mode": "inline", "file_path": test_file},
            headers={
                "X-Tenant-ID": "tenant_test",
                "Idempotency-Key": "key-001",
            },
        )
        assert resp1.status_code == 201
        task_id_1 = resp1.json()["data"]["task_id"]

        resp2 = app_client.post(
            "/api/v1/tasks",
            json={"mode": "inline", "file_path": test_file},
            headers={
                "X-Tenant-ID": "tenant_test",
                "Idempotency-Key": "key-001",
            },
        )
        # Second request returns 200 with existing task
        assert resp2.status_code == 200
        assert resp2.json()["data"]["task_id"] == task_id_1


# ── Presets API ────────────────────────────────────────────────────────


class TestPresetsAPI:
    def test_list_empty_presets(self, app_client):
        resp = app_client.get("/api/v1/presets")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_upsert_and_get_preset(self, app_client):
        resp = app_client.put(
            "/api/v1/presets/my_preset",
            json={
                "description": "My test preset",
                "version": "1.0",
                "config": {"llm": "qwen3-72b"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "my_preset"

        # Get it
        resp = app_client.get("/api/v1/presets/my_preset")
        assert resp.status_code == 200
        assert resp.json()["data"]["description"] == "My test preset"

    def test_delete_preset(self, app_client):
        # Create
        app_client.put(
            "/api/v1/presets/to_delete",
            json={"config": {}},
        )
        # Delete
        resp = app_client.delete("/api/v1/presets/to_delete")
        assert resp.status_code == 200

        # Verify gone
        resp = app_client.get("/api/v1/presets/to_delete")
        assert resp.status_code == 404

    def test_delete_nonexistent_preset(self, app_client):
        resp = app_client.delete("/api/v1/presets/nonexistent")
        assert resp.status_code == 404


# ── Chunk write-back integration tests ────────────────────────────────────

# The update_chunk action is registered on the v2 /invoke endpoint
# (atomic-rag-server-v2.py), not the v1 service app tested here.
# End-to-end tests require a live LightRAG + v2 server.
# Unit tests covering all logic are in test_chunk_repository.py (20 cases).


class TestUpdateChunkHandler:
    """Direct handler tests — bypass HTTP to validate error mapping."""

    @staticmethod
    def _get_handler():
        """Import handle_update_chunk from atomic-rag-server-v2.py (has hyphens)."""
        import importlib.util
        import sys
        mod_name = "atomic_rag_server_v2"
        if mod_name in sys.modules:
            return sys.modules[mod_name].handle_update_chunk
        spec = importlib.util.spec_from_file_location(
            mod_name,
            os.path.join(os.path.dirname(__file__), "..", "..", "atomic-rag-server-v2.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
        return mod.handle_update_chunk

    @pytest.mark.asyncio
    async def test_validate_chunk_id_required(self):
        """Handler raises 400 when chunk_id is empty."""
        from fastapi import HTTPException
        handler = self._get_handler()

        with pytest.raises(HTTPException, match="chunk_id"):
            await handler(
                {"chunk_id": "", "new_content": "test"},
                tenant_id="test_tenant",
                task_manager=None,
            )

    @pytest.mark.asyncio
    async def test_validate_content_required(self):
        """Handler raises 400 when new_content is empty."""
        from fastapi import HTTPException
        handler = self._get_handler()

        with pytest.raises(HTTPException, match="new_content"):
            await handler(
                {"chunk_id": "chunk-123", "new_content": "   "},
                tenant_id="test_tenant",
                task_manager=None,
            )

    @pytest.mark.asyncio
    async def test_routes_exception_to_404(self):
        """ChunkNotFoundError → HTTP 404."""
        from fastapi import HTTPException
        from unittest.mock import AsyncMock, MagicMock
        from raganything.service.exceptions import ChunkNotFoundError

        handler = self._get_handler()
        mock_tm = MagicMock()
        mock_tm.update_chunk = AsyncMock(side_effect=ChunkNotFoundError("chunk-404"))

        with pytest.raises(HTTPException) as exc_info:
            await handler(
                {"chunk_id": "chunk-404", "new_content": "test"},
                tenant_id="test_tenant",
                task_manager=mock_tm,
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_routes_exception_to_409(self):
        """ChunkContentConflictError → HTTP 409."""
        from fastapi import HTTPException
        from unittest.mock import AsyncMock, MagicMock
        from raganything.service.exceptions import ChunkContentConflictError

        handler = self._get_handler()
        mock_tm = MagicMock()
        mock_tm.update_chunk = AsyncMock(
            side_effect=ChunkContentConflictError("chunk-409", "collision")
        )

        with pytest.raises(HTTPException) as exc_info:
            await handler(
                {"chunk_id": "chunk-409", "new_content": "test"},
                tenant_id="test_tenant",
                task_manager=mock_tm,
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_success_returns_result_dict(self):
        """Successful update returns expected response shape."""
        from unittest.mock import AsyncMock, MagicMock
        from raganything.service.models import UpdateChunkResult

        handler = self._get_handler()
        result = UpdateChunkResult(
            old_chunk_id="chunk-old",
            new_chunk_id="chunk-new",
            doc_id="doc-1",
            tokens=10,
            content_length=40,
            updated_at="2026-07-13T00:00:00Z",
            vector_updated=True,
            affected_entities=2,
        )
        mock_tm = MagicMock()
        mock_tm.update_chunk = AsyncMock(return_value=result)

        resp = await handler(
            {"chunk_id": "chunk-old", "new_content": "updated text"},
            tenant_id="test_tenant",
            task_manager=mock_tm,
        )
        assert resp["success"] is True
        assert resp["code"] == 0
        assert resp["data"]["old_chunk_id"] == "chunk-old"
        assert resp["data"]["new_chunk_id"] == "chunk-new"
