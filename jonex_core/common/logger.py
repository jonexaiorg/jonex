#!/usr/bin/python3



import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    jsonlogger = None
    JSON_LOGGER_AVAILABLE = False

from jonex_core.common.config import get_config

config = get_config()



class HealthCheckFilter(logging.Filter):


    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()

        if "/health" in message or "health_check" in message:
            return False
        return True


class RequestIdFilter(logging.Filter):


    def __init__(self, request_id: Optional[str] = None):
        super().__init__()
        self._request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self._request_id or "N/A"
        return True

    def set_request_id(self, request_id: str):
        self._request_id = request_id



request_id_filter = RequestIdFilter()


def set_request_id(request_id: str):

    request_id_filter.set_request_id(request_id)




TEXT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)


TEXT_FORMAT_WITH_REQUEST_ID = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(request_id)s | %(filename)s:%(lineno)d | %(message)s"
)


JSON_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s "
    "%(filename)s %(lineno)d %(message)s"
)


def get_log_formatter(json_output: bool = False, include_request_id: bool = False) -> logging.Formatter:

    if json_output and JSON_LOGGER_AVAILABLE:
        return jsonlogger.JsonFormatter(
            JSON_FORMAT,
            rename_fields={"levelname": "level", "asctime": "timestamp"},
        )
    else:
        fmt = TEXT_FORMAT_WITH_REQUEST_ID if include_request_id else TEXT_FORMAT
        return logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")


def _build_process_log_path(log_path: str) -> str:

    path = Path(log_path)
    return str(path.with_name(f"{path.stem}.{os.getpid()}{path.suffix}"))



def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_output: bool = False,
    enable_console: bool = True,
    enable_file: bool = True,
    max_bytes: int = 100 * 1024 * 1024,
    backup_count: int = 10,
):


    root_logger = logging.getLogger()
    root_logger.setLevel(log_level or config.LOG_LEVEL)


    root_logger.handlers.clear()


    root_logger.addFilter(request_id_filter)


    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(get_log_formatter(json_output=False, include_request_id=False))
        console_handler.addFilter(request_id_filter)
        console_handler.addFilter(HealthCheckFilter())
        root_logger.addHandler(console_handler)


    if enable_file:
        log_path = _build_process_log_path(log_file or config.LOG_FILE_PATH)


        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)


        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(get_log_formatter(json_output=json_output, include_request_id=True))
            file_handler.addFilter(request_id_filter)
            root_logger.addHandler(file_handler)


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
            error_file_handler.addFilter(request_id_filter)
            root_logger.addHandler(error_file_handler)




            _attach_file_handlers_to_named_loggers(file_handler, error_file_handler)
        except Exception as e:
            logging.warning(f"Failed to create file log handler: {e}")


    _set_third_party_log_levels()


def _set_third_party_log_levels():


    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


    logging.getLogger("redis").setLevel(logging.WARNING)


    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def _attach_file_handlers_to_named_loggers(
    file_handler: logging.Handler,
    error_file_handler: logging.Handler,
):
    logger_names = (
        "api_gateway",
        "exception_handler",
        "jonex_core",
        "capabilities",
        "uvicorn",
        "uvicorn.error",
        "watchfiles",
        "watchfiles.main",
    )

    for name in logger_names:
        named_logger = logging.getLogger(name)
        existing_files = {
            getattr(handler, "baseFilename", None)
            for handler in named_logger.handlers
        }
        if getattr(file_handler, "baseFilename", None) not in existing_files:
            named_logger.addHandler(file_handler)
        if getattr(error_file_handler, "baseFilename", None) not in existing_files:
            named_logger.addHandler(error_file_handler)



def get_logger(name: str) -> logging.Logger:

    return logging.getLogger(name)



class LogContext:


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



def log_execution_time(logger: logging.Logger, level: int = logging.INFO):

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
                    f"Function {func.__name__} execution time: {elapsed:.2f}ms"
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
                    f"Function {func.__name__} execution time: {elapsed:.2f}ms"
                )

        return async_wrapper if func.__code__.co_flags & 0x80 else sync_wrapper

    return decorator




try:

    setup_logging(enable_file=True)
except Exception as e:

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.warning(f"Using default logging configuration because the custom configuration failed to load: {e}")
