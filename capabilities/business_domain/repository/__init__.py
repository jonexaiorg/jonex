"""
业务领域 — Repository 层。
"""
from capabilities.business_domain.repository.base import BaseRepository
from capabilities.business_domain.models import (
    Adapter, DataAccessMethod, ModelProvider,
    ParserConfig, SkillCatalog, TenantSkill, TemplateAttribute, TemplateConstraint,
    TemplateDomain, TemplateObject, TemplateRelation, TemplateScenario,
)


class DataAccessMethodRepository(BaseRepository[DataAccessMethod]):
    model = DataAccessMethod


class ParserConfigRepository(BaseRepository[ParserConfig]):
    model = ParserConfig


class ModelProviderRepository(BaseRepository[ModelProvider]):
    model = ModelProvider


class AdapterRepository(BaseRepository[Adapter]):
    model = Adapter


class SkillCatalogRepository(BaseRepository[SkillCatalog]):
    """平台共享 Skill 目录仓库（不传租户）"""
    model = SkillCatalog


class TenantSkillRepository(BaseRepository[TenantSkill]):
    """租户技能启用状态仓库（必须传租户）"""
    model = TenantSkill


class TemplateDomainRepository(BaseRepository[TemplateDomain]):
    model = TemplateDomain


class TemplateScenarioRepository(BaseRepository[TemplateScenario]):
    model = TemplateScenario


class TemplateObjectRepository(BaseRepository[TemplateObject]):
    model = TemplateObject


class TemplateAttributeRepository(BaseRepository[TemplateAttribute]):
    model = TemplateAttribute


class TemplateRelationRepository(BaseRepository[TemplateRelation]):
    model = TemplateRelation


from capabilities.business_domain.models.prompt_template import PromptTemplate


class PromptTemplateRepository(BaseRepository[PromptTemplate]):
    """提示词模板仓储 — 实际实现在 prompt_template_repository.py。
    此处注册基础 BaseRepository 子类供简单操作；复杂查询使用独立文件中的专用方法。"""
    model = PromptTemplate
class TemplateConstraintRepository(BaseRepository[TemplateConstraint]):
    model = TemplateConstraint
