from typing import Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis import redis_client


class RateLimiterMiddleware(BaseHTTPMiddleware):
    rate_limits: dict[str, Tuple[int, int]] = {
        "/api/v1/auth/login": (10, 60),
        "/api/v1/auth/signup": (5, 60),
        "/api/v1/auth/forgot-password": (5, 60),
        "/api/v1/auth/refresh": (15, 60),
        "/api/v1/auth/verify-email": (10, 60),
        "/api/v1/auth/reset-password": (5, 60),
    }

    async def dispatch(self, request: Request, call_next):
        endpoint = request.url.path
        limit = self.rate_limits.get(endpoint)
        if limit:
            client_ip = self._get_client_ip(request)
            key = f"rate:{endpoint}:{client_ip}"
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, limit[1])
            if count > limit[0]:
                return JSONResponse(
                    {"detail": "Too many requests. Please try again later."},
                    status_code=429,
                )
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client is not None else "unknown"
