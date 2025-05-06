from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import contextvars
import logging
from typing import Optional

request_id_contextvar = contextvars.ContextVar[Optional[str]](
    "request_id", default=None
)
logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_contextvar.set(request_id)

        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
            },
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "method": request.method,
                "path": request.url.path,
            },
        )

        return response
