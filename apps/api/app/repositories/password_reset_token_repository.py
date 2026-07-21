from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken
from app.repositories.base_repository import BaseRepository


class PasswordResetTokenRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, token_record: PasswordResetToken) -> PasswordResetToken:
        self._add_tenant_on_create(token_record)
        self.session.add(token_record)
        await self.session.commit()
        await self.session.refresh(token_record)
        return token_record

    async def get_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.revoked == False,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
        statement = self._apply_tenant_filter(statement, PasswordResetToken)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def revoke(self, token_id: str) -> None:
        statement = update(PasswordResetToken).where(PasswordResetToken.id == token_id)
        if self.organization_id:
            statement = statement.where(PasswordResetToken.organization_id == self.organization_id)
        statement = statement.values(revoked=True)
        await self.session.execute(statement)
        await self.session.commit()
