#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""领域能力基类

所有领域能力必须继承此类，领域能力负责编排 1-N 个原子能力，
做领域级数据格式化、校验、聚合，不直接访问数据库。
"""

from abc import abstractmethod
from typing import Any, Dict, Optional

from jonex_core.capability.base import BaseCapability
from jonex_core.capability.models import CapabilityType, CapabilityRequest, CapabilityResponse


class DomainCapability(BaseCapability):
    """领域能力抽象基类

    所有领域能力（语音处理、文本生成、知识检索等）必须继承此类。
    领域能力负责编排 1-N 个原子能力，不直接访问数据库。
    """

    @property
    def capability_type(self) -> CapabilityType:
        """领域能力类型"""
        return CapabilityType.DOMAIN

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
        执行领域能力

        Args:
            request: 能力调用请求

        Returns:
            CapabilityResponse: 标准化的能力调用结果
        """
        pass
