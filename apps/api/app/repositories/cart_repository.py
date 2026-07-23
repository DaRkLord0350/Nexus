from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartStatus
from app.models.cart_item import CartItem
from app.repositories.base_repository import BaseRepository


class CartRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, cart: Cart) -> Cart:
        self._add_tenant_on_create(cart)
        self.session.add(cart)
        await self.session.commit()
        await self.session.refresh(cart)
        return cart

    async def save(self, cart: Cart) -> Cart:
        self.session.add(cart)
        await self.session.commit()
        await self.session.refresh(cart)
        return cart

    async def save_no_commit(self, cart: Cart) -> Cart:
        self.session.add(cart)
        await self.session.flush()
        return cart

    async def get_by_id(self, cart_id: str) -> Cart | None:
        statement = select(Cart).where(Cart.id == cart_id)
        statement = self._apply_tenant_filter(statement, Cart)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_for_customer(self, customer_id: str) -> Cart | None:
        statement = select(Cart).where(Cart.customer_id == customer_id, Cart.status == CartStatus.active).order_by(Cart.created_at.desc())
        statement = self._apply_tenant_filter(statement, Cart)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_active_for_session(self, session_token: str) -> Cart | None:
        statement = select(Cart).where(
            Cart.session_token == session_token, Cart.customer_id.is_(None), Cart.status == CartStatus.active
        ).order_by(Cart.created_at.desc())
        statement = self._apply_tenant_filter(statement, Cart)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def touch(self, cart_id: str) -> None:
        statement = update(Cart).where(Cart.id == cart_id).values(last_activity_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Cart)
        await self.session.execute(statement)
        await self.session.commit()


class CartItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, item: CartItem) -> CartItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def save(self, item: CartItem) -> CartItem:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: str) -> CartItem | None:
        statement = select(CartItem).where(CartItem.id == item_id)
        statement = self._apply_tenant_filter(statement, CartItem)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_product(self, cart_id: str, product_id: str, variant_id: str | None) -> CartItem | None:
        statement = select(CartItem).where(
            CartItem.cart_id == cart_id, CartItem.product_id == product_id, CartItem.variant_id == variant_id, CartItem.saved_for_later.is_(False)
        )
        statement = self._apply_tenant_filter(statement, CartItem)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_cart(self, cart_id: str) -> list[CartItem]:
        statement = select(CartItem).where(CartItem.cart_id == cart_id).order_by(CartItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, CartItem)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def delete(self, item_id: str) -> None:
        statement = select(CartItem).where(CartItem.id == item_id)
        statement = self._apply_tenant_filter(statement, CartItem)
        result = await self.session.execute(statement)
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)
            await self.session.commit()

    async def delete_all_for_cart(self, cart_id: str) -> None:
        items = await self.list_for_cart(cart_id)
        for item in items:
            await self.session.delete(item)
        await self.session.commit()
