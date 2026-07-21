from datetime import datetime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_invitation import OrganizationInvitation
from app.repositories.base_repository import BaseRepository


class OrganizationInvitationRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, invitation: OrganizationInvitation) -> OrganizationInvitation:
        self._add_tenant_on_create(invitation)
        self.session.add(invitation)
        await self.session.commit()
        await self.session.refresh(invitation)
        return invitation

    async def get_valid_by_token_hash(self, token_hash: str) -> OrganizationInvitation | None:
        statement = select(OrganizationInvitation).where(
            OrganizationInvitation.token_hash == token_hash,
            OrganizationInvitation.revoked == False,
            OrganizationInvitation.accepted == False,
            OrganizationInvitation.expires_at > datetime.utcnow(),
        )
        statement = self._apply_tenant_filter(statement, OrganizationInvitation)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def count_pending(self) -> int:
        statement = select(func.count()).select_from(OrganizationInvitation).where(
            OrganizationInvitation.revoked == False,
            OrganizationInvitation.accepted == False,
            OrganizationInvitation.expires_at > datetime.utcnow(),
        )
        statement = self._apply_tenant_filter(statement, OrganizationInvitation)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def mark_accepted(self, invitation_id: str) -> None:
        statement = update(OrganizationInvitation).where(OrganizationInvitation.id == invitation_id).values(accepted=True, accepted_at=datetime.utcnow())
        await self.session.execute(statement)
        await self.session.commit()

    async def revoke(self, invitation_id: str) -> None:
        statement = update(OrganizationInvitation).where(OrganizationInvitation.id == invitation_id).values(revoked=True)
        await self.session.execute(statement)
        await self.session.commit()
