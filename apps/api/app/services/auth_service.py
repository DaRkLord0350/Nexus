from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.email_verification_token import EmailVerificationToken
from app.models.organization import Organization, OrganizationStatus
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.session import Session
from app.models.user import User
from app.repositories.email_verification_token_repository import EmailVerificationTokenRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.services.rbac_service import RBACService
from app.utils.security import create_access_token, hash_password, verify_password
from app.utils.tokens import generate_token, hash_token
from app.utils.text import slugify


def _build_organization_slug(name: str) -> str:
    return slugify(name, fallback="organization")


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.session_repo = SessionRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)
        self.email_verification_repo = EmailVerificationTokenRepository(session)
        self.password_reset_repo = PasswordResetTokenRepository(session)
        self.email_service = EmailService()

    async def register_user(self, email: str, first_name: str, last_name: str, password: str, organization_name: str) -> User:
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")

        organization_slug = _build_organization_slug(organization_name)
        clean_slug = organization_slug
        index = 1
        while await self.organization_repo.get_by_slug(clean_slug):
            clean_slug = f"{organization_slug}-{index}"
            index += 1

        organization = Organization(
            name=organization_name,
            slug=clean_slug,
            status=OrganizationStatus.active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        organization = await self.organization_repo.create(organization)

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password),
            organization_id=organization.id,
            is_active=True,
            is_verified=False,
            is_superuser=False,
        )
        user = await self.user_repo.create(user)

        rbac_service = RBACService(self.session, organization_id=organization.id)
        await rbac_service.initialize_default_roles_and_permissions()
        owner_role = await rbac_service.role_repo.get_by_name("Owner")
        if owner_role:
            await rbac_service.assign_role_to_user(user.id, owner_role.id)

        verification_token = generate_token(48)
        token_record = EmailVerificationToken(
            user_id=user.id,
            organization_id=organization.id,
            token_hash=hash_token(verification_token),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            revoked=False,
        )
        await self.email_verification_repo.create(token_record)

        verification_url = f"{settings.frontend_url}/verify-email?token={verification_token}"
        await self.email_service.send_verification_email(user.email, verification_url)

        return user

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

        user.last_login_at = datetime.utcnow()
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_login_session(self, user: User, device_name: str | None, device_type: str | None, ip_address: str | None, user_agent: str | None) -> Session:
        session_record = Session(
            user_id=user.id,
            organization_id=user.organization_id,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
            last_active_at=datetime.utcnow(),
            revoked=False,
        )
        return await self.session_repo.create(session_record)

    async def create_session_tokens(self, user: User, session_record: Session) -> dict[str, str]:
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
            additional_claims={
                "oid": user.organization_id,
                "sid": session_record.id,
                "is_superuser": user.is_superuser,
            },
        )
        refresh_token_value = generate_token(64)
        token_record = RefreshToken(
            user_id=user.id,
            organization_id=user.organization_id,
            session_id=session_record.id,
            token_hash=hash_token(refresh_token_value),
            expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
            revoked=False,
        )
        await self.refresh_repo.create(token_record)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_value,
            "token_type": "bearer",
        }

    async def login(self, email: str, password: str, device_name: str | None, device_type: str | None, ip_address: str | None, user_agent: str | None) -> dict[str, str]:
        user = await self.authenticate_user(email, password)
        session_record = await self.create_login_session(user, device_name, device_type, ip_address, user_agent)
        return await self.create_session_tokens(user, session_record)

    async def refresh(self, refresh_token: str) -> dict[str, str]:
        token_hash = hash_token(refresh_token)
        token_record = await self.refresh_repo.get_valid_by_hash(token_hash)
        if not token_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

        session_record = await self.session_repo.get_by_id(token_record.session_id)
        if not session_record or session_record.revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session.")

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

        await self.refresh_repo.revoke(token_record.id)
        session_record.last_active_at = datetime.utcnow()
        self.session.add(session_record)
        await self.session.commit()

        return await self.create_session_tokens(user, session_record)

    async def logout(self, user_id: str, session_id: str | None = None, refresh_token: str | None = None) -> None:
        if session_id:
            await self.session_repo.revoke(session_id)
            await self.refresh_repo.revoke_all_for_session(session_id)
            return
        if refresh_token:
            token_hash = hash_token(refresh_token)
            token_record = await self.refresh_repo.get_valid_by_hash(token_hash)
            if token_record:
                await self.session_repo.revoke(token_record.session_id)
                await self.refresh_repo.revoke_all_for_session(token_record.session_id)
            return

    async def forgot_password(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return
        reset_token = generate_token(64)
        token_record = PasswordResetToken(
            user_id=user.id,
            organization_id=user.organization_id,
            token_hash=hash_token(reset_token),
            expires_at=datetime.utcnow() + timedelta(hours=2),
            revoked=False,
        )
        await self.password_reset_repo.create(token_record)
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
        await self.email_service.send_password_reset_email(user.email, reset_url)

    async def reset_password(self, token: str, new_password: str) -> User:
        token_hash = hash_token(token)
        token_record = await self.password_reset_repo.get_valid_by_hash(token_hash)
        if not token_record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token.")

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload.")

        user.hashed_password = hash_password(new_password)
        user.is_verified = True
        self.session.add(user)
        await self.session.commit()

        await self.password_reset_repo.revoke(token_record.id)
        await self.session_repo.revoke_all_for_user(user.id)
        await self.refresh_repo.revoke_all_for_user(user.id)
        return user

    async def verify_email(self, token: str) -> None:
        token_hash = hash_token(token)
        token_record = await self.email_verification_repo.get_valid_by_hash(token_hash)
        if not token_record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token.")

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload.")

        user.is_verified = True
        self.session.add(user)
        await self.session.commit()
        await self.email_verification_repo.revoke(token_record.id)

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

        user.hashed_password = hash_password(new_password)
        self.session.add(user)
        await self.session.commit()

        await self.refresh_repo.revoke_all_for_user(user.id)
