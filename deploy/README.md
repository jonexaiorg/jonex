# deploy

`deploy/` contains Jonex platform deployment files, including Docker build contexts, Nginx configurations, and PostgreSQL migrations.

## Main Directories

The following lists the deployment entry points and primary configurations; build artifacts and local caches are excluded.

```text
deploy/
├── config/                      # Capability runtime and ontology TBox configuration
├── docker/                      # Service image Dockerfiles and build helper scripts
├── nginx/                       # Frontend-gateway and frontend Nginx configurations
├── postgres/
│   ├── init.sql                 # PostgreSQL initialization entry point
│   └── migrations/              # Numbered migration scripts
├── redis/                       # Redis configuration
├── scripts/                     # Build and operations helper scripts
├── docker-compose.yml           # Production baseline, only publishes frontend-gateway
├── docker-compose.override.yml  # Local full Docker integration test ports
├── docker-compose.debug.yml     # Host-side single service debugging override
├── docker-compose.gpu.yml       # NVIDIA GPU override
├── .env.example                 # Platform deployment variable template
├── .env.rag.example             # LightRAG variable template
└── start_capability.py          # Common capability service entry point
```

## Deployment Entry Points

In production, browsers only access `frontend-gateway`:

```text
frontend-gateway:80
  -> shell and sub-app frontend static assets
  -> /api/** -> gateway:8000
  -> LLM calls: lightrag / knowledge-base -> llm-gateway:8787 -> upstream LLM
```

Gateway, Sidecar, LLM Gateway, capability services, RAG services, PostgreSQL, Redis, Milvus, etcd, MinIO, and Neo4j are only accessible via container network in the production baseline. Development environments use `docker-compose.override.yml` to expose debug ports explicitly. To switch individual backend services or `atomic-rag` to host debugging, use `docker-compose.debug.yml`. See [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) for full port and service topology.

## Amazon Linux 2023 Prerequisites

Before deploying on a new Amazon Linux 2023 x86_64 host, verify the OS, architecture, and existing container tooling:

```bash
cat /etc/os-release
uname -m
command -v docker || true
rpm -q docker || true
sudo nginx -t  # when using host Nginx
```

Prefer installing the Docker RPM from Amazon Linux repositories. Do not add RHEL-focused Docker CE repositories or perform a full system upgrade just to install Docker:

```bash
sudo dnf install -y docker
sudo systemctl enable --now containerd.service docker.service
sudo systemctl is-active containerd.service docker.service
sudo docker version
sudo docker buildx version
sudo docker compose version
```

If the RPM does not provide usable Buildx or Compose plugins, download **fixed-version** binaries from the official Docker release only, verifying the publisher-provided SHA-256 before installation. Do not download unpinned `latest`. Production commands should use `sudo docker`; do not add the deployment account to the `docker` group (equivalent to root) for the convenience of omitting `sudo`. Docker's creation of bridge networks and firewall rules is normal behavior — do not disable Docker's firewall integration. If Nginx is already running on the host, run `sudo nginx -t` before and after installation and confirm the service remains active.

## Nginx Files

| File | Responsibility |
|---|---|
| `nginx/frontend-gateway.conf` | Sole frontend entry point, aggregates shell, sub-apps, remote assets, and `/api/**` reverse proxy. |

When adding a new frontend sub-app, update simultaneously:

- Sub-app Dockerfile.
- Sub-app `nginx/default.conf`.
- Standalone routes and remote asset reverse proxy in `deploy/nginx/frontend-gateway.conf`.
- Platform backend app registry.
- `frontends/shell/public/app-manifest.json` local fallback.

## PostgreSQL Migrations

Migration script rules:

- New business tables should include `tenant_id`, timestamps, and soft delete fields by default, plus audit fields where necessary.
- Platform shared metadata (apps, menus, permissions, system config) does not include `tenant_id`.
- Platform runtime data and business data must include a valid `tenant_id`.
- Local development and demo data use `tenant_jonex_demo`.
- Do not write to a default business tenant.

## Common Commands

```bash
make build
make up
make ps
make logs
make down
make docker-local-up
```

- `make up`: Loads `docker-compose.override.yml`, suitable for local full Docker integration testing with regular debug ports exposed.
- `make docker-local-up`: Loads `docker-compose.debug.yml`, suitable for keeping other services in Docker while debugging a single backend service or `atomic-rag` on the host. `lightrag` exposes port `9621` for convenience, but `atomic-rag` inside the container still calls it via `http://lightrag:9621` by default.

Single service:

```bash
make rebuild-service SERVICE=platform-service
make restart-service SERVICE=platform-service
make logs-service SERVICE=platform-service
```

Frontend images:

```bash
make rebuild-frontend-gateway
make rebuild-shell-frontend
make rebuild-core-business-frontend
make rebuild-platform-management-frontend
make rebuild-ecosystem-management-frontend
```

## Build Acceleration (Integrated into Compose Build)

Build optimizations are **directly integrated into `docker compose build`**: extracting a shared base image `python-base`, using `COMPOSE_BAKE` to delegate parallel builds to buildx, and retaining apt/pip/pnpm cache mounts. The output is the same `deploy-*` images that `docker compose up` actually runs — **no separate `jonex/*` images**. Runtime artifacts are identical to pre-optimization (dependency set / ports / commands / health checks / frontend dist unchanged).

How it works: The Dockerfiles for the 7 backend services (4 capability services + gateway/sidecar/llm-gateway) use `FROM ${PYTHON_BASE}`. Compose uses `additional_contexts: python-base: docker-image://jonex/python-base:local` (named context `python-base`, avoiding collision with `AS base` stage alias inside Dockerfiles) to reuse the pre-built shared base layer.

### One-Command Build

```bash
# *nix / CI: build python-base first, then parallel compose build (outputs total time in seconds)
bash deploy/scripts/build_all.sh
bash deploy/scripts/build_all.sh gateway    # build specific compose service

# Windows (cmd)
deploy\scripts\build_all.cmd

# make (automatically builds base first, then COMPOSE_BAKE parallel build)
make build            # local integration test
make build-gpu        # GPU
make build-prod       # production
make build-backend    # backend only
make build-service SERVICE=gateway
```

Equivalent manual two-step process (already wrapped by scripts/Make):

```bash
# 1) Build shared base image and load into local image registry (reused by 7 backend services)
docker buildx build --load -t jonex/python-base:local -f deploy/docker/python-base.Dockerfile .
# 2) Parallel compose build (delegates to buildx bake)
cd deploy && COMPOSE_BAKE=1 docker compose build
```

> `python-base` is not a compose service — `docker compose up` will not start it. It is only referenced as a build-time named context. The layer is rebuilt after first use or when the dependency manifest changes, and cached thereafter.

### Optimization Breakdown

| Optimization | Description |
|---|---|
| Shared base image | `python-base.Dockerfile` consolidates common layers for 7 backend services (timezone / Tencent mirrors / apt / pip dependencies) |
| Parallel build | `COMPOSE_BAKE=1` makes `docker compose build` delegate to buildx bake, running builds in parallel according to dependency graph |
| Frontend pnpm store cache | 5 frontends share `--mount=type=cache,id=jonex-pnpm-store` — zero download when dependencies unchanged |
| Atomic-rag layer pinning | Fixed layer order, source code is the final `COPY` — source-only changes rebuild only 1 layer |

### Build Benchmark (Optional)

```bash
python deploy/scripts/build_benchmark.py --scenario cold --repeat 3 --baseline deploy/build-baseline.json
python deploy/scripts/build_benchmark.py --scenario incremental --repeat 3 --baseline deploy/build-baseline.json
```

### Advanced: CI Cross-Machine Cache (Optional)

To reuse build layer cache across CI runners, declare `build.cache_from` / `build.cache_to` in each compose service's config (for registry or GHA cache, with `docker-container` builder). `COMPOSE_BAKE=1 docker compose build` passes these through to buildx. Local `docker` driver does not support cache export, so no configuration is needed.

### Verification Tests (Optional)

```bash
# Lightweight unit / snapshot tests for build optimization (no Docker required, milliseconds)
uv run pytest tests/unit/test_python_base_dockerfile.py tests/unit/test_build_benchmark.py
```

> The simplest way to verify optimization effectiveness is to run `make build` (or `deploy\scripts\build_all.cmd`) followed by `docker compose up -d` for a smoke test.

## Health Checks and Logs

```bash
# Frontend Nginx health check (production sole external port)
curl http://localhost/health        # Returns 'ok'

# Development mode (compose override exposes ports) — backend directly accessible
curl http://localhost:8000/health   # Gateway
curl http://localhost:8001/health   # Sidecar
curl http://localhost:8003/health   # Knowledge base
curl http://localhost:8005/health   # Business domain
curl http://localhost:8006/health   # Platform
curl http://localhost:8787/health   # LLM Gateway

# Production mode — backend not exposed externally, access via container
docker exec jonex-gateway curl -s http://localhost:8000/health
```

Logs:

```bash
make logs                 # All
make logs-service SERVICE=knowledge-base-service
make logs-sidecar
make logs-postgres
```

Application logs are also mounted to the `jonex-logs` data volume.

## Database Management

```bash
# Connect to PostgreSQL
make shell-postgres
# or: docker exec -it jonex-postgres psql -U jonex -d jonex

# Initialize / recreate schema and seed data
make init-db
```

Migration scripts are located in `postgres/migrations/` and executed in numbered order (`001_schemas` → `002_platform` → `004_knowledge_base` → `005_business_domain` → `006_seed_data` → `007_comments`, subsequent numbers continue sequentially). `postgres/init.sql` is the aggregated initialization entry point for the container's first startup.

> Note: `001` creates platform, knowledge_base, business_domain, and metering schemas; metering table `metering.llm_usage_log` is included in `002`; knowledge base document storage columns, data source tables, and editable fields for ontology compile snapshots are included in `004`; corresponding seed data is in `006`.

If the data volume was initialized before a particular schema was added, it can be applied manually:

```bash
docker exec -i jonex-postgres psql -U jonex -d jonex < postgres/migrations/004_knowledge_base.sql
```

## GPU Acceleration (Optional)

If the host has an NVIDIA GPU with `nvidia-container-toolkit` installed, overlay `docker-compose.gpu.yml` to enable GPU for atomic-rag:

```bash
make build-gpu     # Build images
make up-gpu        # Start (auto-loads gpu.yml)

# Verify GPU is enabled
docker exec jonex-atomic-rag python -c "import torch; print(torch.cuda.is_available())"
```

When GPU is enabled, the MinerU parser automatically uses CUDA, and atomic-rag CPU memory usage decreases significantly.

## Ontology Knowledge Engine Operations

After document parsing and LightRAG ingestion are complete, Stage 4 ontology extraction can be optionally enabled. Current responsibility split:

- **atomic-rag** performs extraction, producing `ontology_data` (entities / relationships), without directly writing to Neo4j.
- **knowledge-base** reconciliation service (`reconciliation_service`) writes `ontology_data` to Neo4j, then updates the PostgreSQL `ontology_status` state machine (write Neo4j first, set `READY` on success, `FAILED` on failure).
- Neo4j schema is initialized automatically by `ensure_ontology_schema()` when knowledge-base starts — failure only generates a warning, does not block the service.
- When Neo4j is unavailable, knowledge base queries and document READY flow degrade gracefully to standard RAG without blocking core functionality.

### Enabling

Enable the extraction switch in `deploy/.env` and restart atomic-rag:

```bash
# deploy/.env
ONTOLOGY_EXTRACT_ENABLED=true
ONTOLOGY_SCHEMA_PATH=deploy/config/ontology/default.yaml

make restart-service SERVICE=atomic-rag
```

Ontology TBox definition is in `deploy/config/ontology/default.yaml` (entity types, aliases, attributes, relationship types).

### Neo4j Container

```bash
# Constraint check
docker exec jonex-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "SHOW CONSTRAINTS;"

# View ontology entities
docker exec jonex-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n:OntologyEntity) RETURN n.tenant_id, n.entity_type, n.canonical_name LIMIT 10;"
```

### Enhanced Search (Ontology-First)

```bash
curl "http://localhost:8000/api/v1/knowledge-base/documents/search/enhanced?query=<query>&knowledge_base_id=KB1&mode=hybrid&top_k=3" \
     -H "Authorization: Bearer <access_token>"
```

Returns `{answer, source:"ontology"|"rag", ontology_instances:[...], rag_used:boolean}`: `source="ontology"` indicates answer based on Neo4j graph facts + LLM; `source="rag"` indicates ontology missed and fell back to full RAG.

Documents with `ontology_status` of `pending`/`failed` are automatically retried by the reconciliation loop.

### Ontology-Related Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ONTOLOGY_EXTRACT_ENABLED` | `false` | Whether to enable ontology extraction |
| `ONTOLOGY_SCHEMA_PATH` | `deploy/config/ontology/default.yaml` | TBox schema path |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USERNAME` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `CHANGE_ME` | Neo4j password (must be changed before deployment) |

## Data Backup

```bash
# PostgreSQL
docker exec jonex-postgres pg_dump -U jonex jonex > backup_$(date +%Y%m%d).sql

# Redis
docker exec jonex-redis redis-cli BGSAVE
docker cp jonex-redis:/data/dump.rdb ./redis_backup.rdb

# Neo4j
docker exec jonex-neo4j neo4j-admin database dump neo4j --to-path=/backups
docker cp jonex-neo4j:/backups ./neo4j_backup
```

## Troubleshooting

Service won't start:

```bash
make logs-service SERVICE=<service>     # View detailed logs
make restart-service SERVICE=<service>  # Restart a single service
make recreate-service SERVICE=<service> # Force recreate
```

Database connection failures:

```bash
make ps                                 # Check container status
make logs-postgres                      # View PostgreSQL logs
docker exec jonex-postgres pg_isready -U jonex
```

Performance issues:

```bash
docker stats                            # Container resource usage
make logs-sidecar
make logs-service SERVICE=knowledge-base-service
```

## Required Security Configuration

After the first run of `make init`, edit `deploy/.env` and replace all `CHANGE_ME` values. At minimum, set: `DB_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `NEO4J_PASSWORD`, `JWT_SECRET`, and `SIDECAR_API_KEY`. `SIDECAR_API_KEY` is the shared secret for Gateway/internal clients to call Sidecar — both Gateway and Sidecar must read the same non-empty value.

Use Python to generate a high-entropy key, and do not commit the output to Git:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`LIGHTRAG_API_KEY` in `deploy/.env.rag` must also match the platform-side calling configuration. In production, also replace `LLMGW_INTERNAL_TOKENS` and configure real upstream LLM credentials.

## Quick Deployment Steps

```bash
make init                # First-time init from public example files to actual env
# Edit deploy/.env, deploy/.env.rag; replace all CHANGE_ME, ensure shared keys match on both sides
make build && make up    # Build and start local Docker deployment (loads override)
make ps                  # Verify status
make logs                # View logs
```

For host-side single-service debugging, use `make docker-local-up`. For production / server orchestration, use `make build-prod` / `make up-prod` or `make build-server` / `make up-server`.

See [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) for detailed deployment topology.
