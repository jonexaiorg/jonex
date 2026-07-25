"""Tests for EventBus and DocStatusListener."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from raganything.event_bus import EventBus, PipelineEvent, DocStatusListener


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish_calls_subscriber(self):
        bus = EventBus()
        called = []

        async def listener(event):
            called.append(event.type)

        bus.subscribe("test", listener)
        await bus.publish(PipelineEvent(type="test", doc_id="d1", file_path="f"))
        assert called == ["test"]

    @pytest.mark.asyncio
    async def test_listener_exception_does_not_propagate(self):
        bus = EventBus()

        async def bad(_):
            raise RuntimeError("boom")

        bus.subscribe("test", bad)
        await bus.publish(PipelineEvent(type="test", doc_id="d1", file_path="f"))

    @pytest.mark.asyncio
    async def test_multiple_listeners_called_in_order(self):
        bus = EventBus()
        order = []

        async def a(_):
            order.append("a")

        async def b(_):
            order.append("b")

        bus.subscribe("test", a)
        bus.subscribe("test", b)
        await bus.publish(PipelineEvent(type="test", doc_id="d1", file_path="f"))
        assert order == ["a", "b"]

    @pytest.mark.asyncio
    async def test_unrelated_event_not_called(self):
        bus = EventBus()
        called = []

        async def listener(_):
            called.append(1)

        bus.subscribe("test", listener)
        await bus.publish(PipelineEvent(type="other", doc_id="d1", file_path="f"))
        assert called == []


class TestDocStatusListener:
    @pytest.mark.asyncio
    async def test_on_document_failed_updates_status(self):
        from raganything.base import DocStatus

        mgr = MagicMock()
        mgr.upsert = AsyncMock()
        listener = DocStatusListener(mgr)
        event = PipelineEvent(
            type="document_failed",
            doc_id="doc-1",
            file_path="f.pdf",
            data={"error": "parse failed"},
        )
        await listener.on_document_failed(event)
        mgr.upsert.assert_awaited_once_with(
            "doc-1", "f.pdf", status=DocStatus.FAILED, error_msg="parse failed"
        )
