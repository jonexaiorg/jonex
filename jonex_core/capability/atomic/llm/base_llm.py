#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""LLM 能力抽象基类"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse


class BaseLLMCapability(AtomicCapability):
    """LLM 抽象基类

    所有大模型适配器必须继承此类，实现统一的文本生成接口。
    """

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:
        """验证 LLM 输入参数"""
        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """执行 LLM 调用"""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        聊天补全接口

        Args:
            messages: 对话历史，格式如 [{"role": "user", "content": "..."}]
            temperature: 温度参数 0-1
            max_tokens: 最大生成长度

        Returns:
            str: 生成的文本内容
        """
        pass

    @abstractmethod
    async def embedding(self, text: str) -> List[float]:
        """
        文本向量化接口

        Args:
            text: 待向量化的文本

        Returns:
            List[float]: 向量数组
        """
        pass
