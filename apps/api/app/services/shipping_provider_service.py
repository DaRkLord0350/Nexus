import json

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_provider import ShippingProvider
from app.repositories.shipping_provider_repository import ShippingProviderRepository


class ShippingProviderService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ShippingProviderRepository(session, organization_id, is_superuser)

    async def _ensure_unique_code(self, code: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A shipping provider with that code already exists.")

    async def create_provider(self, data, created_by: str | None = None) -> ShippingProvider:
        await self._ensure_unique_code(data.code)

        provider = ShippingProvider(
            name=data.name,
            code=data.code,
            provider_type=data.provider_type,
            is_active=data.is_active,
            is_default=data.is_default,
            priority=data.priority,
            credentials=json.dumps(data.credentials) if data.credentials else None,
            webhook_secret=data.webhook_secret,
            supports_cod=data.supports_cod,
            supports_insurance=data.supports_insurance,
            supports_reverse_pickup=data.supports_reverse_pickup,
            supports_international=data.supports_international,
            base_rate=data.base_rate,
            base_transit_days=data.base_transit_days,
            created_by=created_by,
        )
        provider = await self.repo.create(provider)

        if provider.is_default:
            await self.repo.unset_default(exclude_id=provider.id)

        return provider

    async def _get_or_404(self, provider_id: str) -> ShippingProvider:
        provider = await self.repo.get_by_id(provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping provider not found.")
        return provider

    async def get_provider(self, provider_id: str) -> ShippingProvider | None:
        return await self.repo.get_by_id(provider_id)

    async def get_default_provider(self) -> ShippingProvider | None:
        return await self.repo.get_default()

    async def update_provider(self, provider_id: str, data) -> ShippingProvider:
        provider = await self._get_or_404(provider_id)
        changes = data.model_dump(exclude_unset=True)

        if "credentials" in changes:
            changes["credentials"] = json.dumps(changes["credentials"]) if changes["credentials"] else None

        for field, value in changes.items():
            setattr(provider, field, value)

        provider = await self.repo.save(provider)
        if provider.is_default:
            await self.repo.unset_default(exclude_id=provider.id)

        return provider

    async def delete_provider(self, provider_id: str) -> None:
        await self._get_or_404(provider_id)
        await self.repo.soft_delete(provider_id)

    async def list_providers(
        self,
        is_active: bool | None = None,
        provider_type: str | None = None,
        sort_by: str = "priority",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ShippingProvider], int]:
        items = await self.repo.list(is_active, provider_type, sort_by, sort_order, limit, offset)
        total = await self.repo.count(is_active, provider_type)
        return items, total
