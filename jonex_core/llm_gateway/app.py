


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jonex_core.llm_gateway.auth import token_swap
from jonex_core.llm_gateway.router import router
from jonex_core.common.config import get_config


def build_app() -> FastAPI:

    cfg = get_config()

    app = FastAPI(
        title="Jonex平台 - LLM 网关",
        description="OpenAI 兼容代理服务，统一 LLM/Embedding 出口计量",
        version=cfg.APP_VERSION,
    )


    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    app.middleware("http")(token_swap)


    app.include_router(router)


    try:
        from jonex_core.common import register_exception_handlers
        register_exception_handlers(app)
    except ImportError:
        pass

    return app


app = build_app()