# syntax=docker/dockerfile:1
# ============================================================
# Jonex Platform - 能力服务 Dockerfile（模板）
# 功能：独立部署单个能力服务
# 说明：本镜像派生自共享基础镜像 Python_Base（jonex/python-base:local），
#       公共前置层（腾讯源替换、apt 公共三件 gcc/libpq-dev/curl、
#       pip 源配置、requirements.txt 安装）均已在 base 中完成，此处
#       仅追加能力服务特有内容（ffmpeg 系统依赖 + 源码/能力代码）。
# 使用示例：
#   docker build -f capability.Dockerfile --build-arg CAPABILITY_NAME=knowledge_base -t jonex/knowledge-base:latest .
# ============================================================

ARG PYTHON_BASE=jonex/python-base:local
ARG CAPABILITY_NAME=knowledge_base

FROM ${PYTHON_BASE} AS base

WORKDIR /app

# 派生层：仅追加能力服务特有系统依赖 ffmpeg（不回写 base 的公共三件）
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制核心框架
COPY jonex_core/ ./jonex_core/

# 复制能力代码（通过构建参数指定）
ARG CAPABILITY_NAME
COPY capabilities/${CAPABILITY_NAME}/ ./capabilities/${CAPABILITY_NAME}/

# 复制能力启动模板
COPY deploy/start_capability.py .

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动能力服务
CMD ["python", "start_capability.py"]
