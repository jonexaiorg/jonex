#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Atomic capability layer - provides the most fundamental technical capability encapsulation

Recommended entry point: use the FactoryFunction in each `client` module (`get_llm_client()`, etc.),
rather than directly instantiating adapter classes, to support switching between LOCAL / REMOTE / MOCK deployment modes.
"""

from .base import AtomicCapability
from .llm.qwen_adapter import QwenLLMCapability
from .vector.milvus_adapter import MilvusVectorCapability
from .audio.asr_adapter import ASRCapability

# Client Abstract + Factory (recommended entry point)
from .llm.client import LLMClient, get_llm_client
from .vector.client import VectorClient, get_vector_client
from .audio.client import ASRClient, get_asr_client

__all__ = [
    # Adapter (Local implementation / retained for legacy)
    "AtomicCapability",
    "QwenLLMCapability",
    "MilvusVectorCapability",
    "ASRCapability",
    # Client Abstract and Factory (recommended to use)
    "LLMClient",
    "get_llm_client",
    "VectorClient",
    "get_vector_client",
    "ASRClient",
    "get_asr_client",
]
