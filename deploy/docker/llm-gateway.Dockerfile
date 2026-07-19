# syntax=docker/dockerfile:1









ARG PYTHON_BASE=jonex/python-base:local
FROM ${PYTHON_BASE} AS base


COPY jonex_core/ ./jonex_core/


COPY run_llm_gateway.py .


HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8787/health || exit 1


EXPOSE 8787


CMD ["sh", "-c", "uvicorn jonex_core.llm_gateway.app:app --host 0.0.0.0 --port 8787 --workers ${WORKERS:-2}"]
