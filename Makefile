

























.DEFAULT_GOAL := help
SHELL := /bin/sh




ENV_FILE ?= deploy/.env
COMPOSE ?= docker compose
PNPM ?= pnpm
PYTHON ?= python3
SERVICE ?=
N ?= 1
PYTHON_BASE_TAG ?= jonex/python-base:local
PERF_TAIL ?= 1000
METERING_RETENTION_DAYS ?= 90

-include $(ENV_FILE)
export

DB_HOST ?= 127.0.0.1
DB_PORT ?= 5432
DB_USERNAME ?= jonex
DB_PASSWORD ?= CHANGE_ME
DB_NAME ?= jonex

UNAME_S := $(shell uname -s)







COMPOSE_FILES := -f docker-compose.yml
COMPOSE_GPU_FILES := $(COMPOSE_FILES) -f docker-compose.gpu.yml
COMPOSE_MAC_FILES := $(COMPOSE_FILES) -f docker-compose.mac.yml
COMPOSE_LOCAL_FILES := $(COMPOSE_FILES)
ifeq ($(UNAME_S),Darwin)
COMPOSE_LOCAL_FILES := $(COMPOSE_MAC_FILES)
endif
COMPOSE_OVERRIDE_FILES := $(COMPOSE_LOCAL_FILES) -f docker-compose.override.yml
COMPOSE_DEV_FILES := $(COMPOSE_LOCAL_FILES) -f docker-compose.debug.yml

DOCKER_GPU := cd deploy && $(COMPOSE) $(COMPOSE_GPU_FILES)
DOCKER_BASE := cd deploy && $(COMPOSE) $(COMPOSE_LOCAL_FILES)
DOCKER_OVERRIDE := cd deploy && $(COMPOSE) $(COMPOSE_OVERRIDE_FILES)
DOCKER_DEV := cd deploy && $(COMPOSE) $(COMPOSE_DEV_FILES)

MIDDLEWARE_SERVICES := postgres redis etcd minio milvus
RAG_SERVICES := lightrag atomic-rag
BACKEND_SERVICES := gateway sidecar knowledge-base-service business-domain-service platform-service
FRONTEND_SERVICES := frontend-gateway shell-frontend core-business-frontend platform-management-frontend ecosystem-management-frontend

FRONTENDS_DIR := frontends
SHELL_APP := @jonex/shell
CORE_APP := @jonex/core-business
PLATFORM_APP := @jonex/platform-management
ECOSYSTEM_APP := @jonex/ecosystem-management
MAIN_FRONTEND_FILTERS := --filter $(SHELL_APP) --filter $(CORE_APP) --filter $(PLATFORM_APP) --filter $(ECOSYSTEM_APP)

LOCAL_BACKEND_ENV := ENV=dev DB_HOST=127.0.0.1 DB_PORT=$(DB_PORT) DB_USERNAME=$(DB_USERNAME) DB_PASSWORD=$(DB_PASSWORD) DB_NAME=$(DB_NAME) REDIS_URL=redis://127.0.0.1:6379/0 MILVUS_HOST=127.0.0.1 MILVUS_PORT=19530 SIDECAR_URL=http://127.0.0.1:8001 KNOWLEDGE_BASE_URL=http://127.0.0.1:8003 BUSINESS_DOMAIN_URL=http://127.0.0.1:8005 ATOMIC_RAG_URL=http://127.0.0.1:8004 PLATFORM_URL=http://127.0.0.1:8006

.PHONY: help init version \
	build-python-base build build-local build-gpu build-prod build-server build-infra build-rag build-backend build-frontend build-service build-sidecar build-knowledge-base build-business-domain build-platform \
	up up-local up-detached up-gpu up-server up-prod up-infra up-rag up-backend up-frontend up-service up-sidecar up-knowledge-base up-business-domain up-platform \
	down down-local down-gpu down-server down-prod down-v stop stop-service down-service down-gateway down-sidecar down-frontend down-knowledge-base down-business-domain down-platform \
	restart restart-gpu restart-server restart-prod restart-service recreate-service rebuild-service \
	ps ps-gpu ps-server ps-prod \
	logs logs-gpu logs-server logs-prod logs-service logs-gateway logs-sidecar logs-knowledge-base logs-business-domain logs-platform logs-lightrag logs-postgres logs-redis logs-milvus logs-etcd logs-minio logs-infra logs-rag logs-backend logs-frontend \
	perf perf-ingest perf-reconcile perf-chunk perf-thinking perf-extract perf-audit perf-search perf-llm perf-llm-detail metering-rollup \
	dev dev-deps-up dev-infra-up dev-rag-up dev-deps-down dev-deps-logs \
	docker-local-build docker-local-up docker-local-down docker-local-ps docker-local-logs docker-local-restart docker-local-up-service docker-local-down-service docker-local-logs-service docker-local-restart-service docker-local-recreate-service docker-local-rebuild-service \
	docker-gpu-build docker-gpu-up docker-gpu-down docker-gpu-ps docker-gpu-logs docker-gpu-restart docker-gpu-up-service docker-gpu-down-service docker-gpu-logs-service docker-gpu-restart-service docker-gpu-rebuild-service \
	frontends-install dev-gateway dev-frontend dev-frontend-all dev-frontend-shell dev-frontend-core dev-frontend-platform dev-frontend-ecosystem \
	preview-core preview-platform preview-ecosystem preview-all \
	rebuild-gateway rebuild-sidecar rebuild-knowledge-base rebuild-business-domain rebuild-platform \
	rebuild-frontend-gateway rebuild-shell-frontend rebuild-core-business-frontend rebuild-platform-management-frontend rebuild-ecosystem-management-frontend \
	restart-gateway restart-sidecar restart-knowledge-base restart-business-domain restart-platform restart-frontend restart-frontend-gateway restart-shell-frontend restart-core-business-frontend restart-platform-management-frontend restart-ecosystem-management-frontend \
	scale-knowledge-base up-postgres up-redis up-milvus up-lightrag pull-lightrag init-db test clean \
	exec-postgres exec-gateway exec-sidecar exec-knowledge-base exec-business-domain exec-platform exec-lightrag exec-shell-frontend \
	shell-postgres shell-gateway shell-sidecar shell-knowledge-base shell-business-domain shell-platform shell-lightrag shell-frontend \
	_require-service




help:
	@echo "=== Jonex平台 Makefile ==="
	@echo ""
	@echo "初始化:"
	@echo "  make init                         初始化 deploy/.env 与 deploy/.env.rag"
	@echo "  make version                      查看 Docker / Compose 版本"
	@echo ""
	@echo "模式一: macOS/Linux 本机开发"
	@echo "  make dev-deps-up                  启动 postgres/redis/milvus/RAG 等本地依赖"
	@echo "  make dev-deps-down                停止本地依赖（保留容器和数据卷）"
	@echo "  make dev-deps-logs                查看本地依赖日志"
	@echo "  make frontends-install            安装/同步 frontends workspace 依赖"
	@echo "  make dev-gateway                   启动 Dev Gateway 统一入口: http://localhost:8080"
	@echo "  make dev-frontend                 一键启动 shell + 三个 TS 子应用"
	@echo "  make dev-frontend-all             一键启动全部当前前端"
	@echo "  make dev-frontend-shell           启动 shell: http://localhost:5173"
	@echo "  make dev-frontend-core            启动业务领域管理: http://localhost:5175"
	@echo "  make dev-frontend-ecosystem       启动生态管理: http://localhost:5176"
	@echo "  make dev-frontend-platform        启动平台管理: http://localhost:5177"
	@echo "  后端本机断点调试请使用 VSCode Debug，见 local-fullstack-debugging-guide.md"
	@echo ""
	@echo "模式二: 本地 Docker 部署（override）"
	@echo "  make build                        构建本地 Docker 镜像（Mac 自动叠加 docker-compose.mac.yml）"
	@echo "  make up                           启动本地 Docker 部署（加载 docker-compose.override.yml）"
	@echo "  make ps                           查看本地 Docker 状态"
	@echo "  make logs                         查看本地 Docker 日志"
	@echo "  make down                         停止并删除本地 Docker 部署"
	@echo "  make restart                      重启本地 Docker 部署"
	@echo ""
	@echo "模式三: 宿主机单服务调试（debug compose）"
	@echo "  make docker-local-build           构建宿主机单服务调试镜像"
	@echo "  make docker-local-up              启动宿主机单服务调试（加载 docker-compose.debug.yml）"
	@echo "  make docker-local-down            停止并删除宿主机单服务调试环境"
	@echo "  make docker-local-ps              查看宿主机单服务调试状态"
	@echo "  make docker-local-logs            查看宿主机单服务调试日志"
	@echo "  make docker-local-restart         重启宿主机单服务调试环境"
	@echo ""
	@echo "模式四: 生产/服务器 Docker（无 GPU，仅 docker-compose.yml）"
	@echo "  make up-prod                       启动生产部署"
	@echo "  make down-prod                     停止并删除生产部署"
	@echo "  make build-prod                    构建生产镜像"
	@echo "  make ps-prod                       查看生产服务状态"
	@echo "  make logs-prod                     查看生产全部日志"
	@echo "  make restart-prod                  重启生产部署"
	@echo ""
	@echo "模式五: GPU/服务器 Docker（需 NVIDIA Container Toolkit）"
	@echo "  make docker-gpu-build             构建 GPU/服务器镜像（叠加 docker-compose.gpu.yml）"
	@echo "  make docker-gpu-up                启动 GPU/服务器部署"
	@echo "  make docker-gpu-down              停止并删除 GPU/服务器部署"
	@echo "  make docker-gpu-ps                查看 GPU/服务器部署状态"
	@echo "  make docker-gpu-logs              查看 GPU/服务器部署日志"
	@echo "  make docker-gpu-restart           重启 GPU/服务器部署"
	@echo ""
	@echo "单服务操作:"
	@echo "  make docker-local-restart-service SERVICE=gateway"
	@echo "  make docker-local-rebuild-service SERVICE=core-business-frontend"
	@echo "  make logs-service SERVICE=platform-service"
	@echo "  make docker-local-logs-service SERVICE=knowledge-base-service"
	@echo "  make docker-local-down-service SERVICE=shell-frontend"
	@echo "  make docker-gpu-restart-service SERVICE=gateway"
	@echo "  make docker-gpu-logs-service SERVICE=shell-frontend"
	@echo ""
	@echo "性能耗时日志（摄入链路埋点）:"
	@echo "  make perf                         汇总查看 ingest_timing + reconcile_timing"
	@echo "  make perf-ingest                  worker 分阶段耗时 ingest_timing（atomic-rag）"
	@echo "  make perf-reconcile               对账入图库耗时 reconcile_timing（knowledge-base-service）"
	@echo "  make perf-chunk                   LightRAG 内部 chunk_timing（lightrag，拆 extract/merge/persist）"
	@echo "  make perf-thinking                关思考注入 thinking.disabled（llm-gateway）"
	@echo "  make perf-extract                 抽取场景调用 lightrag_extract（llm-gateway，看 latency/token）"
	@echo "  make perf-search                  本体检索 RAG 线路耗时 ontology_search_timing（knowledge-base-service，多库检索/融合）"
	@echo "  make perf-audit                   审计表耗时 audit_logs.duration_ms（postgres）"
	@echo "  make perf-llm                     LLM 计量可读汇总（postgres 视图，DIM=doc|trace|daily）"
	@echo "  make perf-llm-detail              LLM 计量明细可读视图（关联 kb/doc 名称 + 本地时区）"
	@echo "  make metering-rollup              汇总 llm_usage_daily +（dry-run）统计可清理明细；CONFIRM=1 才删除超 $(METERING_RETENTION_DAYS) 天明细"
	@echo "  # 默认查最近 $(PERF_TAIL) 行历史，可调: make perf-ingest PERF_TAIL=5000"
	@echo ""
	@echo "Compose 文件规则:"
	@echo "  docker-compose.yml                通用基线（无 GPU 依赖，所有平台可用）"
	@echo "  docker-compose.gpu.yml            GPU 覆盖（启用 NVIDIA GPU 加速 atomic-rag）"
	@echo "  docker-compose.mac.yml            Mac CPU 覆盖（降低 atomic-rag 资源占用）"
	@echo "  docker-compose.override.yml       通用本地覆盖（端口暴露/常规调试）"
	@echo "  docker-compose.debug.yml          单服务宿主机调试覆盖（sidecar 指向宿主机后端/atomic-rag）"
	@echo ""
	@echo "常用服务名:"
	@echo "  后端: gateway sidecar knowledge-base-service business-domain-service platform-service"
	@echo "  前端: shell-frontend core-business-frontend platform-management-frontend ecosystem-management-frontend"
	@echo "  RAG/原子能力: lightrag atomic-rag"
	@echo "  中间件: postgres redis etcd minio milvus"




init:
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

version:
	@docker --version
	@$(COMPOSE) version







build-python-base:
	@echo "=== 构建共享基础镜像 $(PYTHON_BASE_TAG) ==="
	cd deploy && docker buildx build --load -t $(PYTHON_BASE_TAG) -f docker/python-base.Dockerfile ..

build: build-python-base
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_LOCAL_FILES) build

build-local: build

build-gpu: build-python-base
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_GPU_FILES) build

build-prod: build-python-base
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_LOCAL_FILES) build

build-server: build-prod

build-infra:
	$(DOCKER_BASE) build $(MIDDLEWARE_SERVICES)

build-rag:
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_LOCAL_FILES) build $(RAG_SERVICES)

build-backend: build-python-base
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_LOCAL_FILES) build $(BACKEND_SERVICES)

build-frontend:
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_LOCAL_FILES) build $(FRONTEND_SERVICES)

build-service: _require-service build-python-base
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_LOCAL_FILES) build $(SERVICE)

build-sidecar:
	@$(MAKE) build-service SERVICE=sidecar

build-knowledge-base:
	@$(MAKE) build-service SERVICE=knowledge-base-service

build-business-domain:
	@$(MAKE) build-service SERVICE=business-domain-service

build-platform:
	@$(MAKE) build-service SERVICE=platform-service




up:
	@echo "=== 本地 Docker 部署 ==="
	$(DOCKER_OVERRIDE) up -d
	@echo "服务启动中: make ps / make logs"

up-local: up
up-detached: up

up-gpu:
	@echo "=== GPU Docker 部署 ==="
	$(DOCKER_GPU) up -d

up-server:
	@echo "=== 生产 Docker 部署 ==="
	$(DOCKER_BASE) up -d

up-prod: up-server

up-infra:
	$(DOCKER_OVERRIDE) up -d $(MIDDLEWARE_SERVICES)

up-rag:
	$(DOCKER_OVERRIDE) up -d $(RAG_SERVICES)

up-backend:
	$(DOCKER_OVERRIDE) up -d $(BACKEND_SERVICES)

up-frontend:
	$(DOCKER_OVERRIDE) up -d $(FRONTEND_SERVICES)

up-service: _require-service
	$(DOCKER_OVERRIDE) up -d $(SERVICE)

up-sidecar:
	@$(MAKE) up-service SERVICE=sidecar

up-knowledge-base:
	@$(MAKE) up-service SERVICE=knowledge-base-service

up-business-domain:
	@$(MAKE) up-service SERVICE=business-domain-service

up-platform:
	@$(MAKE) up-service SERVICE=platform-service

down: down-local

down-local:
	$(DOCKER_OVERRIDE) down

down-gpu:
	$(DOCKER_GPU) down

down-server:
	$(DOCKER_BASE) down

down-prod: down-server

down-v:
	@echo "警告: 这会删除数据库、Redis、MinIO、Milvus 等数据卷。"
	@printf "确认继续? (y/N): "; read -r confirm; [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_OVERRIDE) down -v

stop:
	$(DOCKER_OVERRIDE) stop

stop-service: _require-service
	$(DOCKER_OVERRIDE) stop $(SERVICE)

down-service: _require-service
	$(DOCKER_OVERRIDE) stop $(SERVICE)
	$(DOCKER_OVERRIDE) rm -f $(SERVICE)

down-gateway:
	@$(MAKE) down-service SERVICE=gateway

down-sidecar:
	@$(MAKE) down-service SERVICE=sidecar

down-frontend:
	$(DOCKER_OVERRIDE) stop $(FRONTEND_SERVICES)
	$(DOCKER_OVERRIDE) rm -f $(FRONTEND_SERVICES)

down-knowledge-base:
	@$(MAKE) down-service SERVICE=knowledge-base-service

down-business-domain:
	@$(MAKE) down-service SERVICE=business-domain-service

down-platform:
	@$(MAKE) down-service SERVICE=platform-service

restart:
	$(DOCKER_OVERRIDE) restart

restart-gpu:
	$(DOCKER_GPU) restart

restart-server:
	$(DOCKER_BASE) restart

restart-prod: restart-server

restart-service: _require-service
	$(DOCKER_OVERRIDE) restart $(SERVICE)

recreate-service: _require-service
	$(DOCKER_OVERRIDE) up -d --force-recreate $(SERVICE)

rebuild-service: _require-service build-python-base
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_OVERRIDE_FILES) build --no-cache $(SERVICE)
	docker image prune -f --filter "dangling=true"
	$(DOCKER_OVERRIDE) up -d --force-recreate $(SERVICE)




ps:
	$(DOCKER_OVERRIDE) ps

ps-gpu:
	$(DOCKER_GPU) ps

ps-server:
	$(DOCKER_BASE) ps

ps-prod: ps-server

logs:
	$(DOCKER_OVERRIDE) logs -f --tail=100

logs-gpu:
	$(DOCKER_GPU) logs -f --tail=100

logs-server:
	$(DOCKER_BASE) logs -f --tail=100

logs-prod: logs-server

logs-service: _require-service
	$(DOCKER_OVERRIDE) logs -f --tail=100 $(SERVICE)

logs-gateway:
	@$(MAKE) logs-service SERVICE=gateway

logs-sidecar:
	@$(MAKE) logs-service SERVICE=sidecar

logs-knowledge-base:
	@$(MAKE) logs-service SERVICE=knowledge-base-service

logs-business-domain:
	@$(MAKE) logs-service SERVICE=business-domain-service

logs-platform:
	@$(MAKE) logs-service SERVICE=platform-service

logs-lightrag:
	@$(MAKE) logs-service SERVICE=lightrag

logs-postgres:
	@$(MAKE) logs-service SERVICE=postgres

logs-redis:
	@$(MAKE) logs-service SERVICE=redis

logs-milvus:
	@$(MAKE) logs-service SERVICE=milvus

logs-etcd:
	@$(MAKE) logs-service SERVICE=etcd

logs-minio:
	@$(MAKE) logs-service SERVICE=minio

logs-infra:
	$(DOCKER_OVERRIDE) logs -f --tail=100 $(MIDDLEWARE_SERVICES)

logs-rag:
	$(DOCKER_OVERRIDE) logs -f --tail=100 $(RAG_SERVICES)

logs-backend:
	$(DOCKER_OVERRIDE) logs -f --tail=100 $(BACKEND_SERVICES)

logs-frontend:
	$(DOCKER_OVERRIDE) logs -f --tail=100 $(FRONTEND_SERVICES)






perf:
	@echo "=== ingest_timing (atomic-rag, worker 分阶段耗时) ==="
	@$(MAKE) --no-print-directory perf-ingest
	@echo ""
	@echo "=== reconcile_timing (knowledge-base-service, 入图库/端到端耗时) ==="
	@$(MAKE) --no-print-directory perf-reconcile

perf-ingest:
	$(DOCKER_OVERRIDE) logs --tail=$(PERF_TAIL) atomic-rag | grep ingest_timing || true

perf-reconcile:
	$(DOCKER_OVERRIDE) logs --tail=$(PERF_TAIL) knowledge-base-service | grep reconcile_timing || true

perf-chunk:
	$(DOCKER_OVERRIDE) logs --tail=$(PERF_TAIL) lightrag | grep chunk_timing || true

perf-thinking:
	$(DOCKER_OVERRIDE) logs --tail=$(PERF_TAIL) llm-gateway | grep "thinking.disabled" || true

perf-extract:
	$(DOCKER_OVERRIDE) logs --tail=$(PERF_TAIL) llm-gateway | grep lightrag_extract || true

perf-search:
	$(DOCKER_OVERRIDE) logs --tail=$(PERF_TAIL) knowledge-base-service | grep ontology_search_timing || true

perf-audit:
	$(DOCKER_OVERRIDE) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME) -c "SELECT created_at, action, outcome, duration_ms, resource_id, request_params FROM platform.audit_logs WHERE action IN ('document.parse_done','document.parse_failed','document.parse_recover') ORDER BY created_at DESC LIMIT 20;"


PERF_LLM_DIM ?= doc
PERF_LLM_LIMIT ?= 30

perf-llm:
	$(DOCKER_OVERRIDE) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME) -c "SELECT * FROM metering.v_llm_usage_by_$(PERF_LLM_DIM) ORDER BY total_tokens DESC NULLS LAST LIMIT $(PERF_LLM_LIMIT);"

perf-llm-detail:
	$(DOCKER_OVERRIDE) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME) -c "SELECT * FROM metering.v_llm_usage_detail ORDER BY created_local DESC LIMIT $(PERF_LLM_LIMIT);"



metering-rollup:
	@echo "=== 1) rollup → metering.llm_usage_daily（整天重聚合，幂等）==="
	$(DOCKER_OVERRIDE) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME) -c "INSERT INTO metering.llm_usage_daily (day_local, tenant_id, scene, model, call_count, prompt_tokens, completion_tokens, total_tokens, avg_latency_ms) SELECT (created_at AT TIME ZONE 'Asia/Shanghai')::date, tenant_id, scene, model, SUM(call_count), SUM(prompt_tokens), SUM(completion_tokens), SUM(total_tokens), ROUND(AVG(latency_ms)) FROM metering.llm_usage_log GROUP BY 1, tenant_id, scene, model ON CONFLICT (day_local, tenant_id, scene, model) DO UPDATE SET call_count=EXCLUDED.call_count, prompt_tokens=EXCLUDED.prompt_tokens, completion_tokens=EXCLUDED.completion_tokens, total_tokens=EXCLUDED.total_tokens, avg_latency_ms=EXCLUDED.avg_latency_ms;"
ifeq ($(CONFIRM),1)
	@echo "=== 2) 清理超 $(METERING_RETENTION_DAYS) 天且已汇总的明细（CONFIRM=1，实际删除）==="
	$(DOCKER_OVERRIDE) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME) -c "DELETE FROM metering.llm_usage_log u WHERE u.created_at < now() - interval '$(METERING_RETENTION_DAYS) days' AND EXISTS (SELECT 1 FROM metering.llm_usage_daily d WHERE d.day_local=(u.created_at AT TIME ZONE 'Asia/Shanghai')::date AND d.tenant_id=u.tenant_id);"
else
	@echo "=== 2) (dry-run) 将清理以下行数（加 CONFIRM=1 实际删除）==="
	$(DOCKER_OVERRIDE) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME) -c "SELECT count(*) AS deletable_rows FROM metering.llm_usage_log u WHERE u.created_at < now() - interval '$(METERING_RETENTION_DAYS) days' AND EXISTS (SELECT 1 FROM metering.llm_usage_daily d WHERE d.day_local=(u.created_at AT TIME ZONE 'Asia/Shanghai')::date AND d.tenant_id=u.tenant_id);"
endif




dev: dev-deps-up

dev-deps-up:
	$(DOCKER_OVERRIDE) up -d $(MIDDLEWARE_SERVICES) $(RAG_SERVICES)

dev-infra-up:
	$(DOCKER_OVERRIDE) up -d $(MIDDLEWARE_SERVICES)

dev-rag-up:
	$(DOCKER_OVERRIDE) up -d $(RAG_SERVICES)

dev-deps-down:
	$(DOCKER_OVERRIDE) stop $(MIDDLEWARE_SERVICES) $(RAG_SERVICES)

dev-deps-logs:
	$(DOCKER_OVERRIDE) logs -f --tail=100 $(MIDDLEWARE_SERVICES) $(RAG_SERVICES)





docker-local-build: build
docker-local-up:
	@echo "=== 宿主机单服务调试 ==="
	$(DOCKER_DEV) up -d

docker-local-down:
	$(DOCKER_DEV) down

docker-local-ps:
	$(DOCKER_DEV) ps

docker-local-logs:
	$(DOCKER_DEV) logs -f --tail=100

docker-local-restart:
	$(DOCKER_DEV) restart

docker-local-up-service: _require-service
	$(DOCKER_DEV) up -d $(SERVICE)

docker-local-down-service: _require-service
	$(DOCKER_DEV) stop $(SERVICE)
	$(DOCKER_DEV) rm -f $(SERVICE)

docker-local-logs-service: _require-service
	$(DOCKER_DEV) logs -f --tail=100 $(SERVICE)

docker-local-restart-service: _require-service
	$(DOCKER_DEV) restart $(SERVICE)

docker-local-recreate-service: _require-service
	$(DOCKER_DEV) up -d --force-recreate $(SERVICE)

docker-local-rebuild-service: _require-service build-python-base
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_DEV_FILES) build --no-cache $(SERVICE)
	docker image prune -f --filter "dangling=true"
	$(DOCKER_DEV) up -d --force-recreate $(SERVICE)

docker-gpu-build: build-gpu

docker-gpu-up: up-gpu

docker-gpu-down: down-gpu

docker-gpu-ps: ps-gpu

docker-gpu-logs: logs-gpu

docker-gpu-restart: restart-gpu

docker-gpu-up-service: _require-service
	$(DOCKER_GPU) up -d $(SERVICE)

docker-gpu-down-service: _require-service
	$(DOCKER_GPU) stop $(SERVICE)
	$(DOCKER_GPU) rm -f $(SERVICE)

docker-gpu-logs-service: _require-service
	$(DOCKER_GPU) logs -f --tail=100 $(SERVICE)

docker-gpu-restart-service: _require-service
	$(DOCKER_GPU) restart $(SERVICE)

docker-gpu-rebuild-service: _require-service build-python-base
	cd deploy && DOCKER_BUILDKIT=1 COMPOSE_BAKE=1 BUILDX_BAKE_ENTITLEMENTS_FS=0 $(COMPOSE) $(COMPOSE_GPU_FILES) build --no-cache $(SERVICE)
	docker image prune -f --filter "dangling=true"
	$(DOCKER_GPU) up -d --force-recreate $(SERVICE)





frontends-install:
	$(PNPM) -C $(FRONTENDS_DIR) install

dev-gateway:
	$(PNPM) -C $(FRONTENDS_DIR) run dev:gateway

dev-frontend:
	$(PNPM) -C $(FRONTENDS_DIR) -r --parallel $(MAIN_FRONTEND_FILTERS) run dev

dev-frontend-all:
	$(PNPM) -C $(FRONTENDS_DIR) -r --parallel $(MAIN_FRONTEND_FILTERS) run dev

dev-frontend-shell:
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(SHELL_APP) run dev

dev-frontend-core:
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(CORE_APP) run dev


dev-frontend-platform:
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(PLATFORM_APP) run dev

dev-frontend-ecosystem:
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(ECOSYSTEM_APP) run dev

preview-core:
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(CORE_APP) run build
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(CORE_APP) run preview


preview-platform:
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(PLATFORM_APP) run build
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(PLATFORM_APP) run preview

preview-ecosystem:
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(ECOSYSTEM_APP) run build
	$(PNPM) -C $(FRONTENDS_DIR) --filter $(ECOSYSTEM_APP) run preview

preview-all:
	$(PNPM) -C $(FRONTENDS_DIR) -r $(MAIN_FRONTEND_FILTERS) run build
	$(PNPM) -C $(FRONTENDS_DIR) -r --parallel $(MAIN_FRONTEND_FILTERS) run preview




rebuild-gateway:
	@$(MAKE) rebuild-service SERVICE=gateway

rebuild-sidecar:
	@$(MAKE) rebuild-service SERVICE=sidecar

rebuild-knowledge-base:
	@$(MAKE) rebuild-service SERVICE=knowledge-base-service

rebuild-business-domain:
	@$(MAKE) rebuild-service SERVICE=business-domain-service

rebuild-platform:
	@$(MAKE) rebuild-service SERVICE=platform-service

rebuild-frontend-gateway:
	@$(MAKE) rebuild-service SERVICE=frontend-gateway

rebuild-shell-frontend:
	@$(MAKE) rebuild-service SERVICE=shell-frontend

rebuild-core-business-frontend:
	@$(MAKE) rebuild-service SERVICE=core-business-frontend

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

restart-business-domain:
	@$(MAKE) restart-service SERVICE=business-domain-service

restart-platform:
	@$(MAKE) restart-service SERVICE=platform-service

restart-frontend:
	$(DOCKER_OVERRIDE) restart $(FRONTEND_SERVICES)

restart-frontend-gateway:
	@$(MAKE) restart-service SERVICE=frontend-gateway

restart-shell-frontend:
	@$(MAKE) restart-service SERVICE=shell-frontend

restart-core-business-frontend:
	@$(MAKE) restart-service SERVICE=core-business-frontend

restart-platform-management-frontend:
	@$(MAKE) restart-service SERVICE=platform-management-frontend

restart-ecosystem-management-frontend:
	@$(MAKE) restart-service SERVICE=ecosystem-management-frontend

scale-knowledge-base:
	$(DOCKER_OVERRIDE) up -d --scale knowledge-base-service=$(N) knowledge-base-service




up-postgres:
	$(DOCKER_OVERRIDE) up -d postgres

up-redis:
	$(DOCKER_OVERRIDE) up -d redis

up-milvus:
	$(DOCKER_OVERRIDE) up -d etcd minio milvus

up-lightrag:
	$(DOCKER_OVERRIDE) up -d lightrag

pull-lightrag:
	$(DOCKER_GPU) pull lightrag

init-db:
	$(DOCKER_OVERRIDE) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME) -f /docker-entrypoint-initdb.d/init.sql

test:
	$(DOCKER_OVERRIDE) ps
	@echo ""
	@echo "检查 API Gateway..."
	@curl -fsS http://localhost:8000/health || echo "API Gateway 未就绪或未启动"
	@echo ""
	@echo "检查 Sidecar..."
	@curl -fsS http://localhost:8001/health || echo "Sidecar 未就绪或未启动"

clean:
	@echo "警告: 这会删除本项目容器、数据卷和相关镜像。"
	@printf "确认继续? (y/N): "; read -r confirm; [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_OVERRIDE) down -v --rmi all
	docker image prune -f




exec-postgres:
	$(DOCKER_OVERRIDE) exec postgres psql -U $(DB_USERNAME) -d $(DB_NAME)

exec-gateway:
	$(DOCKER_OVERRIDE) exec gateway bash

exec-sidecar:
	$(DOCKER_OVERRIDE) exec sidecar bash

exec-knowledge-base:
	$(DOCKER_OVERRIDE) exec knowledge-base-service bash

exec-business-domain:
	$(DOCKER_OVERRIDE) exec business-domain-service bash

exec-platform:
	$(DOCKER_OVERRIDE) exec platform-service bash

exec-lightrag:
	$(DOCKER_OVERRIDE) exec lightrag bash

exec-shell-frontend:
	$(DOCKER_OVERRIDE) exec shell-frontend sh

shell-postgres: exec-postgres
shell-gateway: exec-gateway
shell-sidecar: exec-sidecar
shell-knowledge-base: exec-knowledge-base
shell-business-domain: exec-business-domain
shell-platform: exec-platform
shell-lightrag: exec-lightrag
shell-frontend: exec-shell-frontend




_require-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "请指定 SERVICE，例如:"; \
		echo "  make docker-local-restart-service SERVICE=gateway"; \
		echo "  make docker-local-rebuild-service SERVICE=core-business-frontend"; \
		exit 1; \
	fi
