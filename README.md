# 悦溪平台 Jonex Platform

悦溪平台是一个插件化、多租户的 AI 能力平台，包含前端工作台、统一 API Gateway、Sidecar 能力治理层、多个后端 capability service、RAG 原子能力和基础设施组件。知识库能力支持 RAG + 本体知识引擎，覆盖 TBox 配置、Stage4 本体抽取、Neo4j ABox 图存储和增强搜索。

当前项目按“全新最终态”维护。新增子应用、新页面、新接口、新实体和新服务不要复制历史旧实现，应优先遵循：

- [jonex-platform-architecture.md](jonex-platform-architecture.md)：系统架构设计文档，包含前端、后端、部署、租户和能力体系。
- [backend-development-standard.md](backend-development-standard.md)：后端开发规范。
- [frontend-development-standard.md](frontend-development-standard.md)：前端开发规范。
- [local-fullstack-debugging-guide.md](local-fullstack-debugging-guide.md)：本地前后端联调和 VSCode Debug 配置说明。

## 架构概览

```text
用户浏览器
  -> frontend-gateway (Nginx, 80)
     -> shell / core-business / platform-management / ecosystem-management
     -> /api/** -> API Gateway (8000)
        -> Sidecar (8001)
           -> platform (8006)
           -> business-domain (8005)
           -> knowledge-base (8003)
           -> atomic-rag (8004) -> lightrag (9621)
                                  -> llm-gateway (8787)  ← 所有 LLM/Embedding 出口
                                                     -> TokenHub / Ollama 等上游

PostgreSQL / Redis / Milvus / etcd / MinIO
```

核心原则：

- 浏览器生产环境只进入 `frontend-gateway`。
- 前端业务请求统一调用 `/api/v1/**`。
- Gateway 保持薄层，只做 HTTP 路由聚合。
- Sidecar 统一做认证、租户上下文、内部 JWT、计量、限流、熔断和能力代理。
- Capability Service 承载业务规则，按 `api/models/repository/services/dtos` 分层。
- 所有业务数据必须显式使用合法 `tenant_id`，禁止默认租户兜底。

知识库能力的本体链路由 knowledge-base service 编排：atomic-rag 产出解析结果和 `ontology_data`，knowledge-base service 负责文档状态、Neo4j 写入、增强搜索和 RAG 降级。

## 目录结构

```text
jonex-platform/
├── api_gateway/                 # FastAPI API Gateway
├── capabilities/                # 后端 capability services
│   ├── platform/
│   ├── business_domain/
│   └── knowledge_base/
├── frontends/                   # pnpm workspace 前端工作区
│   ├── shell/
│   ├── core-business/
│   ├── platform-management/
│   ├── ecosystem-management/
│   ├── shared/
│   └── dev-gateway/             # 本地开发 Node.js 网关（替代 Nginx）
├── jonex_core/                  # 公共内核、Sidecar、能力 SDK、数据库基础设施、LLM 网关
├── deploy/                      # Docker、Nginx、PostgreSQL migrations
├── tests/
├── dev-guide.macos.md           # macOS/Linux 本地调试指南
├── dev-guide.windows.md         # Windows 本地调试指南
```

## 前端应用

`frontends/` 是 pnpm workspace。Shell 是统一入口，业务子应用通过应用注册表挂载。

| 应用 | 包名 | hosted 路径 | standalone 路径 | dev 端口 |
|---|---|---|---|---|
| Shell | `@jonex/shell` | `/` | `/` | `5173` |
| 核心业务 | `@jonex/core-business` | `/apps/core-business` | `/core-business/` | `5175` |
| 生态管理 | `@jonex/ecosystem-management` | `/apps/ecosystem-management` | `/ecosystem-management/` | `5176` |
| 平台管理 | `@jonex/platform-management` | `/apps/platform-management` | `/platform-management/` | `5177` |

生产应用清单以平台后端接口为准：

```text
GET /api/v1/platform/frontend/apps
```

`frontends/shell/public/app-manifest.json` 只作为本地开发和后端不可用时的 fallback。

## 后端服务

| 服务 | 目录 | dev 端口 | 职责 |
|---|---|---|---|
| API Gateway | `api_gateway/` | `8000` | 外部 API 路由聚合 |
| Sidecar | `jonex_core/sidecar/` | `8001` | 认证、治理、能力代理 |
| LLM 网关 | `jonex_core/llm_gateway/` | `8787` | OpenAI 兼容代理，统一 LLM/Embedding 出口计量 |
| Knowledge Base | `capabilities/knowledge_base/` | `8003` | 知识库、文档状态机、RAG 接入、数据源接入（API/存储直连/API开放推送） |
| Atomic RAG | `atomic-rag/` | `8004` | RAG 原子能力 |
| Business Domain | `capabilities/business_domain/` | `8005` | 领域空间、服务、引擎、适配器 |
| Platform | `capabilities/platform/` | `8006` | 登录、RBAC、菜单、应用注册、审计、任务 |

## 本地开发

详细本地调试流程（依赖安装、环境文件、VSCode Debug、Docker、RAG、登录鉴权）见：

- macOS / Linux：[dev-guide.macos.md](dev-guide.macos.md)
- Windows：[dev-guide.windows.md](dev-guide.windows.md)

```bash
# 快速起步（macOS/Linux）
make init                    # 首次：初始化环境文件
make dev-infra-up            # 启动中间件依赖
make dev-gateway             # Dev Gateway http://localhost:8080
make dev-frontend            # 启动前端

# Windows
.\jonex.ps1 init
.\jonex.ps1 dev-infra-up
.\jonex.ps1 dev-gateway
.\jonex.ps1 dev-frontend
```

## API 和租户约定

- 外部 API 统一为 `/api/v1/{capability}/**`。
- 前端不得直连 Sidecar、capability service、容器名或宿主调试端口。
- 知识库入站推送端点 `POST /api/v1/knowledge-base/ingest/{ds_id}` 是面向外部系统的公开端点，用 `X-Ingest-Key` 鉴权（非用户 JWT），租户由 ingest key 解析得到；仍经 Gateway → Sidecar，不绕过治理层。
- 普通业务请求 body 不传 `tenant_id`。
- 租户来自认证上下文、JWT 解析结果或 `X-Tenant-ID`。
- `/api/v1/auth/login` 是认证引导端点，本地 seed 可直接使用 `admin/admin123` 登录；若同一用户名存在多个租户账号，需要携带 `X-Tenant-ID` 明确选择租户。
- 本地开发和演示数据使用 `tenant_jonex_demo`。
- `default`、`default_tenant`、`system` 只允许作为禁止值出现在校验规则和规范文档中。

## 调用方式

平台对外只暴露 `frontend-gateway`，业务请求统一走 `/api/v1/**`。下面三种方式按使用场景区分。

### 方式一：经 API Gateway（业务路径，前端与外部统一入口）

```bash
# 知识库增强语义搜索（本体优先：Neo4j 图谱事实 → LLM 回答 → RAG fallback）
curl "http://localhost/api/v1/knowledge-base/documents/search/enhanced?query=腾讯&knowledge_base_id=KB1&mode=hybrid&top_k=3" \
     -H "Authorization: Bearer <access_token>"

# 平台用户列表
curl "http://localhost/api/v1/platform/users" \
     -H "Authorization: Bearer <access_token>"
```

### 方式二：经 Sidecar 统一 invoke 契约（内部 / 集成调试）

Sidecar（dev 端口 `8001`）提供统一的能力发现与调用入口，前端不得直连，仅用于内部集成或调试。

```bash
# 列出已注册能力
curl http://localhost:8001/capabilities \
     -H "Authorization: Bearer jonex_test_tenant_jonex_demo"

# 统一 invoke 契约
curl -X POST http://localhost:8001/invoke \
     -H "Authorization: Bearer jonex_test_tenant_jonex_demo" \
     -H "Content-Type: application/json" \
     -d '{
           "capability_id": "business.knowledge_base.v1",
           "payload": {"action": "list_documents", "knowledge_base_id": "KB1"}
         }'
```

`/invoke` 请求体字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `capability_id` | 是 | 能力 ID，如 `business.knowledge_base.v1` |
| `payload` | 是 | 能力具体入参（含 action 与业务参数） |
| `tenant_id` | 否 | 仅用于与认证上下文/Header 做一致性校验，不作为新租户来源 |
| `user_id` | 否 | 调用方用户标识 |
| `context` | 否 | 透传上下文 |

返回 `InvokeResult`：`{request_id, success, code, message, data, latency_ms}`。流式能力使用 `/invoke/stream` 与 `/invoke/stream/rag`。

### 方式三：直接访问 capability service（仅本地调试）

各 capability service 在本地暴露独立端口（knowledge-base `8003`、business-domain `8005`、platform `8006`），仅用于本地断点调试，生产不对外。健康检查：

```bash
curl http://localhost:8003/health
```

## 能力契约

能力 ID 统一格式 `{kind}.{name}.v{major}`，例如 `business.knowledge_base.v1`、`domain.rag.text.v1`、`atomic.rag.lightrag.v1`。能力分三层：

- **Business**：用户可感知的业务域，拥有独立数据库 schema，可被 Gateway/Sidecar 调用。
- **Domain**：模态/领域级编排，组合多个 atomic 能力，不承载子应用 CRUD。
- **Atomic**：封装单一技术组件（LLM、Vector、Audio、RAG），对上提供稳定 client。

完整契约与分层规则见 [backend-development-standard.md](backend-development-standard.md) 第 9 节「Capability 契约规范」。

## 文档索引

| 文档 | 用途 |
|---|---|
| [jonex-platform-architecture.md](jonex-platform-architecture.md) | 稳定系统架构、服务边界、目录结构、配置和开发规范。 |
| [backend-development-standard.md](backend-development-standard.md) | 后端 capability service、租户、Repository、DTO 和接口开发规范。 |
| [frontend-development-standard.md](frontend-development-standard.md) | 前端 workspace、子应用、路由、shared 包和页面开发规范。 |
| [dev-guide.macos.md](dev-guide.macos.md) / [dev-guide.windows.md](dev-guide.windows.md) | 本地前后端调试（VSCode Debug、环境文件、RAG venv、常见问题）。 |
| [PROJECT_ISSUES_AND_TODO.md](PROJECT_ISSUES_AND_TODO.md) | 项目议题、风险、后续演进和开发状态跟踪。 |
| [docs/ontology-knowledge-engine-execution-plan.md](docs/ontology-knowledge-engine-execution-plan.md) | 本体知识引擎详细执行计划、阶段任务和历史决策。 |

## 新功能入口

新增后端功能时，从 [backend-development-standard.md](backend-development-standard.md) 开始，先确定实体、租户边界、Repository、Service、DTO 和 Gateway/Sidecar 调用链。

新增前端功能时，从 [frontend-development-standard.md](frontend-development-standard.md) 开始，先确定应用归属、路由、注册表、shared 依赖、API service、页面状态和权限展示。

系统整体设计以 [jonex-platform-architecture.md](jonex-platform-architecture.md) 为准。
