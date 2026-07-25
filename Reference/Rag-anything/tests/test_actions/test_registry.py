"""Tests for ActionRegistry."""

import pytest
from atomic_rag.actions import ActionRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    ActionRegistry.clear()
    yield


@pytest.mark.asyncio
async def test_register_and_get_handler():
    @ActionRegistry.register("test_action")
    async def handler(**kwargs):
        return {"handled": True}

    h = ActionRegistry.get("test_action")
    assert h is not None
    result = await h()
    assert result["handled"]


def test_get_nonexistent_returns_none():
    assert ActionRegistry.get("nonexistent") is None


@pytest.mark.asyncio
async def test_register_multiple_handlers():
    @ActionRegistry.register("action_a")
    async def handler_a(**kwargs):
        return {"action": "a"}

    @ActionRegistry.register("action_b")
    async def handler_b(**kwargs):
        return {"action": "b"}

    assert ActionRegistry.get("action_a") is not None
    assert ActionRegistry.get("action_b") is not None
    assert await ActionRegistry.get("action_a")() == {"action": "a"}
    assert await ActionRegistry.get("action_b")() == {"action": "b"}


def test_clear_removes_all_handlers():
    @ActionRegistry.register("temp")
    async def temp_handler(**kwargs):
        return {}

    assert ActionRegistry.get("temp") is not None
    ActionRegistry.clear()
    assert ActionRegistry.get("temp") is None


@pytest.mark.asyncio
async def test_handler_receives_kwargs():
    @ActionRegistry.register("echo")
    async def echo_handler(**kwargs):
        return kwargs

    result = await ActionRegistry.get("echo")(foo="bar", num=42)
    assert result["foo"] == "bar"
    assert result["num"] == 42
