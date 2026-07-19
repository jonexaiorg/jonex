#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""[yuexi] priority_limit_async_func_call —— context 透传 + 取消/超时语义回归。

对应设计：docs/lightrag-embed-metering-context-propagation-plan.md §7。

为什么是独立脚本而非 pytest：vendored LightRAG 无测试基建，且 lightrag/utils.py
在模块加载期 import numpy 等重依赖，只能在 **lightrag 容器内**运行。用 asyncio.run +
断言，避免依赖 pytest-asyncio。

容器内运行：
    docker exec yuexi-lightrag python /app/tests/test_priority_limiter_context.py
或本机装齐 lightrag 依赖后：
    python Reference/LightRAG/tests/test_priority_limiter_context.py
全部通过打印 "ALL PASSED"，否则抛 AssertionError。
"""

import asyncio
import contextvars

from lightrag.utils import priority_limit_async_func_call

_tv: contextvars.ContextVar[str] = contextvars.ContextVar("test_tv", default="unset")


async def _read_tv() -> str:
    # sleep 让协程真正被调度到 worker 执行
    await asyncio.sleep(0.01)
    return _tv.get()


async def test_context_propagation() -> None:
    """入队时的 contextvar 值应被 worker 执行环境读到（修复前会是 'unset'）。"""
    limited = priority_limit_async_func_call(2, queue_name="test-prop")(_read_tv)
    try:
        _tv.set("doc-A")
        result = await limited()
        assert result == "doc-A", f"期望 worker 读到入队时 context 'doc-A'，实际 {result!r}"
    finally:
        await limited.shutdown()


async def test_context_isolation() -> None:
    """并发不同 context 快照互不串扰。"""
    limited = priority_limit_async_func_call(4, queue_name="test-iso")(_read_tv)

    async def call_with(val: str) -> str:
        _tv.set(val)
        return await limited()

    try:
        a, b, c = await asyncio.gather(
            call_with("A"), call_with("B"), call_with("C")
        )
        assert {a, b, c} == {"A", "B", "C"}, f"context 串扰：{a!r} {b!r} {c!r}"
    finally:
        await limited.shutdown()


async def test_user_timeout_propagates() -> None:
    """用户级 _timeout 到点应向调用方抛 TimeoutError。"""
    async def slow() -> str:
        await asyncio.sleep(5)
        return "done"

    limited = priority_limit_async_func_call(2, queue_name="test-to")(slow)
    try:
        try:
            await limited(_timeout=0.2)
        except TimeoutError:
            return
        raise AssertionError("超时未抛 TimeoutError")
    finally:
        await limited.shutdown()


async def test_swallowed_cancel_still_times_out() -> None:
    """内层 func 吞掉 CancelledError 仍不停，调用方仍应在 _timeout 到点收到 TimeoutError。

    覆盖 review 指出的边界：改用 create_task 包装后，取消的是 Task 层；即便内层
    吞掉取消，wait_func 对 future 的 wait_for(_timeout) 仍独立超时，不会挂死。
    """
    async def swallow_cancel() -> str:
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            # 故意吞掉取消并继续（模拟异常的 retry 宽泛 catch）
            await asyncio.sleep(5)
        return "done"

    limited = priority_limit_async_func_call(2, queue_name="test-swallow")(swallow_cancel)
    try:
        try:
            await limited(_timeout=0.2)
        except TimeoutError:
            return
        raise AssertionError("吞取消场景下超时未抛 TimeoutError")
    finally:
        await limited.shutdown()


async def _main() -> None:
    await test_context_propagation()
    await test_context_isolation()
    await test_user_timeout_propagates()
    await test_swallowed_cancel_still_times_out()
    print("ALL PASSED")


if __name__ == "__main__":
    asyncio.run(_main())
