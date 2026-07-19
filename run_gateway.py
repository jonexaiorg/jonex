#!/usr/bin/python3



import sys
import argparse


sys.path.insert(0, '.')

import uvicorn
from jonex_core.common import get_logger, get_config

config = get_config()
logger = get_logger("gateway_launcher")


def main():
    parser = argparse.ArgumentParser(description="Jonex平台 API 网关")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="监听地址 (默认: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="监听端口 (默认: 8000)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数 (默认: 1)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="开发模式：代码变更自动重载",
    )
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        choices=["dev", "test", "prod"],
        help="运行环境",
    )

    args = parser.parse_args()

    if args.env:
        import os
        os.environ["ENV"] = args.env
        logger.info(f"Setting runtime environment: {args.env}")

    logger.info("=" * 60)
    logger.info("Jonex Platform API Gateway is starting...")
    logger.info(f"Listening address: http://{args.host}:{args.port}")
    logger.info(f"Worker count: {args.workers}")
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
        logger.exception(f"API Gateway startup failed: {e}")
        sys.exit(1)
