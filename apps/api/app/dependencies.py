from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.core.tenant import TenantContext
from app.db import get_db
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.permission_service import PermissionService
from app.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
_optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/customers/auth/login", auto_error=False)


async def get_tenant_context(request: Request) -> TenantContext:
    return getattr(request.state, "tenant_context", TenantContext())


async def get_audit_context(request: Request) -> AuditContext:
    return getattr(request.state, "audit_context", AuditContext())


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    user_id = payload.get("sub")
    session_id = payload.get("sid")
    organization_id = payload.get("oid")
    if not user_id or not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    user = await UserRepository(db, organization_id=organization_id).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")
    if organization_id and user.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    session_record = await SessionRepository(db, organization_id=organization_id).get_by_id(session_id)
    if not session_record or session_record.revoked or session_record.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalid or expired.")

    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user.")
    return current_user


async def get_current_user_optional(token: str | None = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        return None
    try:
        payload = decode_token(token)
    except ValueError:
        return None

    user_id = payload.get("sub")
    session_id = payload.get("sid")
    organization_id = payload.get("oid")
    if not user_id or not session_id:
        return None

    user = await UserRepository(db, organization_id=organization_id).get_by_id(user_id)
    if not user or not user.is_active:
        return None
    if organization_id and user.organization_id != organization_id:
        return None

    session_record = await SessionRepository(db, organization_id=organization_id).get_by_id(session_id)
    if not session_record or session_record.revoked or session_record.user_id != user.id:
        return None

    return user


async def get_current_customer(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    from app.repositories.customer_repository import CustomerRepository

    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    if payload.get("typ") != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    customer_id = payload.get("sub")
    organization_id = payload.get("oid")
    if not customer_id or not organization_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    customer = await CustomerRepository(db, organization_id=organization_id).get_by_id(customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer not found or inactive.")

    return customer


async def get_current_customer_optional(token: str | None = Depends(_optional_oauth2_scheme), db: AsyncSession = Depends(get_db)):
    from app.repositories.customer_repository import CustomerRepository

    if not token:
        return None
    try:
        payload = decode_token(token)
    except ValueError:
        return None

    if payload.get("typ") != "customer":
        return None

    customer_id = payload.get("sub")
    organization_id = payload.get("oid")
    if not customer_id or not organization_id:
        return None

    customer = await CustomerRepository(db, organization_id=organization_id).get_by_id(customer_id)
    if not customer or not customer.is_active:
        return None

    return customer


def require_permission(permission_code: str):
    async def permission_dependency(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
        permission_service = PermissionService(db, current_user.organization_id, current_user.is_superuser)
        if not await permission_service.has_permission(current_user.id, permission_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")
        return current_user

    return permission_dependency


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client is not None else "unknown"
