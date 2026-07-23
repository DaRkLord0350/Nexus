from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wishlist import Wishlist
from app.repositories.product_repository import ProductRepository
from app.repositories.wishlist_repository import WishlistRepository
from app.schemas.cart import CartItemAddRequest
from app.services.cart_service import CartService


class WishlistService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = WishlistRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.cart_service = CartService(session, organization_id, is_superuser)

    async def add_item(self, customer_id: str, data) -> Wishlist:
        product = await self.product_repo.get_by_id(data.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        existing = await self.repo.get_existing(customer_id, data.product_id, data.variant_id)
        if existing:
            return existing

        item = Wishlist(customer_id=customer_id, product_id=data.product_id, variant_id=data.variant_id, notes=data.notes)
        return await self.repo.create(item)

    async def list_items(self, customer_id: str, limit: int = 50, offset: int = 0) -> tuple[list[Wishlist], int]:
        items = await self.repo.list_for_customer(customer_id, limit, offset)
        total = await self.repo.count_for_customer(customer_id)
        return items, total

    async def _get_owned_or_404(self, customer_id: str, item_id: str) -> Wishlist:
        item = await self.repo.get_by_id(item_id)
        if not item or item.customer_id != customer_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found.")
        return item

    async def remove_item(self, customer_id: str, item_id: str) -> None:
        await self._get_owned_or_404(customer_id, item_id)
        await self.repo.delete(item_id)

    async def move_to_cart(self, customer_id: str, item_id: str, session_token: str | None = None, quantity: int = 1):
        item = await self._get_owned_or_404(customer_id, item_id)
        cart = await self.cart_service.get_or_create_cart(customer_id=customer_id, session_token=session_token)
        cart_item = await self.cart_service.add_item(cart.id, CartItemAddRequest(product_id=item.product_id, variant_id=item.variant_id, quantity=quantity))
        await self.repo.delete(item_id)
        return cart_item
