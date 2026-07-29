# deploy

`deploy/` 保存悦溪平台部署相关文件，包括 Docker 构建上下文、Nginx 配置和 PostgreSQL migration。

## 目录

```text
deploy/
├── docker/                      # 服务镜像 Dockerfile
├── nginx/                       # frontend-gateway 与子前端 Nginx 配置
└── postgres/
    └── migrations/              # PostgreSQL 初始化和迁移脚本
```

## 部署入口

生产环境浏览器只访问 `frontend-gateway`：

```text
frontend-gateway:80
  -> shell 和子前端静态资源
  -> /api/** -> gateway:8000
  -> LLM 调用：lightrag / knowledge-base -> llm-gateway:8787 -> 上游 LLM
```

后端服务、Sidecar、能力服务、RAG 服务、PostgreSQL、Redis、Milvus、etcd、MinIO 默认只在容器网络内访问。开发环境可以通过 `docker-compose.override.yml` 暴露常规调试端口；需要把单个业务后端或 `atomic-rag` 切到宿主机调试时，使用 `docker-compose.debug.yml`。

## Nginx 文件

| 文件 | 职责 |
|---|---|
| `nginx/frontend-gateway.conf` | 唯一前端入口，聚合 shell、子应用、remote assets 和 `/api/**` 反代。 |
| `nginx/expert-call.conf` | expert-call 子前端 standalone fallback 和 remote assets。 |

新增前端子应用时，需要同步：

- 子应用 Dockerfile。
- 子应用 `nginx/default.conf`。
- `deploy/nginx/frontend-gateway.conf` 中的 standalone 路由和 remote assets 反代。
- 平台后端应用注册表。
- `frontends/shell/public/app-manifest.json` 本地 fallback。

## PostgreSQL migrations

迁移脚本规则：

- 新业务表默认带 `tenant_id`、时间戳、软删除字段，必要时带审计字段。
- 平台共享元数据不带 `tenant_id`，例如应用、菜单、权限、系统配置。
- 平台运行数据和业务数据必须带合法 `tenant_id`。
- 本地开发和演示数据使用 `tenant_jonex_demo`。
- 不写入默认业务租户。

## 常用命令

```bash
make build
make up
make ps
make logs
make down
make docker-local-up
```

- `make up`：加载 `docker-compose.override.yml`，适合本地整套 Docker 联调并暴露常规调试端口。
- `make docker-local-up`：加载 `docker-compose.debug.yml`，适合其他服务留在 Docker、单个业务后端或 `atomic-rag` 在宿主机调试。`lightrag` 会暴露 `9621` 方便访问，但容器内 `atomic-rag` 默认仍通过 `http://lightrag:9621` 调用它。

单服务：

```bash
make rebuild-service SERVICE=platform-service
make restart-service SERVICE=platform-service
make logs-service SERVICE=platform-service
```

前端镜像：

```bash
make rebuild-frontend-gateway
make rebuild-shell-frontend
make rebuild-expert-call-frontend
make rebuild-core-business-frontend
make rebuild-platform-management-frontend
make rebuild-ecosystem-management-frontend
```

## 构建加速（已融入 compose 构建）

构建优化已**直接整合进 `docker compose build`**：抽取共享基础镜像 `python-base`、用 `COMPOSE_BAKE` 委托 buildx 并行构建、保留 apt/pip/pnpm 缓存挂载。产出的就是 `docker compose up` 实际运行的 `deploy-*` 镜像，**不再有单独的一套 `jonex/*` 镜像**。运行时产物与优化前一致（依赖集合/端口/命令/健康检查/前端 dist 不变）。

工作方式：四个能力服务 + gateway/sidecar/llm-gateway 这 7 个后端镜像的 Dockerfile 改为 `FROM ${PYTHON_BASE}`，compose 中通过 `additional_contexts: python-base: docker-image://jonex/python-base:local`（命名上下文用 `python-base`，避免与 Dockerfile 内 `AS base` 阶段别名撞名）复用预构建的共享基础层。

### 一键构建

```bash
# *nix / CI：先构建 python-base，再并行 compose build（输出秒级总耗时）
bash deploy/scripts/build_all.sh
bash deploy/scripts/build_all.sh gateway    # 仅构建某个 compose 服务

# Windows（cmd）
deploy\scripts\build_all.cmd

# make（自动先构建 base，再 COMPOSE_BAKE 并行构建）
make build            # 本地联调
make build-gpu        # GPU
make build-prod       # 生产
make build-backend    # 仅后端
make build-service SERVICE=gateway
```

等价的手动两步（脚本/Make 已封装）：

```bash
# 1) 构建共享基础镜像并 load 进本地镜像库（被 7 个后端服务复用）
docker buildx build --load -t jonex/python-base:local -f deploy/docker/python-base.Dockerfile .
# 2) 并行 compose 构建（委托 buildx bake）
cd deploy && COMPOSE_BAKE=1 docker compose build
```

> `python-base` 不是 compose 服务，`docker compose up` 不会启动它；它只作为构建期的命名上下文被引用。首次/依赖清单变更后会重建该层，之后命中缓存。

### 优化构成

| 优化项 | 说明 |
|---|---|
| 共享基础镜像 | `python-base.Dockerfile` 收敛 7 个后端服务的公共层（时区 / 腾讯源 / apt / pip 依赖）|
| 并行构建 | `COMPOSE_BAKE=1` 让 `docker compose build` 委托 buildx bake，按依赖图并行 |
| 前端 pnpm store 缓存 | 5 个前端共享 `--mount=type=cache,id=jonex-pnpm-store`，依赖未变零下载 |
| atomic-rag 层固化 | 固定层顺序，源码层为最后 `COPY`，仅源码变更只重建 1 层 |

### 构建耗时度量（可选）

```bash
python deploy/scripts/build_benchmark.py --scenario cold --repeat 3 --baseline deploy/build-baseline.json
python deploy/scripts/build_benchmark.py --scenario incremental --repeat 3 --baseline deploy/build-baseline.json
```

### 进阶：CI 跨机缓存（可选）

如需在 CI 跨 runner 复用构建层缓存，可在 compose 各服务的 `build.cache_from` / `build.cache_to` 中声明 registry 或 GHA 缓存（配合 `docker-container` builder），`COMPOSE_BAKE=1 docker compose build` 会将其透传给 buildx。本地默认 `docker` 驱动不支持 cache 导出，无需配置。

### 验证测试（可选）

```bash
# 构建优化相关的轻量单元 / 快照测试（无需 docker，毫秒级）
uv run pytest tests/unit/test_python_base_dockerfile.py tests/unit/test_build_benchmark.py
```

> 优化是否生效，最直接的方式是 `make build`（或 `deploy\scripts\build_all.cmd`）后 `docker compose up -d` 做一次冒烟。

## 健康检查与日志

```bash
# 前端 Nginx 健康检查（生产唯一对外端口）
curl http://localhost/health        # 返回 'ok'

# 开发模式（compose override 暴露端口）下后端可直连
curl http://localhost:8000/health   # 网关
curl http://localhost:8001/health   # Sidecar
curl http://localhost:8002/health   # 专家访谈
curl http://localhost:8003/health   # 知识库
curl http://localhost:8005/health   # 业务域
curl http://localhost:8006/health   # 平台
curl http://localhost:8787/health   # LLM 网关

# 生产模式后端不对外，进容器访问
docker exec jonex-gateway curl -s http://localhost:8000/health
```

日志：

```bash
make logs                 # 全部
make logs-service SERVICE=knowledge-base-service
make logs-sidecar
make logs-postgres
```

应用日志同时挂载到 `jonex-logs` 数据卷。

## 数据库管理

```bash
# 连接 PostgreSQL
make shell-postgres
# 或：docker exec -it jonex-postgres psql -U jonex -d jonex

# 初始化 / 重建 schema 与种子数据
make init-db
```

迁移脚本位于 `postgres/migrations/`，按编号顺序执行（`001_schemas` → `002_platform` → `003_expert_call` → `004_knowledge_base` → `005_business_domain` → `006_seed_data` → `007_comments`）。`postgres/init.sql` 为容器首次启动的聚合初始化入口。

> 说明：`001` 创建全部 schema（platform/expert_call/knowledge_base/business_domain/metering）；计量表 `metering.llm_usage_log` 并入 `002`；知识库文档存储列、数据源表、本体编译快照的可编辑字段均已并入 `004`；对应种子并入 `006`。

若数据卷在新增某 schema 前已初始化，可手动补建：

```bash
docker exec -i jonex-postgres psql -U jonex -d jonex < postgres/migrations/004_knowledge_base.sql
```

## GPU 加速（可选）

宿主机有 NVIDIA GPU 且已安装 `nvidia-container-toolkit` 时，叠加 `docker-compose.gpu.yml` 为 atomic-rag 启用 GPU：

```bash
make build-gpu     # 构建镜像
make up-gpu        # 启动（自动加载 gpu.yml）

# 验证 GPU 是否生效
docker exec jonex-atomic-rag python -c "import torch; print(torch.cuda.is_available())"
```

GPU 生效后 MinerU 解析器自动使用 CUDA，atomic-rag CPU 内存占用显著下降。

## 本体知识引擎运维

文档解析 + LightRAG 入库完成后，可选开启 Stage 4 本体抽取。当前职责划分：

- **atomic-rag** 负责抽取，产出 `ontology_data`（实体 / 关系），不直接写 Neo4j。
- **knowledge-base** 的对账服务（`reconciliation_service`）负责把 `ontology_data` 写入 Neo4j，再回写 PostgreSQL 的 `ontology_status` 状态机（先写 Neo4j、成功后置 `READY`，失败置 `FAILED`）。
- Neo4j schema 在 knowledge-base 启动时由 `ensure_ontology_schema()` 自动初始化，失败仅告警不阻塞服务。
- Neo4j 不可用时，知识库查询和文档 READY 流程降级到普通 RAG，不阻塞基础能力。

### 启用方式

在 `deploy/.env` 中开启抽取开关并重启 atomic-rag：

```bash
# deploy/.env
ONTOLOGY_EXTRACT_ENABLED=true
ONTOLOGY_SCHEMA_PATH=deploy/config/ontology/default.yaml

make restart-service SERVICE=atomic-rag
```

本体 TBox 定义见 `deploy/config/ontology/default.yaml`（实体类型、别名、属性、关系类型）。

### Neo4j 容器

```bash
# 约束检查
docker exec jonex-neo4j cypher-shell -u neo4j -p jonex_neo4j_123 "SHOW CONSTRAINTS;"

# 查看本体实体
docker exec jonex-neo4j cypher-shell -u neo4j -p jonex_neo4j_123 \
  "MATCH (n:OntologyEntity) RETURN n.tenant_id, n.entity_type, n.canonical_name LIMIT 10;"
```

### 增强搜索（本体优先）

```bash
curl "http://localhost:8000/api/v1/knowledge-base/documents/search/enhanced?query=腾讯&knowledge_base_id=KB1&mode=hybrid&top_k=3" \
     -H "Authorization: Bearer jonex_test_tenant123"
```

返回 `{answer, source:"ontology"|"rag", ontology_instances:[...], rag_used:boolean}`：`source="ontology"` 表示基于 Neo4j 图谱事实 + LLM 回答；`source="rag"` 表示本体未命中、回退完整 RAG。

`ontology_status` 为 `pending`/`failed` 的文档由对账循环自动重试。

### 本体相关环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ONTOLOGY_EXTRACT_ENABLED` | `false` | 是否启用本体抽取 |
| `ONTOLOGY_SCHEMA_PATH` | `deploy/config/ontology/default.yaml` | TBox schema 路径 |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j 连接地址 |
| `NEO4J_USERNAME` | `neo4j` | Neo4j 用户名 |
| `NEO4J_PASSWORD` | `jonex_neo4j_123` | Neo4j 密码 |

## 数据备份

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

## 故障排查

服务无法启动：

```bash
make logs-service SERVICE=<service>     # 查看详细日志
make restart-service SERVICE=<service>  # 重启单个服务
make recreate-service SERVICE=<service> # 强制重建
```

数据库连接失败：

```bash
make ps                                 # 检查容器状态
make logs-postgres                      # 查看 PostgreSQL 日志
docker exec jonex-postgres pg_isready -U jonex
```

性能问题：

```bash
docker stats                            # 容器资源占用
make logs-sidecar
make logs-service SERVICE=knowledge-base-service
```

## 快速部署步骤

```bash
make init                # 初始化 .env / .env.rag（首次）
# 编辑 deploy/.env、deploy/.env.rag，确保两边 LIGHTRAG_API_KEY 一致
make build && make up    # 构建并启动本地 Docker 部署（加载 override）
make ps                  # 验证状态
make logs                # 查看日志
```

宿主机单服务调试使用 `make docker-local-up`。生产 / 服务器编排使用 `make build-prod` / `make up-prod` 或 `make build-server` / `make up-server`。

详细部署拓扑见 [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)。
