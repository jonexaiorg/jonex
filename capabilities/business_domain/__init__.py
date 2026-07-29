"""
业务领域 + 生态管理能力模块 (business.business_domain.v1)

负责：
- 领域空间管理（CRUD + 权限）
- 领域服务管理（CRUD + 知识库关联 + API Key）
- 引擎管理（数据接入/解析器/模型适配）
- 生态适配器管理（钉钉/企业微信/飞书）
- Skills 技能管理
- 业务领域模板 + 业务商场
"""
from capabilities.business_domain.capability import BusinessDomainCapability
from capabilities.business_domain.models import (
    Adapter, DataAccessMethod, ModelProvider,
    ParserConfig, SkillCatalog, TenantSkill,
    TemplateAttribute, TemplateDomain, TemplateObject,
    TemplateRelation, TemplateScenario,
)

__all__ = [
    "BusinessDomainCapability",
    # Models
    "DataAccessMethod", "ParserConfig", "ModelProvider",
    "Adapter", "SkillCatalog", "TenantSkill",
    "TemplateDomain", "TemplateScenario", "TemplateObject",
    "TemplateAttribute", "TemplateRelation",
]