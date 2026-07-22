#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - API Gateway

Unified entry point, responsible for:
- Request routing
- Authentication and authorization
- Rate limiting and circuit breaking
- Log tracing
- CORS handling
- Health check
"""

import time
import uuid
from typing import Optional

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from jonex_core.common import (
    get_config,
    get_logger,
    set_request_id,
    register_exception_handlers,
    MissingApiKeyError,
    InvalidApiKeyError,
)

config = get_config()
logger = get_logger("api_gateway")


# ==================== Request model ====================
class CapabilityInvokeRequest(BaseModel):
    """Capability invocation request"""
    capability_id: str
    action: str = "execute"
    payload: dict
    tenant_id: str = "default"
    user_id: Optional[str] = None
    context: Optional[dict] = None


# ==================== Dependency injection ====================
async def verify_api_key(request: Request) -> str:
    """
    Verify API Key

    Args:
        request: FastAPI Request object

    Returns:
        Tenant ID

    Raises:
        MissingApiKeyError: Missing API Key
        InvalidApiKeyError: Invalid API Key
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise MissingApiKeyError()

    # TODO: Verify API Key from Database
    # Temporary implementation: API Key for testing
    if api_key.startswith("jonex_test_"):
        tenant_id = api_key.replace("jonex_test_", "")
        return tenant_id
    else:
        raise InvalidApiKeyError()


async def rate_limit(request: Request):
    """
    Rate limiting middleware

    TODO: Use Redis to implement real rate limiting
    """
    # No actual rate limiting for now, just a placeholder
    pass


# ==================== Create application ====================
def create_app() -> FastAPI:
    """
    Create FastAPI application

    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="Jonex platform API Gateway",
        description="Jonex platform unified API entry point, providing capability invocation, authentication and authorization, rate limiting and circuit breaking, etc.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    # In production environment, specify specific domains via AUTH_CORS_ORIGINS (supports credentials)
    # In development environment when not configured, defaults to allow_origins=["*"] (credentials not allowed, complies with browser CORS specification)
    origins = config.cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=bool(origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        """Generate a unique ID for each request, used for tracing"""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)
        # Inject Request ID into request state
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        # Calculate request duration
        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"

        return response

    # Logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """Log requests"""
        request_id = getattr(request.state, "request_id", "N/A")
        method = request.method
        url = str(request.url.path)
        client_host = getattr(request.client, "host", "unknown")

        logger.info(
            f"[{request_id}] {method} {url} - from {client_host}"
        )

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"[{request_id}] {method} {url} - "
            f"status code: {response.status_code}, duration: {process_time:.2f}ms"
        )

        return response

    # Global exception handler (unified exception system)
    register_exception_handlers(app)

    # ==================== Route registration ====================
    register_routes(app)

    # ==================== Start event ====================
    @app.on_event("startup")
    async def startup_init_database():
        """Initialize database table structure on startup (auto-create tables)"""
        from jonex_core.common import init_database
        await init_database()

    return app


def register_routes(app: FastAPI):
    """
    Register all routes

    Args:
        app: FastAPI application instance
    """
    # ==================== Health check ====================
    @app.get("/health", summary="Health check", tags=["System"])
    async def health_check():
        """
        Service health check endpoint

        Returns:
            Service status information
        """
        # Note: The capability list is now managed by Sidecar uniformly,
        # API Gateway no longer holds capability instances, only does business route aggregation
        return {
            "status": "healthy",
            "service": "jonex-api-gateway",
            "version": "0.1.0",
            "note": "For the capability list, query via Sidecar endpoint: GET http://sidecar:8001/capabilities",
        }

    @app.get("/ready", summary="Ready check", tags=["System"])
    async def ready_check():
        """
        Service ready check (for K8s readinessProbe)

        Returns:
            Ready status information
        """
        return {
            "status": "ready",
            "service": "jonex-api-gateway",
        }

    # ==================== Capability-related interfaces (migrated to Sidecar) ====================
    # Note: Capability list and invocation interfaces are uniformly provided by Sidecar proxy
    # Sidecar is responsible for: authentication, metering, rate limiting, capability routing
    # API Gateway focuses on: business route aggregation, CORS handling, request tracing

    # ==================== System management interface ====================
    @app.get("/system/info", summary="Get system info", tags=["System management"])
    async def get_system_info(
        _: str = Depends(verify_api_key),
    ):
        """
        Get system info

        Returns:
            System info
        """
        return {
            "code": 0,
            "message": "success",
            "data": {
                "service_name": "jonex-api-gateway",
                "version": "0.1.0",
                "environment": config.ENV,
                "cors_enabled": True,
                "api_key_auth_enabled": True,
                "rate_limit_enabled": False,
            }
        }

    # ==================== Import route modules ====================
    try:
        from api_gateway.routes import knowledge_base_router, tcadp_router, auth_router
        app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
        app.include_router(knowledge_base_router, prefix="/api/v1/knowledge-base", tags=["Knowledge base"])
        app.include_router(tcadp_router)
        logger.info("Business route modules loaded successfully")
    except ImportError as e:
        logger.warning(f"Business route modules failed to load (may not be implemented yet): {e}")


# Global application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting API gateway service...")
    uvicorn.run(
        "api_gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
