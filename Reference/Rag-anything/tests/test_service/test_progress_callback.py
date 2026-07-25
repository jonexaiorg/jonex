"""Tests for ProgressTrackingCallback — pipeline event → TaskInfo updates."""

import asyncio
import time

import pytest
from raganything.service.task_manager import ProgressTrackingCallback, TaskHandle
from raganything.service.models import TaskInfo, TaskStatus, FileType


class TestProgressTrackingCallback:
    """Tests for progress callback wiring."""

    @pytest.fixture
    def task(self):
        return TaskInfo(
            tenant_id="test_tenant",
            name="test.mp4",
            file_path="/data/test.mp4",
            file_type=FileType.VIDEO,
        )

    @pytest.fixture
    def handle(self):
        return TaskHandle(release_cb=lambda: None)

    def test_on_parse_start_updates_task(self, task, handle):
        cb = ProgressTrackingCallback(task, handle)
        cb.on_parse_start("/data/test.mp4")

        assert task.current_step == "parse"
        assert task.progress_detail is not None
        assert task.progress_detail.step_name == "parse"
        assert task.progress_detail.step_detail == "Parsing document..."

    def test_on_parse_complete_updates_progress(self, task, handle):
        cb = ProgressTrackingCallback(task, handle)
        cb.on_parse_complete("/data/test.mp4", content_blocks=42)

        assert task.progress == 0.2
        assert task.progress_detail is not None
        assert "42 blocks" in task.progress_detail.step_detail

    def test_on_text_insert_start(self, task, handle):
        cb = ProgressTrackingCallback(task, handle)
        cb.on_text_insert_start("/data/test.mp4", text_length=1000)

        assert task.current_step == "text_insert"
        assert task.progress_detail.current == 2

    def test_on_multimodal_item_complete_scales_progress(self, task, handle):
        cb = ProgressTrackingCallback(task, handle)
        cb.on_multimodal_item_complete(
            "/data/test.mp4", item_index=5, total_items=10
        )

        # 0.5 + 0.4 * (5/10) = 0.7
        assert task.progress == pytest.approx(0.7, abs=0.01)
        assert task.progress_detail.current == 5
        assert task.progress_detail.total == 10

    def test_on_document_complete_sets_doc_id(self, task, handle):
        cb = ProgressTrackingCallback(task, handle)
        cb.on_document_complete("/data/test.mp4", doc_id="doc-abc123")

        assert task.progress == 1.0
        assert task.current_step == "done"
        assert task.result_summary is not None
        assert task.result_summary.doc_id == "doc-abc123"

    def test_on_document_error_records_stage(self, task, handle):
        cb = ProgressTrackingCallback(task, handle)
        cb.on_document_error(
            "/data/test.mp4", error="Something broke", stage="parse"
        )

        assert task.progress_detail is not None
        assert task.progress_detail.step_name == "parse"
        assert "Something broke" in task.progress_detail.step_detail

    def test_cancel_event_triggers_cancelled_error(self, task, handle):
        cb = ProgressTrackingCallback(task, handle)
        handle.cancel_event.set()

        with pytest.raises(Exception):  # TaskCancelledError
            cb.on_parse_start("/data/test.mp4")

    def test_full_sequence_updates_progress_linearly(self, task, handle):
        """Progress should increase monotonically through the full sequence."""
        cb = ProgressTrackingCallback(task, handle)

        prev = 0.0
        cb.on_parse_start("/data/test.mp4")
        prev = task.progress  # 0.0 (parse_start doesn't set progress)

        cb.on_parse_complete("/data/test.mp4", content_blocks=10)
        assert task.progress == 0.2
        prev = task.progress

        cb.on_text_insert_complete("/data/test.mp4")
        assert task.progress == 0.4
        assert task.progress > prev

        cb.on_multimodal_start("/data/test.mp4", item_count=5)
        assert task.progress == 0.5

        cb.on_multimodal_item_complete("/data/test.mp4", item_index=4, total_items=5)
        assert task.progress == pytest.approx(0.82, abs=0.01)

        cb.on_document_complete("/data/test.mp4", doc_id="final")
        assert task.progress == 1.0
