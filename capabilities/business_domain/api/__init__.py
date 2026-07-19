
from fastapi import APIRouter


def create_router() -> APIRouter:
    router = APIRouter()

    from capabilities.business_domain.api.engines import router as engines_router
    router.include_router(engines_router, prefix="/business-domain", tags=["引擎管理"])

    from capabilities.business_domain.api.adapters import router as adapters_router
    router.include_router(adapters_router, prefix="/business-domain", tags=["生态适配器"])

    from capabilities.business_domain.api.skills import router as skills_router
    router.include_router(skills_router, prefix="/business-domain", tags=["技能管理"])

    from capabilities.business_domain.api.templates import router as templates_router
    router.include_router(templates_router, prefix="/business-domain", tags=["业务模板"])

    from capabilities.business_domain.api.prompt_templates import router as prompt_templates_router
    router.include_router(prompt_templates_router, prefix="/api/v1", tags=["提示词模板"])

    return router