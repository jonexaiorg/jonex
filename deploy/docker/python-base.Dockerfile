# [jonex] syntax=docker/dockerfile:1 已注释 — Docker Hub 不可达，Docker 29.x 内置 BuildKit 已支持所需特性
# ============================================================
# Jonex Platform - Python 共享基础镜像（Python_Base）
# 功能：承载 capability / gateway / sidecar / llm-gateway 四个
#       Python 服务镜像的公共前置层，依赖清单未变时复用本镜像
#       的已构建依赖层，避免重复执行腾讯源替换、apt 安装与 pip 安装。
# 公共层（与优化前逐项一致）：
#   - FROM python:3.12.13-slim
#   - 环境变量 + 时区 Asia/Shanghai
#   - 腾讯源替换（debian / debian-security 精确匹配）
#   - apt 公共三件：gcc / libpq-dev / curl
#   - pip 腾讯云镜像源 + pip install -r requirements.txt
# 说明：本镜像【不含】任何服务特有依赖（如 ffmpeg），服务特有
#       依赖由各服务镜像在派生层追加。
# 产出标签：jonex/python-base:local（本地）；CI 注入 registry tag。
# ============================================================

FROM python:3.12.13-slim AS base

WORKDIR /app

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    LOG_LEVEL=INFO

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

# 替换腾讯源（debian 与 debian-security 各做一次精确匹配替换）
RUN sed -i 's|^URIs: http://deb.debian.org/debian|URIs: http://mirrors.cloud.tencent.com/debian|' /etc/apt/sources.list.d/debian.sources
RUN sed -i 's|^URIs: http://deb.debian.org/debian-security|URIs: http://mirrors.cloud.tencent.com/debian-security|' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖（公共三件，apt 缓存复用）
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# pip 源配置（腾讯云镜像加速，与 apt 源保持一致）
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（BuildKit 缓存挂载，复用已下载 wheel）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
