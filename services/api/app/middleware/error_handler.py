from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
from typing import Any, Dict

logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    error_response = {
        "error": exc.message,
        "status_code": exc.status_code,
        "path": request.url.path,
    }
    if exc.details:
        error_response["details"] = exc.details

    logger.error(
        "API Error",
        extra={
            "error": exc.message,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )
    return JSONResponse(status_code=exc.status_code, content=error_response)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    error_response = {
        "error": "Validation Error",
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "path": request.url.path,
        "details": exc.errors(),
    }

    logger.warning(
        "Validation Error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response
    )


async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    error_response = {
        "error": "Database Error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "path": request.url.path,
    }

    logger.error(
        "Database Error",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error_response = {
        "error": "Internal Server Error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "path": request.url.path,
    }

    logger.error(
        "Unhandled Exception",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response
    )
