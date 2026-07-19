












CREATE TABLE IF NOT EXISTS knowledge_base.spaces (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id VARCHAR(64),
    status VARCHAR(32) DEFAULT 'active',
    knowledge_base_count INTEGER DEFAULT 0,
    service_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kb_sp_tenant ON knowledge_base.spaces(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_sp_is_deleted ON knowledge_base.spaces(is_deleted);


CREATE TABLE IF NOT EXISTS knowledge_base.space_permissions (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    space_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kb_spp_tenant ON knowledge_base.space_permissions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_spp_is_deleted ON knowledge_base.space_permissions(is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_spp_space ON knowledge_base.space_permissions(space_id);
CREATE INDEX IF NOT EXISTS idx_kb_spp_user ON knowledge_base.space_permissions(user_id);




CREATE TABLE IF NOT EXISTS knowledge_base.knowledge_info (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    space_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    data_source_types JSONB DEFAULT '[]'::jsonb,
    document_count INTEGER DEFAULT 0,
    status VARCHAR(32) DEFAULT 'synced',
    owner_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kb_tenant ON knowledge_base.knowledge_info(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_is_deleted ON knowledge_base.knowledge_info(is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_space ON knowledge_base.knowledge_info(space_id);




CREATE TABLE IF NOT EXISTS knowledge_base.services (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    space_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    domain_type VARCHAR(64),
    status VARCHAR(32) DEFAULT 'active',
    api_key_encrypted VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kb_svc_tenant ON knowledge_base.services(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_svc_is_deleted ON knowledge_base.services(is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_svc_space ON knowledge_base.services(space_id);


CREATE TABLE IF NOT EXISTS knowledge_base.service_knowledge_bases (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    service_id VARCHAR(64) NOT NULL,
    kb_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kb_skb_tenant ON knowledge_base.service_knowledge_bases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_skb_is_deleted ON knowledge_base.service_knowledge_bases(is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_skb_service ON knowledge_base.service_knowledge_bases(service_id);


CREATE TABLE IF NOT EXISTS knowledge_base.service_configs (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    service_id VARCHAR(64) NOT NULL,
    config_key VARCHAR(128) NOT NULL,
    config_value TEXT,
    description VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kb_sc_tenant ON knowledge_base.service_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_sc_is_deleted ON knowledge_base.service_configs(is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_sc_service ON knowledge_base.service_configs(service_id);


CREATE TABLE IF NOT EXISTS knowledge_base.service_permissions (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    service_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kb_svcp_tenant ON knowledge_base.service_permissions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_svcp_is_deleted ON knowledge_base.service_permissions(is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_svcp_service ON knowledge_base.service_permissions(service_id);


CREATE TABLE IF NOT EXISTS knowledge_base.service_api_keys (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    service_id VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL DEFAULT 'sk',
    key_encrypted VARCHAR(512) NOT NULL,
    expires_at TIMESTAMP,
    is_active SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kb_sak_tenant ON knowledge_base.service_api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_sak_is_deleted ON knowledge_base.service_api_keys(is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_sak_service ON knowledge_base.service_api_keys(service_id);






CREATE TABLE IF NOT EXISTS knowledge_base.knowledge_documents (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    file_name VARCHAR(512) NOT NULL,
    file_path VARCHAR(1024) NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    mime_type VARCHAR(128),
    storage_backend VARCHAR(16) NOT NULL DEFAULT 'local',
    storage_key VARCHAR(1024) NOT NULL,
    knowledge_base_id VARCHAR(128) NOT NULL,
    status VARCHAR(32) DEFAULT 'pending' NOT NULL,
    rag_task_id VARCHAR(128),
    rag_doc_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    error_message TEXT,
    ontology_status VARCHAR(32) DEFAULT 'pending' NOT NULL,
    ontology_error TEXT,
    ontology_retry_count INTEGER NOT NULL DEFAULT 0,
    extra_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    data_source_type VARCHAR(32),
    folder_id VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_kb_doc_tenant_deleted
    ON knowledge_base.knowledge_documents(tenant_id, is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_doc_tenant_status
    ON knowledge_base.knowledge_documents(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_kb_doc_tenant_ontology_status
    ON knowledge_base.knowledge_documents(tenant_id, ontology_status);
CREATE INDEX IF NOT EXISTS idx_kb_doc_tenant_created
    ON knowledge_base.knowledge_documents(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_kb_doc_tenant_kb
    ON knowledge_base.knowledge_documents(tenant_id, knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_kb_doc_rag_task
    ON knowledge_base.knowledge_documents(rag_task_id);

CREATE INDEX IF NOT EXISTS idx_kb_doc_tenant_kb_type
    ON knowledge_base.knowledge_documents(tenant_id, knowledge_base_id, data_source_type)
    WHERE is_deleted = 0;




CREATE TABLE IF NOT EXISTS knowledge_base.knowledge_search_history (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    query TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    knowledge_base_id VARCHAR(128) NOT NULL,
    mode VARCHAR(32) NOT NULL DEFAULT 'hybrid',
    top_k INTEGER NOT NULL DEFAULT 5,
    status VARCHAR(32) NOT NULL DEFAULT 'done',
    answer_preview TEXT,
    reference_count INTEGER NOT NULL DEFAULT 0,
    result_count INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    extra_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    searched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_search_history_query_kb
    ON knowledge_base.knowledge_search_history(
        tenant_id,
        user_id,
        query_hash,
        knowledge_base_id
    );
CREATE INDEX IF NOT EXISTS idx_kb_hist_tenant_user_time
    ON knowledge_base.knowledge_search_history(tenant_id, user_id, searched_at DESC);
CREATE INDEX IF NOT EXISTS idx_kb_hist_tenant_user_deleted
    ON knowledge_base.knowledge_search_history(tenant_id, user_id, is_deleted);
CREATE INDEX IF NOT EXISTS idx_kb_hist_tenant_user_kb_time
    ON knowledge_base.knowledge_search_history(tenant_id, user_id, knowledge_base_id, searched_at DESC);




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




CREATE TABLE IF NOT EXISTS knowledge_base.ontology_template_bindings (
    id                   BIGSERIAL       PRIMARY KEY,
    tenant_id            VARCHAR(64)     NOT NULL,
    knowledge_base_id    VARCHAR(128)    NOT NULL,
    template_domain_id   VARCHAR(64),
    template_scenario_id VARCHAR(64),
    source_type          VARCHAR(32)     NOT NULL DEFAULT 'business_template',
    status               VARCHAR(32)     NOT NULL DEFAULT 'active',
    created_at           TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, knowledge_base_id)
);
CREATE INDEX IF NOT EXISTS idx_otb_tenant_template
    ON knowledge_base.ontology_template_bindings (tenant_id, template_domain_id, template_scenario_id);





CREATE TABLE IF NOT EXISTS knowledge_base.ontology_compiled_schemas (
    id                    BIGSERIAL       PRIMARY KEY,
    tenant_id             VARCHAR(64)     NOT NULL,
    knowledge_base_id     VARCHAR(128)    NOT NULL,
    template_domain_id    VARCHAR(64),
    template_scenario_id  VARCHAR(64),
    source_type           VARCHAR(32)     NOT NULL DEFAULT 'business_template',
    source_version        INTEGER         NOT NULL DEFAULT 1,
    source_hash           VARCHAR(64),
    schema_version        INTEGER         NOT NULL DEFAULT 1,
    entity_types          JSONB           NOT NULL DEFAULT '[]'::jsonb,
    relation_types        JSONB           NOT NULL DEFAULT '[]'::jsonb,
    constraints           JSONB           NOT NULL DEFAULT '[]'::jsonb,
    disambiguation        JSONB           NOT NULL DEFAULT '{"case_insensitive": true, "alias_merge": true}'::jsonb,
    prompt_schema         JSONB           NOT NULL DEFAULT '{}'::jsonb,
    schema_mode           VARCHAR(32)     NOT NULL DEFAULT 'template_seeded',
    sync_status           VARCHAR(32)     NOT NULL DEFAULT 'synced',
    edited_at             TIMESTAMPTZ,
    edited_by             VARCHAR(128),
    status                VARCHAR(32)     NOT NULL DEFAULT 'active',
    compiled_at           TIMESTAMPTZ     NOT NULL DEFAULT now(),
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, knowledge_base_id)
);
CREATE INDEX IF NOT EXISTS idx_ocs_tenant_kb
    ON knowledge_base.ontology_compiled_schemas (tenant_id, knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_ocs_source
    ON knowledge_base.ontology_compiled_schemas (tenant_id, template_domain_id, template_scenario_id, source_hash);






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

COMMENT ON TABLE knowledge_base.knowledge_parser_settings IS 'Knowledge parser settings table.';
COMMENT ON COLUMN knowledge_base.knowledge_parser_settings.parser_config_id IS 'Parser config id column on knowledge_base.knowledge_parser_settings.';
COMMENT ON COLUMN knowledge_base.knowledge_parser_settings.prompt_template_id IS 'Prompt template id column on knowledge_base.knowledge_parser_settings.';
COMMENT ON COLUMN knowledge_base.knowledge_parser_settings.summary_template_id IS 'Summary template id column on knowledge_base.knowledge_parser_settings.';
COMMENT ON COLUMN knowledge_base.knowledge_parser_settings.tag_template_id IS 'Tag template id column on knowledge_base.knowledge_parser_settings.';




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
COMMENT ON TABLE knowledge_base.folders IS 'Folders table.';

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
