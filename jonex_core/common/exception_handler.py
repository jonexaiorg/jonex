#!/usr/bin/python3



from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from jonex_core.common.exceptions import JonexException, InternalError
from jonex_core.common.response import error_response
from jonex_core.common.logger import get_logger

logger = get_logger("exception_handler")


async def jonex_exception_handler(request: Request, exc: JonexException) -> JSONResponse:

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

    request_id = getattr(request.state, "request_id", "N/A")
    logger.warning(
        f"[{request_id}] HTTP exception: status={exc.status_code}, detail={exc.detail}, "
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

    request_id = getattr(request.state, "request_id", "N/A")
    errors = exc.errors()
    logger.warning(
        f"[{request_id}] Request validation failed: {len(errors)} errors, path={request.url.path}"
    )

    return error_response(
        code=1001,
        message="Request parameter validation failed",
        request_id=request_id,
        status_code=422,
        details={"validation_errors": errors},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    request_id = getattr(request.state, "request_id", "N/A")
    logger.exception(
        f"[{request_id}] Unhandled exception: {type(exc).__name__}: {exc}, "
        f"path={request.url.path}"
    )

    internal_error = InternalError(
        message="Internal server error. Try again later",
        cause=exc,
    )

    return error_response(
        code=internal_error.code,
        message=internal_error.message,
        request_id=request_id,
        status_code=internal_error.status_code,
    )


def register_exception_handlers(app: FastAPI) -> None:


    app.add_exception_handler(JonexException, jonex_exception_handler)

    app.add_exception_handler(HTTPException, http_exception_handler)

    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Global exception handlers registered")
