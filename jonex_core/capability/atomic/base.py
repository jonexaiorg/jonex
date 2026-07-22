#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Atomic capability base class

All atomic capabilities must inherit from this class to ensure a unified invocation contract.
Atomic capabilities only encapsulate pure technical capabilities and do not contain business logic.
"""

from abc import abstractmethod
from typing import Any, Dict, Optional

from jonex_core.capability.base import BaseCapability
from jonex_core.capability.models import CapabilityType, CapabilityRequest, CapabilityResponse


class AtomicCapability(BaseCapability):
    """Atomic capability abstract base class

    All atomic capabilities (LLM, vector search, ASR, TTS, etc.) must inherit from this class,
    and implement the validate_input and execute methods.
    """

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:
        """
        Validate the legitimacy of input parameters

        Args:
            request: Capability invocation request

        Returns:
            bool: Whether the parameters are valid
        """
        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """
        Execute atomic capability

        Args:
            request: Capability invocation request

        Returns:
            CapabilityResponse: Standardized capability invocation result
        """
        pass


    @property
    def capability_type(self) -> CapabilityType:
        return CapabilityType.ATOMIC
