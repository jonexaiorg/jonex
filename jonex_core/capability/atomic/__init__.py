#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""原子能力层 - 提供最基础的技术能力封装

对外建议入口：使用各 `client` 模块下的工厂函数（`get_llm_client()` 等），
而非直接实例化适配器类，以支持 LOCAL / REMOTE / MOCK 三种部署模式切换。
"""

from .base import AtomicCapability
from .llm.qwen_adapter import QwenLLMCapability
from .vector.milvus_adapter import MilvusVectorCapability
from .audio.asr_adapter import ASRCapability

# Client 抽象 + 工厂（推荐入口）
from .llm.client import LLMClient, get_llm_client
from .vector.client import VectorClient, get_vector_client
from .audio.client import ASRClient, get_asr_client

__all__ = [
    # 适配器（Local 实现 / 历史保留）
    "AtomicCapability",
    "QwenLLMCapability",
    "MilvusVectorCapability",
    "ASRCapability",
    # Client 抽象与工厂（推荐使用）
    "LLMClient",
    "get_llm_client",
    "VectorClient",
    "get_vector_client",
    "ASRClient",
    "get_asr_client",
]
