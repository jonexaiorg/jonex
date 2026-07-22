
# syntax=docker/dockerfile:1

FROM --platform=$BUILDPLATFORM oven/bun:1 AS frontend-builder
WORKDIR /app
COPY Reference/LightRAG/lightrag_webui/ ./lightrag_webui/
RUN --mount=type=cache,target=/root/.bun/install/cache \
    cd lightrag_webui \
    && bun install --frozen-lockfile \
    && bun run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1
WORKDIR /app

COPY Reference/LightRAG/pyproject.toml .
COPY Reference/LightRAG/setup.py .
COPY Reference/LightRAG/uv.lock .
RUN --mount=type=cache,target=/root/.local/share/uv \
    uv sync --frozen --no-dev --extra api --extra offline --no-install-project --no-editable

COPY Reference/LightRAG/lightrag/ ./lightrag/
COPY --from=frontend-builder /app/lightrag/api/webui ./lightrag/api/webui
RUN --mount=type=cache,target=/root/.local/share/uv \
    uv sync --frozen --no-dev --extra api --extra offline --no-editable

RUN mkdir -p /app/data/tiktoken \
    && uv run lightrag-download-cache --cache-dir /app/data/tiktoken || status=$?; \
       if [ -n "${status:-}" ] && [ "$status" -ne 0 ] && [ "$status" -ne 2 ]; then exit "$status"; fi

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
