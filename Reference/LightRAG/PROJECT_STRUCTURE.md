# LightRAG 工程结构文档

> **版本**: 1.4.16 | **API 版本**: 0292 | **许可证**: MIT
>
> LightRAG 是一个基于图结构知识表示的高级检索增强生成（RAG）框架，旨在通过知识图谱提升信息检索与生成的质量。

---

## 目录

1. [项目概述](#1-项目概述)
2. [工程目录结构](#2-工程目录结构)
3. [核心架构](#3-核心架构)
4. [存储后端](#4-存储后端)
5. [LLM 提供商](#5-llm-提供商)
6. [API 服务](#6-api-服务)
7. [Web 前端](#7-web-前端)
8. [工具脚本](#8-工具脚本)
9. [快速开始](#9-快速开始)
10. [配置与环境变量](#10-配置与环境变量)
11. [Docker 部署](#11-docker-部署)
12. [Kubernetes 部署](#12-kubernetes-部署)
13. [开发指南](#13-开发指南)

---

## 1. 项目概述

LightRAG 是一个简单、快速的检索增强生成框架。与传统的仅依赖向量检索的 RAG 系统不同，LightRAG 引入了**知识图谱**来表示和检索信息，能够更好地捕捉实体间的结构化关系，从而提升检索的准确性和上下文完整性。

### 核心特性

| 特性 | 说明 |
|------|------|
| 图结构知识表示 | 自动从文档中提取实体和关系，构建知识图谱 |
| 多模式查询 | 支持 local / global / hybrid / naive / mix / bypass 六种检索模式 |
| 多存储后端 | KV 存储、向量存储、图存储均支持多种数据库 |
| 多 LLM 提供商 | 兼容 OpenAI、Anthropic、Gemini、Ollama 等 16+ 种 LLM |
| 异步并发 | 全异步架构，支持高并发 LLM 调用和 Embedding 计算 |
| 工作空间隔离 | 支持 workspace 级别的数据隔离，同一实例多知识库并存 |
| API 服务 | FastAPI 提供完整的 RESTful API，含文档管理、查询、图谱操作 |
| Web UI | React 19 + TypeScript 前端，支持图谱可视化、文档管理、检索测试 |
| 认证授权 | JWT Token 认证，支持多用户账号管理 |
| 混合部署 | 支持 Docker Compose、Kubernetes、离线部署 |

---

## 2. 工程目录结构

```
LightRAG/
│
├── lightrag/                          # 核心 Python 包
│   ├── __init__.py                    # 包入口，导出 LightRAG 类
│   ├── _version.py                    # 版本号定义 (1.4.16)
│   ├── lightrag.py                    # 核心编排器 (LightRAG 主类)
│   ├── base.py                        # 抽象基类 (Storage, QueryParam 等)
│   ├── operate.py                     # 核心操作 (分块、实体提取、查询执行)
│   ├── prompt.py                      # LLM 提示词模板
│   ├── rerank.py                      # 重排序 (Rerank) 逻辑
│   ├── types.py                       # 数据类型定义 (KnowledgeGraph 等)
│   ├── constants.py                   # 全局常量与默认配置
│   ├── namespace.py                   # 存储命名空间定义
│   ├── exceptions.py                  # 自定义异常类
│   ├── utils.py                       # 工具函数 (日志、哈希、编码等)
│   ├── utils_graph.py                 # 图操作工具函数
│   │
│   ├── kg/                            # 知识图谱存储后端实现
│   │   ├── json_kv_impl.py            # JSON 文件 KV 存储
│   │   ├── json_doc_status_impl.py    # 文档处理状态存储
│   │   ├── nano_vector_db_impl.py     # NanoVectorDB 向量存储
│   │   ├── faiss_impl.py              # FAISS 向量存储
│   │   ├── milvus_impl.py             # Milvus 向量存储
│   │   ├── qdrant_impl.py             # Qdrant 向量存储
│   │   ├── redis_impl.py              # Redis KV + 向量存储
│   │   ├── mongo_impl.py              # MongoDB 存储
│   │   ├── neo4j_impl.py              # Neo4j 图存储
│   │   ├── memgraph_impl.py           # Memgraph 图存储
│   │   ├── opensearch_impl.py         # OpenSearch 存储
│   │   ├── postgres_impl.py           # PostgreSQL (PGVector + AGE) 存储
│   │   ├── networkx_impl.py           # NetworkX 内存图存储
│   │   ├── shared_storage.py          # 多进程共享存储管理
│   │   └── deprecated/                # 已废弃的实现
│   │
│   ├── llm/                           # LLM 提供商绑定
│   │   ├── openai.py                  # OpenAI
│   │   ├── azure_openai.py            # Azure OpenAI
│   │   ├── anthropic.py               # Anthropic Claude
│   │   ├── gemini.py                  # Google Gemini
│   │   ├── ollama.py                  # Ollama 本地模型
│   │   ├── bedrock.py                 # AWS Bedrock
│   │   ├── hf.py                      # HuggingFace
│   │   ├── jina.py                    # Jina AI
│   │   ├── voyageai.py                # VoyageAI
│   │   ├── zhipu.py                   # 智谱 AI (GLM)
│   │   ├── nvidia_openai.py          # NVIDIA NIM
│   │   ├── lmdeploy.py               # LMDeploy
│   │   ├── lollms.py                 # Lollms
│   │   ├── llama_index_impl.py       # LlamaIndex 集成
│   │   ├── binding_options.py         # 各绑定的配置选项类
│   │   └── deprecated/                # 已废弃的实现
│   │
│   ├── api/                           # FastAPI 服务
│   │   ├── lightrag_server.py         # 主服务入口
│   │   ├── config.py                  # 服务配置 (CLI 参数解析)
│   │   ├── auth.py                    # JWT 认证处理器
│   │   ├── passwords.py               # 密码验证
│   │   ├── utils_api.py               # API 工具函数
│   │   ├── gunicorn_config.py         # Gunicorn 配置
│   │   ├── run_with_gunicorn.py       # Gunicorn 启动器
│   │   ├── runtime_validation.py      # 运行时环境校验
│   │   ├── routers/                   # API 路由
│   │   │   ├── document_routes.py     # 文档上传/管理路由
│   │   │   ├── query_routes.py        # 查询路由
│   │   │   ├── graph_routes.py        # 图谱操作路由
│   │   │   └── ollama_api.py          # Ollama 兼容 API
│   │   └── static/                    # 静态资源
│   │
│   ├── evaluation/                    # 评测模块
│   │   ├── eval_rag_quality.py        # RAGAS 评测
│   │   ├── offline_retrieval_check.py # 离线检索验证
│   │   └── sample_documents/          # 评测样本
│   │
│   └── tools/                         # CLI 工具
│       ├── clean_llm_query_cache.py   # 清理 LLM 查询缓存
│       ├── download_cache.py          # 下载 Tiktoken 缓存
│       ├── hash_password.py           # 密码哈希生成
│       ├── migrate_llm_cache.py       # LLM 缓存迁移
│       ├── check_initialization.py    # 初始化状态检查
│       └── lightrag_visualizer/       # 图谱可视化工具
│
├── lightrag_webui/                    # React 前端
│   ├── src/
│   │   ├── App.tsx                    # 根应用组件
│   │   ├── AppRouter.tsx              # 路由配置
│   │   ├── main.tsx                   # 应用入口
│   │   ├── i18n.ts                    # 国际化配置
│   │   ├── api/                       # API 调用层
│   │   ├── features/                  # 功能页面
│   │   │   ├── RetrievalTesting.tsx   # 检索测试页
│   │   │   ├── DocumentManager.tsx    # 文档管理页
│   │   │   ├── GraphViewer.tsx        # 图谱可视化页
│   │   │   └── LoginPage.tsx          # 登录页
│   │   ├── components/                # UI 组件
│   │   ├── contexts/                  # React Context
│   │   ├── hooks/                     # 自定义 Hooks
│   │   ├── locales/                   # 多语言翻译 (11 种语言)
│   │   ├── lib/                       # 工具库
│   │   └── services/                  # 服务层
│   ├── package.json                   # 依赖配置
│   └── bun.lock                       # Bun 锁定文件
│
├── tests/                             # 测试套件
│   ├── conftest.py                    # Pytest 配置与 fixtures
│   ├── pytest.ini                     # Pytest 配置
│   ├── test_graph_storage.py          # 图存储集成测试
│   ├── test_lightrag_ollama_chat.py   # Ollama 聊天测试
│   ├── test_auth.py                   # 认证测试
│   ├── test_chunking.py               # 分块测试
│   ├── test_rerank_chunking.py        # 重排序分块测试
│   └── ...                            # 60+ 测试文件
│
├── examples/                          # 使用示例
│   ├── lightrag_openai_demo.py        # OpenAI 示例
│   ├── lightrag_ollama_demo.py        # Ollama 示例
│   ├── lightrag_gemini_demo.py        # Gemini 示例
│   ├── lightrag_azure_openai_demo.py  # Azure OpenAI 示例
│   ├── rerank_example.py              # 重排序示例
│   ├── graph_visual_with_html.py      # HTML 图谱导出
│   ├── graph_visual_with_neo4j.py     # Neo4j 图谱可视化
│   ├── insert_custom_kg.py            # 自定义知识图谱插入
│   └── unofficial-sample/             # 社区贡献示例
│
├── scripts/                           # 辅助脚本
│   ├── setup/                         # 交互式环境配置向导
│   │   ├── setup.sh                   # 配置主脚本
│   │   ├── lib/                       # 辅助函数库
│   │   └── templates/                 # Docker Compose 模板
│   └── release/                       # 发布脚本
│
├── docs/                              # 文档
│   ├── Algorithm.md                   # 算法说明
│   ├── AdvancedFeatures.md            # 高级功能
│   ├── DockerDeployment.md            # Docker 部署指南
│   ├── InteractiveSetup.md            # 交互式设置指南
│   ├── LightRAG-API-Server.md         # API 服务文档
│   ├── LightRAG_concurrent_explain.md # 并发机制说明
│   ├── MultiSiteDeployment.md         # 多站点部署
│   ├── OfflineDeployment.md           # 离线部署指南
│   ├── ProgramingWithCore.md          # 核心 API 编程指南
│   ├── AsymmetricEmbedding.md         # 非对称嵌入说明
│   └── UV_LOCK_GUIDE.md              # UV 锁定指南
│
├── k8s-deploy/                        # Kubernetes 部署配置
│   ├── databases/                     # 数据库 Helm Charts
│   ├── lightrag/                      # LightRAG Helm Chart
│   └── install_lightrag.sh            # 安装脚本
│
├── reproduce/                         # 实验复现脚本
│   ├── Step_0.py ~ Step_3.py          # 分步复现脚本
│   └── batch_eval.py                  # 批量评测
│
├── docker-compose.yml                 # Docker Compose (基础)
├── docker-compose-full.yml            # Docker Compose (全量)
├── env.example                        # 环境变量配置模板
├── Dockerfile                         # Docker 构建文件
├── Dockerfile.lite                    # 轻量 Docker 构建
├── Makefile                           # 便捷构建命令
├── pyproject.toml                     # Python 项目配置
└── setup.py                           # 向后兼容安装脚本
```

---

## 3. 核心架构

### 3.1 数据流概览

```
文档输入 → 文本分块 → 实体/关系提取 → 知识图谱构建 → 向量化 → 存储
                                                          ↓
查询 → 关键词提取 → 图谱检索 + 向量检索 → 上下文组合 → LLM 生成 → 响应
```

### 3.2 LightRAG 主类

文件 [lightrag.py](file:///c:/tyyz-python/LightRAG/lightrag/lightrag.py) 中的 `LightRAG` 类是框架的核心编排器，负责协调所有存储、LLM 调用和查询操作。

**初始化参数摘录**：

| 参数类 | 关键参数 | 说明 |
|--------|----------|------|
| 目录 | `working_dir` | 存储工作目录，默认 `./rag_storage` |
| 存储 | `kv_storage` / `vector_storage` / `graph_storage` / `doc_status_storage` | 四种存储后端选择 |
| 工作空间 | `workspace` | 数据隔离级，默认从 `WORKSPACE` 环境变量读取 |
| 查询 | `top_k` / `chunk_top_k` / `max_entity_tokens` / `max_relation_tokens` / `max_total_tokens` | Token 分级控制 |
| 分块 | `chunk_token_size` / `chunk_overlap_token_size` / `tokenizer` | 文本分块配置 |
| 嵌入 | `embedding_func` / `embedding_batch_num` / `embedding_func_max_async` | Embedding 函数与并发控制 |
| LLM | `llm_model_func` / `llm_model_name` / `llm_model_max_async` | LLM 调用与并发控制 |
| 重排序 | `rerank_model_func` / `min_rerank_score` | 重排序配置 |
| 缓存 | `enable_llm_cache` / `enable_llm_cache_for_entity_extract` | LLM 响应缓存 |
| 提取 | `entity_extract_max_gleaning` / `max_extract_input_tokens` | 实体提取配置 |

**核心方法**：

- `initialize_storages()` / `finalize_storages()` — 存储生命周期管理
- `ainsert()` — 异步文档插入
- `aquery()` / `aquery_stream()` — 异步查询（含流式）
- `adelete_by_doc_id()` — 按文档 ID 删除
- `get_graph_labels()` / `get_knowledge_graph()` — 图谱查询

### 3.3 存储命名空间

[namespace.py](file:///c:/tyyz-python/LightRAG/lightrag/namespace.py) 定义了系统使用的 12 个存储命名空间：

| 命名空间 | 存储实例 | 用途 |
|----------|----------|------|
| `KV_STORE_FULL_DOCS` | `full_docs` | 完整文档存储 |
| `KV_STORE_TEXT_CHUNKS` | `text_chunks` | 文档分块存储 |
| `KV_STORE_LLM_RESPONSE_CACHE` | `llm_response_cache` | LLM 响应缓存 |
| `KV_STORE_FULL_ENTITIES` | `full_entities` | 实体完整数据 |
| `KV_STORE_FULL_RELATIONS` | `full_relations` | 关系完整数据 |
| `KV_STORE_ENTITY_CHUNKS` | `entity_chunks` | 实体-分块关联 |
| `KV_STORE_RELATION_CHUNKS` | `relation_chunks` | 关系-分块关联 |
| `VECTOR_STORE_ENTITIES` | `entities_vdb` | 实体向量索引 |
| `VECTOR_STORE_RELATIONSHIPS` | `relationships_vdb` | 关系向量索引 |
| `VECTOR_STORE_CHUNKS` | `chunks_vdb` | 分块向量索引 |
| `GRAPH_STORE_CHUNK_ENTITY_RELATION` | `chunk_entity_relation_graph` | 知识图谱存储 |
| `DOC_STATUS` | `doc_status` | 文档处理状态跟踪 |

### 3.4 核心操作模块

[operate.py](file:///c:/tyyz-python/LightRAG/lightrag/operate.py) 包含以下核心操作函数：

| 函数 | 功能 |
|------|------|
| `chunking_by_token_size()` | 基于 Token 数量的文本分块 |
| `extract_entities()` | 从文本分块中提取实体和关系 |
| `merge_nodes_and_edges()` | 合并图谱中的节点和边 |
| `kg_query()` | 基于知识图谱的查询 |
| `naive_query()` | 基于向量检索的简单查询 |
| `rebuild_knowledge_from_chunks()` | 从分块重建知识图谱 |

### 3.5 查询模式

`QueryParam.mode` 支持六种检索模式：

| 模式 | 说明 |
|------|------|
| `local` | 聚焦上下文相关信息，检索具体实体及其关系 |
| `global` | 利用全局知识，检索高层次关系和摘要 |
| `hybrid` | 结合 local 和 global 两种模式 |
| `naive` | 纯向量检索，不涉及知识图谱 |
| `mix` | 整合知识图谱检索和向量检索（推荐默认） |
| `bypass` | 跳过检索，直接由 LLM 回答 |

---

## 4. 存储后端

### 4.1 KV 存储

| 实现类 | 文件 | 说明 |
|--------|------|------|
| `JsonKVStorage` | [json_kv_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/json_kv_impl.py) | 基于 JSON 文件的本地 KV 存储（默认） |
| `RedisKVStorage` | [redis_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/redis_impl.py) | Redis KV 存储 |
| `MongoKVStorage` | [mongo_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/mongo_impl.py) | MongoDB KV 存储 |
| `PGGraphStore` | [postgres_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/postgres_impl.py) | PostgreSQL KV 存储 |

### 4.2 向量存储

| 实现类 | 文件 | 说明 |
|--------|------|------|
| `NanoVectorDBStorage` | [nano_vector_db_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/nano_vector_db_impl.py) | 嵌入式向量数据库（默认） |
| `FaissVectorDBStorage` | [faiss_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/faiss_impl.py) | FAISS 向量存储 |
| `MilvusVectorDBStorage` | [milvus_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/milvus_impl.py) | Milvus 向量数据库 |
| `QdrantVectorDBStorage` | [qdrant_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/qdrant_impl.py) | Qdrant 向量数据库 |
| `RedisVectorDBStorage` | [redis_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/redis_impl.py) | Redis 向量存储 |
| `OpenSearchStorage` | [opensearch_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/opensearch_impl.py) | OpenSearch 向量存储 |
| `PGVectorStorage` | [postgres_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/postgres_impl.py) | PGVector 向量存储 |

### 4.3 图存储

| 实现类 | 文件 | 说明 |
|--------|------|------|
| `NetworkXStorage` | [networkx_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/networkx_impl.py) | 基于 NetworkX 的内存图存储（默认） |
| `Neo4JStorage` | [neo4j_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/neo4j_impl.py) | Neo4j 图数据库 |
| `MemgraphStorage` | [memgraph_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/memgraph_impl.py) | Memgraph 图数据库 |
| `MongoGraphStorage` | [mongo_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/mongo_impl.py) | MongoDB 图存储 |
| `OpenSearchStorage` | [opensearch_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/opensearch_impl.py) | OpenSearch 图存储 |
| `PGGraphStore` | [postgres_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/kg/postgres_impl.py) | PostgreSQL (Apache AGE) 图存储 |

### 4.4 存储配置方式

通过环境变量选择存储后端：

```bash
# KV 存储
LIGHTRAG_KV_STORAGE=JsonKVStorage          # 默认
# LIGHTRAG_KV_STORAGE=RedisKVStorage
# LIGHTRAG_KV_STORAGE=MongoKVStorage

# 向量存储
LIGHTRAG_VECTOR_STORAGE=NanoVectorDBStorage  # 默认
# LIGHTRAG_VECTOR_STORAGE=MilvusVectorDBStorage
# LIGHTRAG_VECTOR_STORAGE=QdrantVectorDBStorage

# 图存储
LIGHTRAG_GRAPH_STORAGE=NetworkXStorage       # 默认
# LIGHTRAG_GRAPH_STORAGE=Neo4JStorage
# LIGHTRAG_GRAPH_STORAGE=PGGraphStore
```

---

## 5. LLM 提供商

### 5.1 支持列表

| 绑定标识 | 文件 | 支持的模型 |
|----------|------|------------|
| `openai` | [openai.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/openai.py) | GPT-4o, GPT-4, GPT-3.5-Turbo 等 |
| `azure_openai` | [azure_openai.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/azure_openai.py) | Azure OpenAI 服务 |
| `anthropic` | [anthropic.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/anthropic.py) | Claude 3.5 Sonnet, Claude 3 Opus 等 |
| `gemini` | [gemini.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/gemini.py) | Gemini 2.0 Flash, Gemini 1.5 Pro 等 |
| `ollama` | [ollama.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/ollama.py) | Llama 3, Mistral, Qwen 等本地模型 |
| `bedrock` | [bedrock.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/bedrock.py) | AWS Bedrock 上的模型 |
| `hf` | [hf.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/hf.py) | HuggingFace 推理端点 |
| `jina` | [jina.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/jina.py) | Jina AI 嵌入 |
| `voyageai` | [voyageai.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/voyageai.py) | VoyageAI 嵌入 |
| `zhipu` | [zhipu.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/zhipu.py) | 智谱 GLM-4 系列 |
| `nvidia_openai` | [nvidia_openai.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/nvidia_openai.py) | NVIDIA NIM |
| `lmdeploy` | [lmdeploy.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/lmdeploy.py) | LMDeploy 推理服务 |
| `lollms` | [lollms.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/lollms.py) | Lollms |
| `llama_index` | [llama_index_impl.py](file:///c:/tyyz-python/LightRAG/lightrag/llm/llama_index_impl.py) | LlamaIndex 集成 |

### 5.2 配置示例

```bash
# LLM 配置 (以 OpenAI 为例)
LLM_BINDING=openai
LLM_BINDING_HOST=https://api.openai.com/v1
LLM_BINDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=gpt-4o-mini

# Embedding 配置
EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_BINDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536

# 重排序配置（可选）
RERANK_BINDING=openai
RERANK_BINDING_HOST=https://api.openai.com/v1
RERANK_BINDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RERANK_MODEL=gpt-4o-mini
```

---

## 6. API 服务

### 6.1 服务入口

API 服务基于 FastAPI，通过以下方式启动：

```bash
# 开发模式
lightrag-server

# 生产模式 (Gunicorn)
lightrag-gunicorn

# 直接使用 uvicorn
uvicorn lightrag.api.lightrag_server:app --reload --port 9621
```

### 6.2 API 路由总览

| 路由前缀 | 路由文件 | 主要功能 |
|----------|----------|----------|
| `/docs` | `/document` | 文档上传（TXT/PDF/DOCX/PPTX/XLSX/CSV/MD）、文档列表、删除、清理 |
| `/query` | `/query` | 查询接口（含流式）、查询数据接口 |
| `/graph` | `/graph` | 图谱标签列表、图谱数据查询、DL 格式导出 |
| `/ollama` | `/ollama` | Ollama 兼容 API（`/api/tags`、`/api/chat`） |

### 6.3 核心 API 端点

**文档管理**：

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/documents/upload` | 上传文档文件 |
| `POST` | `/documents/text` | 直接提交文本 |
| `GET` | `/documents` | 获取文档列表及处理状态 |
| `DELETE` | `/documents` | 删除指定文档 |
| `POST` | `/documents/clear` | 清空所有文档 |
| `GET` | `/documents/pipeline_status` | 获取处理管道状态 |

**查询**：

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/query` | 执行 RAG 查询 |
| `POST` | `/query/stream` | 流式 RAG 查询 |
| `POST` | `/query/data` | 仅返回检索数据（不含 LLM 生成） |

**图谱**：

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/graph/label/list` | 获取所有图谱标签 |
| `GET` | `/graph/data` | 获取完整知识图谱数据 |
| `GET` | `/graph/dl` | DL 格式图谱导出 |

### 6.4 认证机制

API 支持 JWT Token 认证：

```bash
# 配置认证账号 (用户:密码)
AUTH_ACCOUNTS='admin:admin123,user1:{bcrypt}$2b$12$...'

# JWT 密钥
TOKEN_SECRET=your-super-secret-key-change-me

# JWT 算法
JWT_ALGORITHM=HS256

# Token 过期时间 (小时)
TOKEN_EXPIRE_HOURS=48
GUEST_TOKEN_EXPIRE_HOURS=24

# Token 自动续期
TOKEN_AUTO_RENEW=true
TOKEN_RENEW_THRESHOLD=0.5
```

密码支持明文和 bcrypt 哈希两种格式。可使用 CLI 工具生成 bcrypt 哈希：

```bash
lightrag-hash-password
```

---

## 7. Web 前端

### 7.1 技术栈

| 技术 | 用途 |
|------|------|
| React 19 | UI 框架 |
| TypeScript 5.9 | 类型安全 |
| Vite 8 | 构建工具 |
| Bun | 包管理与运行时 |
| TailwindCSS 4 | 样式 |
| Sigma.js / Graphology | 图可视化 |
| i18next | 国际化（支持 11 种语言） |
| React Router 7 | 前端路由 |

### 7.2 功能模块

| 模块 | 组件 | 功能 |
|------|------|------|
| **检索测试** | `RetrievalTesting` | 查询输入、模式选择、流式响应、引用展示 |
| **文档管理** | `DocumentManager` | 上传、列表、删除、处理状态跟踪 |
| **图谱可视化** | `GraphViewer` | 知识图谱交互式浏览、搜索、缩放、布局切换 |
| **登录认证** | `LoginPage` | JWT 登录、Token 管理 |
| **API 站点** | `ApiSite` | Swagger UI 内嵌展示 |

### 7.3 前端构建

```bash
cd lightrag_webui

# 安装依赖
bun install

# 开发模式
bun run dev

# 生产构建
bun run build

# 运行测试
bun test

# 代码检查
bun run lint
```

前端构建产物会自动输出到 `lightrag/api/webui/` 目录，API 服务启动时会将其作为静态资源挂载到 `/webui` 路径。

---

## 8. 工具脚本

### 8.1 CLI 工具

| 命令 | 说明 |
|------|------|
| `lightrag-server` | 启动 API 服务 |
| `lightrag-gunicorn` | 通过 Gunicorn 启动 API 服务 |
| `lightrag-hash-password` | 生成 bcrypt 密码哈希 |
| `lightrag-download-cache` | 下载 Tiktoken 离线缓存 |
| `lightrag-clean-llmqc` | 清理 LLM 查询缓存 |

### 8.2 内部工具

| 脚本 | 说明 |
|------|------|
| [clean_llm_query_cache.py](file:///c:/tyyz-python/LightRAG/lightrag/tools/clean_llm_query_cache.py) | 清理过期的 LLM 查询缓存 |
| [migrate_llm_cache.py](file:///c:/tyyz-python/LightRAG/lightrag/tools/migrate_llm_cache.py) | 在不同存储后端之间迁移 LLM 缓存 |
| [download_cache.py](file:///c:/tyyz-python/LightRAG/lightrag/tools/download_cache.py) | 下载离线部署所需的缓存文件 |
| [check_initialization.py](file:///c:/tyyz-python/LightRAG/lightrag/tools/check_initialization.py) | 检查 LightRAG 初始化状态 |
| [prepare_qdrant_legacy_data.py](file:///c:/tyyz-python/LightRAG/lightrag/tools/prepare_qdrant_legacy_data.py) | 准备 Qdrant 旧版数据迁移 |
| [graph_visualizer.py](file:///c:/tyyz-python/LightRAG/lightrag/tools/lightrag_visualizer/graph_visualizer.py) | 独立的图谱可视化工具 |

---

## 9. 快速开始

### 9.1 环境准备

```bash
# 克隆仓库
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# 安装核心包
pip install -e .
# 或安装含 API 的完整包
pip install -e .[api]
```

### 9.2 交互式配置

```bash
# 第一步：配置 LLM / Embedding / Reranker
make env-base

# 第二步：配置存储后端（可选）
make env-storage

# 第三步：配置服务/安全/SSL（可选）
make env-server
```

### 9.3 启动服务

```bash
# 开发模式启动
lightrag-server

# 访问 API 文档
# http://localhost:9621/docs

# 访问 Web UI
# http://localhost:9621/webui
```

### 9.4 Python API 编程使用

```python
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

async def main():
    # 配置 Embedding 函数
    embedding_func = EmbeddingFunc(
        embedding_dim=1536,
        max_token_size=8192,
        func=lambda texts: openai_embed(
            texts, model="text-embedding-3-small"
        ),
    )

    # 创建 LightRAG 实例
    rag = LightRAG(
        working_dir="./rag_storage",
        llm_model_func=lambda prompt, **kwargs: openai_complete_if_cache(
            "gpt-4o-mini", prompt, **kwargs
        ),
        embedding_func=embedding_func,
    )

    # 初始化存储
    await rag.initialize_storages()

    # 插入文档
    with open("document.txt", "r", encoding="utf-8") as f:
        await rag.ainsert(f.read())

    # 执行查询
    response = await rag.aquery(
        "这篇文章的主要内容是什么？",
        param=QueryParam(mode="mix", stream=False),
    )
    print(response)

    # 清理
    await rag.finalize_storages()

asyncio.run(main())
```

---

## 10. 配置与环境变量

### 10.1 环境变量配置文件

| 文件 | 用途 |
|------|------|
| `env.example` | 环境变量模板（含所有可配置项注释） |
| `.env` | 运行时实际使用的环境变量文件 |
| `.env.aoi.example` | API 专用环境变量模板 |

### 10.2 核心环境变量

```bash
# ===== 服务配置 =====
HOST=0.0.0.0
PORT=9621
WORKERS=2
TIMEOUT=150
CORS_ORIGINS=http://localhost:3000

# ===== 路径前缀 (多站点部署) =====
LIGHTRAG_API_PREFIX=/site01

# ===== SSL 配置 =====
SSL=true
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem

# ===== 目录配置 =====
WORKING_DIR=./rag_storage
INPUT_DIR=./inputs
TIKTOKEN_CACHE_DIR=/app/data/tiktoken

# ===== LLM 配置 =====
LLM_BINDING=openai
LLM_MODEL=gpt-4o-mini
LLM_BINDING_HOST=https://api.openai.com/v1
LLM_BINDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MAX_ASYNC=4
LLM_TIMEOUT=180

# ===== Embedding 配置 =====
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_BINDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EMBEDDING_FUNC_MAX_ASYNC=8
EMBEDDING_BATCH_NUM=10

# ===== Rerank 配置 =====
RERANK_BINDING=null
MIN_RERANK_SCORE=0.0
RERANK_BY_DEFAULT=true

# ===== 存储后端 =====
LIGHTRAG_KV_STORAGE=JsonKVStorage
LIGHTRAG_VECTOR_STORAGE=NanoVectorDBStorage
LIGHTRAG_GRAPH_STORAGE=NetworkXStorage
LIGHTRAG_DOC_STATUS_STORAGE=JsonDocStatusStorage

# ===== 查询配置 =====
TOP_K=40
CHUNK_TOP_K=20
MAX_ENTITY_TOKENS=6000
MAX_RELATION_TOKENS=8000
MAX_TOTAL_TOKENS=30000
COSINE_THRESHOLD=0.2

# ===== 分块配置 =====
CHUNK_SIZE=1200
CHUNK_OVERLAP_SIZE=100

# ===== 实体提取 =====
MAX_GLEANING=1
ENTITY_TYPES='["Person","Organization","Location","Event","Concept"]'
SUMMARY_LANGUAGE=English

# ===== 认证 =====
AUTH_ACCOUNTS='admin:admin123'
TOKEN_SECRET=your-super-secret-key
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_HOURS=48

# ===== 日志 =====
LOG_LEVEL=INFO
VERBOSE=false
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
```

---

## 11. Docker 部署

### 11.1 Docker Compose 快速启动

```bash
# 基础部署 (内嵌存储)
docker compose up -d

# 全量部署 (含外部数据库)
docker compose -f docker-compose-full.yml up -d

# 自定义配置后部署
make env-base       # 配置 LLM
make env-storage    # 配置存储
docker compose -f docker-compose.final.yml up -d
```

### 11.2 Docker 镜像构建

```bash
# 标准构建 (含前端)
docker build -t lightrag:latest .

# 轻量构建 (不含前端和离线依赖)
docker build -f Dockerfile.lite -t lightrag:lite .

# 使用构建脚本
./docker-build-push.sh
```

### 11.3 Docker Compose 服务组成

| 服务 | 说明 |
|------|------|
| `lightrag` | LightRAG API 服务（核心） |
| `neo4j` | Neo4j 图数据库（可选） |
| `milvus` | Milvus 向量数据库（可选） |
| `redis` | Redis 缓存和存储（可选） |
| `mongodb` | MongoDB 存储（可选） |
| `postgres` | PostgreSQL（含 PGVector + AGE）（可选） |
| `qdrant` | Qdrant 向量数据库（可选） |
| `opensearch` | OpenSearch 存储（可选） |

---

## 12. Kubernetes 部署

Kubernetes 部署配置位于 `k8s-deploy/` 目录：

```bash
cd k8s-deploy

# 安装 LightRAG 到 Kubernetes
./install_lightrag.sh

# 安装开发版
./install_lightrag_dev.sh

# 卸载
./uninstall_lightrag.sh
```

Helm Chart 包含：

| 资源 | 说明 |
|------|------|
| `deployment.yaml` | LightRAG 应用 Deployment |
| `service.yaml` | 服务暴露配置 |
| `pvc.yaml` | 持久化存储卷 |
| `secret.yaml` | 敏感信息管理 |
| `databases/` | 各数据库的 Helm 配置 |

---

## 13. 开发指南

### 13.1 开发环境搭建

```bash
# 一键搭建开发环境
make dev

# 这将执行：
#   1. uv sync --extra test --extra offline   # Python 依赖
#   2. cd lightrag_webui && bun install       # 前端依赖
#   3. cd lightrag_webui && bun run build     # 前端构建
```

### 13.2 测试

```bash
# 运行所有离线测试（默认）
python -m pytest tests

# 运行含集成测试
python -m pytest tests --run-integration

# 运行单个测试文件
python -m pytest tests/test_graph_storage.py

# 前端测试
cd lightrag_webui && bun test
cd lightrag_webui && bun test --watch
cd lightrag_webui && bun test --coverage
```

测试标记：

- `offline` — 默认运行的离线单元测试
- `integration` — 需要外部服务的集成测试
- `requires_db` — 需要数据库的测试
- `requires_api` — 需要 API 服务的测试

### 13.3 代码检查

```bash
# Python 代码风格检查
ruff check .

# 前端代码检查
cd lightrag_webui && bun run lint
```

### 13.4 添加新存储后端

1. 在 `lightrag/kg/` 目录下创建新的实现文件
2. 继承对应的抽象基类（`BaseKVStorage` / `BaseVectorStorage` / `BaseGraphStorage` / `DocStatusStorage`）
3. 实现所有抽象方法
4. 在 `lightrag/kg/__init__.py` 中注册新的存储类

### 13.5 添加新 LLM 提供商

1. 在 `lightrag/llm/` 目录下创建新的绑定文件
2. 实现 `complete()` 和/或 `embed()` 函数
3. 在 `lightrag/api/config.py` 的 LLM 工厂方法中注册

### 13.6 贡献指南

- 分支命名：从 `main` 创建功能分支
- PR 目标：上游仓库 `HKUDS/LightRAG:main`
- PR 前检查：确保 `ruff check .`、`python -m pytest` 和前端 lint/build/test 全部通过
- 提交信息：使用简洁的祈使句（如 `Fix lock key normalization`）

---

## 附录

### A. 重要链接

- **GitHub 仓库**: https://github.com/HKUDS/LightRAG
- **PyPI 包**: `lightrag-hku`
- **上游仓库**: `HKUDS/LightRAG:main`

### B. 依赖概览

**核心依赖**：`aiohttp`, `networkx`, `numpy`, `pandas`, `pydantic`, `tiktoken`, `tenacity`, `json_repair`, `python-dotenv`, `pipmaster`

**API 扩展依赖**：`fastapi`, `uvicorn`, `gunicorn`, `python-multipart`, `aiofiles`, `PyJWT`, `bcrypt`, `pypdf`, `python-docx`, `python-pptx`, `openpyxl`

**前端依赖**：`react 19`, `typescript 5.9`, `tailwindcss 4`, `sigma.js`, `graphology`, `react-router 7`, `i18next`

**可选存储客户端**：`redis`, `neo4j`, `pymilvus`, `pymongo`, `asyncpg`, `pgvector`, `qdrant-client`, `opensearch-py`

### C. 支持的文档格式

通过文件上传 API 支持以下文档格式：

- 纯文本 (`.txt`)
- Markdown (`.md`)
- PDF (`.pdf`) — 通过 pypdf 解析
- Word (`.docx`) — 通过 python-docx 解析
- PowerPoint (`.pptx`) — 通过 python-pptx 解析
- Excel (`.xlsx`) — 通过 openpyxl 解析
- CSV (`.csv`)
- 高级文档处理 — 可选通过 docling 引擎增强解析能力