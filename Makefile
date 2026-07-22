# ============================================================
# Jonex平台 Makefile
#
# 模式约定:
#   1) Mac 本地开发（中间件/RAG 走 Docker，后端/前端本机运行）
# make mac-dev
# make mac-backend
# make mac-frontend
#   2) 本地 Docker 联调（整套服务容器运行）
# make docker-local-build
# make docker-local-up
# make docker-local-down
#   3) GPU/服务器 Docker（Windows/Linux/服务器）
# make docker-gpu-build
# make docker-gpu-up
# make docker-gpu-down
#   单服务操作:
# make docker-local-restart-service SERVICE=gateway
# make docker-local-rebuild-service SERVICE=core-business-frontend
# make docker-gpu-restart-service SERVICE=gateway
# ============================================================

.DEFAULT_GOAL := help
SHELL := /bin/sh

# ------------------------------------------------------------
# 基础变量
# ------------------------------------------------------------
ENV_FILE ?= deploy/.env
COMPOSE ?= docker compose
PNPM ?= pnpm
PYTHON ?= python3
SERVICE ?=
N ?= 1

-include $(ENV_FILE)
export

DB_HOST ?= 127.0.0.1
DB_PORT ?= 5432
DB_USERNAME ?= jonex
DB_PASSWORD ?= jonex123
DB_NAME ?= jonex

UNAME_S := $(shell uname -s)

# Compose 文件组合规则:
# - docker-compose.yml: 通用基线（无 GPU 依赖，所有平台可用）
# - docker-compose.gpu.yml: GPU 覆盖（为 atomic-rag 启用 NVIDIA GPU 加速）
# - docker-compose.mac.yml: Mac CPU 覆盖（降低 atomic-rag 资源占用）
# - docker-compose.override.yml: 本地 Docker 联调覆盖（端口/挂载/调试）
COMPOSE_FILES := -f docker-compose.yml
COMPOSE_GPU_FILES := $(COMPOSE_FILES) -f docker-compose.gpu.yml
COMPOSE_MAC_FILES := $(COMPOSE_FILES) -f docker-compose.mac.yml
COMPOSE_LOCAL_FILES := $(COMPOSE_FILES)
ifeq ($(UNAME_S),Darwin)
COMPOSE_LOCAL_FILES := $(COMPOSE_MAC_FILES)
endif
COMPOSE_DEV_FILES := $(COMPOSE_LOCAL_FILES) -f docker-compose.override.yml

DOCKER_GPU := cd deploy && $(COMPOSE) $(COMPOSE_GPU_FILES)
DOCKER_BASE := cd deploy && $(COMPOSE) $(COMPOSE_LOCAL_FILES)
DOCKER_DEV := cd deploy && $(COMPOSE) $(COMPOSE_DEV_FILES)

MIDDLEWARE_SERVICES := postgres redis etcd minio milvus
RAG_SERVICES := lightrag atomic-rag
BACKEND_SERVICES := gateway sidecar knowledge-base-service
FRONTEND_SERVICES := frontend-gateway shell-frontend core-business-frontend platform-management-frontend ecosystem-management-frontend

FRONTENDS_DIR := frontends
SHELL_APP := @jonex/shell
CORE_APP := @jonex/core-business
PLATFORM_APP := @jonex/platform-management
ECOSYSTEM_APP := @jonex/ecosystem-management
MAIN_FRONTEND_FILTERS := --filter $(SHELL_APP) --filter $(CORE_APP) --filter $(PLATFORM_APP) --filter $(ECOSYSTEM_APP)

LOCAL_BACKEND_ENV := ENV=dev DB_HOST=127.0.0.1 DB_PORT=$(DB_PORT) DB_USERNAME=$(DB_USERNAME) DB_PASSWORD=$(DB_PASSWORD) DB_NAME=$(DB_NAME) REDIS_URL=redis://127.0.0.1:6379/0 MILVUS_HOST=127.0.0.1 MILVUS_PORT=19530 SIDECAR_URL=http://127.0.0.1:8001 KNOWLEDGE_BASE_URL=http://127.0.0.1:8003 ATOMIC_RAG_URL=http://127.0.0.1:8004

.PHONY: help init version \
	build build-local build-gpu build-prod build-server build-infra build-rag build-backend build-frontend build-service build-sidecar build-knowledge-base \
	up up-local up-detached up-gpu up-server up-prod up-infra up-rag up-backend up-frontend up-service up-sidecar up-knowledge-base \
	down down-local down-gpu down-server down-prod down-v down-service down-gateway down-sidecar down-frontend down-knowledge-base stop stop-service restart restart-gpu restart-server restart-prod restart-service recreate-service rebuild-service \
	ps ps-gpu ps-server ps-prod logs logs-gpu logs-server logs-prod logs-service logs-infra logs-rag logs-backend logs-frontend logs-sidecar logs-knowledge-base logs-lightrag logs-postgres logs-redis logs-milvus logs-etcd logs-minio logs-gateway \
	dev dev-local dev-deps-up dev-infra-up dev-rag-up dev-deps-down dev-deps-logs \
	dev-backend dev-backend-gateway dev-backend-sidecar dev-backend-knowledge-base \
	_run-backend-gateway _run-backend-sidecar _run-backend-knowledge-base \
	frontends-install dev-frontend dev-frontend-all dev-frontend-shell dev-frontend-core dev-frontend-platform dev-frontend-ecosystem \
	preview-core preview-platform preview-ecosystem preview-all preview-core-business preview-platform-management preview-ecosystem-management dev-all \
	rebuild-gateway rebuild-sidecar rebuild-knowledge-base \
	rebuild-frontend-gateway rebuild-shell-frontend rebuild-core-business-frontend rebuild-platform-management-frontend rebuild-ecosystem-management-frontend \
	restart-gateway restart-sidecar restart-knowledge-base restart-frontend restart-frontend-gateway restart-shell-frontend restart-core-business-frontend restart-platform-management-frontend restart-ecosystem-management-frontend \
	up-postgres up-redis up-milvus up-lightrag pull-lightrag scale-knowledge-base init-db test clean \
	exec-postgres exec-gateway exec-sidecar exec-knowledge-base exec-lightrag exec-shell-frontend \
	shell-postgres shell-gateway shell-sidecar shell-knowledge-base shell-lightrag shell-frontend \
	dev-gateway dev-sidecar dev-knowledge-base dev-shell dev-core-business dev-platform-management dev-ecosystem-management \
	mac-dev mac-deps-up mac-infra-up mac-rag-up mac-deps-down mac-deps-logs mac-backend mac-backend-gateway mac-backend-sidecar mac-backend-knowledge-base mac-frontend-install mac-frontend mac-frontend-all mac-frontend-shell mac-frontend-core mac-frontend-platform mac-frontend-ecosystem \
	docker-local-build docker-local-up docker-local-down docker-local-ps docker-local-logs docker-local-restart docker-local-up-service docker-local-down-service docker-local-logs-service docker-local-restart-service docker-local-recreate-service docker-local-rebuild-service \
	docker-gpu-build docker-gpu-up docker-gpu-down docker-gpu-ps docker-gpu-logs docker-gpu-restart docker-gpu-up-service docker-gpu-down-service docker-gpu-logs-service docker-gpu-restart-service docker-gpu-rebuild-service

# ------------------------------------------------------------
# 帮助信息
# ------------------------------------------------------------
help: ## 显示帮助信息
	@echo "=== Jonex平台 Makefile ==="
	@echo ""
	@echo "模式一: Mac 本地开发（推荐）"
	@echo " make mac-dev                      启动本地开发依赖，并提示下一步"
	@echo " make mac-deps-up                  启动 postgres/redis/etcd/minio/milvus/lightrag/atomic-rag"
	@echo " make mac-infra-up                 只启动 postgres/redis/etcd/minio/milvus"
	@echo " make mac-rag-up                   只启动 lightrag/atomic-rag"
	@echo " make mac-backend                  一键启动 gateway/sidecar/knowledge-base"
	@echo " make mac-backend-gateway          启动 API Gateway: http://localhost:8000"
	@echo " make mac-backend-sidecar          启动 Sidecar: http://localhost:8001"
	@echo " make mac-backend-knowledge-base   启动知识库服务: http://localhost:8003"
	@echo " make mac-frontend-install         安装/同步 frontends workspace 依赖"
	@echo " make mac-frontend                 一键启动 shell + 三个 TS 子应用"
	@echo " make mac-frontend-shell           启动 shell: http://localhost:5173"
	@echo " make mac-frontend-core            启动业务领域管理: http://localhost:5175"
	@echo " make mac-frontend-platform        启动平台管理: http://localhost:5177"
	@echo " make mac-frontend-ecosystem       启动生态管理: http://localhost:5176"
	@echo ""
	@echo "模式二: 本地 Docker 联调"
	@echo " make init                         初始化 deploy/.env 与 RAG 配置"
	@echo " make docker-local-build           构建本地联调镜像（Mac 自动叠加 docker-compose.mac.yml）"
	@echo " make docker-local-up              启动本地 Docker 联调（加载 docker-compose.override.yml）"
	@echo " make docker-local-down            停止并删除本地 Docker 联调"
	@echo " make docker-local-ps              查看本地 Docker 联调状态"
	@echo " make docker-local-logs            查看本地 Docker 联调日志"
	@echo " make docker-local-restart         重启本地 Docker 联调"
	@echo ""
	@echo "模式二: 生产/服务器 Docker（无 GPU，仅 docker-compose.yml）"
	@echo " make up-prod                       启动生产部署"
	@echo " make down-prod                     停止并删除生产部署"
	@echo " make build-prod                    构建生产镜像"
	@echo " make ps-prod                       查看生产服务状态"
	@echo " make logs-prod                     查看生产全部日志"
	@echo " make restart-prod                  重启生产部署"
	@echo ""
	@echo "模式三: GPU/服务器 Docker（需 NVIDIA Container Toolkit）"
	@echo " make docker-gpu-build             构建 GPU/服务器镜像（叠加 docker-compose.gpu.yml）"
	@echo " make docker-gpu-up                启动 GPU/服务器部署"
	@echo " make docker-gpu-down              停止并删除 GPU/服务器部署"
	@echo " make docker-gpu-ps                查看 GPU/服务器部署状态"
	@echo " make docker-gpu-logs              查看 GPU/服务器部署日志"
	@echo " make docker-gpu-restart           重启 GPU/服务器部署"
	@echo ""
	@echo "单服务操作:"
	@echo " make docker-local-restart-service SERVICE=gateway"
	@echo " make docker-local-rebuild-service SERVICE=core-business-frontend"
	@echo " make docker-local-logs-service SERVICE=knowledge-base-service"
	@echo " make docker-local-down-service SERVICE=shell-frontend"
	@echo " make docker-gpu-restart-service SERVICE=gateway"
	@echo " make docker-gpu-logs-service SERVICE=shell-frontend"
	@echo ""
	@echo "Compose 文件规则:"
	@echo "  docker-compose.yml                通用基线（无 GPU 依赖，所有平台可用）"
	@echo "  docker-compose.gpu.yml GPU 覆盖（启用 NVIDIA GPU 加速 atomic-rag）"
	@echo "  docker-compose.mac.yml Mac CPU 覆盖（降低 atomic-rag 资源占用）"
	@echo "  docker-compose.override.yml       本地 Docker 联调覆盖"
	@echo ""
	@echo "常用服务名:"
	@echo "  前端: shell-frontend core-business-frontend platform-management-frontend ecosystem-management-frontend"
	@echo "  中间件: postgres redis etcd minio milvus lightrag atomic-rag"

# ------------------------------------------------------------
# 初始化
# ------------------------------------------------------------
init: ## 初始化环境配置
	@echo "=== 初始化环境 ==="
	@if [ ! -f deploy/.env ]; then \
		cp deploy/.env.example deploy/.env; \
		echo "已创建平台配置: deploy/.env"; \
	else \
		echo "平台配置已存在: deploy/.env"; \
	fi
	@if [ ! -f deploy/.env.rag ]; then \
		cp deploy/.env.rag.example deploy/.env.rag; \
		echo "已创建 RAG 配置: deploy/.env.rag"; \
	else \
		echo "RAG 配置已存在: deploy/.env.rag"; \
	fi
	@echo "下一步: 按需修改 deploy/.env 和 deploy/.env.rag"

version: ## 显示 Docker/Compose 版本
	@docker --version
	@$(COMPOSE) version

# ------------------------------------------------------------
# Docker 构建
# ------------------------------------------------------------
build: ## 构建本地 Docker 联调镜像
	$(DOCKER_BASE) build

build-local: build ## 别名: 构建本地 Docker 镜像

build-gpu: ## 构建 GPU Docker 镜像（Windows/Linux/服务器，需 NVIDIA GPU）
	$(DOCKER_GPU) build

build-prod: ## 构建生产 Docker 镜像（不含 GPU）
	$(DOCKER_BASE) build

build-server: build-prod ## 别名: 构建生产 Docker 镜像

build-infra: ## 构建基础设施镜像（通常会直接拉取）
	$(DOCKER_BASE) build $(MIDDLEWARE_SERVICES)

build-rag: ## 构建 RAG 服务镜像
	$(DOCKER_BASE) build $(RAG_SERVICES)

build-backend: ## 构建后端镜像
	$(DOCKER_BASE) build $(BACKEND_SERVICES)

build-frontend: ## 构建前端镜像
	$(DOCKER_BASE) build $(FRONTEND_SERVICES)

build-service: _require-service ## 构建指定服务: make build-service SERVICE=gateway
	$(DOCKER_BASE) build $(SERVICE)

build-sidecar: ## 兼容旧命令: 构建 Sidecar
	@$(MAKE) build-service SERVICE=sidecar

build-knowledge-base: ## 兼容旧命令: 构建知识库服务
	@$(MAKE) build-service SERVICE=knowledge-base-service

# ------------------------------------------------------------
# Docker 启动/停止
# ------------------------------------------------------------
up: ## 启动本地 Docker 联调（加载 override，暴露调试端口）
	@echo "=== 本地 Docker 部署 ==="
	$(DOCKER_DEV) up -d
	@echo "服务启动中: make docker-local-ps / make docker-local-logs"

up-local: up ## 别名: 本地 Docker 部署
up-detached: up ## 兼容旧命令: 后台启动本地 Docker 部署

up-gpu: ## GPU Docker 部署（Windows/Linux/服务器，需 NVIDIA GPU）
	@echo "=== GPU Docker 部署 ==="
	$(DOCKER_GPU) up -d

up-server: ## 服务器/生产部署（不含 GPU，仅 docker-compose.yml）
	@echo "=== 生产 Docker 部署 ==="
	$(DOCKER_BASE) up -d

up-prod: up-server ## 别名: 服务器/生产部署

up-infra: ## 只启动中间件
	$(DOCKER_DEV) up -d $(MIDDLEWARE_SERVICES)

up-rag: ## 只启动 RAG 服务
	$(DOCKER_DEV) up -d $(RAG_SERVICES)

up-backend: ## 只启动后端服务
	$(DOCKER_DEV) up -d $(BACKEND_SERVICES)

up-frontend: ## 只启动前端服务
	$(DOCKER_DEV) up -d $(FRONTEND_SERVICES)

up-service: _require-service ## 启动指定服务: make up-service SERVICE=gateway
	$(DOCKER_DEV) up -d $(SERVICE)

up-sidecar: ## 兼容旧命令: 只启动 Sidecar
	@$(MAKE) up-service SERVICE=sidecar

up-knowledge-base: ## 兼容旧命令: 只启动知识库服务
	@$(MAKE) up-service SERVICE=knowledge-base-service

down: down-local ## 停止并删除本地 Docker 部署

down-local: ## 停止并删除本地 Docker 部署
	$(DOCKER_DEV) down

down-gpu: ## 停止并删除 GPU Docker 部署
	$(DOCKER_GPU) down

down-server: ## 停止并删除服务器/生产部署
	$(DOCKER_BASE) down

down-prod: down-server ## 别名: 停止并删除服务器/生产部署

down-v: ## 停止全部服务并删除数据卷（慎用）
	@echo "警告: 这会删除数据库、Redis、MinIO、Milvus 等数据卷。"
	@printf "确认继续? (y/N): "; read -r confirm; [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_DEV) down -v

stop: ## 停止本地 Docker 服务（保留容器）
	$(DOCKER_DEV) stop

stop-service: _require-service ## 停止指定服务（保留容器）: make stop-service SERVICE=gateway
	$(DOCKER_DEV) stop $(SERVICE)

down-service: _require-service ## 停止并删除指定服务容器: make down-service SERVICE=gateway
	$(DOCKER_DEV) stop $(SERVICE)
	$(DOCKER_DEV) rm -f $(SERVICE)

down-gateway: ## 兼容旧命令: 停止并删除 Gateway 容器
	@$(MAKE) down-service SERVICE=gateway

down-sidecar: ## 兼容旧命令: 停止并删除 Sidecar 容器
	@$(MAKE) down-service SERVICE=sidecar

down-frontend: ## 兼容旧命令: 停止并删除全部前端容器
	$(DOCKER_DEV) stop $(FRONTEND_SERVICES)
	$(DOCKER_DEV) rm -f $(FRONTEND_SERVICES)

down-knowledge-base: ## 兼容旧命令: 停止并删除知识库服务容器
	@$(MAKE) down-service SERVICE=knowledge-base-service

restart: ## 重启本地 Docker 全部服务
	$(DOCKER_DEV) restart

restart-gpu: ## 重启 GPU Docker 全部服务
	$(DOCKER_GPU) restart

restart-server: ## 重启服务器/生产全部服务
	$(DOCKER_BASE) restart

restart-prod: restart-server ## 别名: 重启服务器/生产全部服务

restart-service: _require-service ## 重启指定服务: make restart-service SERVICE=gateway
	$(DOCKER_DEV) restart $(SERVICE)

recreate-service: _require-service ## 强制重建容器: make recreate-service SERVICE=gateway
	$(DOCKER_DEV) up -d --force-recreate $(SERVICE)

rebuild-service: _require-service ## 重新构建并启动指定服务: make rebuild-service SERVICE=core-business-frontend
	$(DOCKER_DEV) build $(SERVICE)
	$(DOCKER_DEV) up -d $(SERVICE)

# ------------------------------------------------------------
# Docker 查看
# ------------------------------------------------------------
ps: ## 查看本地 Docker 服务状态
	$(DOCKER_DEV) ps

ps-gpu: ## 查看 GPU Docker 服务状态
	$(DOCKER_GPU) ps

ps-server: ## 查看服务器/生产服务状态
	$(DOCKER_BASE) ps

ps-prod: ps-server ## 别名: 查看服务器/生产服务状态

logs: ## 查看本地 Docker 全部日志
	$(DOCKER_DEV) logs -f --tail=100

logs-gpu: ## 查看 GPU Docker 全部日志
	$(DOCKER_GPU) logs -f --tail=100

logs-server: ## 查看服务器/生产全部日志
	$(DOCKER_BASE) logs -f --tail=100

logs-prod: logs-server ## 别名: 查看服务器/生产全部日志

logs-service: _require-service ## 查看指定服务日志: make logs-service SERVICE=gateway
	$(DOCKER_DEV) logs -f --tail=100 $(SERVICE)

logs-gateway: ## 查看 Gateway 日志
	@$(MAKE) logs-service SERVICE=gateway

logs-sidecar: ## 查看 Sidecar 日志
	@$(MAKE) logs-service SERVICE=sidecar

logs-knowledge-base: ## 查看知识库服务日志
	@$(MAKE) logs-service SERVICE=knowledge-base-service

logs-lightrag: ## 查看 LightRAG 日志
	@$(MAKE) logs-service SERVICE=lightrag

logs-postgres: ## 查看 Postgres 日志
	@$(MAKE) logs-service SERVICE=postgres

logs-redis: ## 查看 Redis 日志
	@$(MAKE) logs-service SERVICE=redis

logs-milvus: ## 查看 Milvus 日志
	@$(MAKE) logs-service SERVICE=milvus

logs-etcd: ## 查看 Etcd 日志
	@$(MAKE) logs-service SERVICE=etcd

logs-minio: ## 查看 MinIO 日志
	@$(MAKE) logs-service SERVICE=minio

logs-infra: ## 查看中间件日志
	$(DOCKER_DEV) logs -f --tail=100 $(MIDDLEWARE_SERVICES)

logs-rag: ## 查看 RAG 日志
	$(DOCKER_DEV) logs -f --tail=100 $(RAG_SERVICES)

logs-backend: ## 查看后端日志
	$(DOCKER_DEV) logs -f --tail=100 $(BACKEND_SERVICES)

logs-frontend: ## 查看前端日志
	$(DOCKER_DEV) logs -f --tail=100 $(FRONTEND_SERVICES)

# ------------------------------------------------------------
# Mac 本地开发: Docker 常驻依赖
# ------------------------------------------------------------
dev: dev-local ## Mac 本地开发入口

dev-local: dev-deps-up ## 启动本地开发依赖并提示下一步
	@echo ""
	@echo "本地开发依赖已启动。"
	@echo "后端: make mac-backend"
	@echo "前端: make mac-frontend"

dev-deps-up: ## 启动本地开发依赖（中间件 + RAG）
	$(DOCKER_DEV) up -d $(MIDDLEWARE_SERVICES) $(RAG_SERVICES)

dev-infra-up: ## 只启动中间件常驻服务
	$(DOCKER_DEV) up -d $(MIDDLEWARE_SERVICES)

dev-rag-up: ## 只启动 RAG 服务
	$(DOCKER_DEV) up -d $(RAG_SERVICES)

dev-deps-down: ## 停止本地开发依赖（保留容器和数据卷）
	$(DOCKER_DEV) stop $(MIDDLEWARE_SERVICES) $(RAG_SERVICES)

dev-deps-logs: ## 查看本地开发依赖日志
	$(DOCKER_DEV) logs -f --tail=100 $(MIDDLEWARE_SERVICES) $(RAG_SERVICES)

# ------------------------------------------------------------
# 模式化命令入口
# ------------------------------------------------------------
mac-dev: dev-local ## 推荐入口: Mac 本地开发

mac-deps-up: dev-deps-up ## Mac: 启动中间件 + RAG

mac-infra-up: dev-infra-up ## Mac: 启动中间件

mac-rag-up: dev-rag-up ## Mac: 启动 RAG

mac-deps-down: dev-deps-down ## Mac: 停止中间件 + RAG

mac-deps-logs: dev-deps-logs ## Mac: 查看中间件 + RAG 日志

docker-local-build: build ## 本地 Docker: 构建镜像

docker-local-up: up ## 本地 Docker: 启动整套服务

docker-local-down: down-local ## 本地 Docker: 停止整套服务

docker-local-ps: ps ## 本地 Docker: 查看状态

docker-local-logs: logs ## 本地 Docker: 查看日志

docker-local-restart: restart ## 本地 Docker: 重启整套服务

docker-local-up-service: up-service ## 本地 Docker: 启动单服务

docker-local-down-service: down-service ## 本地 Docker: 停止并删除单服务

docker-local-logs-service: logs-service ## 本地 Docker: 查看单服务日志

docker-local-restart-service: restart-service ## 本地 Docker: 重启单服务

docker-local-recreate-service: recreate-service ## 本地 Docker: 强制重建单服务容器

docker-local-rebuild-service: rebuild-service ## 本地 Docker: 重建并启动单服务

docker-gpu-build: build-gpu ## GPU/服务器 Docker: 构建镜像

docker-gpu-up: up-gpu ## GPU/服务器 Docker: 启动整套服务

docker-gpu-down: down-gpu ## GPU/服务器 Docker: 停止整套服务

docker-gpu-ps: ps-gpu ## GPU/服务器 Docker: 查看状态

docker-gpu-logs: logs-gpu ## GPU/服务器 Docker: 查看日志

docker-gpu-restart: restart-gpu ## GPU/服务器 Docker: 重启整套服务

docker-gpu-up-service: _require-service ## GPU/服务器 Docker: 启动单服务
	$(DOCKER_GPU) up -d $(SERVICE)

docker-gpu-down-service: _require-service ## GPU/服务器 Docker: 停止并删除单服务
	$(DOCKER_GPU) stop $(SERVICE)
	$(DOCKER_GPU) rm -f $(SERVICE)

docker-gpu-logs-service: _require-service ## GPU/服务器 Docker: 查看单服务日志
	$(DOCKER_GPU) logs -f --tail=100 $(SERVICE)

docker-gpu-restart-service: _require-service ## GPU/服务器 Docker: 重启单服务
	$(DOCKER_GPU) restart $(SERVICE)

docker-gpu-rebuild-service: _require-service ## GPU/服务器 Docker: 重建并启动单服务
	$(DOCKER_GPU) build $(SERVICE)
	$(DOCKER_GPU) up -d $(SERVICE)

# ------------------------------------------------------------
# Mac 本地开发: 后端
# ------------------------------------------------------------
dev-backend: dev-deps-up ## 一键启动本机后端
	@echo "=== 启动本机后端: gateway / sidecar / knowledge-base ==="
	@$(MAKE) -j3 _run-backend-sidecar _run-backend-gateway _run-backend-knowledge-base

dev-backend-gateway: dev-deps-up ## 启动 API Gateway
	$(LOCAL_BACKEND_ENV) $(PYTHON) run_gateway.py --reload

dev-backend-sidecar: dev-deps-up ## 启动 Sidecar
	$(LOCAL_BACKEND_ENV) $(PYTHON) main.py


dev-backend-knowledge-base: dev-deps-up ## 启动知识库服务
	$(LOCAL_BACKEND_ENV) CAPABILITY_NAME=knowledge_base SERVICE_PORT=8003 $(PYTHON) deploy/start_capability.py

dev-gateway: dev-backend-gateway ## 兼容旧命令: 启动 API Gateway
dev-sidecar: dev-backend-sidecar ## 兼容旧命令: 启动 Sidecar
dev-knowledge-base: dev-backend-knowledge-base ## 兼容旧命令: 启动知识库服务

_run-backend-gateway:
	$(LOCAL_BACKEND_ENV) $(PYTHON) run_gateway.py --reload

_run-backend-sidecar:
	$(LOCAL_BACKEND_ENV) $(PYTHON) main.py

_run-backend-knowledge-base:
	$(LOCAL_BACKEND_ENV) CAPABILITY_NAME=knowledge_base SERVICE_PORT=8003 $(PYTHON) deploy/start_capability.py

# ------------------------------------------------------------
# Mac 本地开发: 前端 TypeScript workspace
# ------------------------------------------------------------
frontends-install: ## 安装/同步前端 workspace 依赖
	$(PNPM) -C $(FRONTENDS_DIR) install

mac-backend: dev-backend ## Mac: 一键启动本机后端

mac-backend-gateway: dev-backend-gateway ## Mac: 启动 API Gateway

mac-backend-sidecar: dev-backend-sidecar ## Mac: 启动 Sidecar

mac-backend-knowledge-base: dev-backend-knowledge-base ## Mac: 启动知识库服务

mac-frontend-install: frontends-install ## Mac: 安装/同步前端依赖

mac-frontend: dev-frontend ## Mac: 一键启动 shell + 三个 TS 子应用

mac-frontend-all: dev-frontend-all ## Mac: 一键启动全部前端

mac-frontend-shell: dev-frontend-shell ## Mac: 启动 shell

mac-frontend-core: dev-frontend-core ## Mac: 启动业务领域管理

mac-frontend-platform: dev-frontend-platform ## Mac: 启动平台管理

mac-frontend-ecosystem: dev-frontend-ecosystem ## Mac: 启动生态管理

dev-frontend: ## 一键启动 shell + 三个新 TS 子应用
	$(PNPM) -C $(FRONTENDS_DIR) -r --parallel $(MAIN_FRONTEND_FILTERS) run dev

dev-frontend-all: ## 一键启动全部已配置前端
	$(PNPM) -C $(FRONTENDS_DIR) -r --parallel $(MAIN_FRONTEND_FILTERS) run dev

dev-frontend-shell: ## 启动 shell
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(SHELL_APP) run dev


dev-frontend-core: ## 启动业务领域管理
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(CORE_APP) run dev

dev-frontend-platform: ## 启动平台管理
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(PLATFORM_APP) run dev

dev-frontend-ecosystem: ## 启动生态管理
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(ECOSYSTEM_APP) run dev

preview-core: ## 构建并 preview 业务领域管理
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(CORE_APP) run build
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(CORE_APP) run preview

preview-platform: ## 构建并 preview 平台管理
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(PLATFORM_APP) run build
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(PLATFORM_APP) run preview

preview-ecosystem: ## 构建并 preview 生态管理
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(ECOSYSTEM_APP) run build
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(ECOSYSTEM_APP) run preview

preview-all: ## 构建并 preview 三个新 TS 子应用
	$(PNPM) -C $(FRONTENDS_DIR) -r $(MAIN_FRONTEND_FILTERS) run build
	$(PNPM) -C $(FRONTENDS_DIR) -r --parallel $(MAIN_FRONTEND_FILTERS) run preview

# 兼容旧命令
dev-all: dev-frontend
dev-shell: dev-frontend-shell
dev-core-business: dev-frontend-core
dev-platform-management: dev-frontend-platform
dev-ecosystem-management: dev-frontend-ecosystem
preview-core-business: preview-core
preview-platform-management: preview-platform
preview-ecosystem-management: preview-ecosystem

# ------------------------------------------------------------
# 常用单服务别名
# ------------------------------------------------------------
rebuild-gateway:
	@$(MAKE) rebuild-service SERVICE=gateway

rebuild-sidecar:
	@$(MAKE) rebuild-service SERVICE=sidecar

rebuild-knowledge-base:
	@$(MAKE) rebuild-service SERVICE=knowledge-base-service

rebuild-frontend-gateway:
	@$(MAKE) rebuild-service SERVICE=frontend-gateway

rebuild-shell-frontend:
	@$(MAKE) rebuild-service SERVICE=shell-frontend

rebuild-core-business-frontend:
	@$(MAKE) rebuild-service SERVICE=core-business-frontend

	@$(MAKE) rebuild-service SERVICE=intelligent-engine-frontend

rebuild-platform-management-frontend:
	@$(MAKE) rebuild-service SERVICE=platform-management-frontend

rebuild-ecosystem-management-frontend:
	@$(MAKE) rebuild-service SERVICE=ecosystem-management-frontend

restart-gateway:
	@$(MAKE) restart-service SERVICE=gateway

restart-sidecar:
	@$(MAKE) restart-service SERVICE=sidecar

restart-knowledge-base:
	@$(MAKE) restart-service SERVICE=knowledge-base-service

restart-frontend:
	$(DOCKER_DEV) restart $(FRONTEND_SERVICES)

restart-frontend-gateway:
	@$(MAKE) restart-service SERVICE=frontend-gateway

restart-shell-frontend:
	@$(MAKE) restart-service SERVICE=shell-frontend

restart-core-business-frontend:
	@$(MAKE) restart-service SERVICE=core-business-frontend

	@$(MAKE) restart-service SERVICE=intelligent-engine-frontend

restart-platform-management-frontend:
	@$(MAKE) restart-service SERVICE=platform-management-frontend

restart-ecosystem-management-frontend:
	@$(MAKE) restart-service SERVICE=ecosystem-management-frontend

scale-knowledge-base: ## 扩缩知识库服务: make scale-knowledge-base N=3
	$(DOCKER_DEV) up -d --scale knowledge-base-service=$(N) knowledge-base-service

# ------------------------------------------------------------
# 常用基础服务别名
# ------------------------------------------------------------
up-postgres:
	$(DOCKER_DEV) up -d postgres

up-redis:
	$(DOCKER_DEV) up -d redis

up-milvus:
	$(DOCKER_DEV) up -d etcd minio milvus

up-lightrag:
	$(DOCKER_DEV) up -d lightrag

pull-lightrag:
	$(DOCKER_GPU) pull lightrag

init-db: ## 初始化数据库
	$(DOCKER_DEV) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME) -f /docker-entrypoint-initdb.d/init.sql

test: ## 运行基础健康检查
	$(DOCKER_DEV) ps
	@echo ""
	@echo "检查 API Gateway..."
	@curl -fsS http://localhost:8000/health || echo "API Gateway 未就绪或未启动"
	@echo ""
	@echo "检查 Sidecar..."
	@curl -fsS http://localhost:8001/health || echo "Sidecar 未就绪或未启动"

clean: ## 清理容器、数据卷和镜像（慎用）
	@echo "警告: 这会删除本项目容器、数据卷和相关镜像。"
	@printf "确认继续? (y/N): "; read -r confirm; [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_DEV) down -v --rmi all
	docker image prune -f

# ------------------------------------------------------------
# 进入容器
# ------------------------------------------------------------
exec-postgres:
	$(DOCKER_DEV) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME)

exec-gateway:
	$(DOCKER_DEV) exec gateway bash

exec-sidecar:
	$(DOCKER_DEV) exec sidecar bash


exec-knowledge-base:
	$(DOCKER_DEV) exec knowledge-base-service bash

exec-lightrag:
	$(DOCKER_DEV) exec lightrag bash

exec-shell-frontend:
	$(DOCKER_DEV) exec shell-frontend sh

shell-postgres: exec-postgres
shell-gateway: exec-gateway
shell-sidecar: exec-sidecar
shell-knowledge-base: exec-knowledge-base
shell-lightrag: exec-lightrag
shell-frontend: exec-shell-frontend

# ------------------------------------------------------------
# 内部校验
# ------------------------------------------------------------
_require-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "请指定 SERVICE，例如:"; \
		echo " make docker-local-restart-service SERVICE=gateway"; \
		echo " make docker-local-rebuild-service SERVICE=core-business-frontend"; \
		exit 1; \
	fi
