# [jonex] syntax=docker/dockerfile:1 已注释 — Docker Hub 不可达，Docker 29.x 内置 BuildKit 已支持所需特性
# ============================================================
# Jonex Platform - LLM 网关 Dockerfile
# 功能：OpenAI 兼容代理、Token 计量、上游路由
# 说明：派生自共享基础镜像 Python_Base（jonex/python-base:local），
#       公共前置层（时区 / 腾讯源 / apt 三件 / pip 源 / 依赖安装）
#       已由 base 镜像承载，本文件仅追加 llm-gateway 特有源码。
#       llm-gateway 无额外系统依赖，故不派生 apt 层。
# ============================================================

ARG PYTHON_BASE=jonex/python-base:local
FROM ${PYTHON_BASE} AS base

# 复制核心代码
COPY jonex_core/ ./jonex_core/

# 启动入口
COPY run_llm_gateway.py .

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8787/health || exit 1

# 暴露端口
EXPOSE 8787

# 启动命令
CMD ["sh", "-c", "uvicorn jonex_core.llm_gateway.app:app --host 0.0.0.0 --port 8787 --workers ${WORKERS:-2}"]
