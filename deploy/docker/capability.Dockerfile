# syntax=docker/dockerfile:1











ARG PYTHON_BASE=jonex/python-base:local
ARG CAPABILITY_NAME=knowledge_base

FROM ${PYTHON_BASE} AS base

WORKDIR /app


RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


COPY jonex_core/ ./jonex_core/


ARG CAPABILITY_NAME
COPY capabilities/${CAPABILITY_NAME}/ ./capabilities/${CAPABILITY_NAME}/


COPY deploy/start_capability.py .


HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1


EXPOSE 8000


CMD ["python", "start_capability.py"]
