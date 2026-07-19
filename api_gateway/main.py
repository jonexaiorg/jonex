#!/usr/bin/python3



import time
import uuid

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from jonex_core.common import (
    get_config,
    get_logger,
    setup_logging,
    set_request_id,
    register_exception_handlers,
    MissingApiKeyError,
    InvalidApiKeyError,
    require_tenant,
)

config = get_config()
logger = get_logger("api_gateway")



async def verify_api_key(request: Request) -> str:

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise MissingApiKeyError()



    if config.ENV.lower() in {"dev", "test"} and api_key.startswith("jonex_test_"):
        return require_tenant(api_key.removeprefix("jonex_test_"))
    else:
        raise InvalidApiKeyError()



def create_app() -> FastAPI:

    app = FastAPI(
        title="Jonex平台 API 网关",
        description="Jonex平台统一 API 入口，提供能力调用、认证鉴权、限流熔断等功能",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )




    origins = config.cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=bool(origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )


    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)

        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)


        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"

        return response


    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):

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
            f"Status code: {response.status_code}, Duration: {process_time:.2f}ms"
        )

        return response


    register_exception_handlers(app)

    @app.on_event("startup")
    async def configure_local_file_logging():


        setup_logging(enable_file=True)
        logger.info("API Gateway local file logging enabled")


    register_routes(app)

    return app


def register_routes(app: FastAPI):


    @app.get("/health", summary="健康检查", tags=["系统"])
    async def health_check():



        return {
            "status": "healthy",
            "service": "jonex-api-gateway",
            "version": "0.1.0",
            "note": "能力列表请通过 Sidecar 端点查询: GET http://sidecar:8001/capabilities",
        }

    @app.get("/ready", summary="就绪检查", tags=["系统"])
    async def ready_check():

        return {
            "status": "ready",
            "service": "jonex-api-gateway",
        }







    @app.get("/system/info", summary="获取系统信息", tags=["系统管理"])
    async def get_system_info(
        _: str = Depends(verify_api_key),
    ):

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


    try:
        from api_gateway.routes import knowledge_base_router, tcadp_router, auth_router, platform_router, ecosystem_router
        from api_gateway.routes import knowledge_base_ingest_router
        app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
        app.include_router(platform_router, prefix="/api/v1/platform", tags=["平台管理"])
        app.include_router(knowledge_base_router, prefix="/api/v1/knowledge-base", tags=["知识库"])
        app.include_router(knowledge_base_ingest_router, prefix="/api/v1/knowledge-base", tags=["知识库-入站推送"])
        app.include_router(ecosystem_router, tags=["生态管理"])
        app.include_router(tcadp_router)
        logger.info("Business route module loaded successfully")
    except ImportError as e:
        logger.warning(f"Failed to load business route module (it may not be implemented yet): {e}")



app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting API Gateway service...")
    uvicorn.run(
        "api_gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
