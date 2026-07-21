from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.utils.security import decode_token
from app.core.tenant import TenantContext


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_context = TenantContext()
        authorization = request.headers.get("authorization")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
            try:
                payload = decode_token(token)
                tenant_context.organization_id = payload.get("oid")
                tenant_context.user_id = payload.get("sub")
                tenant_context.is_superuser = bool(payload.get("is_superuser"))
            except Exception:
                tenant_context = TenantContext()

        request.state.tenant_context = tenant_context
        return await call_next(request)
