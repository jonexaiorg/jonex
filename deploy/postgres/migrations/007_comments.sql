




COMMENT ON SCHEMA platform IS 'Data schema for platform.';
COMMENT ON SCHEMA knowledge_base IS 'Data schema for knowledge base.';
COMMENT ON SCHEMA business_domain IS 'Data schema for business domain.';
COMMENT ON SCHEMA metering IS 'Data schema for metering.';


COMMENT ON TABLE metering.llm_usage_log IS 'Llm usage log table.';
COMMENT ON COLUMN metering.llm_usage_log.request_id IS 'Request id column on metering.llm_usage_log.';
COMMENT ON COLUMN metering.llm_usage_log.trace_id IS 'Trace id column on metering.llm_usage_log.';
COMMENT ON COLUMN metering.llm_usage_log.scene IS 'Scene column on metering.llm_usage_log.';
COMMENT ON COLUMN metering.llm_usage_log.is_estimated IS 'Is estimated column on metering.llm_usage_log.';
COMMENT ON COLUMN metering.llm_usage_log.latency_ms IS 'Latency ms column on metering.llm_usage_log.';


COMMENT ON TABLE platform.tenants IS 'Tenants table.';
COMMENT ON TABLE platform.api_keys IS 'Api keys table.';
COMMENT ON TABLE platform.users IS 'Users table.';
COMMENT ON TABLE platform.login_tickets IS 'Login tickets table.';
COMMENT ON TABLE platform.roles IS 'Roles table.';
COMMENT ON TABLE platform.permissions IS 'Permissions table.';
COMMENT ON TABLE platform.role_permissions IS 'Role permissions table.';
COMMENT ON TABLE platform.user_roles IS 'User roles table.';
COMMENT ON TABLE platform.menus IS 'Menus table.';
COMMENT ON TABLE platform.applications IS 'Applications table.';
COMMENT ON TABLE platform.application_routes IS 'Application routes table.';
COMMENT ON TABLE platform.system_configs IS 'System configs table.';
COMMENT ON TABLE platform.audit_logs IS 'Audit logs table.';
COMMENT ON TABLE platform.task_schedules IS 'Task schedules table.';


COMMENT ON TABLE knowledge_base.knowledge_documents IS 'Knowledge documents table.';
COMMENT ON TABLE knowledge_base.knowledge_search_history IS 'Knowledge search history table.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.id IS 'Id column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.tenant_id IS 'Tenant id column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.file_name IS 'File name column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.file_path IS 'File path column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.file_size IS 'File size column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.mime_type IS 'Mime type column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.knowledge_base_id IS 'Knowledge base id column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.status IS 'Status column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.rag_task_id IS 'Rag task id column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.rag_doc_ids IS 'Rag doc ids column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.error_message IS 'Error message column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.ontology_status IS 'Ontology status column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.ontology_error IS 'Ontology error column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.ontology_retry_count IS 'Ontology retry count column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.extra_metadata IS 'Extra metadata column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.storage_backend IS 'Storage backend column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.storage_key IS 'Storage key column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.is_deleted IS 'Is deleted column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.id IS 'Id column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.tenant_id IS 'Tenant id column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.user_id IS 'User id column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.query IS 'Query column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.query_hash IS 'Query hash column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.knowledge_base_id IS 'Knowledge base id column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.mode IS 'Mode column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.top_k IS 'Top k column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.status IS 'Status column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.answer_preview IS 'Answer preview column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.reference_count IS 'Reference count column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.result_count IS 'Result count column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.duration_ms IS 'Duration ms column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.extra_metadata IS 'Extra metadata column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.searched_at IS 'Searched at column on knowledge_base.knowledge_search_history.';
COMMENT ON COLUMN knowledge_base.knowledge_search_history.is_deleted IS 'Is deleted column on knowledge_base.knowledge_search_history.';
COMMENT ON TABLE knowledge_base.spaces IS 'Spaces table.';
COMMENT ON TABLE knowledge_base.space_permissions IS 'Space permissions table.';
COMMENT ON TABLE knowledge_base.services IS 'Services table.';
COMMENT ON TABLE knowledge_base.service_knowledge_bases IS 'Service knowledge bases table.';
COMMENT ON TABLE knowledge_base.service_configs IS 'Service configs table.';
COMMENT ON TABLE knowledge_base.service_permissions IS 'Service permissions table.';
COMMENT ON TABLE knowledge_base.service_api_keys IS 'Service api keys table.';


COMMENT ON TABLE knowledge_base.knowledge_data_sources IS 'Knowledge data sources table.';

COMMENT ON TABLE knowledge_base.ontology_template_bindings IS 'Ontology template bindings table.';
COMMENT ON COLUMN knowledge_base.ontology_template_bindings.tenant_id IS 'Tenant id column on knowledge_base.ontology_template_bindings.';
COMMENT ON COLUMN knowledge_base.ontology_template_bindings.knowledge_base_id IS 'Knowledge base id column on knowledge_base.ontology_template_bindings.';
COMMENT ON COLUMN knowledge_base.ontology_template_bindings.template_domain_id IS 'Template domain id column on knowledge_base.ontology_template_bindings.';
COMMENT ON COLUMN knowledge_base.ontology_template_bindings.template_scenario_id IS 'Template scenario id column on knowledge_base.ontology_template_bindings.';
COMMENT ON COLUMN knowledge_base.ontology_template_bindings.source_type IS 'Source type column on knowledge_base.ontology_template_bindings.';
COMMENT ON COLUMN knowledge_base.ontology_template_bindings.status IS 'Status column on knowledge_base.ontology_template_bindings.';

COMMENT ON TABLE knowledge_base.ontology_compiled_schemas IS 'Ontology compiled schemas table.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.tenant_id IS 'Tenant id column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.knowledge_base_id IS 'Knowledge base id column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.template_domain_id IS 'Template domain id column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.template_scenario_id IS 'Template scenario id column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.source_type IS 'Source type column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.source_version IS 'Source version column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.source_hash IS 'Source hash column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.schema_version IS 'Schema version column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.entity_types IS 'Entity types column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.relation_types IS 'Relation types column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.constraints IS 'Constraints column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.disambiguation IS 'Disambiguation column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.prompt_schema IS 'Prompt schema column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.schema_mode IS 'Schema mode column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.sync_status IS 'Sync status column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.edited_at IS 'Edited at column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.edited_by IS 'Edited by column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.status IS 'Status column on knowledge_base.ontology_compiled_schemas.';
COMMENT ON COLUMN knowledge_base.ontology_compiled_schemas.compiled_at IS 'Compiled at column on knowledge_base.ontology_compiled_schemas.';

COMMENT ON TABLE knowledge_base.ontology_synonyms IS 'Ontology synonyms table.';
COMMENT ON COLUMN knowledge_base.ontology_synonyms.tenant_id IS 'Tenant id column on knowledge_base.ontology_synonyms.';
COMMENT ON COLUMN knowledge_base.ontology_synonyms.knowledge_base_id IS 'Knowledge base id column on knowledge_base.ontology_synonyms.';
COMMENT ON COLUMN knowledge_base.ontology_synonyms.terms IS 'Terms column on knowledge_base.ontology_synonyms.';
COMMENT ON COLUMN knowledge_base.ontology_synonyms.canonical IS 'Canonical column on knowledge_base.ontology_synonyms.';
COMMENT ON COLUMN knowledge_base.ontology_synonyms.is_deleted IS 'Is deleted column on knowledge_base.ontology_synonyms.';


COMMENT ON TABLE business_domain.data_access_methods IS 'Data access methods table.';
COMMENT ON TABLE business_domain.parser_configs IS 'Parser configs table.';
COMMENT ON TABLE business_domain.model_providers IS 'Model providers table.';
COMMENT ON TABLE business_domain.adapters IS 'Adapters table.';
COMMENT ON TABLE business_domain.skill_catalog IS 'Skill catalog table.';
COMMENT ON TABLE business_domain.tenant_skills IS 'Tenant skills table.';

COMMENT ON TABLE business_domain.template_domains IS 'Template domains table.';
COMMENT ON TABLE business_domain.template_scenarios IS 'Template scenarios table.';
COMMENT ON COLUMN business_domain.template_objects.ontology_code IS 'Ontology code column on business_domain.template_objects.';
COMMENT ON COLUMN business_domain.template_objects.aliases IS 'Aliases column on business_domain.template_objects.';
COMMENT ON COLUMN business_domain.template_attributes.ontology_code IS 'Ontology code column on business_domain.template_attributes.';
COMMENT ON COLUMN business_domain.template_relations.ontology_code IS 'Ontology code column on business_domain.template_relations.';
COMMENT ON COLUMN business_domain.template_relations.aliases IS 'Aliases column on business_domain.template_relations.';





COMMENT ON TABLE knowledge_base.knowledge_info IS 'Knowledge info table.';
COMMENT ON COLUMN knowledge_base.knowledge_info.id IS 'Id column on knowledge_base.knowledge_info.';
COMMENT ON COLUMN knowledge_base.knowledge_info.tenant_id IS 'Tenant id column on knowledge_base.knowledge_info.';
COMMENT ON COLUMN knowledge_base.knowledge_info.space_id IS 'Space id column on knowledge_base.knowledge_info.';
COMMENT ON COLUMN knowledge_base.knowledge_info.name IS 'Name column on knowledge_base.knowledge_info.';
COMMENT ON COLUMN knowledge_base.knowledge_info.description IS 'Description column on knowledge_base.knowledge_info.';
COMMENT ON COLUMN knowledge_base.knowledge_info.data_source_types IS 'Data source types column on knowledge_base.knowledge_info.';
COMMENT ON COLUMN knowledge_base.knowledge_info.document_count IS 'Document count column on knowledge_base.knowledge_info.';
COMMENT ON COLUMN knowledge_base.knowledge_info.status IS 'Status column on knowledge_base.knowledge_info.';
COMMENT ON COLUMN knowledge_base.knowledge_info.owner_id IS 'Owner id column on knowledge_base.knowledge_info.';

COMMENT ON COLUMN knowledge_base.knowledge_documents.data_source_type IS 'Data source type column on knowledge_base.knowledge_documents.';





COMMENT ON TABLE business_domain.template_objects IS 'Template objects table.';
COMMENT ON TABLE business_domain.template_attributes IS 'Template attributes table.';
COMMENT ON TABLE business_domain.template_relations IS 'Template relations table.';

COMMENT ON TABLE business_domain.prompt_templates IS 'Prompt templates table.';
COMMENT ON COLUMN business_domain.prompt_templates.id IS 'Id column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.tenant_id IS 'Tenant id column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.name IS 'Name column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.category IS 'Category column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.scope IS 'Scope column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.description IS 'Description column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.status IS 'Status column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.current_version IS 'Current version column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.versions_json IS 'Versions json column on business_domain.prompt_templates.';
COMMENT ON COLUMN business_domain.prompt_templates.created_by IS 'Created by column on business_domain.prompt_templates.';

COMMENT ON TABLE business_domain.template_constraints IS 'Template constraints table.';
COMMENT ON COLUMN business_domain.template_constraints.id IS 'Id column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.tenant_id IS 'Tenant id column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.domain_id IS 'Domain id column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.scenario_id IS 'Scenario id column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.name IS 'Name column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.target_type IS 'Target type column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.target_id IS 'Target id column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.target_label IS 'Target label column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.constraint_type IS 'Constraint type column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.expression IS 'Expression column on business_domain.template_constraints.';
COMMENT ON COLUMN business_domain.template_constraints.suggestion IS 'Suggestion column on business_domain.template_constraints.';













CREATE OR REPLACE VIEW metering.v_llm_usage_detail AS
SELECT
    u.id,
    (u.created_at AT TIME ZONE 'Asia/Shanghai')          AS created_local,
    u.tenant_id,
    u.scene,
    u.model,
    ki.name                                              AS kb_name,
    kd.file_name                                         AS doc_name,
    u.prompt_tokens, u.completion_tokens, u.total_tokens,
    u.latency_ms, u.is_stream, u.is_estimated,
    u.trace_id, u.request_id, u.kb_id, u.doc_id
FROM metering.llm_usage_log u
LEFT JOIN knowledge_base.knowledge_info      ki ON ki.id = u.kb_id
LEFT JOIN knowledge_base.knowledge_documents kd ON kd.id = u.doc_id;


CREATE OR REPLACE VIEW metering.v_llm_usage_by_doc AS
SELECT
    u.tenant_id,
    ki.name                                              AS kb_name,
    kd.file_name                                         AS doc_name,
    u.scene, u.model,
    SUM(u.call_count)                                    AS call_count,
    SUM(u.prompt_tokens)                                 AS prompt_tokens,
    SUM(u.completion_tokens)                             AS completion_tokens,
    SUM(u.total_tokens)                                  AS total_tokens,
    ROUND(AVG(u.latency_ms))                             AS avg_latency_ms,
    MIN(u.created_at AT TIME ZONE 'Asia/Shanghai')       AS first_local,
    MAX(u.created_at AT TIME ZONE 'Asia/Shanghai')       AS last_local
FROM metering.llm_usage_log u
LEFT JOIN knowledge_base.knowledge_info      ki ON ki.id = u.kb_id
LEFT JOIN knowledge_base.knowledge_documents kd ON kd.id = u.doc_id
GROUP BY u.tenant_id, ki.name, kd.file_name, u.scene, u.model;


CREATE OR REPLACE VIEW metering.v_llm_usage_by_trace AS
SELECT
    u.tenant_id, u.trace_id, u.scene, u.model,
    SUM(u.call_count)                                    AS call_count,
    SUM(u.total_tokens)                                  AS total_tokens,
    ROUND(AVG(u.latency_ms))                             AS avg_latency_ms,
    MIN(u.created_at AT TIME ZONE 'Asia/Shanghai')       AS first_local,
    MAX(u.created_at AT TIME ZONE 'Asia/Shanghai')       AS last_local
FROM metering.llm_usage_log u
GROUP BY u.tenant_id, u.trace_id, u.scene, u.model;


CREATE OR REPLACE VIEW metering.v_llm_usage_daily AS
SELECT
    (u.created_at AT TIME ZONE 'Asia/Shanghai')::date    AS day_local,
    u.tenant_id, u.scene, u.model,
    SUM(u.call_count)                                    AS call_count,
    SUM(u.prompt_tokens)                                 AS prompt_tokens,
    SUM(u.completion_tokens)                             AS completion_tokens,
    SUM(u.total_tokens)                                  AS total_tokens,
    ROUND(AVG(u.latency_ms))                             AS avg_latency_ms
FROM metering.llm_usage_log u
GROUP BY 1, u.tenant_id, u.scene, u.model;

COMMENT ON VIEW metering.v_llm_usage_detail   IS U&'LLM \8BA1\91CF\660E\7EC6\53EF\8BFB\89C6\56FE（\5173\8054 kb/doc \540D\79F0 + \672C\5730\65F6\533A）';
COMMENT ON VIEW metering.v_llm_usage_by_doc   IS U&'LLM \8BA1\91CF\6309\6587\6863\6C47\603B（call_count/tokens/avg_latency）';
COMMENT ON VIEW metering.v_llm_usage_by_trace IS U&'LLM \8BA1\91CF\6309\94FE\8DEF trace \6C47\603B';
COMMENT ON VIEW metering.v_llm_usage_daily    IS U&'LLM \8BA1\91CF\6309\5929\6C47\603B（\8D8B\52BF/\5BF9\8D26）';