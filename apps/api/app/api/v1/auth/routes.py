from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.core.config import settings
from app.dependencies import get_audit_context, get_current_active_user, get_db, get_client_ip
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserRead
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter(prefix="", tags=["auth"])

COOKIE_NAME = "refresh_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * int(30)


def _set_refresh_cookie(response: Response, token: str, secure: bool = True) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
        max_age=COOKIE_MAX_AGE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


@router.post("/auth/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    auth_service = AuthService(db)
    user = await auth_service.register_user(
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        password=data.password,
        organization_name=data.organization_name,
    )
    await AuditService(db, user.organization_id).log(
        action="create",
        module="auth",
        entity="User",
        entity_id=user.id,
        user_id=user.id,
        after={"email": user.email},
        context=audit_context,
    )
    return user


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: Request, response: Response, data: LoginRequest, db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    auth_service = AuthService(db)
    device_name = request.headers.get("x-device-name")
    device_type = request.headers.get("x-device-type")
    user = await auth_service.authenticate_user(data.email, data.password)
    session_record = await auth_service.create_login_session(
        user, device_name, device_type, get_client_ip(request), request.headers.get("user-agent")
    )
    token_data = await auth_service.create_session_tokens(user, session_record)
    await AuditService(db, user.organization_id).log(
        action="login",
        module="auth",
        entity="User",
        entity_id=user.id,
        user_id=user.id,
        context=audit_context,
    )
    _set_refresh_cookie(response, token_data["refresh_token"], secure=settings.is_production_like)
    return token_data


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, data: RefreshTokenRequest | None = None, db: AsyncSession = Depends(get_db)):
    refresh_token = data.refresh_token if data and data.refresh_token else request.cookies.get(COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found.")
    auth_service = AuthService(db)
    token_data = await auth_service.refresh(refresh_token)
    _set_refresh_cookie(response, token_data["refresh_token"], secure=settings.is_production_like)
    return token_data


@router.post("/auth/logout")
async def logout(
    request: Request,
    response: Response,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    refresh_token = request.cookies.get(COOKIE_NAME)
    auth_service = AuthService(db)
    await auth_service.logout(user_id=current_user.id, refresh_token=refresh_token)
    await AuditService(db, current_user.organization_id).log(
        action="logout",
        module="auth",
        entity="User",
        entity_id=current_user.id,
        user_id=current_user.id,
        context=audit_context,
    )
    _clear_refresh_cookie(response)
    return {"detail": "Logged out successfully."}


@router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.forgot_password(data.email)
    return {"detail": "If an account exists for that email, instructions have been sent."}


@router.post("/auth/reset-password")
async def reset_password(data: PasswordResetRequest, db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    auth_service = AuthService(db)
    user = await auth_service.reset_password(data.token, data.new_password)
    await AuditService(db, user.organization_id).log(
        action="password_change",
        module="auth",
        entity="User",
        entity_id=user.id,
        user_id=user.id,
        context=audit_context,
    )
    return {"detail": "Password has been reset successfully."}


@router.post("/auth/verify-email")
async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.verify_email(data.token)
    return {"detail": "Email has been verified successfully."}


@router.post("/auth/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    auth_service = AuthService(db)
    await auth_service.change_password(current_user, data.current_password, data.new_password)
    await AuditService(db, current_user.organization_id).log(
        action="password_change",
        module="auth",
        entity="User",
        entity_id=current_user.id,
        user_id=current_user.id,
        context=audit_context,
    )
    return {"detail": "Password changed successfully."}


@router.get("/auth/me", response_model=UserRead)
async def get_me(current_user=Depends(get_current_active_user)):
    return current_user

