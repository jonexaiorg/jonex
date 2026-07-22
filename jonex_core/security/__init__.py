#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Security module

Contains inter-service internal authentication, permission verification and other security-related functionality
"""

from jonex_core.security.internal_auth import (
    InternalAuth,
    get_internal_auth,
    verify_internal_service,
)

__all__ = [
    "InternalAuth",
    "get_internal_auth",
    "verify_internal_service",
]
