from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, refresh_token: RefreshToken) -> RefreshToken:
        self._add_tenant_on_create(refresh_token)
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_valid_by_hash(self, token_hash: str) -> RefreshToken | None:
        statement = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
        statement = self._apply_tenant_filter(statement, RefreshToken)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def revoke(self, token_id: str) -> None:
        statement = update(RefreshToken).where(RefreshToken.id == token_id)
        if self.organization_id:
            statement = statement.where(RefreshToken.organization_id == self.organization_id)
        statement = statement.values(revoked=True)
        await self.session.execute(statement)
        await self.session.commit()

    async def revoke_all_for_session(self, session_id: str) -> None:
        statement = update(RefreshToken).where(RefreshToken.session_id == session_id)
        if self.organization_id:
            statement = statement.where(RefreshToken.organization_id == self.organization_id)
        statement = statement.values(revoked=True)
        await self.session.execute(statement)
        await self.session.commit()

    async def revoke_all_for_user(self, user_id: str) -> None:
        statement = update(RefreshToken).where(RefreshToken.user_id == user_id)
        if self.organization_id:
            statement = statement.where(RefreshToken.organization_id == self.organization_id)
        statement = statement.values(revoked=True)
        await self.session.execute(statement)
        await self.session.commit()

    async def revoke_all_for_organization(self, organization_id: str) -> None:
        statement = (
            update(RefreshToken)
            .where(RefreshToken.organization_id == organization_id)
            .values(revoked=True)
        )
        await self.session.execute(statement)
        await self.session.commit()
