# syntax=docker/dockerfile:1
# ============================================================
# Jonex Platform - API Gateway Dockerfile
# 功能：统一入口、请求路由、CORS、日志追踪
# 说明：派生自共享基础镜像 Python_Base（公共前置层已收敛至
#       python-base.Dockerfile：时区/腾讯源/apt gcc·libpq-dev·curl/
#       pip 源/requirements 安装）。gateway 无额外系统依赖，无需派生
#       apt 层；仅追加自身源码与运行配置。运行时行为与优化前逐字一致。
# ============================================================

ARG PYTHON_BASE=jonex/python-base:local
FROM ${PYTHON_BASE} AS base

WORKDIR /app

# 复制核心代码
COPY jonex_core/ ./jonex_core/
COPY capabilities/ ./capabilities/

# 复制 API Gateway 代码
COPY api_gateway/ ./api_gateway/

# 复制主入口（可选，因为直接用 api_gateway.main:app）
COPY run_gateway.py .

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
