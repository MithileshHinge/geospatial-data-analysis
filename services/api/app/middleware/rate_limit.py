from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from tsg_common.cache import Cache
import time
from typing import Any
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        cache: Cache,
        requests_per_minute: int = 60,
        cache_prefix: str = "ratelimit:",
    ):
        super().__init__(app)
        self.cache = cache
        self.requests_per_minute = requests_per_minute
        self.cache_prefix = cache_prefix
        logger.info(
            f"RateLimitMiddleware initialized with {requests_per_minute} requests per minute"
        )

    def get_client_identifier(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        client_id = self.get_client_identifier(request)
        current_time = int(time.time())
        minute_key = f"{self.cache_prefix}{client_id}:{current_time // 60}"

        logger.debug(f"Rate limit check for client_id: {client_id}, key: {minute_key}")

        try:
            # Get current count or initialize to 0
            count_str = self.cache.get(minute_key)
            logger.debug(f"Current count from cache: {count_str}")

            count = int(count_str) if count_str is not None else 0
            count += 1

            logger.debug(f"New count after increment: {count}")

            # Store with 1 minute expiry
            self.cache.set(minute_key, str(count), ttl=60)

            if count > self.requests_per_minute:
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "client_id": client_id,
                        "requests": count,
                        "limit": self.requests_per_minute,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                )

        except Exception as e:
            if not isinstance(e, HTTPException):
                logger.error(
                    f"Rate limiting error: {str(e)}",
                    extra={
                        "error": str(e),
                        "client_id": client_id,
                    },
                    exc_info=True,
                )
            # On cache errors, we'll let the request through but log the error
            if isinstance(e, HTTPException):
                raise
            return await call_next(request)

        response = await call_next(request)

        # Add rate limit headers
        try:
            remaining = max(0, self.requests_per_minute - count)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str((current_time // 60 + 1) * 60)
        except Exception as e:
            logger.error("Error setting rate limit headers", extra={"error": str(e)})

        return response
