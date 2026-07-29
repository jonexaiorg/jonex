"""
本体论引擎 — TBox 定义与注册。

提供 OntologyRegistry（本体注册中心）及相关的数据模型（EntityTypeDef、RelationTypeDef）。
由 atomic-rag 的 Stage4 OntologyExtractor 在文档抽取时使用，亦可供 knowledge-base
服务在查询时检索类型定义。
"""

from .models import EntityTypeDef, AttributeDef, RelationTypeDef, OntologySchema
from .registry import OntologyRegistry

__all__ = [
    "EntityTypeDef",
    "AttributeDef",
    "RelationTypeDef",
    "OntologySchema",
    "OntologyRegistry",
]
