#!/usr/bin/env python3


import os
import importlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from jonex_core.capability import get_capability_registry
from jonex_core.common.exception_handler import register_exception_handlers
from jonex_core.discovery import get_service_registry, HeartbeatManager, ServiceInstance
from jonex_core.security import verify_internal_service


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


CAPABILITY_NAME = os.getenv("CAPABILITY_NAME", "knowledge_base")
CAPABILITY_KIND = os.getenv("CAPABILITY_KIND", "business")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")


SERVICE_ENDPOINT = os.getenv("SERVICE_ENDPOINT", f"http://{CAPABILITY_KIND}-{CAPABILITY_NAME.replace('_', '-')}:{SERVICE_PORT}")



CAPABILITY_ID = f"{CAPABILITY_KIND}.{CAPABILITY_NAME}.v1"

logger.info(f"Starting capability service: {CAPABILITY_NAME}")
logger.info(f"Service endpoint: {SERVICE_ENDPOINT}")
logger.info(f"Capability ID: {CAPABILITY_ID}")



heartbeat_manager: HeartbeatManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global heartbeat_manager


    registry = get_capability_registry()
    capability = None
    try:
        module_overrides = {
            ("atomic", "rag.lightrag"): (
                "jonex_core.capability.atomic.rag.lightrag_adapter",
                "LightRAGAdapter",
            ),
            ("domain", "rag.text"): (
                "jonex_core.capability.domain.rag_text.rag_text",
                "DomainRAGText",
            ),
        }
        override = module_overrides.get((CAPABILITY_KIND, CAPABILITY_NAME))
        if override:
            module_path, class_name = override
        elif CAPABILITY_KIND == "business":
            module_path = f"capabilities.{CAPABILITY_NAME}"
            class_name = "".join(word.title() for word in CAPABILITY_NAME.split("_")) + "Capability"
        elif CAPABILITY_KIND in {"atomic", "domain"}:
            module_path = f"jonex_core.capability.{CAPABILITY_KIND}.{CAPABILITY_NAME.replace('.', '_')}"
            class_name = "".join(
                word.title() for word in CAPABILITY_NAME.replace(".", "_").split("_")
            ) + "Capability"
        else:
            raise ValueError(f"不支持的能力类型: {CAPABILITY_KIND}")


        module = importlib.import_module(module_path)
        capability_class = getattr(module, class_name)
        capability = capability_class()
        registry.register(capability)
        await capability.initialize()

        if hasattr(capability, "register_routes"):
            try:
                capability.register_routes(app)
            except Exception:
                logger.exception("Custom capability route registration failed")
        logger.info(f"Capability {CAPABILITY_KIND}.{CAPABILITY_NAME} registered locally")
    except Exception as e:
        logger.exception(f"Local capability registration failed: {e}")
        raise


    try:
        service_registry = get_service_registry()
        instance = ServiceInstance(
            service_name=CAPABILITY_NAME,
            service_type="capability",
            endpoint=SERVICE_ENDPOINT,
            capability_id=CAPABILITY_ID,
            version="v1",
            metadata={
                "capability_name": capability.get_metadata().capability_name,
                "description": capability.get_metadata().description,
            }
        )
        heartbeat_manager = HeartbeatManager(
            registry=service_registry,
            instance=instance,
            interval=30,
        )
        await heartbeat_manager.start()
        logger.info(f"Capability service {CAPABILITY_NAME} registered with service discovery")
    except Exception as e:
        logger.exception(f"Service registration failed: {e}")


    yield


    if capability:
        try:
            await capability.shutdown()
        except Exception as e:
            logger.exception(f"Capability shutdown failed: {e}")
    if heartbeat_manager:
        try:
            await heartbeat_manager.stop()
            logger.info(f"Capability service {CAPABILITY_NAME} deregistered from service discovery")
        except Exception as e:
            logger.exception(f"Service deregistration failed: {e}")



app = FastAPI(
    title=f"Jonex Capability: {CAPABILITY_NAME}",
    description=f"Jonex平台能力服务: {CAPABILITY_NAME}",
    version="1.0.0",
    lifespan=lifespan,
)
register_exception_handlers(app)



@app.get("/health")
async def health_check():

    registry = get_capability_registry()
    return {
        "status": "healthy",
        "capability": CAPABILITY_NAME,
        "capability_id": CAPABILITY_ID,
        "endpoint": SERVICE_ENDPOINT,
        "capabilities": registry.list_capabilities(),
    }



@app.post("/invoke")
async def invoke_capability(
    request: dict,
    service_name: str = Depends(verify_internal_service)
):

    capability_id = request.get("capability_id")
    payload = request.get("payload", {})
    tenant_id = request.get("tenant_id", "default")

    from jonex_core.capability.models import CapabilityRequest
    req = CapabilityRequest(
        tenant_id=tenant_id,
        capability_id=capability_id,
        payload=payload,
        user_id=request.get("user_id"),
        username=request.get("username"),
        ip=request.get("ip"),
    )


    incoming_request_id = request.get("request_id")
    if incoming_request_id:
        req.request_id = incoming_request_id

    registry = get_capability_registry()
    result = await registry.invoke(capability_id, req)

    return {
        "request_id": result.request_id,
        "success": result.success,
        "code": result.code,
        "message": result.message,
        "data": result.data
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
