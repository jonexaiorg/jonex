#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""向量检索抽象基类"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse


class BaseVectorCapability(AtomicCapability):
    """向量检索抽象基类

    所有向量数据库适配器必须继承此类。
    """

    @abstractmethod
    async def validate_input(self, request: CapabilityRequest) -> bool:
        """验证向量检索输入参数"""
        pass

    @abstractmethod
    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """执行向量检索调用"""
        pass

    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        插入向量数据

        Args:
            collection_name: 集合名称
            vectors: 向量数组
            metadatas: 元数据数组（与 vectors 一一对应）

        Returns:
            bool: 是否插入成功
        """
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        向量相似度检索

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回结果数量

        Returns:
            List[Dict]: 检索结果列表，包含 id、score、metadata 等
        """
        pass

    @abstractmethod
    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """
        删除向量数据

        Args:
            collection_name: 集合名称
            ids: 待删除的 ID 列表

        Returns:
            bool: 是否删除成功
        """
        pass
