#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""LLM capability abstract base class"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse


class BaseLLMCapability(AtomicCapability):
    """LLM abstract base class

    All large language model adapters must inherit from this class and implement the unified text generation interface.
    """

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:
        """Validate LLM input parameters"""
        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """Execute LLM invocation"""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Chat completion interface

        Args:
            messages: Conversation history, format like [{"role": "user", "content": "..."}]
            temperature: Temperature parameter 0-1
            max_tokens: Maximum generation length

        Returns:
            str: Generated text content
        """
        pass

    @abstractmethod
    async def embedding(self, text: str) -> List[float]:
        """
        Text vectorizationInterface

        Args:
            text: Text to be vectorized

        Returns:
            List[float]: Vector array
        """
        pass
