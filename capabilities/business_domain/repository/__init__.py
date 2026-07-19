
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

    model = SkillCatalog


class TenantSkillRepository(BaseRepository[TenantSkill]):

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

    model = PromptTemplate
class TemplateConstraintRepository(BaseRepository[TemplateConstraint]):
    model = TemplateConstraint
