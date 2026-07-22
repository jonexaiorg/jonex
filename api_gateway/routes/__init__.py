#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - API route module
"""

from .knowledge_base import router as knowledge_base_router
from .tcadp import router as tcadp_router
from .auth import router as auth_router

__all__ = ["knowledge_base_router", "tcadp_router", "auth_router"]
