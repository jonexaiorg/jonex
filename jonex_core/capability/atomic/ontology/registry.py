"""
本体注册中心 — 加载、缓存、查询 TBox schema。

OntologyRegistry 是一个轻量级注册中心，负责：
1. 从 YAML 文件加载本体定义
2. 按领域（domain）缓存多个 schema
3. 提供实体类型/关系类型的查找和校验方法

使用示例::

    registry = OntologyRegistry()
    registry.load("deploy/config/ontology/default.yaml")
    schema = registry.get("default")
    et = schema.find_entity_type("Organization")  # → EntityTypeDef
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import EntityTypeDef, OntologySchema, RelationTypeDef

# 尝试导入 yaml，若不存在则给出友好提示
try:
    from yaml import SafeLoader
except ImportError:
    SafeLoader = None  # type: ignore[assignment]


class OntologyRegistry:
    """本体注册中心 — 按领域管理的只读 TBox 缓存。"""

    def __init__(self):
        self._schemas: Dict[str, OntologySchema] = {}

    # ── 加载 ────────────────────────────────────

    def load(self, path: str | Path) -> OntologySchema:
        """从 YAML 文件加载本体 schema。"""
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"本体 schema 文件不存在: {path}")

        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        schema = OntologySchema.from_dict(raw)
        self._schemas[schema.domain] = schema
        return schema

    def load_from_dict(self, data: dict, domain: str = "default") -> OntologySchema:
        """从字典加载本体 schema（用于测试或动态定义）。"""
        schema = OntologySchema.from_dict(data)
        # 如果 data 中指定了 domain 则覆盖
        if schema.domain != domain:
            schema.domain = domain
        self._schemas[domain] = schema
        return schema

    # ── 查询 ────────────────────────────────────

    def get(self, domain: str = "default") -> Optional[OntologySchema]:
        """获取指定领域的 schema。"""
        return self._schemas.get(domain)

    def get_or_default(self, domain: str = "default") -> OntologySchema:
        """获取指定领域的 schema，不存在则返回默认 schema（空定义）。"""
        schema = self._schemas.get(domain)
        if schema is not None:
            return schema
        # 若已加载过 default 则作为 fallback
        if domain != "default":
            return self._schemas.get("default", OntologySchema())
        return OntologySchema()

    def list_domains(self) -> List[str]:
        return list(self._schemas.keys())

    # ── 校验 ────────────────────────────────────

    def validate_entity_type(self, type_name: str, domain: str = "default") -> bool:
        """检查实体类型是否在 schema 中定义。"""
        schema = self.get(domain)
        if schema is None:
            return True  # 无 schema 时不拦截
        return schema.find_entity_type(type_name) is not None

    def validate_relation_type(self, type_name: str, domain: str = "default") -> bool:
        """检查关系类型是否在 schema 中定义。"""
        schema = self.get(domain)
        if schema is None:
            return True
        return schema.find_relation_type(type_name) is not None

    # ── 序列化 ──────────────────────────────────

    def to_prompt_json(self, domain: str = "default") -> str:
        """将 schema 转为 JSON，供 LLM prompt 拼接使用。"""
        import json

        schema = self.get_or_default(domain)
        payload = {
            "entity_types": [
                {
                    "name": et.name,
                    "aliases": et.aliases,
                    "attributes": [
                        {"name": a.name, "type": a.type, "required": a.required}
                        for a in et.attributes
                    ],
                }
                for et in schema.entity_types
            ],
            "relation_types": [
                {
                    "name": rt.name,
                    "source": rt.source,
                    "target": rt.target,
                }
                for rt in schema.relation_types
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
