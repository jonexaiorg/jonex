# syntax=docker/dockerfile:1
# ============================================================
# Jonex Platform - Sidecar 代理 Dockerfile
# 功能：统一 API 入口、认证、计量、限流
# 说明：派生自共享基础镜像 Python_Base（jonex/python-base:local），
#       公共前置层（时区 / 腾讯源 / apt 三件 / pip 源 / 依赖安装）
#       已由 base 镜像承载，本文件仅追加 sidecar 特有源码。
#       sidecar 无额外系统依赖，故不派生 apt 层。
# ============================================================

ARG PYTHON_BASE=jonex/python-base:local
FROM ${PYTHON_BASE} AS base

# 复制核心代码
COPY jonex_core/ ./jonex_core/

# 复制主入口
COPY main.py .

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令（支持通过环境变量调整 worker 数量）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4}"]
