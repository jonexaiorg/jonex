# Jonex Platform Deployment Architecture

This document describes the current Docker Compose deployment topology. Production uses `docker-compose.yml` as the baseline. Browsers access `frontend-gateway` only; local integration and host-side single-service debugging layer `docker-compose.override.yml` and `docker-compose.debug.yml` on top of the baseline.

## 1. Overall Topology

```text
User browser / external caller
  |
  v
frontend-gateway (Nginx, host ${FRONTEND_PORT:-80} -> container 80)
  |-- shell-frontend
  |-- core-business-frontend
  |-- platform-management-frontend
  |-- ecosystem-management-frontend
  `-- /api/** -> gateway:8000
                  |
                  v
                sidecar:8000
                  |-- platform-service:8000
                  |-- business-domain-service:8000
                  |-- knowledge-base-service:8000
                  `-- atomic-rag:8000 -> lightrag:9621

LLM / Embedding callers
  `-- llm-gateway:8787 -> TokenHub / Ollama and other upstreams

Infrastructure: PostgreSQL / Redis / Milvus / etcd / MinIO / Neo4j
```

`gateway` owns HTTP route aggregation; `sidecar` owns authentication context, internal JWTs, invocation governance, and capability proxying; capability services implement business rules. `llm-gateway` is the unified egress for platform LLM, Embedding, and rerank calls.

## 2. Compose Modes and Ports

### 2.1 Production Baseline

```bash
cd deploy
docker compose -f docker-compose.yml up -d
```

The production baseline publishes only:

| Service | Host port | Container port | Description |
|---|---:|---:|---|
| `frontend-gateway` | `${FRONTEND_PORT:-80}` | `80` | The only external entry point; an upstream HTTPS load balancer or host Nginx may proxy to it. |

Gateway, Sidecar, capability services, RAG services, the LLM Gateway, and infrastructure communicate only through `jonex-network`; they do not publish host ports.

### 2.2 Local Full-Stack Docker Integration

```bash
cd deploy
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

`docker-compose.override.yml` publishes the following debugging ports:

| Category | Host ports |
|---|---|
| Frontend entry | `80` or `FRONTEND_PORT` |
| Gateway / Sidecar / LLM Gateway | `8000` / `8001` / `8787` |
| Capabilities | `8003` / `8004` / `8005` / `8006` |
| LightRAG | `9621` |
| PostgreSQL / Redis | `5432` / `6379` |
| MinIO | `9000` / `9001` |
| Milvus | `19530` / `9091` |
| Neo4j | `7474` / `7687` |

### 2.3 Host-Side Single-Service Debugging

```bash
cd deploy
docker compose -f docker-compose.yml -f docker-compose.debug.yml up -d
```

`docker-compose.debug.yml` keeps the debugging ports above and points Sidecar capability addresses to `host.docker.internal`, allowing one business backend or `atomic-rag` to run on the host. On Linux, `host-gateway` is used to resolve the host.

macOS and GPU environments can add:

- `docker-compose.mac.yml`: macOS CPU development override.
- `docker-compose.gpu.yml`: assigns an NVIDIA GPU to `atomic-rag`.

## 3. Service Inventory

The current Compose project contains 19 runtime services.

### 3.1 Frontend Containers (5)

| Service | Container port | Responsibility |
|---|---:|---|
| `frontend-gateway` | `80` | Only entry point; aggregates static assets, provides SPA fallback, proxies `/api/**`, and sets security headers. |
| `shell-frontend` | `80` | Authenticated workspace, navigation, application loading, and context injection. |
| `core-business-frontend` | `80` | Core business sub-application. |
| `platform-management-frontend` | `80` | Platform management sub-application. |
| `ecosystem-management-frontend` | `80` | Ecosystem management sub-application. |

The production application list comes from:

```text
GET /api/v1/platform/frontend/apps
```

`frontends/shell/public/app-manifest.json` is only a local-development fallback used when the backend is unavailable.

### 3.2 Gateway and Governance Services (3)

| Service | Container port | Dev host port | Responsibility |
|---|---:|---:|---|
| `gateway` | `8000` | `8000` | External API route aggregation and protocol adaptation. |
| `sidecar` | `8000` | `8001` | Authentication context, internal JWTs, metering/rate-limit/circuit-breaker hooks, and capability proxying. |
| `llm-gateway` | `8787` | `8787` | OpenAI-compatible proxy, unified LLM/Embedding/rerank egress, and metering. |

### 3.3 Capability and RAG Services (5)

| Service | Container port | Dev host port | Responsibility |
|---|---:|---:|---|
| `knowledge-base-service` | `8000` | `8003` | Knowledge bases, document state, RAG integration, data sources, and ontology graph orchestration. |
| `atomic-rag` | `8000` | `8004` | Multimodal parsing, RAG tasks, and `ontology_data` production. |
| `business-domain-service` | `8000` | `8005` | Domain services, engines, adapters, skills, and templates. |
| `platform-service` | `8000` | `8006` | Login, RBAC, menus, application registration, auditing, and tasks. |
| `lightrag` | `9621` | `9621` | Indexing, retrieval, generation, and WebUI. |

Capability services are built with [`docker/capability.Dockerfile`](docker/capability.Dockerfile). `start_capability.py` loads capabilities and registers service discovery, `/invoke`, and `/health`. `atomic-rag` and LightRAG use separate images and runtime configuration.

### 3.4 Infrastructure Services (6)

| Service | Image/version | Container ports | Purpose |
|---|---|---:|---|
| `postgres` | PostgreSQL 15 | `5432` | Platform, business-domain, knowledge-base, and metering data. |
| `redis` | Redis 7 | `6379` | Service discovery, heartbeats, task state, caching, and governance state. |
| `etcd` | etcd 3.5 | `2379` | Milvus metadata dependency. |
| `minio` | Pinned MinIO version | `9000` / `9001` | Milvus object-storage dependency. |
| `milvus` | Milvus 2.5 | `19530` / `9091` | Vector retrieval. |
| `neo4j` | Neo4j 5.26 Community | `7474` / `7687` | Ontology ABox graph storage. |

## 4. Routes and Call Chains

Production browser paths:

| Path | Target |
|---|---|
| `/` | Shell |
| `/apps/{app-id}/**` | Shell hosted sub-application route |
| `/{app-id}/**` | Sub-application standalone route |
| `/remotes/{app-id}/**` | Module Federation remote assets |
| `/api/**` | API Gateway |

Backend business path:

```text
Browser / Client
  -> frontend-gateway
    -> gateway
      -> sidecar
        -> capability service
          -> service / repository
            -> PostgreSQL / Redis / Neo4j / external engine
```

RAG path:

```text
knowledge-base
  -> sidecar invoke
    -> atomic-rag
      -> lightrag

LLM, Embedding, and rerank calls from knowledge-base / atomic-rag / lightrag
  -> llm-gateway
    -> upstream model services
```

## 5. Network and Authentication

All containers join `jonex-network` and resolve one another by Compose service name. Key communication paths are:

| Path | Protocol and container port | Authentication |
|---|---|---|
| `frontend-gateway -> gateway` | HTTP `8000` | External user JWT is handled at the business entry point. |
| `gateway -> sidecar` | HTTP `8000` | Shared Sidecar API key. |
| `sidecar -> capability` | HTTP `8000` | Short-lived internal JWT issued by Sidecar. |
| `atomic-rag -> lightrag` | HTTP `9621` | `X-API-Key`. |
| LLM callers `-> llm-gateway` | HTTP `8787` | Internal token; upstream keys stay in the Gateway. |
| capability `-> postgres/redis` | TCP `5432` / `6379` | Database credentials and the internal network. |
| knowledge-base `-> neo4j` | Bolt `7687` | Neo4j username and password. |

Do not add backend or infrastructure ports to the production baseline for debugging convenience. Use a controlled VPN, SSH tunnel, or temporary override instead.

## 6. Persistent Data

| Named volume | Purpose |
|---|---|
| `jonex-postgres-data` | PostgreSQL data. |
| `jonex-redis-data` | Redis data. |
| `jonex-etcd-data` | etcd data. |
| `jonex-minio-data` | MinIO data. |
| `jonex-milvus-data` | Milvus data. |
| `jonex-neo4j-data` / `jonex-neo4j-logs` | Neo4j graph data and logs. |
| `jonex-rag-inputs` | Shared input files between Gateway, knowledge-base, atomic-rag, and LightRAG. |
| `jonex-rag-storage` | RAG intermediate artifacts and workspaces. |
| `jonex-rag-models` | Model caches. |
| `jonex-logs` | Aggregated application logs. |

Model caches use the default cache paths. Updating preloaded models in an image does not automatically replace an existing named volume; during a maintenance window, stop the affected services, back up the volume, and recreate it as required.

## 7. Health Checks

| Service | Check |
|---|---|
| PostgreSQL | `pg_isready` |
| Redis | `redis-cli ping` |
| etcd | `etcdctl endpoint health` |
| MinIO | `/minio/health/live` |
| Milvus | `/healthz` |
| Gateway / Sidecar / LLM Gateway / capabilities | `GET /health` |
| LightRAG | `GET /health` |
| Neo4j | HTTP `7474` |
| frontend-gateway / frontend containers | `GET /health` |

In development mode, verify from the host:

```bash
curl http://localhost/health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
curl http://localhost:8006/health
curl http://localhost:8787/health
curl http://localhost:9621/health
```

In production mode, check backend services from the container network or inside a container, for example:

```bash
docker exec jonex-gateway curl -fsS http://localhost:8000/health
```

## 8. Build and Operations Entry Points

```bash
make build
make up                  # Baseline + docker-compose.override.yml
make ps
make logs
make down

make build-prod
make up-prod             # docker-compose.yml only
make ps-prod
make logs-prod
make down-prod

make docker-local-up     # Baseline + docker-compose.debug.yml
```

GPU environment:

```bash
make build-gpu
make up-gpu
```

Single-service maintenance:

```bash
make rebuild-service SERVICE=platform-service
make restart-service SERVICE=platform-service
make logs-service SERVICE=platform-service
```

## 9. Configuration and Migrations

- Platform deployment variables: `deploy/.env`; template: `deploy/.env.example`.
- LightRAG variables: `deploy/.env.rag`; template: `deploy/.env.rag.example`.
- Capability runtime mode: `deploy/config/capability_runtime.yaml`.
- Ontology TBox: `deploy/config/ontology/default.yaml`.
- PostgreSQL initialization entry point: `deploy/postgres/init.sql`.
- Numbered migrations: `deploy/postgres/migrations/`.

Sensitive values must not be committed to Git. Production deployments must set separate credentials for the database, JWT, Sidecar, LLM Gateway, LightRAG, MinIO, and Neo4j at minimum.

## 10. Related Documentation

- [System architecture](../jonex-platform-architecture.md)
- [Deployment guide](README.md)
- [Backend development standards](../backend-development-standard.md)
- [Frontend development standards](../frontend-development-standard.md)
- [Local full-stack debugging guide](../local-fullstack-debugging-guide.md)