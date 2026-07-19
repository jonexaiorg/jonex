# Local Full-Stack Debugging Guide

This document explains how to start and debug Jonex Platform's frontend, API Gateway, Sidecar, and each capability service locally.

Applicable scenarios:

- Local frontend with local backend
- Local frontend with server backend
- VSCode backend breakpoint debugging
- VSCode frontend page debugging
- Integration testing of a single sub-application or a single capability

## Service Chain

The local frontend-backend chain is typically as follows:

```text
Browser
  -> Dev Gateway 8080
     -> Shell Frontend 5173
     -> Sub-app Frontend 5175/5176/5177
     -> /api relative path -> API Gateway 8000
                               -> Sidecar 8001
                                  -> capability service 8003/8004/8005/8006
                                     -> PostgreSQL / Redis / Milvus / Neo4j
                                     -> LightRAG 9621
                                     -> LLM Gateway 8787 -> upstream model service
```

Default ports:

- Dev Gateway: `8080`
- Shell Frontend: `5173`
- Core Business Frontend: `5175`
- Ecosystem Management Frontend: `5176`
- Platform Management Frontend: `5177`
- API Gateway: `8000`
- LLM Gateway: `8787`
- Knowledge Base capability: `8003`
- Business Domain capability: `8005`
- Platform capability: `8006`
- Atomic RAG capability: `8004`
- LightRAG Server: `9621`

The browser-side API uses the relative path `/api` by default. It is currently recommended to access via the unified entry point `http://localhost:8080`. Frontend requests enter dev-gateway first, then are forwarded to the shell, each sub-app dev server, or the local API Gateway.

## Recommended Startup Methods

Navigate to the project root directory:

```bash
cd jonex
```

On macOS/Linux, use `Makefile`; on Windows, use `jonex.ps1`. There are some identically named commands on both sides, but they are not exactly the same command set; refer to each tool's `help` output for details.

### macOS/Linux

First start local dependencies:

```bash
make dev-deps-up
```

Backend:

```bash
# Makefile no longer provides native backend startup commands.
# When backend breakpoint debugging is needed, use the following in VSCode Debug:
# - Backend: Sidecar
# - Backend: API Gateway
# - Backend: Capability - Knowledge Base / Business Domain / Platform
```

Start the unified entry point and frontend as needed:

```bash
make frontends-install
make dev-gateway
make dev-frontend
# Or start individually as needed
make dev-frontend-shell
make dev-frontend-core
make dev-frontend-ecosystem
make dev-frontend-platform
```

### Windows PowerShell

Execute the following commands in the project root directory. If your local PowerShell execution policy blocks `.ps1` scripts, use instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\jonex.ps1 help
```

First start local dependencies:

```powershell
.\jonex.ps1 dev-deps-up
```

Start backends as needed:

```powershell
.\jonex.ps1 dev-backend-sidecar
.\jonex.ps1 dev-backend-gateway
.\jonex.ps1 dev-backend-knowledge-base
.\jonex.ps1 dev-backend-business-domain
.\jonex.ps1 dev-backend-platform
```

Start the unified entry point and frontends as needed:

```powershell
.\jonex.ps1 frontends-install
.\jonex.ps1 dev-gateway
.\jonex.ps1 dev-frontend
# Or start individually as needed
.\jonex.ps1 dev-frontend-shell
.\jonex.ps1 dev-frontend-core
.\jonex.ps1 dev-frontend-ecosystem
.\jonex.ps1 dev-frontend-platform
```

You can also use the frontend workspace scripts directly:

```bash
cd frontends
pnpm run dev:gateway
pnpm run dev:shell
pnpm run dev:core-business
pnpm run dev:ecosystem-management
pnpm run dev:platform-management
```

Common entry points:

- Unified entry: `http://localhost:8080`
- Shell home page: `http://localhost:8080/`
- Core Business (shell route): `http://localhost:8080/apps/core-business`
- Ecosystem Management (shell route): `http://localhost:8080/apps/ecosystem-management`
- Platform Management (shell route): `http://localhost:8080/apps/platform-management`
- Sub-app standalone entry example: `http://localhost:8080/core-business/`


## Infrastructure on Server - Application Service Local Development (Current Status)

The repository already includes:

- Server infrastructure orchestration file: `deploy/docker-compose.infra.yml`
- Local environment template: `.env.server-local.example`

However, note that **currently `make dev-backend-*` / `.\jonex.ps1 dev-backend-*` are still in "local-only dependency mode"**. These scripts will:

- Automatically start local `postgres/redis/etcd/minio/milvus/lightrag/atomic-rag`
- Force-override variables like `DB_HOST`, `REDIS_URL`, `MILVUS_HOST` back to `127.0.0.1`

Therefore, "server infrastructure + local application services" currently **cannot** be started directly with the `dev-backend-*` set of scripts.

### Two Currently Available Approaches

1. Most stable local integration mode
   Use the default flow from earlier in this document: local dependencies + local backend + `8080` unified frontend entry.
2. Local frontend with server backend
   The frontend still runs locally, but the API target is changed to the server.

### Frontend with Server Backend

If you are currently accessing the frontend via `http://localhost:8080`, you need to modify the API forwarding target of `dev-gateway`, not the Vite proxy of the shell.

Create `.env` under `frontends/dev-gateway/`:

```powershell
cd frontends\dev-gateway
Copy-Item .env.example .env
```

Then change it to:

```env
API_TARGET=http://server-address:8000
```

After restarting `pnpm run dev:gateway`, `http://localhost:8080/api/...` will be forwarded to the server Gateway.

If you bypass `8080` and directly access the shell via `5173`, use:

```env
VITE_API_TARGET=http://server-address:8000
```

In this case, the Vite proxy is controlled via `frontends/.env.local`.

### Server Infrastructure Template

Applicable scenarios: when Docker cannot be run locally, or when you want multiple people to share infrastructure like PostgreSQL / Redis / Milvus / Neo4j, but backend processes will be started manually or via VSCode Debug.

Architecture reference:

```text
Browser
  -> Dev Gateway (local 8080)
  -> /api/ -> API Gateway (local 8000)
               -> Sidecar (local 8001)
                  -> capability service (local 8003/8005/8006)
                  -> PostgreSQL / Redis / Milvus / Neo4j (server)
```

On the server (requires Docker + Docker Compose), enter the `deploy/` directory:

```bash
cd jonex/deploy
docker compose -f docker-compose.infra.yml up -d
docker compose -f docker-compose.infra.yml ps
docker compose -f docker-compose.infra.yml logs -f
```

The project root provides an environment template:

```powershell
Copy-Item .env.server-local.example .env
```

Then replace all `SERVER_IP` entries with the actual server IP (e.g., `your-server-ip`).

This template is suitable for manually starting Python processes or VSCode Debug usage; it is **not applicable** to the current `.\jonex.ps1 dev-backend-*` scripts.

### Current Limitations

- `.\jonex.ps1 dev-backend-*` will overwrite database, Redis, Milvus, and capability addresses to `127.0.0.1`
- `.\jonex.ps1 dev-backend-*` will also start local Docker dependencies
- Therefore, in server infrastructure mode, use VSCode Debug or manual commands for the backend; do not use these scripts directly

## VSCode Debug Configuration

## Backend Breakpoint Debugging

The Makefile no longer provides native backend startup commands. When breakpoints are needed, it is recommended to use VSCode Debug to start the corresponding backend configuration.

Common approach:

1. `make dev-deps-up`
2. VSCode Debug starts `Backend: Sidecar`
3. VSCode Debug starts `Backend: API Gateway`
4. VSCode Debug starts the target capability, e.g., `Backend: Capability - Business Domain`
5. Start the corresponding frontend and browser entry

If debugging only a single capability or `atomic-rag`, you can first use `make docker-local-up` to keep other services running in Docker, then use VSCode Debug to start the target service on the host machine.

Windows PowerShell equivalent steps:

1. `.\jonex.ps1 dev-deps-up`
2. VSCode Debug starts `Backend: Sidecar`
3. VSCode Debug starts `Backend: API Gateway`
4. VSCode Debug starts the target capability, e.g., `Backend: Capability - Business Domain`
5. Start the corresponding frontend and browser entry

If debugging only capability internal logic, you can also use `.\jonex.ps1 dev-backend-sidecar` and `.\jonex.ps1 dev-backend-gateway` to start the base backends, then use VSCode Debug to start the target capability.

## Local Debugging of RAG Services (LightRAG + Atomic RAG)

The Reference directory contains two RAG-related services that require special handling for local debugging:

| Service | Source Directory | Local Port | Docker Service Name | env File |
|---|---|---|---|---|
| LightRAG | `Reference/LightRAG/` | 9621 | `lightrag` | `.env.rag` / `.env.rag.local` |
| Atomic RAG | `Reference/Rag-anything/` | 8004 | `atomic-rag` | `.env` / `.env.local` |

### Why a Separate venv is Needed

Atomic RAG depends on `raganything` (which includes `mineru`, `torch`, `lightrag-hku`, etc.). These packages require **pydantic v2**. The project baseline (Sidecar, Gateway, Business Capabilities) uses **pydantic v1.10.x**. To isolate the conflict, a separate virtual environment must be created for the RAG services.

This debugging involves a key code fix: `jonex_core/common/config.py`'s `_load_env_file()` originally used `load_dotenv(path, override=True)`, which forcefully overwrote runtime environment variables with values from the `.env` file. It has been changed to `override=False`, allowing local debugging to override Docker internal domain names via environment variables or `envFile`. This change has no impact on Docker deployments (values are the same).

### Step 1: Create a Separate venv and Install Dependencies

```bash
cd jonex-platform

# Create a separate venv
uv venv .venv-atomic-rag

# Activate the venv (subsequent pip install commands will install into this venv)
source .venv-atomic-rag/bin/activate

# Install base dependencies (jonex_core, FastAPI, SQLAlchemy, etc.)
uv pip install -e ".[dev]"

# Upgrade pydantic to v2 (required by mineru)
uv pip install --upgrade 'pydantic>=2.0,<3.0' pydantic-settings

# Install raganything source code (includes mineru, torch, lightrag-hku, etc.)
uv pip install -e "Reference/Rag-anything[all]"

# Install atomic-rag specific dependencies (httpx, pymupdf, sentence-transformers, etc.)
uv pip install -r deploy/docker/atomic-rag-requirements.txt

# Exit the venv (subsequent operations return to the system or default .venv)
deactivate
```

> **Note**: The above commands must be executed after `source .venv-atomic-rag/bin/activate`, otherwise they will be installed into the default `.venv` instead of `.venv-atomic-rag`.

After installation, create the local data directory:

```bash
mkdir -p .lightrag_data/rag_storage .lightrag_data/inputs
```

### Step 2: Create Local Environment Files

The `.env` and `.env.rag` files used in Docker deployments contain Docker internal domain names (e.g., `redis`, `postgres`, `llm-gateway`), which need to be replaced with `127.0.0.1` for local debugging. The project provides local override files:

| File | Purpose | Changes Compared to Original |
|---|---|---|
| `.env.local` | Atomic RAG local debugging | `DB_HOST`, `REDIS_URL`, `MILVUS_HOST`, etc. changed to `127.0.0.1` |
| `.env.rag.local` | LightRAG local debugging | `LLM_BINDING_HOST`, `EMBEDDING_BINDING_HOST`, `NEO4J_URI` changed to `127.0.0.1`; `WORKING_DIR` changed to local path |

Generate from templates on first use (templates are provided with the project):

```bash
# macOS/Linux
sed -e 's|DB_HOST=postgres|DB_HOST=127.0.0.1|' \
    -e 's|REDIS_URL=redis://redis:6379/0|REDIS_URL=redis://127.0.0.1:6379/0|' \
    -e 's|MILVUS_HOST=milvus|MILVUS_HOST=127.0.0.1|' \
    -e 's|AUDIT_INGEST_URL=.*|AUDIT_INGEST_URL=http://127.0.0.1:8006|' \
    .env > .env.local

sed -e 's|llm-gateway:8787|127.0.0.1:8787|g' \
    -e 's|neo4j:7687|127.0.0.1:7687|' \
    -e 's|${NEO4J_PASSWORD:-CHANGE_ME}|CHANGE_ME|' \
    -e 's|WORKING_DIR=/app/data/rag_storage|WORKING_DIR=.lightrag_data/rag_storage|' \
    -e 's|INPUT_DIR=/app/data/inputs|INPUT_DIR=.lightrag_data/inputs|' \
    .env.rag > .env.rag.local
```

> `.env.local` and `.env.rag.local` are already added to `.gitignore` and will not be committed to the repository.

### Step 3: Start Debugging

**Method 1: VSCode Debug (Recommended)**

1. `make dev-deps-up` to start middleware (postgres, redis, milvus, neo4j, llm-gateway, etc.)
2. In the VSCode Run and Debug panel, select the corresponding configuration:
   - Debug LightRAG alone: `Backend: LightRAG`
   - Debug Atomic RAG alone: `Backend: Capability - Atomic RAG`
   - One-click start full RAG chain: `Debug: RAG Services` (Sidecar + Gateway + Knowledge Base + LightRAG + Atomic RAG + Shell + Browser)

**Method 2: Command Line Manual Startup**

```bash
cd jonex-platform

# First start dependencies
make dev-deps-up

# Start LightRAG (one terminal)
set -a && source .env.rag.local && set +a && \
.venv-atomic-rag/bin/python -m lightrag.api.lightrag_server

# Start Atomic RAG (another terminal)
set -a && source .env.local && source .env.rag.local && set +a && \
CAPABILITY_KIND=atomic \
CAPABILITY_NAME=rag.lightrag \
SERVICE_PORT=8004 \
SERVICE_ENDPOINT=http://127.0.0.1:8004 \
CAPABILITY_RUNTIME_FILE=deploy/config/capability_runtime.yaml \
LIGHTRAG_API_URL=http://127.0.0.1:9621 \
.venv-atomic-rag/bin/python deploy/start_capability.py
```

**Method 3: Run Other Services in Docker + Debug RAG on Host**

```bash
# First start all services with debug compose
make docker-local-up

# Stop the Docker service you want to debug
docker stop jonex-lightrag      # When debugging LightRAG
docker stop jonex-atomic-rag    # When debugging Atomic RAG

# Then start the corresponding RAG configuration in VSCode Debug
# extra_hosts in docker-compose.debug.yml already resolves lightrag DNS to the host
```

### Verification

After Atomic RAG starts, the logs should show:

```
✅ Redis connection pool initialized (host=127.0.0.1:6379)
✅ Startup cleanup: no non-terminal orphan tasks
✅ Service registered successfully: rag.lightrag @ http://127.0.0.1:8004
```

Docker domain names (e.g., `host=redis:6379`) or Redis connection errors indicate that the environment file was not loaded correctly.

### venv Usage Comparison

| venv | pydantic | Applicable Services |
|---|---|---|
| `.venv` | 1.10.x (v1) | Sidecar, API Gateway, Knowledge Base, Business Domain, Platform |
| `.venv-atomic-rag` | 2.x (v2) | LightRAG, Atomic RAG |

The `python` field in the VSCode launch.json for the two RAG configurations already points to `.venv-atomic-rag/bin/python`, while all other backend configurations continue to use `.venv/bin/python`.

## Direct Backend Invocation (Without Frontend)

In addition to page-level integration testing, you can also call the backend directly to help isolate issues across layers.

Via API Gateway (business path, recommended):

```bash
curl "http://localhost:8000/api/v1/platform/users" \
     -H "Authorization: Bearer <access_token>"
```

Via Sidecar unified invoke contract (verify capability registration and proxy are working):

```bash
# List registered capabilities
curl http://localhost:8001/capabilities \
     -H "Authorization: Bearer jonex_test_tenant_jonex_demo"

# Invoke capability (payload contains action and business parameters)
curl -X POST http://localhost:8001/invoke \
     -H "Authorization: Bearer jonex_test_tenant_jonex_demo" \
     -H "Content-Type: application/json" \
     -d '{"capability_id":"business.knowledge_base.v1","payload":{"action":"list_documents","knowledge_base_id":"KB1"}}'
```

In the local `dev` / `test` environment, you can use `Authorization: Bearer jonex_test_{tenant_id}` to quickly carry a tenant (e.g., `jonex_test_tenant_jonex_demo`), which is equivalent to `X-Tenant-ID: tenant_jonex_demo`, without needing to log in first. This token does not provide real identity authentication and is strictly prohibited for shared, UAT, or production environments; `uat` / `prod` must be forcefully rejected by Gateway and Sidecar.

Directly connecting to a capability service (only confirms the service itself is alive):

```bash
curl http://localhost:8003/health   # Knowledge Base
curl http://localhost:8005/health   # Business Domain
```

Recommended troubleshooting order: capability `/health` is OK -> Sidecar `/capabilities` lists the capability -> Sidecar `/invoke` succeeds -> Gateway business path succeeds. Whichever layer breaks, the issue lies between that layer and the previous one.

## Frontend Breakpoint Debugging

The frontend can be debugged using Chrome DevTools, or by using the VSCode JavaScript Debugger to connect to the browser.

Page requests use relative paths by default:

```text
/api/...
```

The local Vite will proxy requests to the API Gateway. Do not expose container-internal addresses like `gateway:8000` directly in browser-side configuration.

## frontends/.env.local

`frontends/.env.local` can still be used normally.

But distinguish between two entry points:

1. Access via `http://localhost:8080`
2. Direct access to the shell via `http://localhost:5173`

When debugging a local frontend with a local backend, modifications are usually not needed.

If you access the shell directly via `5173`, the default forwarding target is:

```text
http://localhost:8000
```

If you access via the `8080` unified entry, first modify `frontends/dev-gateway/.env`:

```env
API_TARGET=http://your-server-ip:8000
```

To make the `5173` shell target the server backend directly, then set in `frontends/.env.local`:

```env
VITE_API_TARGET=http://your-server-ip:8000
```

The frontend dev server needs to be restarted after modification.

## Debugging Example: Template Domains Page

The Template Domains page is a page within the Ecosystem Management sub-application and can serve as an example of page-level integration testing.

Related entry points:

- Frontend page: `frontends/ecosystem-management/src/pages/TemplateDomains/index.tsx`
- Frontend API: `frontends/ecosystem-management/src/api/templateDomains.ts`
- Backend API: `capabilities/business_domain/api/templates.py`
- Local access URL: `http://localhost:8080/apps/ecosystem-management/template-domains`

The chain is as follows:

```text
Dev Gateway 8080
  -> Shell Frontend 5173
  -> ecosystem-management sub-app 5176
  -> /api/v1/ecosystem/templates/domains
  -> API Gateway 8000
  -> business_domain capability 8005
  -> capabilities/business_domain/api/templates.py
```

Recommended debugging approach:

1. `make dev-deps-up`
2. VSCode Debug starts `Debug: Template Domains`
3. Set breakpoints in `capabilities/business_domain/api/templates.py` or frontend page files
4. Open `http://localhost:8080/apps/ecosystem-management/template-domains`

Windows PowerShell:

1. `.\jonex.ps1 dev-deps-up`
2. VSCode Debug starts `Debug: Template Domains`
3. Set breakpoints in `capabilities/business_domain/api/templates.py` or frontend page files
4. Open `http://localhost:8080/apps/ecosystem-management/template-domains`

## Login and Authentication

Most Gateway routes require authentication. If the page redirects to login or returns unauthorized responses during debugging, first log in through the Shell, then access the target sub-app page.

The local seed data provides an admin account under the `tenant_jonex_demo` tenant by default:

```text
username: admin
password: admin123
```

`deploy/postgres/migrations/006_seed_data.sql` also provides a set of multi-tenant login test accounts for verifying flows such as "login without tenant, password match then select tenant, login with specified tenant":

| Username | Password | Tenant | Expected Result |
| --- | --- | --- | --- |
| `admin` | `admin123` | `tenant_jonex_demo` | Single-tenant account, logs in directly. |
| `multi_same_pass` | `admin123` | `tenant_jonex_demo`, `tenant_jonex_alpha` | User exists in multiple tenants with matching passwords; returns `tenant_selection_required` when logging in without `X-Tenant-ID`. |
| `multi_one_match` | `admin123` | `tenant_jonex_demo` | User exists in multiple tenants, but only the demo tenant password matches; logs into `tenant_jonex_demo` directly. |
| `multi_one_match` | `other123` | `tenant_jonex_alpha` | User exists in multiple tenants, but only the Alpha tenant password matches; logs into `tenant_jonex_alpha` directly. |
| `tenant_header_user` | `admin123` | `tenant_jonex_beta` | Used to test login with a specified tenant via `X-Tenant-ID: tenant_jonex_beta`. |

The login endpoint is an authentication bootstrap endpoint and can be called without pre-specifying a tenant:

```bash
curl 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  --data-raw '{"username":"admin","password":"admin123"}'
```

If the same username exists across multiple active tenant accounts, the tenant must be explicitly selected:

```bash
curl 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: tenant_jonex_demo' \
  --data-raw '{"username":"multi_same_pass","password":"admin123"}'
```

You can also test the "specified tenant header" scenario:

```bash
curl 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: tenant_jonex_beta' \
  --data-raw '{"username":"tenant_header_user","password":"admin123"}'
```

After successful login, testing business interfaces directly requires carrying the returned `access_token`:

```bash
curl 'http://localhost:8000/api/v1/platform/users' \
  -H 'Authorization: Bearer <access_token>'
```

## Common Issues

### Page Does Not Load

Ensure both the Shell and the target sub-app frontend are started. For example, when debugging Ecosystem Management:

```bash
make dev-frontend-shell
make dev-frontend-ecosystem
```

Windows PowerShell:

```powershell
.\jonex.ps1 dev-frontend-shell
.\jonex.ps1 dev-frontend-ecosystem
```

Then visit:

```text
http://localhost:8080/apps/ecosystem-management
```

### API Returns 404

Ensure both the API Gateway and the target capability are started. For example, when debugging Business Domain:

```bash
# Use VSCode Debug to start:
# - Backend: API Gateway
# - Backend: Capability - Business Domain
```

Windows PowerShell:

```powershell
.\jonex.ps1 dev-backend-gateway
.\jonex.ps1 dev-backend-business-domain
```

Also confirm that the frontend request path starts with `/api`, and check that the Gateway route is already registered.

### API Returns 401 or 403

First log in through the Shell, then revisit the page. When testing interfaces directly, first call `/api/v1/auth/login` to obtain an `access_token`, then include `Authorization: Bearer <access_token>`. If it returns "please select a tenant to log in", add `X-Tenant-ID: tenant_jonex_demo` to the login request.

### Python Breakpoint Not Hit

Do not use `.\jonex.ps1 dev-backend-xxx` to start backend services that need breakpoints, and do not expect `make` to have native backend startup commands. Instead, use VSCode Debug to start the corresponding `Backend: ...` configuration, or start the corresponding `Debug: ...` compound configuration.

### Frontend with Server Backend Not Working

First confirm whether you are accessing the frontend via `8080` or `5173`.

If using the `8080` unified entry, check `frontends/dev-gateway/.env`:

```env
API_TARGET=http://server-address:8000
```

If accessing `5173` directly, check `frontends/.env.local`:

```env
VITE_API_TARGET=http://server-address:8000
```

Restart the corresponding frontend dev server after modification.

### Atomic RAG Startup Error: `ModuleNotFoundError: No module named 'raganything'`

This means the current environment is `.venv` instead of `.venv-atomic-rag`. Confirm that VSCode Debug has selected `Backend: Capability - Atomic RAG` (the command line should show `.venv-atomic-rag/bin/python`).

If `.venv-atomic-rag` has not been created yet, refer to the "Local Debugging of RAG Services -> Step 1" section above.

### Redis / Database Connection Error: `nodename nor servname provided`

The logs show `host=redis:6379` instead of `host=127.0.0.1:6379`, meaning the Docker internal domain names were not overridden. Check:

1. Whether the `override` parameter of `_load_env_file()` in `jonex_core/common/config.py` is set to `False`
2. Whether the VSCode launch configuration's `envFile` points to `.env.local` (for Atomic RAG) or `.env.rag.local` (for LightRAG)

### LightRAG Server Started but Atomic RAG Cannot Connect

Confirm LightRAG is running locally on port `9621`. The `Debug: RAG Services` compound configuration will start services in order automatically. When starting individually, LightRAG must be started first, then Atomic RAG.
