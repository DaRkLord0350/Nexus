from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete as sa_delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.models.product_channel import ProductChannel
from app.repositories.base_repository import BaseRepository


class ChannelRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, channel: Channel) -> Channel:
        self._add_tenant_on_create(channel)
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def save(self, channel: Channel) -> Channel:
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def get_by_id(self, channel_id: str) -> Channel | None:
        statement = select(Channel).where(Channel.id == channel_id)
        statement = self._apply_tenant_filter(statement, Channel)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Channel | None:
        statement = select(Channel).where(Channel.code == code)
        statement = self._apply_tenant_filter(statement, Channel)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(self, is_active: bool | None = None, limit: int = 100, offset: int = 0) -> list[Channel]:
        statement = select(Channel).order_by(Channel.name.asc()).limit(limit).offset(offset)
        if is_active is not None:
            statement = statement.where(Channel.is_active == is_active)
        statement = self._apply_tenant_filter(statement, Channel)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None) -> int:
        statement = select(func.count(Channel.id))
        if is_active is not None:
            statement = statement.where(Channel.is_active == is_active)
        statement = self._apply_tenant_filter(statement, Channel)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def unset_default(self, exclude_id: str | None = None) -> None:
        statement = update(Channel).where(Channel.is_default.is_(True)).values(is_default=False)
        if exclude_id:
            statement = statement.where(Channel.id != exclude_id)
        statement = self._apply_tenant_filter(statement, Channel)
        await self.session.execute(statement)

    async def soft_delete(self, channel_id: str) -> None:
        statement = update(Channel).where(Channel.id == channel_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Channel)
        await self.session.execute(statement)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Product <-> Channel assignment
    # ------------------------------------------------------------------
    async def set_product_channels(self, product_id: str, channel_ids: list[str]) -> None:
        await self.session.execute(sa_delete(ProductChannel).where(ProductChannel.product_id == product_id))
        for channel_id in channel_ids:
            link = ProductChannel(product_id=product_id, channel_id=channel_id, is_published=True, published_at=datetime.utcnow())
            self._add_tenant_on_create(link)
            self.session.add(link)
        await self.session.commit()

    async def get_product_channels(self, product_id: str) -> list[tuple[Channel, ProductChannel]]:
        statement = (
            select(Channel, ProductChannel)
            .join(ProductChannel, ProductChannel.channel_id == Channel.id)
            .where(ProductChannel.product_id == product_id)
            .order_by(Channel.name.asc())
        )
        result = await self.session.execute(statement)
        return result.all()
