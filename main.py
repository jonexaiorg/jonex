#!/usr/bin/env python3


import uvicorn
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def create_app():

    from jonex_core.sidecar import get_sidecar_app


    sidecar_app = get_sidecar_app()

    logger.info("=" * 60)
    logger.info("Jonex Platform Sidecar proxy started successfully")
    logger.info("Operating mode: reverse proxy (invokes independent capability services)")
    logger.info(f"Listening port: {sidecar_app.app.state}.{8001}")
    logger.info("API documentation: http://localhost:8001/docs")
    logger.info("=" * 60)

    return sidecar_app.get_app()



app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
