from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.audit_context import AuditContext
from app.core.request_context import set_request_id


class AuditContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid4().hex
        set_request_id(request_id)
        request.state.audit_context = AuditContext(
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_id=request_id,
        )
        try:
            response = await call_next(request)
        finally:
            set_request_id(None)
        response.headers["X-Request-ID"] = request_id
        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client is not None else "unknown"
