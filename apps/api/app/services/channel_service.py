from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel, ChannelType
from app.repositories.channel_repository import ChannelRepository
from app.repositories.product_repository import ProductRepository
from app.utils.text import slugify


class ChannelService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ChannelRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)

    async def _ensure_unique_code(self, code: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A channel with that code already exists.")

    async def create_channel(self, data, created_by: str | None = None) -> Channel:
        code = slugify(data.code or data.name, fallback="channel")
        await self._ensure_unique_code(code)

        channel = Channel(
            name=data.name, code=code, channel_type=ChannelType(data.channel_type.value),
            is_active=data.is_active, is_default=data.is_default, created_by=created_by,
        )
        created = await self.repo.create(channel)

        if created.is_default:
            await self.repo.unset_default(exclude_id=created.id)
            await self.session.commit()

        return created

    async def update_channel(self, channel_id: str, data) -> Channel:
        channel = await self.repo.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

        if data.code is not None:
            new_code = slugify(data.code, fallback="channel")
            await self._ensure_unique_code(new_code, exclude_id=channel.id)
            channel.code = new_code

        changes = data.model_dump(exclude_unset=True, exclude={"code", "channel_type"})
        for field, value in changes.items():
            setattr(channel, field, value)
        if data.channel_type is not None:
            channel.channel_type = ChannelType(data.channel_type.value)

        saved = await self.repo.save(channel)
        if saved.is_default:
            await self.repo.unset_default(exclude_id=saved.id)
            await self.session.commit()
        return saved

    async def delete_channel(self, channel_id: str) -> None:
        channel = await self.repo.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")
        await self.repo.soft_delete(channel_id)

    async def get_channel(self, channel_id: str) -> Channel | None:
        return await self.repo.get_by_id(channel_id)

    async def list_channels(self, is_active: bool | None = None, limit: int = 100, offset: int = 0) -> tuple[list[Channel], int]:
        items = await self.repo.list(is_active, limit, offset)
        total = await self.repo.count(is_active)
        return items, total

    # ------------------------------------------------------------------
    # Product assignment
    # ------------------------------------------------------------------
    async def set_product_channels(self, product_id: str, channel_ids: list[str]) -> None:
        if not await self.product_repo.get_by_id(product_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        for channel_id in channel_ids:
            if not await self.repo.get_by_id(channel_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Channel {channel_id} not found.")
        await self.repo.set_product_channels(product_id, channel_ids)

    async def get_product_channels(self, product_id: str) -> list[dict]:
        if not await self.product_repo.get_by_id(product_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        rows = await self.repo.get_product_channels(product_id)
        return [
            {
                "channel_id": channel.id,
                "name": channel.name,
                "code": channel.code,
                "channel_type": channel.channel_type,
                "is_published": link.is_published,
                "published_at": link.published_at,
            }
            for channel, link in rows
        ]
