#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""原子能力基类

所有原子能力必须继承此类，保证统一的调用契约。
原子能力只做纯技术能力封装，不包含业务逻辑。
"""

from abc import abstractmethod
from typing import Any, Dict, Optional

from jonex_core.capability.base import BaseCapability
from jonex_core.capability.models import CapabilityType, CapabilityRequest, CapabilityResponse


class AtomicCapability(BaseCapability):
    """原子能力抽象基类

    所有原子能力（LLM、向量检索、ASR、TTS等）必须继承此类，
    实现 validate_input 和 execute 方法。
    """

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:
        """
        验证输入参数的合法性

        Args:
            request: 能力调用请求

        Returns:
            bool: 参数是否合法
        """
        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """
        执行原子能力

        Args:
            request: 能力调用请求

        Returns:
            CapabilityResponse: 标准化的能力调用结果
        """
        pass


    @property
    def capability_type(self) -> CapabilityType:
        return CapabilityType.ATOMIC
