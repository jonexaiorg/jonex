# syntax=docker/dockerfile:1









ARG PYTHON_BASE=jonex/python-base:local
FROM ${PYTHON_BASE} AS base


COPY jonex_core/ ./jonex_core/


COPY main.py .


HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1


EXPOSE 8000


CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4}"]
