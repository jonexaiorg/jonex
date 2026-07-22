# Jonex平台 Docker 部署指南

## 🚀 快速开始

### 1. 环境准备

```bash
# 检查 Docker 和 Docker Compose
docker --version
docker-compose --version
```

### 2. 初始化配置

```bash
# 进入项目根目录
cd jonex-platform

# 使用 Makefile 初始化
make init

# 或手动复制
cp deploy/.env.example deploy/.env
cp deploy/.env.rag.example deploy/.env.rag      # LightRAG 容器专属配置（含 LLM/Embedding/存储后端）
# 编辑 deploy/.env 和 deploy/.env.rag 配置文件
# 注意：deploy/.env 中的 LIGHTRAG_API_KEY 必须与 deploy/.env.rag 中的 LIGHTRAG_API_KEY 保持一致
```

### 3. 启动服务

**开发模式**（默认，自动加载 `docker-compose.override.yml`）：
```bash
# 方式一：使用 Makefile（Linux/macOS）
make build
make up           # Gateway 8000 / Sidecar 8001 对外，便于直连调试

# 方式二：使用 jonex.ps1（Windows）
.\jonex.ps1 build
.\jonex.ps1 up

# 方式三：使用 docker-compose
cd deploy
docker-compose build
docker-compose up -d
```

**生产模式**（仅暴露 Frontend 80）：
```bash
make up-prod                # 显式跳过 override.yml
.\jonex.ps1 up-prod
# 或：cd deploy && docker-compose -f docker-compose.yml up -d
```

### 4. 验证服务

```bash
# 查看服务状态
make ps

# 查看日志
make logs

# 健康检查
make test

# 访问健康检查接口
curl http://localhost:8000/health   # 网关
curl http://localhost:8001/health   # Sidecar
```

## 📦 服务列表

| 服务名称 | 容器内端口 | 开发模式宿主端口 | 生产模式宿主端口 | 说明 |
|---------|-----------|----------------|-----------------|------|
| **frontend** | 80 | 80 | **80** | 前端 Nginx，唯一对外入口（静态资源 + /api 反向代理） |
| **gateway** | 8000 | 8000 | 仅容器内 | API 网关（业务路由聚合、CORS） |
| **sidecar** | 8000 | 8001 | 仅容器内 | 内部能力代理（认证、计量、限流） |
| **knowledge-base-service** | 8000 | 8003 | 仅容器内 | 知识库能力服务 |
| **atomic-rag** | 8000 | 8004 | 仅容器内 | RAG 原子能力服务（解析 + HTTP 调 lightrag） |
| **lightrag** | 9621 | 9621 | 仅容器内 | LightRAG 引擎 + WebUI（源码自建镜像 jonex-lightrag-source，源码集成于 Reference/LightRAG，think 开关默认关闭 Qwen3.5 思考模式） |
| **redis** | 6379 | 6379 | 6379 | Redis 缓存 / 服务发现 |
| **neo4j** | 7687 / 7474(browser) | — | 仅容器内 | Neo4j 5.26 图数据库（本体 ABox 存储，APOC 插件，持久化卷 jonex-neo4j-data） |
| **milvus** / **etcd** / **minio** | - | - | 仅容器内 | 预留：知识库存储后端切 PG/Milvus 时启用（首版未连） |

> 端口策略：开发模式自动加载 `docker-compose.override.yml`，把 Gateway 8000、Sidecar 8001、lightrag 9621、atomic-rag 8004 同时映射到宿主机便于直连调试；生产模式 (`make up-prod` / `.\jonex.ps1 up-prod`) 显式跳过 override，仅暴露 Frontend 80。

> 知识库 RAG 链路：浏览器 → Frontend → Gateway（文件落地）→ Sidecar → knowledge-base 服务（业务层 CRUD + 状态机）→ Sidecar → atomic-rag（解析）→ lightrag（向量/图谱/LLM）。**lightrag 不直接对外**，所有调用必须经过 atomic-rag 包装。knowledge-base 不参与文件 IO，仅处理 file_path 字符串。

## 🔧 常用命令

### 使用 Makefile

```bash
# 查看所有命令
make help

# 构建镜像
make build

# 启动服务
make up

# 停止服务
make down

# 查看日志
make logs
make logs-sidecar
make logs-knowledge-base

# 进入容器
make shell-sidecar
make shell-postgres
```

### 使用 Docker Compose

```bash
cd deploy

# 构建所有镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f sidecar
docker-compose logs -f knowledge-base-service

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和数据卷（慎用）
docker-compose down -v
```

## 📊 扩缩容

```bash

# 或直接使用 docker-compose
cd deploy
```

## 🔨 开发模式

```bash
# 开发模式启动（代码热重载）
make dev
```

## 📈 监控

### 健康检查

```bash
# 前端 Nginx 健康检查（生产唯一对外端口）
curl http://localhost/health        # 返回 'ok'（text/plain）

# 开发模式下后端服务可直连
curl http://localhost:8000/health   # 网关
curl http://localhost:8001/health   # Sidecar
curl http://localhost:8003/health   # 知识库服务（首次需先 docker-compose up -d knowledge-base-service）

# 生产模式下后端不对外，需进容器或通过反代访问
docker-compose exec gateway curl http://localhost:8000/health
```

### 日志位置

- 容器日志：通过 `docker logs` 查看
- 应用日志：挂载到 `jonex-logs` 数据卷

## 🗄️ 数据库管理

### 连接数据库

```bash
# 使用 Makefile
make shell-postgres

# 或直接连接
cd deploy
docker-compose exec postgres psql -U jonex -d jonex
```

### 初始化本体表

如果 PostgreSQL 数据卷在添加 `ontology` schema 之前已初始化，需要手动补建：

```bash
cd deploy
docker-compose exec -T postgres psql -U jonex -d jonex < postgres/init.sql
```

或只建 ontology 部分：

```bash
docker exec jonex-postgres psql -U jonex -d jonex -c "CREATE SCHEMA IF NOT EXISTS ontology;"
```

## 🚀 GPU 加速（可选）

宿主机有 NVIDIA GPU 并已安装 `nvidia-container-toolkit` 时，叠加 `docker-compose.gpu.yml` 为 atomic-rag 启用 GPU：

```bash
# 使用 Makefile（推荐）
make docker-gpu-build    # 构建镜像
make docker-gpu-up       # 启动（自动加载 gpu.yml）

# 或手动指定
cd deploy
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# 验证 GPU 是否生效
docker exec jonex-atomic-rag python -c "import torch; print(torch.cuda.is_available())"
```

GPU 生效后 MinerU 解析器自动使用 CUDA，atomic-rag CPU 内存占用从 ~4G 降至 ~2G。

## 🧠 本体知识引擎（Ontology Engine）

文档解析 + LightRAG 入库完成后，可选开启 Stage 4 本体抽取，将结构化实体和关系写入 Neo4j 图数据库（`:OntologyEntity` 节点 / `[:ONT_REL]` 边），实现跨文档实体自动连通。

### 启用方式

在 `deploy/.env` 中添加：

```bash
ONTOLOGY_EXTRACT_ENABLED=true
```

重启 atomic-rag：

```bash
cd deploy
docker compose up -d atomic-rag
```

### 本体 schema 配置

本体 TBox 定义在 YAML 文件中，默认路径 `deploy/config/ontology/default.yaml`：

```yaml
entity_types:
  - name: Organization
    aliases: ["公司", "企业"]
    attributes:
      - { name: legal_name, type: string }
relation_types:
  - name: BELONGS_TO
    source: Person
    target: Organization
```

自定义 schema 可通过 `ONTOLOGY_SCHEMA_PATH` 环境变量指定。

### Neo4j 容器

Neo4j 随 `docker compose up` 自动启动，schema 由 knowledge-base 服务启动时自动初始化（`ensure_ontology_schema()`）：

```bash
# 健康检查
docker exec jonex-neo4j cypher-shell -u neo4j -p jonex_neo4j_123 "SHOW CONSTRAINTS;"

# 查看本体实体
docker exec jonex-neo4j cypher-shell -u neo4j -p jonex_neo4j_123 \
  "MATCH (n:OntologyEntity) RETURN n.tenant_id, n.entity_type, n.canonical_name LIMIT 10;"
```

### 本体查询（Ontology Query）

增强搜索 API 实现本体优先分流，通过 API Gateway 调用：

```bash
curl "http://localhost:8000/api/v1/knowledge-base/documents/search/enhanced?query=腾讯&knowledge_base_id=KB1&mode=hybrid&top_k=3" \
     -H "Authorization: Bearer jonex_test_tenant123"
```

返回格式：`{answer, source:"ontology"|"rag", ontology_instances:[...], rag_used:boolean}`

- `source="ontology"`：基于 Neo4j 图谱事实 + LLM 回答，未使用 RAG
- `source="rag"`：本体未命中或知识不足，回退到完整 RAG

解析结果实体/关系类型覆盖：

```bash
# 获取解析结果实体列表（Neo4j 实体类型叠加）
curl "http://localhost:8000/api/v1/knowledge-base/bases/KB1/parse-result/entities?entity_type=Organization" \
     -H "Authorization: Bearer jonex_test_tenant123"
```

### 本体重试

`ontology_status` 为 `pending` 或 `failed` 的文档会由对账循环自动重试（最多 3 次），也可手动触发：

```bash
curl -X POST http://localhost:8003/invoke \
  -H "Authorization: Bearer jonex_test_tenant123" \
  -d '{"action": "retry_ontology_extract", "data": {"document_id": "...", "knowledge_base_id": "..."}}'
```

### 配置参考

关键环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ONTOLOGY_EXTRACT_ENABLED` | `false` | 是否启用本体抽取 |
| `ONTOLOGY_SCHEMA_PATH` | `deploy/config/ontology/default.yaml` | TBox schema 路径 |
| `ONTOLOGY_LLM_BINDING_HOST` | `LLM_BINDING_HOST` | 本体抽取 LLM 地址 |
| `ONTOLOGY_LLM_MODEL` | `deepseek-v4-flash` | 本体抽取 LLM 模型 |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j 连接地址 |
| `NEO4J_USERNAME` | `neo4j` | Neo4j 用户名 |
| `NEO4J_PASSWORD` | `jonex_neo4j_123` | Neo4j 密码 |

### 扩展点（待实现）

- **多 domain 支持**：`ONTOLOGY_SCHEMA_DIR` 加载多个 YAML 文件，按 `domain` 区分
- **知识库→domain 映射**：通过 `extra_metadata` 指定知识库所属 domain
- **本体查询增强**：查询结果用本体实体做事实校验 / rerank

### 数据备份

```bash
# 备份 PostgreSQL
docker exec jonex-postgres pg_dump -U jonex jonex > backup_$(date +%Y%m%d).sql

# 备份 Redis
docker exec jonex-redis redis-cli BGSAVE
docker cp jonex-redis:/data/dump.rdb ./redis_backup.rdb

# 备份 Neo4j
docker exec jonex-neo4j neo4j-admin database dump neo4j --to-path=/backups
docker cp jonex-neo4j:/backups ./neo4j_backup
```

## 🚀 生产部署

### 1. 环境配置

复制生产环境配置：

```bash
cp deploy/.env.example deploy/.env.production
# 修改为生产环境配置
```

### 2. 使用生产环境配置启动

```bash
cd deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. 建议配置

- **高可用**：使用 PostgreSQL 主从复制
- **缓存集群**：部署 Redis Cluster
- **负载均衡**：使用 Nginx 或云服务商 LB
- **监控告警**：接入 Prometheus + Grafana + Alertmanager

## 🔍 故障排查

### 服务无法启动

```bash
# 查看详细日志
docker-compose logs --tail=100 [service_name]

# 重启单个服务
docker-compose restart [service_name]

# 重建服务
docker-compose up -d --force-recreate [service_name]
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否正常运行
docker-compose ps postgres

# 查看 PostgreSQL 日志
docker-compose logs postgres

# 手动连接测试
docker-compose exec postgres pg_isready -U jonex
```

### 性能问题

```bash
# 查看容器资源使用
docker stats

# 查看服务内部日志
make logs-sidecar
```

## 📝 文件结构

```
deploy/
├── docker/                          # Dockerfile
│   ├── sidecar.Dockerfile          # Sidecar 代理镜像
│   ├── capability.Dockerfile       # 能力服务镜像模板
│   ├── gateway.Dockerfile          # API Gateway 镜像
│   ├── frontend-entrypoint.py      # 运行时注入 window.__JONEX_CONFIG__
│   ├── atomic-rag.Dockerfile       # RAG 原子能力服务镜像
│   ├── atomic-rag-requirements.txt # atomic-rag 专属依赖
│   └── lightrag-source.Dockerfile # LightRAG 源码自建镜像（Reference/LightRAG 1.4.16）
├── nginx/
│   └── frontend.conf               # 前端 Nginx 配置（CSP / SPA 回退 / API 反代）
├── docker-compose.yml              # 生产 Compose 编排
├── docker-compose.override.yml     # 开发模式覆盖（Gateway/Sidecar 端口对外）
├── docker-compose.gpu.yml          # GPU 加速覆盖（NVIDIA GPU）
├── docker-compose.mac.yml          # macOS 开发覆盖（CPU 降配）
├── .env.example                    # 环境变量模板
├── postgres/                       # PostgreSQL 配置
├── config/                         # 运行时配置
│   └── ontology/                   # 本体 schema 定义（TBox YAML）
├── redis/                          # Redis 配置
│   └── redis.conf                  # Redis 配置文件
├── DEPLOYMENT_ARCHITECTURE.md      # 架构设计文档
└── README.md                       # 本文档
```

## 🎯 快速部署步骤总结

```bash
# 1. 克隆项目
git clone <repository-url>
cd jonex-platform

# 2. 初始化配置
make init
# 编辑 deploy/.env

# 3. 构建并启动
make build && make up

# 4. 验证服务
make test

# 5. 查看日志
make logs
```

## 📞 技术支持

如遇问题，请：
1. 查看服务日志：`make logs`
2. 检查配置文件：`deploy/.env`
3. 参考架构设计文档：`DEPLOYMENT_ARCHITECTURE.md`
