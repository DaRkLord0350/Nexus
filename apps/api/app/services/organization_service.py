from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.organization import Organization, OrganizationStatus
from app.models.user import User
from app.models.organization_invitation import OrganizationInvitation
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.organization_invitation_repository import OrganizationInvitationRepository
from app.services.email_service import EmailService
from app.services.rbac_service import RBACService
from app.utils.security import hash_password
from app.utils.tokens import generate_token, hash_token


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.organization_repo = OrganizationRepository(session)
        self.user_repo = UserRepository(session)
        self.session_repo = SessionRepository(session)
        self.refresh_token_repo = RefreshTokenRepository(session)
        self.invitation_repo = OrganizationInvitationRepository(session)
        self.email_service = EmailService()

    async def get_organization(self, organization_id: str) -> Organization | None:
        return await self.organization_repo.get_by_id(organization_id)

    async def list_members(self, organization_id: str) -> list[User]:
        scoped_user_repo = UserRepository(self.session, organization_id=organization_id)
        return await scoped_user_repo.list_for_organization()

    async def update_organization(self, organization_id: str, data: dict) -> Organization:
        organization = await self.get_organization(organization_id)
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

        for field, value in data.items():
            if hasattr(organization, field):
                setattr(organization, field, value)

        self.session.add(organization)
        await self.session.commit()
        await self.session.refresh(organization)
        return organization

    async def deactivate_organization(self, organization_id: str) -> Organization:
        organization = await self.get_organization(organization_id)
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

        organization.status = OrganizationStatus.suspended
        self.session.add(organization)
        await self.session.commit()
        await self.session.refresh(organization)

        # Without this, suspending an organization had no actual effect: every
        # member's already-issued access/refresh tokens kept working until
        # they happened to expire naturally.
        await self.session_repo.revoke_all_for_organization(organization_id)
        await self.refresh_token_repo.revoke_all_for_organization(organization_id)
        return organization

    async def delete_organization(self, organization_id: str) -> Organization:
        organization = await self.get_organization(organization_id)
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

        organization.status = OrganizationStatus.deleted
        organization.deleted_at = datetime.utcnow()
        self.session.add(organization)
        await self.session.commit()
        await self.session.refresh(organization)

        await self.session_repo.revoke_all_for_organization(organization_id)
        await self.refresh_token_repo.revoke_all_for_organization(organization_id)
        return organization

    async def invite_member(self, organization_id: str, invited_by_id: str, email: str) -> OrganizationInvitation:
        organization = await self.get_organization(organization_id)
        if not organization or organization.status != OrganizationStatus.active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization is not active.")

        existing_user = await self.user_repo.get_by_email(email)
        if existing_user and existing_user.organization_id == organization_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this organization.")
        if existing_user and existing_user.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already belongs to a different organization.")

        invite_token = generate_token(64)
        invitation = OrganizationInvitation(
            organization_id=organization_id,
            invited_by_id=invited_by_id,
            email=email,
            token_hash=hash_token(invite_token),
            expires_at=datetime.utcnow() + timedelta(days=7),
            accepted=False,
            revoked=False,
        )
        invitation = await self.invitation_repo.create(invitation)

        invite_url = f"{settings.frontend_url}/accept-invite?token={invite_token}"
        await self.email_service.send_email(
            recipient=email,
            subject="You are invited to join CommerceOS",
            body=f"You have been invited to join {organization.name}. Accept your invitation by visiting {invite_url}",
        )

        return invitation

    async def accept_invitation(self, token: str, first_name: str, last_name: str, password: str) -> User:
        token_hash = hash_token(token)
        invitation = await self.invitation_repo.get_valid_by_token_hash(token_hash)
        if not invitation:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation token.")

        existing_user = await self.user_repo.get_by_email(invitation.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists.")

        user = User(
            email=invitation.email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password),
            organization_id=invitation.organization_id,
            is_active=True,
            is_verified=True,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        await self.invitation_repo.mark_accepted(invitation.id)

        rbac_service = RBACService(self.session, organization_id=invitation.organization_id)
        await rbac_service.initialize_default_roles_and_permissions()
        staff_role = await rbac_service.role_repo.get_by_name("Staff")
        if staff_role:
            await rbac_service.assign_role_to_user(user.id, staff_role.id)

        return user

    async def transfer_ownership(self, organization_id: str, current_owner_id: str, new_owner_id: str) -> None:
        rbac_service = RBACService(self.session, organization_id)
        owner_role = await rbac_service.role_repo.get_by_name("Owner")
        if not owner_role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner role not configured.")

        active_owner = await self.user_repo.get_by_id(current_owner_id)
        if not active_owner or active_owner.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user does not belong to this organization.")

        owner_membership = await rbac_service.user_role_repo.get_by_user_and_role(current_owner_id, owner_role.id)
        if not owner_membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the current owner may transfer ownership.")

        new_owner = await self.user_repo.get_by_id(new_owner_id)
        if not new_owner or new_owner.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New owner must belong to the same organization.")

        await rbac_service.assign_role_to_user(new_owner_id, owner_role.id)
        await rbac_service.remove_role_from_user(current_owner_id, owner_role.id)
