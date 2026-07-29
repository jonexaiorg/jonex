"""
业务领域 — 枚举定义
"""
from enum import Enum


class AdapterType(str, Enum):
    DINGTALK = "dingtalk"
    WECHAT_WORK = "wechat_work"
    FEISHU = "feishu"


class AdapterStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class SkillCatalogStatus(str, Enum):
    """系统 Skill 目录状态"""
    PUBLISHED = "published"
    DISABLED = "disabled"


class TenantSkillStatus(str, Enum):
    """租户技能启用状态"""
    ENABLED = "enabled"
    DISABLED = "disabled"


class SkillCategory(str, Enum):
    """Skill 分类（对应旧 SkillType）"""
    IMAGE = "image"
    VOICE = "voice"
    DOCUMENT = "document"
    VIDEO = "video"
    FUSION = "fusion"
    CUSTOM = "custom"


# 兼容旧代码，DEPRECATED
class SkillStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    RUNNING = "running"


class SkillType(str, Enum):
    CUSTOM = "custom"
    LLM_CHAIN = "llm_chain"
    RAG_PIPELINE = "rag_pipeline"
    API_PROXY = "api_proxy"


class ModelProviderType(str, Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    RERANKER = "reranker"


class ModelProviderStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class TemplateStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"