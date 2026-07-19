













ALTER TABLE platform.audit_logs
    ADD COLUMN IF NOT EXISTS log_type VARCHAR(32),
    ADD COLUMN IF NOT EXISTS service_name VARCHAR(64),
    ADD COLUMN IF NOT EXISTS outcome VARCHAR(16),
    ADD COLUMN IF NOT EXISTS log_level VARCHAR(16),
    ADD COLUMN IF NOT EXISTS error_message TEXT,
    ADD COLUMN IF NOT EXISTS method VARCHAR(8),
    ADD COLUMN IF NOT EXISTS path VARCHAR(512);

COMMENT ON COLUMN platform.audit_logs.log_type IS 'Log type column on platform.audit_logs.';
COMMENT ON COLUMN platform.audit_logs.service_name IS 'Service name column on platform.audit_logs.';
COMMENT ON COLUMN platform.audit_logs.outcome IS 'SUCCESS / FAILED';
COMMENT ON COLUMN platform.audit_logs.log_level IS 'INFO / WARN / ERROR';
COMMENT ON COLUMN platform.audit_logs.error_message IS 'Error message column on platform.audit_logs.';
COMMENT ON COLUMN platform.audit_logs.method IS 'Method column on platform.audit_logs.';
COMMENT ON COLUMN platform.audit_logs.path IS 'Path column on platform.audit_logs.';


ALTER TABLE knowledge_base.knowledge_documents
    ADD COLUMN IF NOT EXISTS folder_id VARCHAR(64);

ALTER TABLE knowledge_base.knowledge_documents
    ADD COLUMN IF NOT EXISTS data_source_type VARCHAR(32);

COMMENT ON COLUMN knowledge_base.knowledge_documents.folder_id IS 'Folder id column on knowledge_base.knowledge_documents.';
COMMENT ON COLUMN knowledge_base.knowledge_documents.data_source_type IS 'Data source type column on knowledge_base.knowledge_documents.';






CREATE TABLE IF NOT EXISTS knowledge_base.knowledge_data_sources (
    id                VARCHAR(64) PRIMARY KEY,
    tenant_id         VARCHAR(64)  NOT NULL,
    knowledge_base_id VARCHAR(128) NOT NULL,
    access_method_id  VARCHAR(64),
    access_type       VARCHAR(32)  NOT NULL,
    name              VARCHAR(255) NOT NULL,
    config_json       JSONB        NOT NULL DEFAULT '{}',
    sync_mode         VARCHAR(16)  NOT NULL DEFAULT 'manual',
    cron_expr         VARCHAR(128),
    schedule_task_id  INTEGER,
    status            VARCHAR(32)  NOT NULL DEFAULT 'active',
    last_sync_at      TIMESTAMPTZ,
    last_sync_status  VARCHAR(32),
    last_sync_message TEXT,
    document_count    INTEGER      NOT NULL DEFAULT 0,
    is_deleted        SMALLINT     NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_data_sources_kb
    ON knowledge_base.knowledge_data_sources (tenant_id, knowledge_base_id, is_deleted);

CREATE UNIQUE INDEX IF NOT EXISTS uq_kb_ds_file_per_kb
    ON knowledge_base.knowledge_data_sources (tenant_id, knowledge_base_id)
    WHERE access_type = 'file' AND is_deleted = 0;

COMMENT ON TABLE knowledge_base.knowledge_data_sources IS 'Knowledge data sources table.';






CREATE TABLE IF NOT EXISTS knowledge_base.ontology_synonyms (
    id                VARCHAR(64) PRIMARY KEY,
    tenant_id         VARCHAR(64) NOT NULL,
    knowledge_base_id VARCHAR(128) NOT NULL,
    terms             JSONB NOT NULL DEFAULT '[]'::jsonb,
    canonical         VARCHAR(255),
    created_at        TIMESTAMP NOT NULL DEFAULT now(),
    updated_at        TIMESTAMP NOT NULL DEFAULT now(),
    is_deleted        SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_kb_synonyms_tenant_kb
    ON knowledge_base.ontology_synonyms (tenant_id, knowledge_base_id, is_deleted);






CREATE TABLE IF NOT EXISTS knowledge_base.knowledge_parser_settings (
    id                         VARCHAR(64) PRIMARY KEY,
    tenant_id                  VARCHAR(64)  NOT NULL,
    knowledge_base_id          VARCHAR(128) NOT NULL,
    file_type                  VARCHAR(64)  NOT NULL,
    file_type_label            VARCHAR(128) NOT NULL,
    parser_config_id           VARCHAR(64),
    preprocessing_json         JSONB        NOT NULL DEFAULT '[]'::jsonb,
    postprocessing_json        JSONB        NOT NULL DEFAULT '[]'::jsonb,
    prompt_text                TEXT,
    prompt_template_id         VARCHAR(64),
    prompt_template_version    VARCHAR(32),
    summary_prompt_text        TEXT,
    summary_template_id        VARCHAR(64),
    summary_template_version   VARCHAR(32),
    tag_prompt_text            TEXT,
    tag_template_id            VARCHAR(64),
    tag_template_version       VARCHAR(32),
    status                     VARCHAR(32)  NOT NULL DEFAULT 'active',
    is_deleted                 SMALLINT     NOT NULL DEFAULT 0,
    created_at                 TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at                 TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kps_kb
    ON knowledge_base.knowledge_parser_settings (tenant_id, knowledge_base_id, is_deleted);

CREATE INDEX IF NOT EXISTS idx_kps_parser
    ON knowledge_base.knowledge_parser_settings (tenant_id, parser_config_id)
    WHERE parser_config_id IS NOT NULL AND is_deleted = 0;

CREATE UNIQUE INDEX IF NOT EXISTS uq_kps_file_type_per_kb
    ON knowledge_base.knowledge_parser_settings (tenant_id, knowledge_base_id, file_type)
    WHERE is_deleted = 0;






CREATE TABLE IF NOT EXISTS knowledge_base.folders (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    knowledge_base_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_preset BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_by VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_kb_folders_tenant_kb
    ON knowledge_base.folders (tenant_id, knowledge_base_id, is_deleted);

CREATE UNIQUE INDEX IF NOT EXISTS uq_kb_folders_name_per_kb
    ON knowledge_base.folders (tenant_id, knowledge_base_id, name)
    WHERE is_deleted = 0;

CREATE INDEX IF NOT EXISTS idx_kb_doc_folder
    ON knowledge_base.knowledge_documents (tenant_id, knowledge_base_id, folder_id)
    WHERE is_deleted = 0 AND folder_id IS NOT NULL;






CREATE TABLE IF NOT EXISTS knowledge_base.knowledge_search_feedback (
    id              VARCHAR(64) PRIMARY KEY,
    tenant_id       VARCHAR(64) NOT NULL,
    user_id         VARCHAR(128) NOT NULL,
    session_id      VARCHAR(128) NOT NULL,
    query           TEXT NOT NULL,
    answer_preview  TEXT,
    knowledge_base_id       VARCHAR(128) NOT NULL,
    knowledge_base_name     VARCHAR(256),
    feedback_type   VARCHAR(16) NOT NULL,
    adopted         BOOLEAN NOT NULL DEFAULT FALSE,
    searched_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_deleted      INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_kb_feedback_tenant_kb_time
    ON knowledge_base.knowledge_search_feedback (tenant_id, knowledge_base_id, searched_at);

CREATE INDEX IF NOT EXISTS idx_kb_feedback_tenant_user
    ON knowledge_base.knowledge_search_feedback (tenant_id, user_id);

CREATE INDEX IF NOT EXISTS idx_kb_feedback_session
    ON knowledge_base.knowledge_search_feedback (session_id);

CREATE INDEX IF NOT EXISTS idx_kb_feedback_user_id
    ON knowledge_base.knowledge_search_feedback (user_id);






CREATE TABLE IF NOT EXISTS business_domain.template_constraints (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    domain_id VARCHAR(64) NOT NULL,
    scenario_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    target_type VARCHAR(32) NOT NULL,
    target_id VARCHAR(64) NOT NULL,
    target_label VARCHAR(255) NOT NULL,
    constraint_type VARCHAR(32) NOT NULL,
    expression TEXT,
    suggestion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_tc_tenant ON business_domain.template_constraints(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tc_is_deleted ON business_domain.template_constraints(is_deleted);
CREATE INDEX IF NOT EXISTS idx_tc_domain ON business_domain.template_constraints(domain_id);
CREATE INDEX IF NOT EXISTS idx_tc_scenario ON business_domain.template_constraints(scenario_id);
CREATE INDEX IF NOT EXISTS idx_tc_target ON business_domain.template_constraints(target_id);






CREATE TABLE IF NOT EXISTS business_domain.prompt_templates (
    id              VARCHAR(64) PRIMARY KEY,
    tenant_id       VARCHAR(64),
    name            VARCHAR(255) NOT NULL,
    category        VARCHAR(64) NOT NULL,
    scope           VARCHAR(16) NOT NULL DEFAULT 'domain',
    description     TEXT,
    status          VARCHAR(16) NOT NULL DEFAULT 'enabled',
    current_version VARCHAR(32) NOT NULL DEFAULT '1.0',
    versions_json   JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_by      VARCHAR(128),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted      SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pt_tenant_scope
    ON business_domain.prompt_templates(tenant_id, scope)
    WHERE tenant_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_pt_tenant_deleted
    ON business_domain.prompt_templates(tenant_id, is_deleted)
    WHERE tenant_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_pt_scope_system
    ON business_domain.prompt_templates(scope, is_deleted)
    WHERE tenant_id IS NULL AND scope = 'system';






CREATE TABLE IF NOT EXISTS metering.llm_usage_daily (
    day_local          DATE         NOT NULL,
    tenant_id          VARCHAR(64)  NOT NULL,
    scene              VARCHAR(64)  NOT NULL,
    model              VARCHAR(128) NOT NULL,
    call_count         BIGINT       NOT NULL DEFAULT 0,
    prompt_tokens      BIGINT       NOT NULL DEFAULT 0,
    completion_tokens  BIGINT       NOT NULL DEFAULT 0,
    total_tokens       BIGINT       NOT NULL DEFAULT 0,
    avg_latency_ms     INTEGER,
    PRIMARY KEY (day_local, tenant_id, scene, model)
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_daily_tenant
    ON metering.llm_usage_daily (tenant_id, day_local);
