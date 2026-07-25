"""Unit tests for TaskManager HTTP mode and TaskInfo fields."""

import json
import pytest
from unittest import mock
from datetime import datetime, timezone

from raganything.service.models import (
    TaskInfo,
    TaskStatus,
    FileType,
    ResultSummary,
    ErrorCode,
)


class TestTaskInfoHttpFields:
    """Test TaskInfo backward compatibility with new HTTP mode fields."""

    def test_new_fields_have_defaults(self):
        task = TaskInfo(tenant_id="t1", name="test.pdf", file_path="/tmp/test.pdf")
        assert task.lightrag_doc_ids == []
        assert task.pending_track_ids == []
        assert task.failed_chunk_count == 0
        assert task.total_chunk_count == 0

    def test_old_json_deserializes_with_defaults(self):
        """Old task JSON (no HTTP fields) should deserialize with defaults."""
        old_data = {
            "task_id": "abc123",
            "tenant_id": "t1",
            "name": "doc.pdf",
            "file_path": "/tmp/doc.pdf",
            "file_type": "document",
            "status": "completed",
            "progress": 1.0,
            "created_at": "2026-07-13T00:00:00Z",
            "updated_at": "2026-07-13T00:00:00Z",
            "kb_id": "kb1",
        }
        task = TaskInfo(**old_data)
        assert task.lightrag_doc_ids == []
        assert task.pending_track_ids == []
        assert task.failed_chunk_count == 0
        assert task.total_chunk_count == 0

    def test_full_serialization_roundtrip(self):
        """TaskInfo with HTTP fields should serialize/deserialize correctly."""
        task = TaskInfo(
            tenant_id="t1",
            name="doc.pdf",
            file_path="/tmp/doc.pdf",
            lightrag_doc_ids=["chunk-doc-1", "chunk-doc-2"],
            pending_track_ids=["trk-1"],
            failed_chunk_count=1,
            total_chunk_count=10,
            document_id="doc-uuid-123",
        )
        data = task.model_dump(mode="json")
        restored = TaskInfo(**data)
        assert restored.lightrag_doc_ids == ["chunk-doc-1", "chunk-doc-2"]
        assert restored.pending_track_ids == ["trk-1"]
        assert restored.failed_chunk_count == 1
        assert restored.total_chunk_count == 10
        assert restored.document_id == "doc-uuid-123"


class TestResultSummaryHttp:
    """Test ResultSummary used in HTTP mode."""

    def test_summary_with_http_counts(self):
        summary = ResultSummary(
            doc_id="doc-123",
            chunks=50,
            entities=30,
            relations=20,
            duration_seconds=120.5,
        )
        assert summary.doc_id == "doc-123"
        assert summary.chunks == 50
        assert summary.entities == 30
        assert summary.relations == 20
        assert summary.duration_seconds == 120.5


class TestErrorCodeCompat:
    """Test ErrorCode enum has required values."""

    def test_internal_error_exists(self):
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"

    def test_lightrag_error_exists(self):
        assert ErrorCode.LIGHTRAG_ERROR == "LIGHTRAG_ERROR"

    def test_task_cancelled_exists(self):
        assert ErrorCode.TASK_CANCELLED == "TASK_CANCELLED"
