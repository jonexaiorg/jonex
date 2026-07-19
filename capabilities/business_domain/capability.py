
import logging

from jonex_core.capability import BaseCapability
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityType,
)
from jonex_core.common.exceptions import TenantIsolationError, JonexException
from jonex_core.common.tenant import require_tenant

from capabilities.business_domain.services import (
    EngineService,
    AdapterService, SkillService, TemplateService,
)
from capabilities.business_domain.services.prompt_template_service import PromptTemplateService

logger = logging.getLogger(__name__)


class BusinessDomainCapability(BaseCapability):


    def __init__(self):
        self._engine = EngineService()
        self._adapter = AdapterService()
        self._skill = SkillService()
        self._template = TemplateService()
        self._prompt_template = PromptTemplateService()
        self._dispatch = self._build_dispatch()
        super().__init__()

    def register_routes(self, app):

        from capabilities.business_domain.api import create_router

        router = create_router()
        app.include_router(router, prefix="/api/v1")

    def _build_dispatch(self) -> dict:
        e = self._engine
        a = self._adapter
        sk = self._skill
        t = self._template
        pt = self._prompt_template
        return {

            "list_access_methods":    lambda r, d: e.list_access_methods(r.tenant_id, d.get("offset", 0), d.get("limit", 20)),
            "create_access_method":   lambda r, d: e.create_access_method(r.tenant_id, d),
            "update_access_method":   lambda r, d: e.update_access_method(d["method_id"], r.tenant_id, d),
            "list_parsers":           lambda r, d: e.list_parsers(r.tenant_id, d.get("offset", 0), d.get("limit", 20)),
            "create_parser":          lambda r, d: e.create_parser(r.tenant_id, d),
            "update_parser":          lambda r, d: e.update_parser(d["parser_id"], r.tenant_id, d),
            "list_providers":         lambda r, d: e.list_providers(r.tenant_id, d.get("offset", 0), d.get("limit", 20)),
            "create_provider":        lambda r, d: e.create_provider(r.tenant_id, d),
            "update_provider":        lambda r, d: e.update_provider(d["provider_id"], r.tenant_id, d),
            "test_provider":          lambda r, d: e.test_provider(d["provider_id"], r.tenant_id),

            "list_adapters":          lambda r, d: a.list(r.tenant_id, d.get("offset", 0), d.get("limit", 20)),
            "create_adapter":         lambda r, d: a.create(r.tenant_id, d),
            "update_adapter":         lambda r, d: a.update(d["adapter_id"], r.tenant_id, d),
            "connect_adapter":        lambda r, d: a.connect(d["adapter_id"], r.tenant_id),
            "disconnect_adapter":     lambda r, d: a.disconnect(d["adapter_id"], r.tenant_id),

            "list_skills":            lambda r, d: sk.list(r.tenant_id, d.get("offset", 0), d.get("limit", 20), d.get("category"), d.get("keyword")),
            "get_skill":              lambda r, d: sk.get(r.tenant_id, d["skill_id"]),
            "enable_skill":           lambda r, d: sk.enable(r.tenant_id, d["skill_id"]),
            "disable_skill":          lambda r, d: sk.disable(r.tenant_id, d["skill_id"]),
            "list_enabled_mcp_tools": lambda r, d: sk.list_enabled_mcp_tools(r.tenant_id),

            "list_template_domains":    lambda r, d: t.list_domains(r.tenant_id, d.get("offset", 0), d.get("limit", 20)),
            "get_template_domain":      lambda r, d: t.get_domain(d["domain_id"], r.tenant_id),
            "create_template_domain":   lambda r, d: t.create_domain(r.tenant_id, d),
            "update_template_domain":   lambda r, d: t.update_domain(d["domain_id"], r.tenant_id, d),
            "delete_template_domain":   lambda r, d: _deleted(t.delete_domain(d["domain_id"], r.tenant_id)),
            "list_template_scenarios":  lambda r, d: t.list_scenarios(r.tenant_id, d.get("domain_id"), d.get("offset", 0), d.get("limit", 20)),
            "get_template_scenario":    lambda r, d: t.get_scenario(d["scenario_id"], r.tenant_id),
            "create_template_scenario": lambda r, d: t.create_scenario(r.tenant_id, d),
            "update_template_scenario": lambda r, d: t.update_scenario(d["scenario_id"], r.tenant_id, d),
            "delete_template_scenario": lambda r, d: _deleted(t.delete_scenario(d["scenario_id"], r.tenant_id)),
            "list_template_objects":    lambda r, d: t.list_objects(r.tenant_id, d["scenario_id"], d.get("offset", 0), d.get("limit", 20)),
            "create_template_object":   lambda r, d: t.create_object(r.tenant_id, d["scenario_id"], d),
            "update_template_object":   lambda r, d: t.update_object(d["object_id"], r.tenant_id, d),
            "delete_template_object":   lambda r, d: _deleted(t.delete_object(d["object_id"], r.tenant_id)),
            "list_template_relations":  lambda r, d: t.list_relations(r.tenant_id, d["scenario_id"], d.get("offset", 0), d.get("limit", 20)),
            "create_template_relation": lambda r, d: t.create_relation(r.tenant_id, d["scenario_id"], d),
            "update_template_relation": lambda r, d: t.update_relation(d["relation_id"], r.tenant_id, d),
            "delete_template_relation": lambda r, d: _deleted(t.delete_relation(d["relation_id"], r.tenant_id)),

            "list_prompt_templates":      lambda r, d: pt.list_templates(
                r.tenant_id, d.get("scope"), d.get("category"),
                d.get("keyword"), d.get("offset", 0), d.get("limit", 20),
            ),
            "get_prompt_template":         lambda r, d: pt.get_template(d["template_id"], r.tenant_id),
            "create_prompt_template":      lambda r, d: pt.create_template(
                r.tenant_id, d, d.get("user_id"),
            ),
            "update_prompt_template":      lambda r, d: pt.update_template(
                d["template_id"], r.tenant_id, d, d.get("user_id"),
            ),
            "delete_prompt_template":      lambda r, d: _deleted(
                pt.delete_template(d["template_id"], r.tenant_id)
            ),
            "copy_prompt_template":        lambda r, d: pt.copy_template(
                d["template_id"], r.tenant_id, d.get("user_id"),
            ),
            "list_prompt_template_versions": lambda r, d: pt.list_versions(
                d["template_id"], r.tenant_id,
            ),
            "rollback_prompt_template":    lambda r, d: pt.rollback_version(
                d["template_id"], r.tenant_id, d["target_version"], d.get("user_id"),
            ),
            "list_template_constraints":   lambda r, d: t.list_constraints(r.tenant_id, d["scenario_id"], d.get("offset", 0), d.get("limit", 20)),
            "create_template_constraint":  lambda r, d: t.create_constraint(r.tenant_id, d["scenario_id"], d),
            "update_template_constraint":  lambda r, d: t.update_constraint(d["constraint_id"], r.tenant_id, d),
            "delete_template_constraint":  lambda r, d: _deleted(t.delete_constraint(d["constraint_id"], r.tenant_id)),
        }

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="business_domain",
            capability_name="业务领域与生态管理",
            capability_type=CapabilityType.BUSINESS,
            version="v1",
            description="领域空间、领域服务、引擎管理、生态适配器、Skills、业务模板",
            author="jonex",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": sorted(self._dispatch.keys()),
                        "description": "操作类型",
                    },
                    "data": {"type": "object", "description": "操作数据"},
                },
                "required": ["action"],
            },
            output_schema={"type": "object"},
            tags=["业务领域", "生态管理"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        action = request.payload.get("action")
        data = request.payload.get("data", {})

        handler = self._dispatch.get(action)
        if not handler:
            return CapabilityResponse.error(request.request_id, 400, f"不支持的操作: {action}")

        try:
            request.tenant_id = require_tenant(request.tenant_id)
            result = await handler(request, data)
            return CapabilityResponse.ok(request.request_id, result)
        except TenantIsolationError as e:
            return CapabilityResponse.error(request.request_id, 403, str(e))
        except JonexException as e:
            return CapabilityResponse.error(request.request_id, e.code, e.message)
        except Exception as e:
            logger.exception(f"Business domain capability execution failed: {e}")
            return CapabilityResponse.error(request.request_id, 500, f"执行失败: {str(e)}")


async def _deleted(coro) -> dict:
    result = await coro
    return {"deleted": result}


async def _updated(coro) -> dict:
    result = await coro
    return {"updated": result}
