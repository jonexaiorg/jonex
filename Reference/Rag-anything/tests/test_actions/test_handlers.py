"""Tests for action handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from atomic_rag.actions import ActionRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    ActionRegistry.clear()
    yield


@pytest.fixture
def mock_task_manager():
    tm = MagicMock()
    tm.create_task = MagicMock(return_value="task-abc-123")
    tm.lightrag = MagicMock()
    tm.lightrag.query = AsyncMock(return_value="test answer")
    tm.lightrag.delete_doc = AsyncMock(return_value=True)
    tm.get_status = MagicMock(return_value={
        "task_id": "task-xyz", "status": "completed", "progress": 1.0,
        "error": None, "doc_ids": ["doc-1"],
    })
    return tm


@pytest.mark.asyncio
async def test_insert_handler_success(mock_task_manager):
    from atomic_rag.actions.insert import handle_insert  # noqa: F811

    params = {"file_path": "/tmp/doc.pdf", "tenant_id": "tenant-1"}
    result = await handle_insert(params, "tenant-1", task_manager=mock_task_manager)
    assert result["success"]
    assert result["data"]["task_id"] == "task-abc-123"

    mock_task_manager.create_task.assert_called_once_with(
        file_path="/tmp/doc.pdf", tenant_id="tenant-1",
        output_dir=None, mps_video_url=None,
    )


@pytest.mark.asyncio
async def test_insert_handler_missing_file_and_url(mock_task_manager):
    from atomic_rag.actions.insert import handle_insert  # noqa: F811

    with pytest.raises(HTTPException) as exc:
        await handle_insert({"file_path": "", "mps_video_url": ""}, "tenant-1", task_manager=mock_task_manager)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_insert_handler_mps_video_url(mock_task_manager):
    from atomic_rag.actions.insert import handle_insert  # noqa: F811

    params = {"mps_video_url": "https://cos.example.com/video.mp4", "tenant_id": "tenant-1"}
    result = await handle_insert(params, "tenant-1", task_manager=mock_task_manager)
    assert result["success"]
    mock_task_manager.create_task.assert_called_once_with(
        file_path=None, tenant_id="tenant-1",
        output_dir=None, mps_video_url="https://cos.example.com/video.mp4",
    )


@pytest.mark.asyncio
async def test_query_handler_success(mock_task_manager):
    from atomic_rag.actions.query import handle_query  # noqa: F811

    params = {"query": "test query", "mode": "hybrid", "top_k": 5}
    result = await handle_query(params, "tenant-1", task_manager=mock_task_manager)
    assert result["success"]
    assert result["data"]["answer"] == "test answer"
    mock_task_manager.lightrag.query.assert_awaited_once_with(
        query="test query", workspace="tenant_tenant-1",
        mode="hybrid", top_k=5,
    )


@pytest.mark.asyncio
async def test_query_handler_empty_query(mock_task_manager):
    from atomic_rag.actions.query import handle_query  # noqa: F811

    with pytest.raises(HTTPException) as exc:
        await handle_query({"query": ""}, "tenant-1", task_manager=mock_task_manager)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_handler_success(mock_task_manager):
    from atomic_rag.actions.delete import handle_delete  # noqa: F811

    result = await handle_delete({"doc_id": "doc-1"}, "tenant-1", task_manager=mock_task_manager)
    assert result["success"]
    assert result["data"]["success"] is True
    mock_task_manager.lightrag.delete_doc.assert_awaited_once_with(doc_id="doc-1")


@pytest.mark.asyncio
async def test_delete_handler_empty_doc_id(mock_task_manager):
    from atomic_rag.actions.delete import handle_delete  # noqa: F811

    with pytest.raises(HTTPException) as exc:
        await handle_delete({"doc_id": ""}, "tenant-1", task_manager=mock_task_manager)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_task_status_handler_success(mock_task_manager):
    from atomic_rag.actions.status import handle_get_task_status  # noqa: F811

    result = await handle_get_task_status(
        {"task_id": "task-xyz"}, "tenant-1", task_manager=mock_task_manager,
    )
    assert result["success"]
    assert result["data"]["lightrag_doc_ids"] == ["doc-1"]
    # Ensure doc_ids was renamed to lightrag_doc_ids
    assert "doc_ids" not in result["data"]


@pytest.mark.asyncio
async def test_get_task_status_handler_empty_task_id(mock_task_manager):
    from atomic_rag.actions.status import handle_get_task_status  # noqa: F811

    with pytest.raises(HTTPException) as exc:
        await handle_get_task_status({"task_id": ""}, "tenant-1", task_manager=mock_task_manager)
    assert exc.value.status_code == 400


