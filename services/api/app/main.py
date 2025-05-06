from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware
from typing import Union, Callable, Any
from starlette.requests import Request
from starlette.responses import Response

from .settings import get_settings
from .routers import health, places, reverse, quickfacts, tiles
from .middleware.error_handler import (
    APIError,
    api_error_handler,
    validation_error_handler,
    sqlalchemy_error_handler,
    generic_error_handler,
)
from .middleware.request_id import RequestContextMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .logging_config import setup_logging
from .deps import get_cache

# Setup logging first
setup_logging()

settings = get_settings()

app = FastAPI(
    title="Geo API",
    version="1.0.0",
    default_response_class=ORJSONResponse,
)

# ---- exception handlers ---- #
# Type cast handlers to match FastAPI's expected types
ExceptionHandler = Callable[[Request, Exception], Union[Response, Any]]

app.add_exception_handler(APIError, api_error_handler)  # type: ignore
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)  # type: ignore
app.add_exception_handler(Exception, generic_error_handler)  # type: ignore

# ---- middleware ---- #
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(RequestContextMiddleware)

# Setup rate limiting
app.add_middleware(
    RateLimitMiddleware,
    cache=get_cache(),
    requests_per_minute=settings.rate_limit_per_minute,
)

if settings.cors_allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins.split(","),
        allow_methods=["GET"],
        allow_headers=["*"],
    )

# ---- mount routers ---- #
for r in (
    health.router,
    places.router,
    reverse.router,
    quickfacts.router,
    tiles.router,
):
    app.include_router(r)
