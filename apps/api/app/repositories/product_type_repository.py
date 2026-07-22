from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete as sa_delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute import Attribute
from app.models.product_type import ProductType
from app.models.product_type_attribute import ProductTypeAttribute
from app.repositories.base_repository import BaseRepository


class ProductTypeRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, product_type: ProductType) -> ProductType:
        self._add_tenant_on_create(product_type)
        self.session.add(product_type)
        await self.session.commit()
        await self.session.refresh(product_type)
        return product_type

    async def save(self, product_type: ProductType) -> ProductType:
        self.session.add(product_type)
        await self.session.commit()
        await self.session.refresh(product_type)
        return product_type

    async def get_by_id(self, product_type_id: str) -> ProductType | None:
        statement = select(ProductType).where(ProductType.id == product_type_id)
        statement = self._apply_tenant_filter(statement, ProductType)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> ProductType | None:
        statement = select(ProductType).where(ProductType.slug == slug)
        statement = self._apply_tenant_filter(statement, ProductType)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(self, is_active: bool | None = None, q: str | None = None, limit: int = 100, offset: int = 0) -> list[ProductType]:
        statement = select(ProductType).order_by(ProductType.name.asc()).limit(limit).offset(offset)
        if is_active is not None:
            statement = statement.where(ProductType.is_active == is_active)
        if q:
            statement = statement.where(ProductType.name.ilike(f"%{q}%"))
        statement = self._apply_tenant_filter(statement, ProductType)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None, q: str | None = None) -> int:
        statement = select(func.count(ProductType.id))
        if is_active is not None:
            statement = statement.where(ProductType.is_active == is_active)
        if q:
            statement = statement.where(ProductType.name.ilike(f"%{q}%"))
        statement = self._apply_tenant_filter(statement, ProductType)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, product_type_id: str) -> None:
        statement = update(ProductType).where(ProductType.id == product_type_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, ProductType)
        await self.session.execute(statement)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Attribute assignments
    # ------------------------------------------------------------------
    async def set_attributes(self, product_type_id: str, configs: list[dict]) -> None:
        await self.session.execute(sa_delete(ProductTypeAttribute).where(ProductTypeAttribute.product_type_id == product_type_id))
        for config in configs:
            link = ProductTypeAttribute(
                product_type_id=product_type_id,
                attribute_id=config["attribute_id"],
                is_required=config.get("is_required", False),
                sort_order=config.get("sort_order", 0),
            )
            self._add_tenant_on_create(link)
            self.session.add(link)
        await self.session.commit()

    async def get_attributes(self, product_type_id: str) -> list[tuple[Attribute, ProductTypeAttribute]]:
        statement = (
            select(Attribute, ProductTypeAttribute)
            .join(ProductTypeAttribute, ProductTypeAttribute.attribute_id == Attribute.id)
            .where(ProductTypeAttribute.product_type_id == product_type_id)
            .order_by(ProductTypeAttribute.sort_order.asc())
        )
        result = await self.session.execute(statement)
        return result.all()
