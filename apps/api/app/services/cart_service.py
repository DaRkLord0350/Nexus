from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartStatus
from app.models.cart_item import CartItem
from app.repositories.cart_repository import CartItemRepository, CartRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.variant_repository import VariantRepository
from app.services.coupon_service import CouponService
from app.services.pricing_service import PricingService


class CartService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = CartRepository(session, organization_id, is_superuser)
        self.item_repo = CartItemRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.variant_repo = VariantRepository(session, organization_id, is_superuser)
        self.inventory_repo = InventoryRepository(session, organization_id, is_superuser)
        self.pricing_service = PricingService(session, organization_id, is_superuser)
        self.coupon_service = CouponService(session, organization_id, is_superuser)

    def assert_access(self, cart: Cart, customer_id: str | None, session_token: str | None) -> None:
        if cart.customer_id:
            if not customer_id or customer_id != cart.customer_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this cart.")
        else:
            if not session_token or session_token != cart.session_token:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this cart.")

    async def get_or_create_cart(self, customer_id: str | None, session_token: str | None, currency: str = "USD") -> Cart:
        if customer_id:
            cart = await self.repo.get_active_for_customer(customer_id)
            if cart:
                return cart
            cart = Cart(customer_id=customer_id, currency=currency, last_activity_at=datetime.utcnow())
            return await self.repo.create(cart)

        if not session_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_token is required for guest carts.")

        cart = await self.repo.get_active_for_session(session_token)
        if cart:
            return cart
        cart = Cart(session_token=session_token, currency=currency, last_activity_at=datetime.utcnow())
        return await self.repo.create(cart)

    async def _get_or_404(self, cart_id: str) -> Cart:
        cart = await self.repo.get_by_id(cart_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")
        return cart

    async def get_cart(self, cart_id: str) -> Cart:
        return await self._get_or_404(cart_id)

    async def get_cart_detail(self, cart_id: str) -> tuple[Cart, list[CartItem]]:
        cart = await self._get_or_404(cart_id)
        items = await self.item_repo.list_for_cart(cart_id)
        return cart, items

    async def _available_stock(self, product_id: str, variant_id: str | None) -> int:
        rows = await self.inventory_repo.list(product_id=product_id, limit=500)
        matching = [row for row in rows if row.variant_id == variant_id]
        return sum(row.quantity_available - row.quantity_reserved for row in matching)

    async def _recompute_totals(self, cart: Cart) -> Cart:
        items = await self.item_repo.list_for_cart(cart.id)
        active_items = [item for item in items if not item.saved_for_later]
        subtotal = sum(item.unit_price * item.quantity for item in active_items)
        cart.subtotal = round(subtotal, 2)

        if cart.coupon_code:
            result = await self.coupon_service.validate_coupon(
                code=cart.coupon_code,
                order_amount=cart.subtotal,
                product_ids=[item.product_id for item in active_items],
                customer_id=cart.customer_id,
            )
            if result["valid"]:
                cart.discount_amount = result["discount_amount"]
            else:
                cart.coupon_id = None
                cart.coupon_code = None
                cart.discount_amount = 0
        else:
            cart.discount_amount = 0

        cart.total = round(cart.subtotal - cart.discount_amount + cart.tax_amount + cart.shipping_amount, 2)
        return cart

    async def add_item(self, cart_id: str, data) -> CartItem:
        cart = await self._get_or_404(cart_id)
        if cart.status != CartStatus.active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify a cart that is not active.")

        product = await self.product_repo.get_by_id(data.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        if product.status.value != "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This product is not available for purchase.")

        if data.variant_id:
            variant = await self.variant_repo.get_by_id(data.variant_id)
            if not variant or variant.product_id != product.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found for this product.")

        price = await self.pricing_service.resolve_price(product.id, cart.currency, data.variant_id)
        if not price:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No price is configured for this product.")

        existing = await self.item_repo.get_by_product(cart_id, data.product_id, data.variant_id)
        requested_quantity = (existing.quantity if existing else 0) + data.quantity

        if product.track_inventory and not product.allow_backorders:
            available = await self._available_stock(product.id, data.variant_id)
            if requested_quantity > available:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {available} unit(s) available for this product.")

        if existing:
            existing.quantity = requested_quantity
            existing.unit_price = price.selling_price
            if data.gift_note is not None:
                existing.gift_note = data.gift_note
            item = await self.item_repo.save(existing)
        else:
            item = await self.item_repo.create(CartItem(
                cart_id=cart_id,
                product_id=data.product_id,
                variant_id=data.variant_id,
                quantity=data.quantity,
                unit_price=price.selling_price,
                gift_note=data.gift_note,
            ))

        cart = await self._recompute_totals(cart)
        await self.repo.save(cart)
        return item

    async def _get_item_or_404(self, cart_id: str, item_id: str) -> CartItem:
        item = await self.item_repo.get_by_id(item_id)
        if not item or item.cart_id != cart_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
        return item

    async def update_item(self, cart_id: str, item_id: str, data) -> CartItem:
        cart = await self._get_or_404(cart_id)
        item = await self._get_item_or_404(cart_id, item_id)

        changes = data.model_dump(exclude_unset=True)
        if "quantity" in changes and not changes.get("saved_for_later", item.saved_for_later):
            product = await self.product_repo.get_by_id(item.product_id)
            if product and product.track_inventory and not product.allow_backorders:
                available = await self._available_stock(item.product_id, item.variant_id)
                if changes["quantity"] > available:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {available} unit(s) available for this product.")

        for field, value in changes.items():
            setattr(item, field, value)
        item = await self.item_repo.save(item)

        cart = await self._recompute_totals(cart)
        await self.repo.save(cart)
        return item

    async def remove_item(self, cart_id: str, item_id: str) -> None:
        await self._get_or_404(cart_id)
        await self._get_item_or_404(cart_id, item_id)
        await self.item_repo.delete(item_id)

        cart = await self._get_or_404(cart_id)
        cart = await self._recompute_totals(cart)
        await self.repo.save(cart)

    async def apply_coupon(self, cart_id: str, code: str) -> Cart:
        cart = await self._get_or_404(cart_id)
        items = await self.item_repo.list_for_cart(cart_id)
        active_items = [item for item in items if not item.saved_for_later]
        subtotal = sum(item.unit_price * item.quantity for item in active_items)

        result = await self.coupon_service.validate_coupon(
            code=code, order_amount=subtotal, product_ids=[item.product_id for item in active_items], customer_id=cart.customer_id,
        )
        if not result["valid"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["reason"] or "Coupon is not valid.")

        cart.coupon_id = result["coupon_id"]
        cart.coupon_code = code.strip().upper()
        cart = await self._recompute_totals(cart)
        return await self.repo.save(cart)

    async def remove_coupon(self, cart_id: str) -> Cart:
        cart = await self._get_or_404(cart_id)
        cart.coupon_id = None
        cart.coupon_code = None
        cart = await self._recompute_totals(cart)
        return await self.repo.save(cart)

    async def merge_guest_cart(self, customer_id: str, session_token: str) -> Cart:
        guest_cart = await self.repo.get_active_for_session(session_token)
        target_cart = await self.get_or_create_cart(customer_id, None)

        if not guest_cart or guest_cart.id == target_cart.id:
            return target_cart

        guest_items = await self.item_repo.list_for_cart(guest_cart.id)
        for guest_item in guest_items:
            existing = await self.item_repo.get_by_product(target_cart.id, guest_item.product_id, guest_item.variant_id)
            if existing and not guest_item.saved_for_later:
                existing.quantity += guest_item.quantity
                await self.item_repo.save(existing)
            else:
                await self.item_repo.create(CartItem(
                    cart_id=target_cart.id,
                    product_id=guest_item.product_id,
                    variant_id=guest_item.variant_id,
                    quantity=guest_item.quantity,
                    unit_price=guest_item.unit_price,
                    saved_for_later=guest_item.saved_for_later,
                    gift_note=guest_item.gift_note,
                ))

        guest_cart.status = CartStatus.merged
        await self.repo.save(guest_cart)

        target_cart = await self._recompute_totals(target_cart)
        return await self.repo.save(target_cart)
