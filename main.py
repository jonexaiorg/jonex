#!/usr/bin/env python3
"""
Jonex platform Sidecar proxy entry point

Sidecar acts as the unified entry point for internal capability invocation, invoking capability services via reverse proxy
Provides: authentication, metering, rate limiting, log tracing and other cross-cutting concerns
"""

import uvicorn
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def create_app():
    """Create Sidecar application"""
    from jonex_core.sidecar import get_sidecar_app

    # Get Sidecar application
    sidecar_app = get_sidecar_app()

    logger.info("=" * 60)
    logger.info("Jonex platform Sidecar proxy started successfully")
    logger.info("Running mode: reverse proxy mode (invoking standalone capability services)")
    logger.info(f"Listening port: {sidecar_app.app.state}.{8001}")
    logger.info("API docs: http://localhost:8001/docs")
    logger.info("=" * 60)

    return sidecar_app.get_app()


# Create FastAPI application for uvicorn to start
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Sidecar uses port 8001
        reload=True,
        log_level="info"
    )
