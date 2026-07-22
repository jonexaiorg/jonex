
CREATE SCHEMA IF NOT EXISTS platform;
CREATE SCHEMA IF NOT EXISTS knowledge_base;
CREATE SCHEMA IF NOT EXISTS ontology;

CREATE TABLE IF NOT EXISTS platform.tenants (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status SMALLINT DEFAULT 1,
    plan_type VARCHAR(32) DEFAULT 'free',
    expire_time TIMESTAMP,
    quota_config JSONB,
    extra_config JSONB,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS platform.api_keys (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    api_key VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(255),
    description TEXT,
    status SMALLINT DEFAULT 1,
    rate_limit INTEGER DEFAULT 100,
    expire_time TIMESTAMP,
    last_used_at TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);

CREATE INDEX idx_api_keys_tenant ON platform.api_keys(tenant_id);
CREATE INDEX idx_api_keys_key ON platform.api_keys(api_key);

CREATE TABLE IF NOT EXISTS platform.users (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default_tenant',
    username VARCHAR(128) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(32) NOT NULL DEFAULT 'user',
    status SMALLINT DEFAULT 1,
    last_login_at TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0,
    UNIQUE(tenant_id, username)
);

CREATE INDEX idx_users_tenant ON platform.users(tenant_id);
CREATE INDEX idx_users_username ON platform.users(tenant_id, username);

CREATE TABLE IF NOT EXISTS platform.login_tickets (
    id BIGSERIAL PRIMARY KEY,
    ticket_hash VARCHAR(128) NOT NULL UNIQUE,
    tenant_id VARCHAR(64) NOT NULL,
    user_id BIGINT NOT NULL,
    app_id VARCHAR(64) NOT NULL,
    redirect_uri VARCHAR(1024) NOT NULL,
    state VARCHAR(256),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    client_ip VARCHAR(64),
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_login_tickets_hash
    ON platform.login_tickets(ticket_hash);

CREATE INDEX IF NOT EXISTS idx_login_tickets_expires
    ON platform.login_tickets(expires_at);

CREATE INDEX IF NOT EXISTS idx_login_tickets_app_redirect
    ON platform.login_tickets(app_id, redirect_uri);

CREATE TABLE IF NOT EXISTS platform.usage_metrics (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    capability_id VARCHAR(128) NOT NULL,
    request_id VARCHAR(128) NOT NULL UNIQUE,
    user_id VARCHAR(64),
    invocation_count INTEGER DEFAULT 1,
    tokens_used INTEGER DEFAULT 0,
    processing_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_tenant ON platform.usage_metrics(tenant_id);
CREATE INDEX idx_usage_capability ON platform.usage_metrics(capability_id);
CREATE INDEX idx_usage_time ON platform.usage_metrics(request_time);

CREATE TABLE IF NOT EXISTS knowledge_base.knowledge_documents (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    file_name VARCHAR(512) NOT NULL,
    file_path VARCHAR(1024) NOT NULL,
    file_size BIGINT DEFAULT 0,
    mime_type VARCHAR(128),
    status VARCHAR(32) DEFAULT 'pending' NOT NULL,
    rag_task_id VARCHAR(64),
    rag_doc_ids JSONB DEFAULT '[]'::jsonb,
    error_message TEXT,
    ontology_status VARCHAR(32) DEFAULT 'pending' NOT NULL,
    ontology_error TEXT,
    ontology_retry_count INTEGER DEFAULT 0,
    extra_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_kb_doc_tenant ON knowledge_base.knowledge_documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_kb_doc_status ON knowledge_base.knowledge_documents(status);
CREATE INDEX IF NOT EXISTS idx_kb_doc_created ON knowledge_base.knowledge_documents(created_at DESC);

CREATE TABLE IF NOT EXISTS knowledge_base.knowledge_search_history (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    query TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    domain_id VARCHAR(128) NOT NULL DEFAULT 'all',
    domain_name VARCHAR(128),
    mode VARCHAR(32) NOT NULL DEFAULT 'hybrid',
    top_k INTEGER NOT NULL DEFAULT 5,
    status VARCHAR(32) NOT NULL DEFAULT 'done',
    answer_preview TEXT,
    reference_count INTEGER NOT NULL DEFAULT 0,
    result_count INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    extra_metadata JSONB DEFAULT '{}'::jsonb,
    searched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT uq_knowledge_search_history_query_domain
        UNIQUE (tenant_id, user_id, query_hash, domain_id)
);

CREATE INDEX IF NOT EXISTS idx_kb_hist_tenant_user_time
    ON knowledge_base.knowledge_search_history(tenant_id, user_id, searched_at);
CREATE INDEX IF NOT EXISTS idx_kb_hist_tenant_user_deleted
    ON knowledge_base.knowledge_search_history(tenant_id, user_id, is_deleted);

INSERT INTO platform.tenants (id, name, description, plan_type)
VALUES ('default_tenant', '默认租户', '系统默认租户', 'free')
ON CONFLICT (id) DO NOTHING;

INSERT INTO platform.api_keys (tenant_id, api_key, name, rate_limit)
VALUES ('default_tenant', 'jonex_test_key', '测试用 API Key', 1000)
ON CONFLICT (api_key) DO NOTHING;

INSERT INTO platform.users (tenant_id, username, password_hash, display_name, role)
VALUES ('default_tenant', 'admin',
        '$2b$12$IRcfNr1RSXcVINY.tBvnGefCYSiMdQLI/BaUk/ARNpVFzr0BVQhCG',
        '系统管理员', 'admin')
ON CONFLICT (tenant_id, username) DO NOTHING;

COMMENT ON SCHEMA platform IS '平台核心数据';
COMMENT ON SCHEMA knowledge_base IS '知识库业务层数据（CRUD + 状态机，与 LightRAG 内部存储分离）';
COMMENT ON TABLE platform.tenants IS '租户信息表';
COMMENT ON TABLE platform.api_keys IS 'API Key 管理表';
COMMENT ON TABLE platform.users IS '用户表';
COMMENT ON TABLE platform.login_tickets IS '一次性登录票据表（跨域 ticket/code 交换，只存 hash 不存明文）';
COMMENT ON TABLE platform.usage_metrics IS '调用计量表';
COMMENT ON TABLE knowledge_base.knowledge_documents IS '知识库文档元数据表（业务层独有，含状态机和 RAG 对账字段）';
COMMENT ON TABLE knowledge_base.knowledge_search_history IS '知识检索历史表（按 tenant+user+query+domain 去重，软删除）';
