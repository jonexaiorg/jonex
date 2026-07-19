









CREATE TABLE IF NOT EXISTS platform.tenants (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status SMALLINT DEFAULT 1,
    plan_type VARCHAR(32) DEFAULT 'free',
    expire_time TIMESTAMP,
    quota_config JSONB,
    extra_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON platform.api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON platform.api_keys(api_key);


CREATE TABLE IF NOT EXISTS platform.users (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    username VARCHAR(128) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(32) NOT NULL DEFAULT 'user',
    status SMALLINT DEFAULT 1,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0,
    UNIQUE(tenant_id, username)
);

CREATE INDEX IF NOT EXISTS idx_users_tenant ON platform.users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON platform.users(tenant_id, username);


CREATE TABLE IF NOT EXISTS platform.login_tickets (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    ticket_hash VARCHAR(128) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    app_id VARCHAR(64) NOT NULL,
    redirect_uri VARCHAR(1024) NOT NULL,
    state VARCHAR(256),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    client_ip VARCHAR(64),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_login_tickets_tenant ON platform.login_tickets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_login_tickets_hash ON platform.login_tickets(ticket_hash);
CREATE INDEX IF NOT EXISTS idx_login_tickets_expires ON platform.login_tickets(expires_at);
CREATE INDEX IF NOT EXISTS idx_login_tickets_app_redirect ON platform.login_tickets(app_id, redirect_uri);





CREATE TABLE IF NOT EXISTS platform.roles (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    description VARCHAR(512),
    is_system SMALLINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_roles_tenant ON platform.roles(tenant_id);


CREATE TABLE IF NOT EXISTS platform.permissions (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    resource VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL,
    description VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS platform.role_permissions (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rp_tenant ON platform.role_permissions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rp_role ON platform.role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_rp_perm ON platform.role_permissions(permission_id);


CREATE TABLE IF NOT EXISTS platform.user_roles (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ur_tenant ON platform.user_roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ur_user ON platform.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_ur_role ON platform.user_roles(role_id);


CREATE TABLE IF NOT EXISTS platform.menus (
    id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT DEFAULT 0,
    name VARCHAR(128) NOT NULL,
    path VARCHAR(256),
    icon VARCHAR(128),
    app_id BIGINT,
    sort_order SMALLINT DEFAULT 0,
    visible SMALLINT DEFAULT 1,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);


CREATE TABLE IF NOT EXISTS platform.applications (
    id BIGSERIAL PRIMARY KEY,
    app_code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    entry_path VARCHAR(256),
    icon VARCHAR(128),
    description VARCHAR(512),
    status SMALLINT DEFAULT 1,
    sort_order SMALLINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);


CREATE TABLE IF NOT EXISTS platform.application_routes (
    id BIGSERIAL PRIMARY KEY,
    app_id BIGINT NOT NULL,
    route_path VARCHAR(256) NOT NULL,
    title VARCHAR(128),
    permission_code VARCHAR(128),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ar_app ON platform.application_routes(app_id);


CREATE TABLE IF NOT EXISTS platform.system_configs (
    id BIGSERIAL PRIMARY KEY,
    config_group VARCHAR(64) NOT NULL,
    config_key VARCHAR(128) NOT NULL UNIQUE,
    config_value TEXT,
    value_type VARCHAR(32) DEFAULT 'string',
    description VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS platform.audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64),
    user_id BIGINT,
    username VARCHAR(128),
    ip VARCHAR(64),
    action VARCHAR(64) NOT NULL,
    resource VARCHAR(128),
    resource_id VARCHAR(64),
    status_code SMALLINT,
    duration_ms BIGINT,
    request_params JSONB,
    response_body JSONB,
    error_stack TEXT,
    trace_id VARCHAR(128),

    log_type VARCHAR(32),
    service_name VARCHAR(64),
    outcome VARCHAR(16),
    log_level VARCHAR(16),
    error_message TEXT,
    method VARCHAR(8),
    path VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant ON platform.audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON platform.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON platform.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_time ON platform.audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_type ON platform.audit_logs(log_type);
CREATE INDEX IF NOT EXISTS idx_audit_service ON platform.audit_logs(service_name);
CREATE INDEX IF NOT EXISTS idx_audit_outcome ON platform.audit_logs(outcome);

CREATE INDEX IF NOT EXISTS idx_audit_tenant_type_time
    ON platform.audit_logs(tenant_id, log_type, created_at DESC);


CREATE TABLE IF NOT EXISTS platform.task_schedules (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    task_type VARCHAR(64) NOT NULL,
    cron_expr VARCHAR(128),
    status SMALLINT DEFAULT 1,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    config_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_task_tenant ON platform.task_schedules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_task_type ON platform.task_schedules(task_type);







CREATE TABLE IF NOT EXISTS metering.llm_usage_log (
    id               BIGSERIAL PRIMARY KEY,
    request_id       VARCHAR(64) UNIQUE,
    trace_id         VARCHAR(64),
    tenant_id        VARCHAR(64) NOT NULL,
    user_id          VARCHAR(64),
    scene            VARCHAR(64) NOT NULL,
    model            VARCHAR(128) NOT NULL,
    kb_id            VARCHAR(64),
    doc_id           VARCHAR(64),
    prompt_tokens    INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens     INTEGER DEFAULT 0,
    latency_ms       INTEGER,
    is_stream        BOOLEAN DEFAULT false,
    is_estimated     BOOLEAN DEFAULT false,
    call_count       INTEGER NOT NULL DEFAULT 1,
    created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_tenant_time
    ON metering.llm_usage_log (tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_usage_scene
    ON metering.llm_usage_log (scene);
CREATE INDEX IF NOT EXISTS idx_llm_usage_trace
    ON metering.llm_usage_log (trace_id);




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
