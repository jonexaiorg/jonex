#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - Logging configuration module

Supports:
- Multi-level logging (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- Console output + file output
- Log rotation (by size, by date)
- JSON format logging (for log collection)
- Log filtering (e.g. health check)
- Request ID tracking
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

# Optional dependency: python-json-logger
try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    jsonlogger = None
    JSON_LOGGER_AVAILABLE = False

from jonex_core.common.config import get_config

config = get_config()


# ==================== Log filters ====================
class HealthCheckFilter(logging.Filter):
    """Filter health check request logs"""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        # Filter health check related logs
        if "/health" in message or "health_check" in message:
            return False
        return True


class RequestIdFilter(logging.Filter):
    """Inject request ID into logs"""

    def __init__(self, request_id: Optional[str] = None):
        super().__init__()
        self._request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self._request_id or "N/A"
        return True

    def set_request_id(self, request_id: str):
        self._request_id = request_id


# Global request ID filter
request_id_filter = RequestIdFilter()


def set_request_id(request_id: str):
    """Set current request ID (for log tracing)"""
    request_id_filter.set_request_id(request_id)


# ==================== Log format configuration ====================
# Text format (console)
TEXT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)

# Text format with request_id
TEXT_FORMAT_WITH_REQUEST_ID = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(request_id)s | %(filename)s:%(lineno)d | %(message)s"
)

# JSON format (file output, for ELK and other log collection systems)
JSON_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s "
    "%(filename)s %(lineno)d %(message)s"
)


def get_log_formatter(json_output: bool = False, include_request_id: bool = False) -> logging.Formatter:
    """
    Get log formatter

    Args:
        json_output: Whether to output JSON format
        include_request_id: Whether to include request_id field
    """
    if json_output and JSON_LOGGER_AVAILABLE:
        return jsonlogger.JsonFormatter(
            JSON_FORMAT,
            rename_fields={"levelname": "level", "asctime": "timestamp"},
        )
    else:
        fmt = TEXT_FORMAT_WITH_REQUEST_ID if include_request_id else TEXT_FORMAT
        return logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")


# ==================== Logging configuration ====================
def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_output: bool = False,
    enable_console: bool = True,
    enable_file: bool = True,
    max_bytes: int = 100 * 1024 * 1024,  # 100MB
    backup_count: int = 10,
):
    """
    Configure logging System

    Args:
        log_level: Log level, default reads from configuration
        log_file: Log file path, default reads from configuration
        json_output: Whether to output JSON format
        enable_console: Whether to enable console output
        enable_file: Whether to enable file output
        max_bytes: Maximum size of single log file
        backup_count: Number of log files to retain
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level or config.LOG_LEVEL)

    # Clear existing handlers (avoid duplicate output)
    root_logger.handlers.clear()

    # Add request ID filter
    root_logger.addFilter(request_id_filter)

    # 1. Console output
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(get_log_formatter(json_output=False, include_request_id=False))
        console_handler.addFilter(HealthCheckFilter())
        root_logger.addHandler(console_handler)

    # 2. File output
    if enable_file:
        log_path = log_file or config.LOG_FILE_PATH

        # Ensure log directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Rotate by size
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(get_log_formatter(json_output=json_output, include_request_id=True))
            root_logger.addHandler(file_handler)

            # Rotate by date (optional, for error logs)
            error_log_path = f"{os.path.splitext(log_path)[0]}_error{os.path.splitext(log_path)[1]}"
            error_file_handler = logging.handlers.TimedRotatingFileHandler(
                error_log_path,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
            )
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(get_log_formatter(json_output=json_output, include_request_id=True))
            root_logger.addHandler(error_file_handler)
        except Exception as e:
            logging.warning(f"Unable to create file log handler: {e}")

    # 3. Set third-party library log levels
    _set_third_party_log_levels()


def _set_third_party_log_levels():
    """Set third-party library log levels to avoid excessive logs"""
    # HTTP related
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

    # Database
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Redis
    logging.getLogger("redis").setLevel(logging.WARNING)

    # HTTP client
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


# ==================== Get logger ====================
def get_logger(name: str) -> logging.Logger:
    """
    Get logger

    Args:
        name: Logger name, typically use __name__

    Returns:
        logging.Logger instance
    """
    return logging.getLogger(name)


# ==================== Context manager ====================
class LogContext:
    """Log context manager, temporarily adds additional fields"""

    def __init__(self, **kwargs):
        self.extra = kwargs
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.extra.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# ==================== Performance logging decorator ====================
def log_execution_time(logger: logging.Logger, level: int = logging.INFO):
    """
    Decorator that records function execution time

    Args:
        logger: Logger instance
        level: Log level
    """
    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.log(
                    level,
                    f"Function {func.__name__} Execution time: {elapsed:.2f}ms"
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.log(
                    level,
                    f"Function {func.__name__} Execution time: {elapsed:.2f}ms"
                )

        return async_wrapper if func.__code__.co_flags & 0x80 else sync_wrapper

    return decorator


# ==================== Initialization ====================
# Initialize logging by default (using configuration)
try:
    # Disable file logging to avoid errors when file does not exist
    setup_logging(enable_file=False)
except Exception as e:
    # Use basic configuration when configuration fails
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.warning(f"Using default logging configuration, custom configuration loading failed: {e}")
