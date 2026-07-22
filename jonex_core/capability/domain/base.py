#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Domain capability base class

All domain capabilities must inherit this class. Domain capabilities are responsible
for orchestrating 1-N atomic capabilities, performing domain-level data formatting,
validation and aggregation, without directly accessing the database.
"""

from abc import abstractmethod
from typing import Any, Dict, Optional

from jonex_core.capability.base import BaseCapability
from jonex_core.capability.models import CapabilityType, CapabilityRequest, CapabilityResponse


class DomainCapability(BaseCapability):
    """Domain capability abstract base class

    All domain capabilities (speech processing, text generation, knowledge retrieval, etc.)
    must inherit this class. Domain capabilities are responsible for orchestrating 1-N
    atomic capabilities, without directly accessing the database.
    """

    @property
    def capability_type(self) -> CapabilityType:
        """Domain capability type"""
        return CapabilityType.DOMAIN

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
        Execute domain capability

        Args:
            request: Capability invocation request

        Returns:
            CapabilityResponse: Standardized capability invocation result
        """
        pass
