

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from jonex_core.capability import BaseCapability
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityType,
)
from jonex_core.common.exceptions import TenantIsolationError, JonexException
from jonex_core.common.neo4j_client import close_neo4j_driver, ensure_ontology_schema
from jonex_core.common.tenant import require_tenant

from .services import DomainServiceService, KnowledgeBaseService, SpaceService

logger = logging.getLogger(__name__)

ActionHandler = Callable[[CapabilityRequest, dict[str, Any]], Awaitable[dict]]


class KnowledgeBaseCapability(BaseCapability):


    _INTERNAL_ACTIONS = {"reconcile_documents", "reconcile_ontology", "ingest_push"}

    def __init__(self):
        self.service = KnowledgeBaseService()
        self._space = SpaceService()
        self._domain_service = DomainServiceService()
        self._dispatch = self._build_dispatch()
        self._reconcile_task: asyncio.Task | None = None
        super().__init__()

    def register_routes(self, app):

        from capabilities.knowledge_base.api import create_router

        router = create_router()
        app.include_router(router, prefix="/api/v1")

    async def initialize(self) -> None:
        try:
            await ensure_ontology_schema()
        except Exception as exc:
            logger.warning("Neo4j schema init failed, ontology queries may degrade: %s", exc)

        self._reconcile_task = asyncio.create_task(self._reconcile_loop())
        logger.info("Knowledge Base capability initialized (reconciliation loop started)")

    async def shutdown(self) -> None:
        if self._reconcile_task:
            self._reconcile_task.cancel()
            try:
                await self._reconcile_task
            except asyncio.CancelledError:
                pass
        await close_neo4j_driver()
        logger.info("Knowledge Base capability shutdown complete")

    async def _reconcile_loop(self) -> None:

        logger.info("Reconciliation loop started (first run immediately)")
        first_run = True
        while True:
            try:
                if not first_run:
                    await asyncio.sleep(30)
                first_run = False

                logger.debug("Reconciliation cycle begin")
                doc_result = await self.service.reconciliation.reconcile_documents(limit=50)
                logger.info("Reconciliation → documents: %s", doc_result)
                onto_result = await self.service.reconciliation.reconcile_ontology(limit=50)
                logger.info("Reconciliation → ontology: %s", onto_result)
            except asyncio.CancelledError:
                logger.info("Reconciliation loop cancelled, exiting")
                break
            except Exception as e:
                if "connection" in str(e).lower() or "connection_lost" in str(e).lower():
                    logger.warning("Reconciliation loop: DB connection lost, will retry. %s", e)
                else:
                    logger.exception("Reconciliation loop error")
                await asyncio.sleep(10)

    def _build_dispatch(self) -> dict[str, ActionHandler]:
        docs = self.service.documents
        search = self.service.search
        history = self.service.history
        feedback = self.service.feedback
        parse = self.service.parse_results
        ontology = self.service.ontology
        reconcile = self.service.reconciliation
        kbinfo = self.service.knowledge_infos
        compiler = self.service.compiler
        folders = self.service.folders
        syn = self.service.synonyms
        oq = self.service.ontology_query
        ds = self.service.data_sources
        ps = self.service.parser_settings
        s = self._space
        sv = self._domain_service

        return {

            "upload_document": lambda r, d: docs.upload_document(r.tenant_id, d, user_id=r.user_id, username=r.username, ip=r.ip),
            "list_documents": lambda r, d: docs.list_documents(r.tenant_id, d),
            "get_document": lambda r, d: docs.get_document(r.tenant_id, d["document_id"], d),
            "delete_document": lambda r, d: docs.delete_document(r.tenant_id, d["document_id"], d, user_id=r.user_id, username=r.username, ip=r.ip),
            "generate_upload_url": lambda r, d: docs.generate_upload_url(
                r.tenant_id, d["knowledge_base_id"], d["file_name"], d.get("content_type"),
            ),
            "get_raw_url": lambda r, d: docs.get_raw_url(r.tenant_id, d["document_id"]),
            "get_raw_content": lambda r, d: docs.get_raw_content(r.tenant_id, d["document_id"]),
            "get_raw_location": lambda r, d: docs.get_raw_location(r.tenant_id, d["document_id"]),
            "set_document_folder": lambda r, d: docs.set_document_folder(
                r.tenant_id, d["document_id"], d
            ),

            "search": lambda r, d: search.search(r.tenant_id, _user_id(r), d, trace_id=r.request_id),
            "search_enhanced": lambda r, d: search.enhanced_search(r.tenant_id, _user_id(r), d, trace_id=r.request_id),
            "query_with_ontology": lambda r, d: search.query_with_ontology(r.tenant_id, _user_id(r), d, trace_id=r.request_id),
            "get_search_overview": lambda r, d: history.get_overview(r.tenant_id, _user_id(r), d),
            "list_search_history": lambda r, d: history.list_history(r.tenant_id, _user_id(r), d),
            "save_search_history": lambda r, d: history.save_history(r.tenant_id, _user_id(r), d),
            "delete_search_history": lambda r, d: history.delete_history(
                r.tenant_id, _user_id(r), d["history_id"], d
            ),
            "clear_search_history": lambda r, d: history.clear_history(r.tenant_id, _user_id(r), d),

            "submit_search_feedback": lambda r, d: feedback.submit_feedback(r.tenant_id, _user_id(r), d),
            "cancel_search_feedback": lambda r, d: feedback.cancel_feedback(r.tenant_id, _user_id(r), d),
            "list_search_feedback": lambda r, d: feedback.list_feedback(r.tenant_id, d),
            "toggle_search_feedback_adopted": lambda r, d: feedback.toggle_adopted(r.tenant_id, d),
            "get_search_feedback_stats": lambda r, d: feedback.get_stats(r.tenant_id, d),

            "get_parse_result_summary": lambda r, d: parse.get_summary(r.tenant_id, d),
            "get_parse_result_documents": lambda r, d: parse.list_documents(r.tenant_id, d),
            "get_parse_result_entities": lambda r, d: parse.list_entities(r.tenant_id, d),
            "get_parse_result_relationships": lambda r, d: parse.list_relationships(r.tenant_id, d),
            "get_parse_result_graph_summary": lambda r, d: parse.get_graph_summary(r.tenant_id, d),
            "get_parse_result_graph": lambda r, d: parse.get_graph(r.tenant_id, d),
            "get_document_parse_result": lambda r, d: parse.get_document_parse_result(r.tenant_id, d),

            "retry_ontology_extract": lambda r, d: ontology.retry_extract(
                r.tenant_id,
                d["document_id"],
                d["knowledge_base_id"],
            ),

            "get_editor_state": lambda r, d: compiler.get_editor_state(
                r.tenant_id, d["knowledge_base_id"],
            ),
            "get_compiled_schema": lambda r, d: compiler.get_compiled_schema(
                r.tenant_id, d["knowledge_base_id"],
            ),
            "save_compiled_schema": lambda r, d: compiler.save_compiled_schema(
                r.tenant_id, d["knowledge_base_id"],
                d.get("entity_types", []), d.get("relation_types", []),
                edited_by=r.user_id,
                constraints=(d["constraints"] if "constraints" in d else None),
                expected_schema_version=d.get("expected_schema_version"),
            ),
            "reseed_compiled_schema": lambda r, d: compiler.reseed_from_template(
                r.tenant_id, d["knowledge_base_id"],
                d["template_scenario_id"], d.get("template_domain_id"),
                d.get("source_type", "business_template"),
            ),

            "list_folders": lambda r, d: folders.list_folders(
                r.tenant_id, d["knowledge_base_id"]
            ),
            "create_folder": lambda r, d: folders.create_folder(r.tenant_id, d),
            "rename_folder": lambda r, d: folders.rename_folder(
                r.tenant_id, d["folder_id"], d["knowledge_base_id"], d["name"]
            ),
            "delete_folder": lambda r, d: _deleted(folders.delete_folder(
                r.tenant_id, d["folder_id"], d["knowledge_base_id"]
            )),

            "list_synonyms": lambda r, d: syn.list(
                r.tenant_id, d["knowledge_base_id"], d.get("page", 1), d.get("page_size", 20)
            ),
            "create_synonym": lambda r, d: syn.create(r.tenant_id, d),
            "update_synonym": lambda r, d: syn.update(r.tenant_id, d["synonym_id"], d),
            "delete_synonym": lambda r, d: _deleted(syn.delete(r.tenant_id, d["synonym_id"])),
            "import_synonyms": lambda r, d: syn.batch_import(
                r.tenant_id, d["knowledge_base_id"], d.get("groups", [])
            ),

            "reconcile_documents": lambda r, d: reconcile.reconcile_documents(d.get("limit", 50)),
            "reconcile_ontology": lambda r, d: reconcile.reconcile_ontology(d.get("limit", 50)),

            "list_knowledge_info": lambda r, d: kbinfo.list(
                r.tenant_id, d.get("space_id"), d.get("status"),
                d.get("keyword"), d.get("offset", 0), d.get("limit", 20),
            ),
            "create_knowledge_info": lambda r, d: kbinfo.create(r.tenant_id, d),
            "get_knowledge_info": lambda r, d: kbinfo.get(d["kb_id"], r.tenant_id),
            "update_knowledge_info": lambda r, d: kbinfo.update(d["kb_id"], r.tenant_id, d),
            "delete_knowledge_info": lambda r, d: kbinfo.delete(d["kb_id"], r.tenant_id),

            "list_spaces": lambda r, d: s.list(r.tenant_id, d.get("offset", 0), d.get("limit", 20)),
            "create_space": lambda r, d: s.create(r.tenant_id, d),
            "get_space": lambda r, d: s.get(d["space_id"], r.tenant_id),
            "update_space": lambda r, d: s.update(d["space_id"], r.tenant_id, d),
            "delete_space": lambda r, d: _deleted(s.delete(d["space_id"], r.tenant_id)),
            "get_space_permissions": lambda r, d: _list_result(s.get_permissions(d["space_id"], r.tenant_id)),
            "set_space_permissions": lambda r, d: _updated(
                s.set_permissions(d["space_id"], r.tenant_id, d.get("permissions", []))
            ),

            "list_services": lambda r, d: sv.list(
                r.tenant_id, d.get("space_id"), d.get("offset", 0), d.get("limit", 20)
            ),
            "create_service": lambda r, d: sv.create(r.tenant_id, d),
            "get_service": lambda r, d: sv.get(d["service_id"], r.tenant_id),
            "update_service": lambda r, d: sv.update(d["service_id"], r.tenant_id, d),
            "delete_service": lambda r, d: _deleted(sv.delete(d["service_id"], r.tenant_id)),
            "rotate_service_api_key": lambda r, d: sv.rotate_api_key(d["service_id"], r.tenant_id),
            "list_service_api_keys": lambda r, d: sv.list_api_keys(d["service_id"], r.tenant_id),
            "create_service_api_key": lambda r, d: sv.create_api_key(d["service_id"], r.tenant_id, d),
            "delete_service_api_key": lambda r, d: _deleted(
                sv.delete_api_key(d["key_id"], d["service_id"], r.tenant_id)
            ),
            "get_service_configs": lambda r, d: sv.get_configs(d["service_id"], r.tenant_id),
            "update_service_configs": lambda r, d: _updated(
                sv.update_configs(d["service_id"], r.tenant_id, d.get("configs", {}))
            ),
            "get_service_permissions": lambda r, d: _list_result(sv.get_permissions(d["service_id"], r.tenant_id)),
            "set_service_permissions": lambda r, d: _updated(
                sv.set_permissions(d["service_id"], r.tenant_id, d.get("permissions", []))
            ),
            "search_service": lambda r, d: sv.search(d["service_id"], r.tenant_id, d["query"]),

            "resolve_references": lambda r, d: search.resolve_references(
                r.tenant_id,
                doc_ids=d.get("doc_ids"),
                refs=d.get("refs"),
            ),

            "get_ontology_statistics": lambda r, d: oq.get_kb_statistics(r.tenant_id, d),
            "list_ontology_instances": lambda r, d: oq.list_instances(r.tenant_id, d),
            "list_ontology_relations": lambda r, d: oq.list_relations(r.tenant_id, d),
            "get_ontology_graph": lambda r, d: oq.get_kb_graph(r.tenant_id, d),
            "expand_ontology_neighbors": lambda r, d: oq.expand_ontology_neighbors(r.tenant_id, d),
            "list_ontology_entity_types": lambda r, d: oq.list_entity_types(r.tenant_id, d),
            "list_ontology_relation_types": lambda r, d: oq.list_relation_types(r.tenant_id, d),

            "list_data_sources": lambda r, d: ds.list_sources(r.tenant_id, d["knowledge_base_id"]),
            "get_data_source": lambda r, d: ds.get_source(r.tenant_id, d["ds_id"]),
            "create_data_source": lambda r, d: ds.create_source(r.tenant_id, d),
            "update_data_source": lambda r, d: ds.update_source(r.tenant_id, d["ds_id"], d),
            "delete_data_source": lambda r, d: ds.delete_source(r.tenant_id, d["ds_id"]),
            "test_data_source": lambda r, d: ds.test_source(r.tenant_id, d["ds_id"]),
            "sync_data_source": lambda r, d: ds.sync_source(r.tenant_id, d["ds_id"]),
            "reset_ingest_key": lambda r, d: ds.reset_ingest_key(r.tenant_id, d["ds_id"]),

            "list_parser_settings": lambda r, d: ps.list_settings(r.tenant_id, d["knowledge_base_id"]),
            "create_parser_setting": lambda r, d: ps.create_setting(r.tenant_id, d),
            "update_parser_setting": lambda r, d: ps.update_setting(r.tenant_id, d["setting_id"], d),
            "delete_parser_setting": lambda r, d: ps.delete_setting(r.tenant_id, d["setting_id"]),

            "ingest_push": lambda r, d: ds.ingest_push(
                d["ds_id"], d["ingest_key"],
                storage_key=d["storage_key"], file_name=d["file_name"],
                mime_type=d.get("mime_type"), file_size=d.get("file_size", 0),
                external_id=d.get("external_id"),
            ),
        }

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="knowledge_base",
            capability_name="知识库能力",
            capability_type=CapabilityType.BUSINESS,
            version="v1",
            description="知识文档、检索、检索历史、解析结果和本体抽取能力",
            author="jonex",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": sorted(self._dispatch.keys()),
                    },
                    "data": {"type": "object"},
                },
                "required": ["action"],
            },
            output_schema={"type": "object"},
            tags=["知识库", "文档管理", "语义检索", "本体"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        action = request.payload.get("action")
        if action not in self._dispatch:
            return False
        data = request.payload.get("data") or {}
        if not isinstance(data, dict):
            return False
        required_fields = {
            "get_document": ("document_id", "knowledge_base_id"),
            "delete_document": ("document_id", "knowledge_base_id"),
            "upload_document": ("knowledge_base_id",),
            "list_documents": ("knowledge_base_id",),
            "search": ("query",),
            "search_enhanced": ("query", "knowledge_base_id"),
            "query_with_ontology": ("query",),
            "get_search_overview": (),
            "list_search_history": (),
            "save_search_history": ("query",),
            "delete_search_history": ("history_id",),
            "clear_search_history": (),
            "get_parse_result_summary": ("knowledge_base_id",),
            "get_parse_result_documents": ("knowledge_base_id",),
            "get_parse_result_entities": ("knowledge_base_id",),
            "get_parse_result_relationships": ("knowledge_base_id",),
            "get_parse_result_graph_summary": ("knowledge_base_id",),
            "get_parse_result_graph": ("knowledge_base_id",),
            "get_document_parse_result": ("document_id", "knowledge_base_id"),
            "retry_ontology_extract": ("document_id", "knowledge_base_id"),
            "get_editor_state": ("knowledge_base_id",),
            "get_compiled_schema": ("knowledge_base_id",),
            "save_compiled_schema": ("knowledge_base_id",),
            "reseed_compiled_schema": ("knowledge_base_id", "template_scenario_id"),

            "list_folders": ("knowledge_base_id",),
            "create_folder": ("knowledge_base_id", "name"),
            "rename_folder": ("folder_id", "knowledge_base_id", "name"),
            "delete_folder": ("folder_id", "knowledge_base_id"),

            "list_synonyms": ("knowledge_base_id",),
            "create_synonym": ("knowledge_base_id",),
            "update_synonym": ("synonym_id",),
            "delete_synonym": ("synonym_id",),
            "import_synonyms": ("knowledge_base_id",),

            "list_spaces": (),
            "create_space": ("name",),
            "get_space": ("space_id",),
            "update_space": ("space_id",),
            "delete_space": ("space_id",),
            "get_space_permissions": ("space_id",),
            "set_space_permissions": ("space_id",),

            "list_services": (),
            "create_service": ("space_id", "name"),
            "get_service": ("service_id",),
            "update_service": ("service_id",),
            "delete_service": ("service_id",),
            "rotate_service_api_key": ("service_id",),
            "list_service_api_keys": ("service_id",),
            "create_service_api_key": ("service_id",),
            "delete_service_api_key": ("service_id", "key_id"),
            "get_service_configs": ("service_id",),
            "update_service_configs": ("service_id",),
            "get_service_permissions": ("service_id",),
            "set_service_permissions": ("service_id",),
            "search_service": ("service_id", "query"),
            "set_document_folder": ("document_id", "knowledge_base_id"),
            "generate_upload_url": ("knowledge_base_id", "file_name"),
            "get_raw_url": ("document_id",),
            "get_raw_content": ("document_id",),
            "get_raw_location": ("document_id",),

            "get_ontology_statistics": ("knowledge_base_id",),
            "get_ontology_graph": ("knowledge_base_id",),
            "expand_ontology_neighbors": ("knowledge_base_id", "entity_type", "canonical_name"),
            "list_ontology_instances": ("knowledge_base_id",),
            "list_ontology_relations": ("knowledge_base_id",),
            "list_ontology_entity_types": ("knowledge_base_id",),
            "list_ontology_relation_types": ("knowledge_base_id",),

            "submit_search_feedback": ("session_id", "query", "feedback_type", "knowledge_base_ids"),
            "cancel_search_feedback": ("session_id", "feedback_type", "knowledge_base_ids"),
            "list_search_feedback": ("knowledge_base_id",),
            "toggle_search_feedback_adopted": ("feedback_id",),
            "get_search_feedback_stats": ("knowledge_base_id",),

            "list_data_sources": ("knowledge_base_id",),
            "get_data_source": ("ds_id",),
            "create_data_source": ("knowledge_base_id", "access_type", "name"),
            "update_data_source": ("ds_id",),
            "delete_data_source": ("ds_id",),
            "test_data_source": ("ds_id",),
            "sync_data_source": ("ds_id",),
            "reset_ingest_key": ("ds_id",),

            "list_parser_settings": ("knowledge_base_id",),
            "create_parser_setting": ("knowledge_base_id", "file_type", "file_type_label"),
            "update_parser_setting": ("setting_id",),
            "delete_parser_setting": ("setting_id",),
            "ingest_push": ("ds_id", "ingest_key", "storage_key", "file_name"),
        }
        return all(data.get(field) for field in required_fields.get(action, ()))

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        action = request.payload.get("action")
        data = request.payload.get("data") or {}
        handler = self._dispatch.get(action)

        if handler is None:
            return CapabilityResponse.error(request.request_id, 400, f"不支持的操作: {action}")

        try:
            if action not in self._INTERNAL_ACTIONS:
                request.tenant_id = require_tenant(request.tenant_id)
            result = await handler(request, data)
            return CapabilityResponse.ok(request.request_id, result)
        except TenantIsolationError as exc:
            return CapabilityResponse.error(request.request_id, exc.code, exc.message)
        except JonexException as exc:
            return CapabilityResponse.error(request.request_id, exc.code, exc.message)
        except Exception as exc:
            logger.exception("Knowledge Base capability action failed: %s", action)
            return CapabilityResponse.error(request.request_id, 500, f"执行失败: {exc}")


def _user_id(request: CapabilityRequest) -> str:
    return request.user_id or "anonymous"


async def _deleted(coro) -> dict:
    result = await coro
    return {"deleted": result}


async def _updated(coro) -> dict:
    result = await coro
    return {"updated": result}


async def _list_result(coro) -> dict:

    result = await coro
    return {"permissions": result} if isinstance(result, list) else result
