#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - Global exception handler

Provides FastAPI global exception handler functions, mapping exceptions to HTTP responses in a unified way
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from jonex_core.common.exceptions import JonexException, InternalError
from jonex_core.common.response import error_response
from jonex_core.common.logger import get_logger

logger = get_logger("exception_handler")


async def jonex_exception_handler(request: Request, exc: JonexException) -> JSONResponse:
    """
    Handle Jonex platform custom exceptions

    Args:
        request: FastAPI Request object
        exc: JonexException instance

    Returns:
        Unified format error response
    """
    request_id = getattr(request.state, "request_id", "N/A")
    logger.warning(
        f"[{request_id}] Business exception: code={exc.code}, message={exc.message}, "
        f"path={request.url.path}"
    )

    if exc.cause:
        logger.debug(f"[{request_id}] Original exception: {exc.cause}")

    return error_response(
        code=exc.code,
        message=exc.message,
        request_id=request_id,
        status_code=exc.status_code,
        details=exc.details if exc.details else None,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException

    Args:
        request: FastAPI Request object
        exc: HTTPException instance

    Returns:
        Unified format error response
    """
    request_id = getattr(request.state, "request_id", "N/A")
    logger.warning(
        f"[{request_id}] HTTP Exception: status={exc.status_code}, detail={exc.detail}, "
        f"path={request.url.path}"
    )

    return error_response(
        code=exc.status_code,
        message=str(exc.detail),
        request_id=request_id,
        status_code=exc.status_code,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request parameter validation errors (pydantic validation exception)

    Args:
        request: FastAPI Request object
        exc: RequestValidationError instance

    Returns:
        Unified format error response
    """
    request_id = getattr(request.state, "request_id", "N/A")
    errors = exc.errors()
    logger.warning(
        f"[{request_id}] Parameter validation failed: {len(errors)} error(s), path={request.url.path}"
    )

    return error_response(
        code=1001,
        message="Request parameter validation failed",
        request_id=request_id,
        status_code=422,
        details={"validation_errors": errors},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all uncaught exceptions (fallback)

    Args:
        request: FastAPI Request object
        exc: Exception instance

    Returns:
        Unified format 500 error response
    """
    request_id = getattr(request.state, "request_id", "N/A")
    logger.exception(
        f"[{request_id}] Uncaught exception: {type(exc).__name__}: {exc}, "
        f"path={request.url.path}"
    )

    internal_error = InternalError(
        message="Internal server error, please retry later",
        cause=exc,
    )

    return error_response(
        code=internal_error.code,
        message=internal_error.message,
        request_id=request_id,
        status_code=internal_error.status_code,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers to FastAPI application

    Args:
        app: FastAPI application instance
    """
    # Business exception (most specific)
    app.add_exception_handler(JonexException, jonex_exception_handler)
    # HTTP Exception
    app.add_exception_handler(HTTPException, http_exception_handler)
    # Parameter validation exception
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # Fallback exception handler
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Global exception handlers registered")
