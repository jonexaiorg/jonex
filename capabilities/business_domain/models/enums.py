
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

    PUBLISHED = "published"
    DISABLED = "disabled"


class TenantSkillStatus(str, Enum):

    ENABLED = "enabled"
    DISABLED = "disabled"


class SkillCategory(str, Enum):

    IMAGE = "image"
    VOICE = "voice"
    DOCUMENT = "document"
    VIDEO = "video"
    FUSION = "fusion"
    CUSTOM = "custom"



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