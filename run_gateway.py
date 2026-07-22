#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - API Gateway startup script

Usage:
    python run_gateway.py          # Start gateway
    python run_gateway.py --port 8080  # Specify port
"""

import sys
import argparse

# Add project root directory to path
sys.path.insert(0, '.')

import uvicorn
from jonex_core.common import get_logger, get_config

config = get_config()
logger = get_logger("gateway_launcher")


def main():
    parser = argparse.ArgumentParser(description="Jonex platform API Gateway")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Listen address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Listen port (default: 8000)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Development mode: auto-reload on code changes",
    )
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        choices=["dev", "test", "prod"],
        help="Runtime environment",
    )

    args = parser.parse_args()

    if args.env:
        import os
        os.environ["ENV"] = args.env
        logger.info(f"Set runtime environment: {args.env}")

    logger.info("=" * 60)
    logger.info("Jonex platform API Gateway starting...")
    logger.info(f"Listen address: http://{args.host}:{args.port}")
    logger.info(f"Number of worker processes: {args.workers}")
    logger.info(f"Development mode: {'enabled' if args.reload else 'disabled'}")
    logger.info(f"Runtime environment: {config.ENV}")
    logger.info("=" * 60)

    uvicorn.run(
        "api_gateway.main:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("API Gateway stopped")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"API Gateway failed to start: {e}")
        sys.exit(1)
