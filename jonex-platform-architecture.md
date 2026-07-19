# Jonex Platform System Architecture

> Updated: 2026-07-16
> Document version: 0.4.0
> Document role: stable architecture reference; historical execution records are not public architecture contracts.


## 1. Project Positioning

Jonex Platform is a pluggable, multi-tenant AI capability platform. It consists of a frontend workspace, a unified API entry point, a Sidecar governance layer, multiple capability services, atomic RAG capabilities, and infrastructure components.

The platform is not a single business application. It is a common engineering foundation for continuously onboarding new applications, business domains, and AI capabilities.

### 1.1 Core Goals

| Goal | Description |
|---|---|
| Unified entry for multiple applications | `frontend-gateway` aggregates the shell, core business, platform management, and ecosystem management applications. |
| Independently evolving capability services | `platform`, `business_domain`, `knowledge_base`, and `atomic-rag` can be deployed and scaled independently. |
| Consistent engineering standards | Backend work follows [backend-development-standard.md](backend-development-standard.md); frontend work follows [frontend-development-standard.md](frontend-development-standard.md). |
| Explicit tenant isolation | Business data must use a valid `tenant_id`; default-tenant fallback is forbidden. |
| Thin entry points, substantial services | Gateway performs HTTP aggregation; Sidecar performs authentication, governance, and proxying; business rules belong in capability services. |
| Governable capability system | Capabilities are layered as atomic, domain, and business capabilities and are invoked through a common contract. |

### 1.2 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | pnpm workspace, React, TypeScript, Vite, Ant Design, shared theme package, and shell-sdk |
| Frontend entry | Nginx `frontend-gateway`, aggregating static assets and proxying `/api/**` |
| Backend framework | Python 3.12, FastAPI, Uvicorn, Pydantic v1 compatibility mode |
| Data access | SQLAlchemy 2.0 async, asyncpg, and the shared `BaseRepository` |
| Database | PostgreSQL 15 with `platform`, `business_domain`, `knowledge_base`, and `metering` schemas |
| Cache and discovery | Redis 7 for service registration, heartbeats, task state, and caching |
| RAG and vectors | atomic-rag, LightRAG, Milvus 2.5, etcd 3.5, and MinIO |
| Object storage | COS in production or the local filesystem as a development fallback, through the `ObjectStorage` abstraction |
| Ontology graph | TBox YAML, Stage 4 ontology extraction, Neo4j ABox storage, and enhanced search |
| Deployment | Docker, Docker Compose, multiple ports in development, and port 80 only in production |

## 2. Overall Architecture

### 2.1 System View

```text
User browser
  |
  v
frontend-gateway (Nginx, 80)
  |-- shell / core-business / platform-management / ecosystem-management
  |-- /api/** -> API Gateway (8000)
                 |
                 v
              Sidecar (8001)
                 |-- authentication / tenant context / internal JWTs
                 |-- metering / rate limiting / circuit-breaker hooks
                 |-- capability proxying
                 |
                 +--> platform-service (8006)
                 +--> business-domain-service (8005)
                 +--> knowledge-base-service (8003)
                 +--> atomic-rag (8004) -> lightrag (9621)
                                            -> llm-gateway (8787)  <- unified LLM/Embedding egress
                                               -> TokenHub / Ollama and other upstreams

PostgreSQL / Redis / Neo4j / Milvus / etcd / MinIO
```

### 2.2 Exposure Principles

| Mode | External ports | Description |
|---|---|---|
| Production | `frontend-gateway:80` | The only browser entry point; all other backend, capability, and infrastructure services are container-internal. |
| Development | Applications: `80`, `8000`, `8001`, `8003`, `8004`, `8005`, `8006`, `8787`, `9621`; dependencies: `5432`, `6379`, `9000/9001`, `19530/9091`, `7474/7687` | Exposed through Compose overrides; the production baseline does not publish debugging ports. |

Production browsers enter through `frontend-gateway` only. Frontend business requests use `/api/v1/**`, which Gateway forwards to Sidecar before Sidecar invokes a capability service.

### 2.3 Service Responsibilities

| Service | Dev port | Responsibility |
|---|---:|---|
| `frontend-gateway` | `80` | Aggregates frontend assets, proxies `/api/**`, and sets basic security headers and caching rules. |
| `api_gateway` | `8000` | External API aggregation, CORS, request IDs, basic logging, and protocol adaptation. |
| `sidecar` | `8001` | Authentication, tenant context, internal JWTs, governance hooks, capability proxying, and streaming proxying. |
| `llm-gateway` | `8787` | OpenAI-compatible proxy, unified LLM/Embedding egress, and token metering through Redis and PostgreSQL. |
| `knowledge-base-service` | `8003` | Knowledge bases, document state, RAG integration, ontology graph, enhanced search, and data sources. |
| `atomic-rag` | `8004` | Multimodal parsing, RAG tasks, LightRAG calls, and `ontology_data` production. |
| `business-domain-service` | `8005` | Domain spaces, services, engines, adapters, skills, and templates. |
| `platform-service` | `8006` | Login, RBAC, menus, application registration, auditing, and tasks. |
| `lightrag` | `9621` | Document indexing, RAG retrieval, generation, and WebUI. |
| `neo4j` | `7474`/`7687` dev | Ontology ABox storage with `:OntologyEntity` nodes and `[:ONT_REL]` relationships. |

### 2.4 Call Chain

```text
Frontend
  -> API Gateway
    -> Sidecar
      -> Capability Service
        -> Service
          -> Repository
            -> PostgreSQL / Redis / Neo4j / External Engine

All LLM/Embedding calls go through llm-gateway:
  LightRAG / ontology_extractor / ontology_llm / other LLM callers
    -> llm-gateway (8787)
      -> Token Swap (validate internal token -> inject upstream key)
      -> Metering (Redis realtime + PostgreSQL batches + structured logs)
      -> Upstream LLM (TokenHub / Ollama and other providers)
```

This is the default structure for new backend development. Historical flat `service.py` / `dao.py` / `models.py` layouts must not be used as templates for new features.

## 3. Frontend Architecture

### 3.1 Frontend Workspace

`frontends/` is a pnpm workspace monorepo containing four applications and shared packages.

| Directory | Responsibility |
|---|---|
| `frontends/shell` | Authenticated workspace, application navigation, route guards, application loading, and shared context. |
| `frontends/core-business` | Core business sub-application and business-domain entry point. |
| `frontends/platform-management` | User, role, menu, application, permission, audit, and task screens. |
| `frontends/ecosystem-management` | Ecosystem onboarding and external integration screens. |
| `frontends/dev-gateway` | Local unified entry point proxying `/api`, remote assets, and standalone paths to development servers. |
| `frontends/shared/platform-theme` | Shared theme, Ant Design theme, CSS tokens, and layout styles. |
| `frontends/shared/shell-sdk` | Authentication bootstrap, auth storage, redirects, standalone shell context, and shared types. |
| `frontends/shared/i18n-resources` | Shared Chinese and English locale resources and types. |

### 3.2 Frontend Entry and Routing

`frontend-gateway`:

- Aggregates the four frontend build outputs.
- Provides SPA fallback for the shell and sub-applications.
- Proxies `/api/**` to API Gateway.
- Applies common security headers, caching rules, and static-asset access rules.

Frontend route boundaries:

| Route | Owner |
|---|---|
| `/` and shell routes | `frontends/shell` |
| `/core-business/**` | `frontends/core-business` |
| `/platform-management/**` | `frontends/platform-management` |
| `/ecosystem-management/**` | `frontends/ecosystem-management` |
| `/api/**` | Proxied to API Gateway |

The platform backend application registry is the single source of truth for production applications. Shell reads the list from `GET /api/v1/platform/frontend/apps`; the static `frontends/shell/public/app-manifest.json` is only a local-development fallback.

### 3.3 Frontend Boundaries

- Shell owns shared authentication state, navigation, application loading, and cross-application context.
- Each sub-application owns its business UI and does not own global authentication, global navigation, or platform-wide state.
- Shared themes, authentication storage, and redirect handling belong in `frontends/shared`.
- New sub-applications must integrate with Shell and `frontend-gateway` instead of adding another external entry point.
- Frontends use Gateway paths by default and must not bypass Sidecar to call backend services directly.

## 4. Backend Architecture

### 4.1 API Gateway

Code location: `api_gateway/`

Gateway is the HTTP route aggregation layer. Its responsibilities are:

- Mount `/api/v1/auth`, `/api/v1/platform`, `/api/v1/knowledge-base`, `/api/v1/business-domain`, TCADP, and related routes.
- Handle CORS, request IDs, basic logging, and common exceptions.
- Forward business requests to Sidecar.
- Adapt protocol details for file uploads, streaming queries, and similar entry points.

Gateway must not implement business CRUD, assemble business data, inject a default tenant, or replace capability-service business authorization.

#### 4.1.1 Proxy Modes and Routing Rules

Gateway -> Sidecar -> capability services support two proxy modes. Both pass through Sidecar governance for authentication, tenancy, metering, rate limiting, and circuit breaking, but their contracts differ:

| Mode | Representative service | Sidecar entry | Business route location | Request mapping |
|---|---|---|---|---|
| REST passthrough | `platform` | `/platform/{path:path}`, `/auth/*` | REST routes in the target container | Method, path, query, and body are passed through |
| Invoke action contract | `business_domain`, `knowledge_base` | `/invoke`, `/invoke/stream` | Capability `_build_dispatch` action map and `execute()` | Fixed POST with `{capability_id, payload:{action,data}, tenant_id}` |

Routing rules:

- **Keep platform as REST passthrough.** It handles authentication bootstrap (`/auth/login` without a token or tenant) and tenant-free shared platform metadata (`Application`, `Menu`, `Permission`, and `SystemConfig` through `*_shared` methods). The invoke contract requires authentication and a tenant, so it would block those endpoints.
- **Business capabilities use the invoke action contract.** Tenant business capabilities such as `business_domain` and `knowledge_base` use `/invoke`; action dispatch makes metering, rate limiting, circuit breaking, and streaming dimensions explicit.
- Capability containers may retain a parallel REST `api/` layer for direct debugging through `register_routes`, but the Gateway path does not use it. `execute()` through the invoke contract is the authoritative path.
- The controlled exception is the knowledge-base `api_push` path in section 6.4: a public endpoint without a user JWT, authenticated by a self-contained ingest key that resolves the real tenant.

### 4.2 Sidecar

Code location: `jonex_core/sidecar/`

Sidecar is the governance entry point for capability calls. It:

- Validates user JWTs and API keys. Development test tokens are accepted only in `dev` / `test` and must be rejected in `uat` / `prod`.
- Extracts and normalizes tenant context.
- Validates consistency between JWT claims and `X-Tenant-ID`.
- Issues internal service JWTs.
- Runs metering, rate-limit, and circuit-breaker hooks.
- Proxies by capability ID to the target capability service.
- Supports ordinary calls, standard streaming calls, and the RAG-specific streaming proxy.

Core endpoints:

| Endpoint | Description |
|---|---|
| `/health` | Sidecar health check. |
| `/capabilities` | Capability list. |
| `/auth/login`, `/auth/me`, `/auth/refresh` | Authentication proxies or stateless authentication endpoints. |
| `/platform/{path:path}` | Platform service reverse proxy. |
| `/invoke` | Standard capability invocation. |
| `/invoke/stream` | Standard streaming capability invocation. |
| `/invoke/stream/rag` | Streaming RAG query proxy. |

Static Sidecar fallback configuration:

| Service key | Configuration |
|---|---|
| `platform` | `PLATFORM_URL` |
| `business_domain` | `BUSINESS_DOMAIN_URL` |
| `knowledge_base` | `KNOWLEDGE_BASE_URL` |
| `rag.lightrag` | `ATOMIC_RAG_URL` |

### 4.3 Capability Services

Each business domain under `capabilities/` is an independent capability service. The standard structure is:

```text
capabilities/{capability_name}/
├── api/             # FastAPI routes: parse input, extract tenant, call services
├── models/          # SQLAlchemy entities
├── repository/      # Data access, extending BaseRepository
├── services/        # Business rules
├── dtos/            # Pydantic v1 request/response models
├── contracts/       # Public contracts, capability declarations, and integration contracts
├── integrations/    # External-system adapters
└── workers/         # Background tasks
```

| Service | Main responsibilities |
|---|---|
| `platform` | Login, users, roles, permissions, menus, applications, auditing, and scheduled tasks. |
| `business_domain` | Domain spaces, domain services, engines, adapters, skills, and templates. |
| `knowledge_base` | Knowledge bases, document state, search history, RAG integration, Neo4j ontology graph, enhanced search, and data sources. |

## 5. Capability System

### 5.1 Capability Layers

```text
Business Capability
  Orchestrates domain and atomic capabilities for product features and sellable capabilities

Domain Capability
  Reuses scenario-level capabilities such as text RAG, semantic search, and summarization

Atomic Capability
  Wraps one technical component such as an LLM, vector store, ASR, RAG engine, or multimodal parser
```

Capability IDs use `{kind}.{name}.v{major}`:

| Example | Meaning |
|---|---|
| `business.knowledge_base.v1` | Knowledge-base business capability. |
| `business.business_domain.v1` | Business-domain capability. |
| `atomic.rag.lightrag.v1` | LightRAG-based atomic RAG capability. |

### 5.2 Capability SDK

Code location: `jonex_core/capability/`

| Module | Responsibility |
|---|---|
| `base.py` | `BaseCapability` abstract base class. |
| `models.py` | `CapabilityMetadata`, `CapabilityRequest`, `CapabilityResponse`, and `CapabilityType`. |
| `registry.py` | Capability registry. |
| `locator.py` | Reads the runtime manifest and selects local, remote, or mock invocation. |
| `atomic/` | LLM, vector, ASR, RAG, and ontology-extraction clients and adapters. |
| `domain/` | Scenario-oriented domain capabilities. |

### 5.3 Ontology Knowledge Engine

The knowledge-base capability combines RAG with an ontology engine. The ontology layer models strongly typed entities, relationships, and attributes as business ABox data outside the internal LightRAG graph.

Core design:

- TBox configuration lives in `deploy/config/ontology/default.yaml`.
- atomic-rag performs Stage 4 ontology extraction after parsing and RAG ingestion and produces `ontology_data`.
- atomic-rag does not depend directly on Neo4j; it places extraction results in the task result.
- knowledge-base reads `ontology_data` and writes Neo4j through `OntologyGraphRepository`.
- Neo4j represents ABox data with `:OntologyEntity` nodes and `[:ONT_REL]` relationships.
- Ontology data is isolated and merged by `tenant_id`, `knowledge_base_id`, entity type, and canonical name.
- If Neo4j is unavailable, knowledge-base falls back to ordinary RAG without blocking the basic document and retrieval flows.

The knowledge-base document state machine is managed by `DocStatus` in `capabilities/knowledge_base/models/document.py`:

```text
pending -> parsing -> ready
                \-> failed
ready -> deleting -> deleted
              \-> failed
```

`capabilities/knowledge_base/capability.py` starts a 30-second asynchronous reconciliation loop implemented by `ReconciliationService`:

| atomic-rag state | knowledge-base action |
|---|---|
| `completed` | Move the document to `ready` and store `rag_doc_ids`; if ontology data exists, write Neo4j before updating PostgreSQL ontology state. |
| `failed` | Move the document to `failed` and store `error_message`. |
| `not_found` | Try to recover `rag_doc_ids` through the LightRAG storage fallback; if recovery fails, mark the document failed and ask the user to delete and re-upload it. |
| `processing` / `pending` | Keep `parsing` and record only DEBUG progress logs. |

The business document table is separate from LightRAG internal storage and is mapped through `rag_task_id` and `rag_doc_ids`.

atomic-rag persists asynchronous task state in Redis:

- Key format: `rag:task:{uuid}`.
- TTL: seven days; terminal state is reconciled back to PostgreSQL by knowledge-base.
- `LightRAGAdapter._cleanup_orphan_tasks()` scans `rag:task:*` at startup and marks `pending` and `processing` tasks as failed, preventing a container restart from losing in-memory work and leaving documents stuck in `parsing`.
- Task fields include `task_id`, `tenant_id`, `file_path`, `output_dir`, `status`, `progress`, `lightrag_doc_ids`, and `error`.

The ontology state machine is managed by `OntologyStatus`:

```text
pending -> extracting -> ready
                   \-> failed
```

- `pending`: parsing is complete but ontology extraction has not run, or there are no candidate entities.
- `extracting`: ontology extraction is in progress.
- `ready`: extraction succeeded and data was written to Neo4j through Cypher `MERGE`.
- `failed`: extraction failed and the reason is stored in `ontology_error`.

`ReconciliationService.reconcile_ontology()` scans `pending`, `failed`, and `extracting` documents and triggers retries through atomic-rag's `retry_ontology_extract`, with a maximum of three attempts.

Complete ingestion path:

```text
Upload to local storage / COS presigned upload
  -> Download from COS when storage_backend=cos
  -> Stage 1: MinerU parsing
  -> Stage 2: video/audio transcription:
       - video + MPS_ENABLED + COS storage: Tencent Cloud MPS video analysis
         replaces ffmpeg + whisper ASR; failure becomes failed without fallback;
         parse_video metadata blocks are retained
       - other video/audio: ffmpeg extracts audio + whisper ASR with timestamped segments
  -> Stage 3: push text to LightRAG (embedding + graph extraction with file_source anchors)
  -> Stage 4: ontology extraction when ONTOLOGY_EXTRACT_ENABLED=true
       -> LLM classifies, disambiguates, and enriches attributes according to the TBox
       -> task result stores ontology_data
       -> knowledge-base reconciliation writes Neo4j
```

Neo4j schema is initialized idempotently by `ensure_ontology_schema()` in `jonex_core/common/neo4j_client.py` when knowledge-base starts:

| Name | Type | Purpose |
|---|---|---|
| `ont_entity_key` | Composite uniqueness constraint | Makes entity `MERGE` idempotent for `(tenant_id, kb_id, entity_type, canonical_name)`. |
| `ont_entity_ft` | Full-text index | Covers `canonical_name` and `aliases_text` for Chinese and multilingual entity search. |

Enhanced search path:

```text
User query
  -> SearchService.query_with_ontology
  -> Neo4j full-text search for candidate entities
  -> read one-hop facts when score >= ONTOLOGY_ROUTE_SCORE_MIN
  -> LLM answers from facts
  -> ordinary RAG fallback when facts are insufficient
```

The P0 orchestration reasoning chain is implemented through `ReasoningCollector`. Ontology matching, routing, neighborhood evidence, LLM answering, RAG fallback, and multi-answer fusion are collected structurally and returned in the `reasoning` field. It is disabled by default through `with_reasoning=False` and protected by both a request-level switch and the process-level `REASONING_TRACE_ENABLED` flag.

Parse-result overlay:

- `ParseResultService` reads atomic-rag parse results.
- Entity lists may receive Neo4j type overlays and an `ontology_typed` marker.
- Relation lists may receive Neo4j relation-type overlays.
- Frontends can display both raw parser output and the structured ontology view.

### 5.4 Knowledge-Base Data Sources

In addition to file upload, knowledge-base supports multiple data-source modes. KB-scoped instances are registered in `knowledge_base.knowledge_data_sources`, and each instance can reference a method definition in `business_domain.data_access_methods`:

| `access_type` | Direction | Description |
|---|---|---|
| `api` | Outbound pull | Pull documents from an external REST API returning JSON lists through `services/ingestion/api_adapter.py`. |
| `storage` | Outbound pull | Pull documents from an external MinIO/S3 bucket through `services/ingestion/storage_adapter.py`. |
| `api_push` | Inbound push | Expose an OpenAPI endpoint for external systems to push documents with an ingest key. |
| `file` | Upload | Existing file-upload path. |

- Outbound synchronization (`api`/`storage`) pulls bytes, stores them through `get_object_storage().put_bytes()`, and reuses `DocumentService.upload_document` and the common parsing/ontology pipeline.
- An external customer MinIO/S3 bucket is the source; the platform object-storage backend is the ingestion destination.
- The platform supports COS in production and local filesystem storage in development, selected by `OBJECT_STORAGE_BACKEND`.
- External API tokens and S3 access keys are encrypted with Fernet through `jonex_core/common/crypto.py` and masked as `***` in list/detail APIs.
- Phase-one scope is immediate synchronization only; scheduled workers are future work. Storage supports MinIO/S3 and APIs support REST+JSON.
- Backend code is under `capabilities/knowledge_base/services/ingestion/`; the frontend entry point is `frontends/core-business/src/pages/DomainKnowledgeDataSource/`.

## 6. Tenancy and Authentication

### 6.1 Tenant Principles

The tenant standard is defined in [backend-development-standard.md](backend-development-standard.md). The architecture-level constraints are:

- Every business record must have a valid `tenant_id`.
- Forbidden tenants are the empty string, `default`, `default_tenant`, and `system`.
- Ordinary external business API bodies must not declare a business `tenant_id`.
- `tenant_id` in a Sidecar `/invoke` body is only a consistency check and is not a new tenant source.
- An API key identifies the caller, not the business tenant; tenant isolation additionally requires a valid `X-Tenant-ID`.
- Sidecar parses user JWTs, and downstream services receive normalized `X-Tenant-ID`.
- Local development and demo data use `tenant_jonex_demo`.

### 6.2 Tenant Extraction Flow

```text
Ordinary business request
  -> Gateway validates that Authorization exists
  -> In dev/test only, Gateway may extract tenant from a test token; otherwise it uses authenticated context and X-Tenant-ID
  -> Sidecar parses the formal JWT / API key / X-Tenant-ID and validates consistency
  -> Sidecar forwards normalized X-Tenant-ID downstream
  -> Capability route calls extract_tenant_id(request) again
  -> Service / Repository calls require_tenant()
```

Production invariant: Gateway and Sidecar must reject `jonex_test_*` tokens in `uat` and `prod`. This is an enforced authentication rule with automated coverage, not an operational convention.

Login is an authentication bootstrap flow and does not use the ordinary business request's mandatory tenant precondition:

```text
POST /api/v1/auth/login
  -> Gateway forwards the body and optional X-Tenant-ID unchanged
  -> Sidecar allows a tenant-less proxy to platform
  -> Platform AuthService logs in by exact X-Tenant-ID + username
  -> Without X-Tenant-ID, tenant_id is inferred only when the username has one active account
  -> Successful login writes user.tenant_id into the JWT; later requests use the JWT tenant as authority
```

If the same username exists in multiple active tenants, the user must select a tenant and retry. The system must not choose randomly or fall back to a default tenant.

### 6.3 Shared Platform Data and Tenant Data

| Type | Examples | Access rule |
|---|---|---|
| Shared platform metadata | `Application`, `ApplicationRoute`, `Menu`, `Permission`, `SystemConfig` | No `tenant_id`; repositories use `*_shared` methods. |
| Tenant runtime data | `User`, `Role`, `UserRole`, `RolePermission`, `AuditLog`, `TaskSchedule`, `LoginTicket` | Must contain a valid `tenant_id`. |

Business capability data is tenant data by default, including `business_domain`, `knowledge_base`, and new business capabilities.

### 6.4 Inbound Push Authentication (`api_push` Exception)

`POST /api/v1/knowledge-base/ingest/{ds_id}` is a public external-system endpoint. It does not use a platform user JWT; it is a controlled exception in the tenant extraction flow:

- The external system sends `X-Ingest-Key`. The self-contained key format is `yxk_<base64(tenant|kb|ds|random)>.<HMAC signature>` and contains the tenant, knowledge base, and data-source identity; only a signature hash is stored in the database.
- Gateway uses `decode_ingest_key` to extract the real `tenant_id`, verifies that the key `ds_id` matches the URL, and passes it through Sidecar `invoke`. For the `ingest_push` system action in `_SYSTEM_INVOKE_ACTIONS`, Sidecar uses that real tenant and never falls back to `system`; rate limiting, metering, and auditing still use the real tenant.
- The capability's `ingest_push` action uses `verify_ingest_key` as the authoritative signature check and cross-checks the tenant, knowledge base, and data source records.
- The path still goes through Gateway -> Sidecar, preserving the rules that frontends do not call capabilities directly and default tenants are forbidden.

## 7. Data and Infrastructure

### 7.1 PostgreSQL

PostgreSQL is the platform's primary data store:

| Schema | Ownership |
|---|---|
| `platform` | Platform management, authentication, RBAC, menus, applications, auditing, and tasks. |
| `business_domain` | Business domains, domain services, engines, adapters, skills, and templates. |
| `knowledge_base` | Knowledge bases, documents, parsing state, RAG associations, and data-source instances. |
| `metering` | LLM/Embedding token usage details in `llm_usage_log`, written by llm-gateway. `trace_id` groups a business request; unique `request_id` provides retry idempotency. Dimensions include tenant, user, scene, model, KB, and document. |

New persistent business entities should use mixins from `jonex_core/common/entity.py`:

- `TenantMixin`
- `TimestampMixin`
- `SoftDeleteMixin`
- `AuditMixin`

### 7.2 Redis

Redis is used for service registration and heartbeats, Sidecar and capability caches, RAG task state, and metering/rate-limit/circuit-breaker extension state.

### 7.3 RAG and Ontology Infrastructure

| Component | Purpose |
|---|---|
| `atomic-rag` | Multimodal document parsing, task persistence, LightRAG calls, and `ontology_data` production. |
| `lightrag` | Document indexing, RAG retrieval, generation, and WebUI. |
| `Neo4j` | Ontology ABox graph storage, entity full-text search, and neighborhood queries. |
| `Milvus` | Vector retrieval infrastructure. |
| `etcd` | Milvus metadata dependency. |
| `MinIO` | Milvus object-storage dependency. |

## 8. Code Structure

```text
jonex/
├── README.md                                      # Project entry point and documentation index
├── LICENSE                                        # Apache License 2.0
├── NOTICE / THIRD_PARTY_NOTICES.md                 # Project and bundled dependency attribution
├── .github/                                       # Issue and pull-request templates
├── CONTRIBUTING.md / SECURITY.md                  # Contribution and security reporting
├── backend-development-standard.md                # Backend capability-service standards
├── frontend-development-standard.md               # Frontend workspace and application standards
├── local-fullstack-debugging-guide.md             # Local integration and debugging guide
├── jonex-platform-architecture.md                 # Stable system architecture
├── Makefile / jonex.ps1                            # macOS/Linux and Windows operations entry points
├── pyproject.toml / requirements.txt               # Python project and dependency configuration
├── api_gateway/                                    # External API entry and route aggregation
├── jonex_core/                                     # Shared framework and infrastructure
│   ├── capability/                                 # Capability SDK and layered abstractions
│   │   ├── atomic/                                 # LLM, vector, ASR, RAG, and ontology adapters
│   │   └── domain/                                 # Scenario-level capabilities
│   ├── common/                                    # Config, database, repository, tenancy, cache, logging, Neo4j, storage
│   ├── discovery/                                 # Redis service discovery and heartbeats
│   ├── integrations/                              # External-system integrations
│   ├── security/                                  # Internal JWT and user authentication
│   ├── sidecar/                                   # Governance proxy and streaming proxy
│   └── llm_gateway/                               # OpenAI-compatible proxy and token metering
├── capabilities/                                  # Independently evolving business capabilities
│   ├── platform/                                  # Login, RBAC, menus, applications, auditing, tasks
│   ├── business_domain/                           # Domain spaces, services, engines, adapters, skills, templates
│   └── knowledge_base/                            # Knowledge bases, documents, RAG, ontology, and data sources
├── frontends/                                     # Four applications and shared packages
├── deploy/                                        # Docker, Nginx, databases, ontology config, and deployment docs
│   ├── config/                                    # Runtime and TBox configuration
│   ├── docker/                                    # Dockerfiles and build helpers
│   ├── nginx/                                     # Frontend gateway configuration
│   ├── postgres/                                  # Initialization and numbered migrations
│   ├── docker-compose.yml                         # Production Compose baseline
│   ├── docker-compose.override.yml                # Local Docker integration override
│   ├── docker-compose.debug.yml                   # Host-side backend/RAG debugging override
│   ├── start_capability.py                        # Generic capability-service entry point
│   ├── README.md                                  # Deployment guide
│   └── DEPLOYMENT_ARCHITECTURE.md                 # Detailed deployment architecture
├── tests/                                         # Unit, integration, and end-to-end tests
└── Reference/                                     # LightRAG/RAG-Anything source and upstream licenses
```

## 9. Configuration and Environment Variables

Core configuration sources:

- **Local debugging:** root `.env.local` for backend and atomic-rag, and `.env.rag.local` for LightRAG, loaded by VS Code `envFile` or local scripts.
- **Docker deployment:** `deploy/.env`, `deploy/.env.rag`, and Compose environment variables.
- **Application code:** `jonex_core/common/config.py` reads environment variables.

| Variable | Description |
|---|---|
| `ENV` | Runtime environment: `dev`, `test`, `uat`, or `prod`. |
| `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_NAME` | PostgreSQL connection. |
| `REDIS_URL`, `REDIS_HOST`, `REDIS_PORT` | Redis connection. |
| `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_DAYS` | User JWT configuration. |
| `JWT_INTERNAL_SECRET` | Internal service JWT secret. |
| `SIDECAR_URL` | Gateway-to-Sidecar address. |
| `SIDECAR_API_KEY` | Gateway-to-Sidecar service credential; it must be explicitly configured and rotated outside source control. |
| `PLATFORM_URL` | Sidecar-to-platform address. |
| `KNOWLEDGE_BASE_URL` | Sidecar-to-knowledge-base address. |
| `BUSINESS_DOMAIN_URL` | Sidecar-to-business-domain address. |
| `ATOMIC_RAG_URL` | Sidecar-to-atomic-rag address. |
| `LIGHTRAG_API_KEY` | API key used by atomic-rag to call LightRAG. |
| `CAPABILITY_RUNTIME_FILE` | Local, remote, and mock capability runtime manifest. |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | Neo4j connection configuration. |
| `ONTOLOGY_EXTRACT_ENABLED` | Enables Stage 4 ontology extraction. |
| `ONTOLOGY_SCHEMA_DIR` | TBox YAML directory. |
| `ONTOLOGY_ROUTE_SCORE_MIN` | Minimum score for routing enhanced search through ontology facts. |
| `REASONING_TRACE_ENABLED` | Process-level gate for orchestration reasoning; requests additionally use `with_reasoning`. |
| `DATA_SOURCE_SECRET_KEY` | Fernet key for encrypting external data-source credentials; in development it may be derived from `JWT_SECRET`. |
| `PUBLIC_API_BASE` | Public base URL used to build `api_push` ingest URLs. |
| `LLMGW_UPSTREAM_LLM_HOST` / `LLMGW_UPSTREAM_LLM_API_KEY` | Upstream LLM address and key; the key belongs only in the LLM Gateway. |
| `LLMGW_UPSTREAM_EMBED_HOST` / `LLMGW_UPSTREAM_EMBED_API_KEY` | Upstream Embedding address and key. |
| `LLMGW_INTERNAL_TOKENS` | Comma-separated internal token allowlist. |
| `LLMGW_METERING_ENABLED` | Enables token metering through Redis, PostgreSQL, and logs. |
| `LLMGW_PG_FLUSH_MAX_ROWS` / `LLMGW_PG_FLUSH_MAX_SECONDS` | PostgreSQL batch threshold and flush interval. |
| `OBJECT_STORAGE_BACKEND` | `cos` in production or `local` as the development fallback. |
| `COS_KEY_PREFIX` | COS object-key prefix; default `jonex`. |
| `COS_REGION` / `COS_SECRET_ID` / `COS_SECRET_KEY` / `COS_BUCKET` | COS region, credentials, and bucket. |
| `COS_PRESIGN_EXPIRES` | Presigned URL lifetime in seconds; default `900`. |

## 10. New-Feature Development Rules

New backend capabilities and backend features must follow [backend-development-standard.md](backend-development-standard.md). New frontend applications, pages, and features must follow [frontend-development-standard.md](frontend-development-standard.md).

### 10.1 Backend Layering

| Layer | Rule |
|---|---|
| Gateway route | Protocol entry and forwarding only; no business rules. |
| Capability route | Parse requests, extract tenant, and call a service. |
| Service | Sole owner of business rules, tenant validation, resource ownership, transactions, and exception conversion. |
| Repository | Extend `BaseRepository`; tenant-entity queries must include a valid tenant filter. |
| Model | Business entities normally extend the shared mixins. |
| DTO | External request/response models; do not expose ORM objects. |

### 10.2 Frontend Integration

New frontend applications must:

- Live in the `frontends/` workspace.
- Integrate `frontends/shared/platform-theme`.
- Reuse authentication state and redirects through `frontends/shared/shell-sdk`.
- Declare the application in the platform application registry; Shell reads it from `GET /api/v1/platform/frontend/apps`, with the static manifest used only as a local fallback.
- Add static routes and SPA fallback to `frontend-gateway` Nginx configuration.
- Call the backend through `/api/v1/**` rather than backend container ports.

### 10.3 Data Rules

- New business entities normally include `tenant_id`.
- Shared platform metadata must be explicitly listed as shared; otherwise treat it as tenant data.
- Do not add `default`, `default_tenant`, or `system` as business tenants.
- Local development and demo data use `tenant_jonex_demo`.
- New endpoints must not accept the business tenant from the request body.
- Custom SQL and repository queries must include explicit tenant and soft-delete conditions.

### 10.4 Ontology Rules

- Put TBox changes in `deploy/config/ontology/default.yaml`.
- atomic-rag produces ontology extraction results but does not write Neo4j directly.
- Neo4j writes, queries, deletion, and fallback strategy belong to knowledge-base.
- Enhanced search must preserve ordinary RAG fallback.
- Parse-result overlay may enhance presentation and search but must not destroy raw parser results.

## 11. Key Files

| Module | File | Purpose |
|---|---|---|
| Capability base | `jonex_core/capability/base.py` | Base class for capabilities and custom `register_routes()` hooks. |
| Capability registry | `jonex_core/capability/registry.py` | Global capability registration and routing. |
| Capability locator | `jonex_core/capability/locator.py` | Manifest-driven runtime mode and endpoint resolution. |
| Atomic capability base | `jonex_core/capability/atomic/base.py` | Base for LLM, vector, audio, and RAG capabilities. |
| Domain capability base | `jonex_core/capability/domain/base.py` | Base for capabilities orchestrating atomic capabilities. |
| RAG client factory | `jonex_core/capability/atomic/rag/client.py` | RAG client abstraction and REMOTE / LOCAL / MOCK factory. |
| Ontology registry | `jonex_core/capability/atomic/ontology/registry.py` | Loads, caches, and validates TBox schemas. |
| Ontology extractor | `jonex_core/capability/atomic/rag/ontology_extractor.py` | Stage 4 LLM ontology extraction, classification, disambiguation, and attribute enrichment. |
| Sidecar application | `jonex_core/sidecar/main.py` | Unified authenticated and metered API entry point. |
| Sidecar proxy | `jonex_core/sidecar/proxy.py` | Capability HTTP reverse and streaming proxy. |
| Service discovery | `jonex_core/discovery/registry.py` | Dynamic capability-service endpoint discovery. |
| Heartbeats | `jonex_core/discovery/heartbeat.py` | Heartbeat renewal management. |
| Internal authentication | `jonex_core/security/internal_auth.py` | Service-to-service JWT authentication. |
| User authentication | `jonex_core/security/user_auth.py` | bcrypt password hashing and user JWT issuance/verification. |
| API Gateway | `api_gateway/main.py` | Public API entry point and middleware. |
| LLM Gateway app | `jonex_core/llm_gateway/app.py` | FastAPI application factory and Token Swap middleware. |
| LLM Gateway routes | `jonex_core/llm_gateway/router.py` | `/v1/chat/completions`, `/v1/embeddings`, and `/metering/usage`. |
| LLM Gateway upstream | `jonex_core/llm_gateway/upstream.py` | Upstream host/key resolution and streaming/non-streaming forwarding. |
| LLM Gateway recorder | `jonex_core/llm_gateway/recorder.py` | Redis realtime, PostgreSQL batches, and structured logs. |
| LLM usage extraction | `jonex_core/llm_gateway/metering.py` | Extracts token usage from chat, embedding, and streaming responses. |
| LLM context | `jonex_core/llm_gateway/context.py` | Parses metering context from `X-Jonex-*` headers. |
| Capability startup | `deploy/start_capability.py` | Loads capability classes, registers discovery, and renews heartbeats. |
| Ontology repository | `capabilities/knowledge_base/repository/ontology_graph_repository.py` | Neo4j Cypher `MERGE`, full-text search, and neighborhood queries. |
| Neo4j client | `jonex_core/common/neo4j_client.py` | Async Neo4j singleton and schema initialization. |
| Ontology QA LLM | `jonex_core/common/ontology_llm.py` | Answers from graph facts through `answer_from_facts()`. |
| Entity mixins | `jonex_core/common/entity.py` | `TenantMixin`, `TimestampMixin`, `SoftDeleteMixin`, and `AuditMixin`. |
| Repository base | `jonex_core/common/repository.py` | `BaseRepository` with tenant isolation, soft deletion, and pagination. |
| Tenant utilities | `jonex_core/common/tenant.py` | `extract_tenant_id`, `require_tenant`, `TenantContext`, and `tenant_scope`. |
| Configuration | `jonex_core/common/config.py` | Application configuration management. |
| Database | `jonex_core/common/database.py` | Async SQLAlchemy database and tenant context. |
| Cache | `jonex_core/common/cache.py` | Redis helpers with tenant isolation. |
| Logging | `jonex_core/common/logger.py` | Structured logging and request IDs. |
| Exceptions | `jonex_core/common/exceptions.py` | Five business-exception classes with 1xxx-5xxx error codes. |
| Exception handler | `jonex_core/common/exception_handler.py` | Converts FastAPI exceptions to standard JSON responses. |
| Standard responses | `jonex_core/common/response.py` | `StandardResponse`, `success_response`, and `error_response`. |
| Data-source crypto | `jonex_core/common/crypto.py` | Fernet encryption plus ingest-key generation, signing, verification, and decoding. |
| Data-source service | `capabilities/knowledge_base/services/data_source_service.py` | Data-source CRUD, connection tests, immediate sync, and inbound push. |
| Ingestion adapters | `capabilities/knowledge_base/services/ingestion/` | REST+JSON API and external MinIO/S3 outbound adapters. |
| Object-storage factory | `jonex_core/common/object_storage/__init__.py` | Selects COS or local storage from `OBJECT_STORAGE_BACKEND`. |
| File-source utilities | `jonex_core/common/file_source_util.py` | Builds and parses location-anchored `file_source` values and classifies media. |
| Reference DTOs | `capabilities/knowledge_base/dtos/reference.py` | `SourceLocation`, `SourceReference`, `ParsedRef`, and reference-resolution requests. |
| Reasoning DTOs | `capabilities/knowledge_base/dtos/reasoning.py` | Reasoning steps, traces, and stage/status constants. |
| Reasoning collector | `capabilities/knowledge_base/services/reasoning_trace.py` | No-op orchestration trace collection when disabled. |
| Reference enrichment | `capabilities/knowledge_base/services/search_service.py` | Resolves file-source references, enriches them from the database, and creates COS presigned URLs. |

## 12. Architecture Conclusion

The target Jonex Platform architecture is:

```text
frontend-gateway + shell/sub-applications
  -> API Gateway
    -> Sidecar
      -> platform / business_domain / knowledge_base / atomic-rag
        -> PostgreSQL / Redis / Neo4j / LightRAG / Milvus / MinIO / COS
```

New work should follow the final conventions directly:

- Frontend work belongs in the `frontends/` workspace and integrates with Shell.
- Backend work belongs in the corresponding capability service.
- Business rules belong in services.
- Data access belongs in repositories.
- Pydantic v1 request/response models belong in `dtos`.
- Tenant isolation uses `extract_tenant_id`, `require_tenant`, `TenantContext`, and `BaseRepository`.
- Cross-service calls go through Sidecar; in-service calls use explicit service/repository boundaries.
