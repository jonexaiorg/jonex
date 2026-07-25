"""
FastAPI application factory for RAGAnything Service.

Middleware stack:
  - X-Request-ID injection (via contextvars)
  - X-Tenant-ID extraction + validation
  - Unified error handler (Spec §4.1 — code = HTTP*100 + sub)
  - Graceful shutdown hook (Spec §4.8)

Usage:
    python -m raganything.service.app --profile dev --port 8004
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from raganything.service.context import request_id_var, tenant_id_var, get_request_id
from raganything.service.routes.tasks import router as tasks_router
from raganything.service.routes.presets import router as presets_router
from raganything.service.routes.prompts import router as prompts_router
from raganything.service.routes.health import router as health_router
from raganything.service.task_manager import TaskManager, SlotFullError
from raganything.service.config_resolver import ConfigResolver, ConfigResolveError
from raganything.service.model_factory import ModelFactory
from raganything.service.prompt_config_manager import PromptConfigManager
from raganything.service.models import ErrorResponse

logger = logging.getLogger(__name__)


# ── Error code helpers (Spec §4.1: code = HTTP_STATUS * 100 + sub) ──

def _error(code: int, message: str, data: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=code // 100,
        content=ErrorResponse(
            code=code, request_id=get_request_id(), message=message, data=data,
        ).model_dump(mode="json"),
    )


# ── Middleware ──────────────────────────────────────────────────────


async def _request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    request_id_var.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


async def _tenant_middleware(request: Request, call_next):
    tenant = request.headers.get("X-Tenant-ID", "")
    # Open endpoints (health, presets list) allow empty tenant
    tenant_id_var.set(tenant)
    return await call_next(request)


# ── Exception handlers ──────────────────────────────────────────────


async def _slot_full_handler(request: Request, exc: SlotFullError):
    return JSONResponse(status_code=429, content=exc.response.model_dump(mode="json"))


async def _config_resolve_handler(request: Request, exc: ConfigResolveError):
    return _error(40002, str(exc))


async def _generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return _error(50001, "Internal server error")


# ── App factory ─────────────────────────────────────────────────────


def create_app(
    task_manager: TaskManager,
    config_resolver: ConfigResolver,
    prompt_config_manager: PromptConfigManager | None = None,
    title: str = "RAGAnything Service",
) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        await task_manager.start()
        yield
        # Shutdown — graceful stop (Spec §4.8)
        await task_manager.shutdown()

    app = FastAPI(title=title, version="1.0.0", lifespan=lifespan)

    # ── Middleware ─────────────────────────────────────────────────
    app.middleware("http")(_request_id_middleware)
    app.middleware("http")(_tenant_middleware)

    # ── Exception handlers ─────────────────────────────────────────
    app.add_exception_handler(SlotFullError, _slot_full_handler)
    app.add_exception_handler(ConfigResolveError, _config_resolve_handler)
    app.add_exception_handler(Exception, _generic_exception_handler)

    # ── Inject dependencies into routes ────────────────────────────
    app.state.task_manager = task_manager
    app.state.config_resolver = config_resolver
    app.state.prompt_config_manager = prompt_config_manager or PromptConfigManager()

    # ── Routes ─────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(presets_router, prefix="/api/v1")
    app.include_router(prompts_router, prefix="/api/v1")

    return app


# ── CLI entry ──────────────────────────────────────────────────────


def main():
    import argparse, os

    parser = argparse.ArgumentParser(description="RAGAnything Service")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8004)
    parser.add_argument("--profile", default="dev")
    parser.add_argument("--base-dir", default="./rag_service_data")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    profiles_dir = os.path.join("config", "profiles")
    presets_dir = os.path.join("config", "presets")

    mf = ModelFactory(profiles_dir=profiles_dir)
    tm = TaskManager(base_dir=args.base_dir, model_factory=mf)
    cr = ConfigResolver(profiles_dir=profiles_dir, presets_dir=presets_dir)
    tm.set_config_resolver(cr)

    app = create_app(tm, cr)

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())


if __name__ == "__main__":
    main()
