from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        statement = self._apply_tenant_filter(statement, User)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        statement = select(User).where(User.id == user_id)
        statement = self._apply_tenant_filter(statement, User)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def count(self) -> int:
        statement = select(func.count()).select_from(User)
        statement = self._apply_tenant_filter(statement, User)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def count_verified(self) -> int:
        statement = select(func.count()).select_from(User).where(User.is_verified == True)
        statement = self._apply_tenant_filter(statement, User)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_for_organization(self, limit: int = 200, offset: int = 0) -> list[User]:
        statement = select(User).order_by(User.created_at.asc()).limit(limit).offset(offset)
        statement = self._apply_tenant_filter(statement, User)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(self, user: User) -> User:
        self._add_tenant_on_create(user)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
