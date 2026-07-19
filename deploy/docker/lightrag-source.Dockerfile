# ============================================================
# LightRAG, RAG configuration for this setting.
# ============================================================
# Path configuration for this setting.
# Docker configuration for this setting.
#
# Docker configuration for this setting.
# LightRAG, RAG configuration for this setting.
# Configuration note for this setting.
# LightRAG, RAG configuration for FROM.
# LightRAG, RAG configuration for FROM.
# ============================================================

# syntax=docker/dockerfile:1

# frontend configuration for FROM.
FROM --platform=$BUILDPLATFORM oven/bun:1 AS frontend-builder
WORKDIR /app
COPY Reference/LightRAG/lightrag_webui/ ./lightrag_webui/
RUN --mount=type=cache,target=/root/.bun/install/cache \
    cd lightrag_webui \
    && bun install --frozen-lockfile \
    && bun --bun ./node_modules/vite/bin/vite.js build

# Service dependency and startup ordering for FROM.
# Service dependency and startup ordering for FROM.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    UV_HTTP_TIMEOUT=120
WORKDIR /app

# Service dependency and startup ordering for COPY.
COPY Reference/LightRAG/pyproject.toml .
COPY Reference/LightRAG/setup.py .
COPY Reference/LightRAG/README.md .
COPY Reference/LightRAG/lightrag/ ./lightrag/
RUN --mount=type=cache,target=/root/.local/share/uv \
    uv sync --no-dev --extra api --extra offline-storage --extra offline-llm --no-install-project --no-editable

# LightRAG, RAG configuration for COPY.
COPY --from=frontend-builder /app/lightrag/api/webui ./lightrag/api/webui
RUN --mount=type=cache,target=/root/.local/share/uv \
    uv sync --frozen --no-dev --extra api --extra offline --no-editable

# Sensitive configuration for RUN; use a securely generated environment-specific value.
RUN --mount=type=cache,target=/app/tiktoken_cache \
    mkdir -p /app/tiktoken_cache \
    && uv run lightrag-download-cache --cache-dir /app/tiktoken_cache \
    || case $? in 2) ;; *) exit $? ;; esac \
    && mkdir -p /app/data/tiktoken \
    && cp -r /app/tiktoken_cache/. /app/data/tiktoken/

# Configuration note for FROM.
# Copy the required files into the image.
FROM python:3.12-slim
WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/lightrag ./lightrag
COPY --from=builder /app/data/tiktoken /app/data/tiktoken

RUN mkdir -p /app/data/rag_storage /app/data/inputs

ENV TIKTOKEN_CACHE_DIR=/app/data/tiktoken \
    WORKING_DIR=/app/data/rag_storage \
    INPUT_DIR=/app/data/inputs

EXPOSE 9621
ENTRYPOINT ["python", "-m", "lightrag.api.lightrag_server"]
