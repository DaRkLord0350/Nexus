from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import CartStatus
from app.models.order import Order
from app.repositories.address_repository import AddressRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput
from app.services.cart_service import CartService
from app.services.customer_auth_service import CustomerAuthService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.tax_service import TaxService

# Flat-rate placeholder until Phase 5 wires up real carrier rate-shopping
# (ShippingProvider / ShippingRate comparison across couriers).
FREE_SHIPPING_THRESHOLD = 100.0
STANDARD_SHIPPING_RATE = 10.0
EXPRESS_SHIPPING_RATE = 25.0


class CheckoutService:
    def __init__(self, session: AsyncSession, organization_id: str, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.cart_service = CartService(session, organization_id, is_superuser)
        self.order_service = OrderService(session, organization_id, is_superuser)
        self.customer_service = CustomerService(session, organization_id, is_superuser)
        self.customer_auth_service = CustomerAuthService(session, organization_id)
        self.address_repo = AddressRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.warehouse_repo = WarehouseRepository(session, organization_id, is_superuser)
        self.tax_service = TaxService(session, organization_id, is_superuser)

    def _estimate_shipping(self, subtotal: float, shipping_method: str) -> float:
        if shipping_method == "express":
            return EXPRESS_SHIPPING_RATE
        if subtotal >= FREE_SHIPPING_THRESHOLD:
            return 0.0
        return STANDARD_SHIPPING_RATE

    async def _line_tax(self, product, line_subtotal: float, country: str, state: str | None) -> float:
        if not product or not product.tax_class_id or line_subtotal <= 0:
            return 0.0
        try:
            result = await self.tax_service.calculate_tax(product.tax_class_id, line_subtotal, country, state)
            return result["tax_amount"]
        except HTTPException:
            return 0.0

    async def _resolve_address(self, address_id: str | None, inline: OrderAddressInput | None, customer_id: str) -> OrderAddressInput:
        if address_id:
            address = await self.address_repo.get_by_id(address_id)
            if not address or address.customer_id != customer_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
            return OrderAddressInput(
                first_name=address.first_name, last_name=address.last_name, company=address.company,
                phone=address.phone, line1=address.line1, line2=address.line2, city=address.city,
                state=address.state, postal_code=address.postal_code, country=address.country,
            )
        if not inline:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An address is required.")
        return inline

    async def _resolve_warehouse_id(self) -> str | None:
        warehouse = await self.warehouse_repo.get_default()
        if warehouse:
            return warehouse.id
        candidates = await self.warehouse_repo.list(is_active=True, limit=1)
        return candidates[0].id if candidates else None

    async def _active_cart_items(self, cart_id: str):
        items = await self.cart_service.item_repo.list_for_cart(cart_id)
        active = [item for item in items if not item.saved_for_later]
        if not active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty.")
        return active

    async def get_quote(self, data, current_customer_id: str | None):
        cart = await self.cart_service.get_cart(data.cart_id)
        self.cart_service.assert_access(cart, current_customer_id, data.session_token)
        active_items = await self._active_cart_items(cart.id)

        subtotal = sum(item.unit_price * item.quantity for item in active_items)
        tax_total = 0.0
        for item in active_items:
            product = await self.product_repo.get_by_id(item.product_id)
            tax_total += await self._line_tax(product, item.unit_price * item.quantity, data.country, data.state)

        shipping_amount = self._estimate_shipping(subtotal, data.shipping_method)
        total = round(subtotal - cart.discount_amount + tax_total + shipping_amount, 2)
        return {
            "currency": cart.currency,
            "subtotal": round(subtotal, 2),
            "discount_amount": cart.discount_amount,
            "tax_amount": round(tax_total, 2),
            "shipping_amount": shipping_amount,
            "total": total,
        }

    async def checkout(self, data, current_customer_id: str | None) -> Order:
        cart = await self.cart_service.get_cart(data.cart_id)
        self.cart_service.assert_access(cart, current_customer_id, data.session_token)
        active_items = await self._active_cart_items(cart.id)

        customer_id = current_customer_id or cart.customer_id
        if not customer_id:
            if not data.guest_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="guest_email is required for guest checkout.")
            first_name = data.guest_first_name or (data.billing_address.first_name if data.billing_address else None)
            last_name = data.guest_last_name or (data.billing_address.last_name if data.billing_address else None)
            if not first_name or not last_name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="guest_first_name and guest_last_name are required.")
            guest = await self.customer_auth_service.get_or_create_guest(data.guest_email, first_name, last_name)
            customer_id = guest.id

        billing_address = await self._resolve_address(data.billing_address_id, data.billing_address, customer_id)
        shipping_address = await self._resolve_address(data.shipping_address_id, data.shipping_address, customer_id)

        if data.save_addresses:
            from app.schemas.address import AddressCreateRequest, AddressType

            if not data.billing_address_id:
                await self.customer_service.add_address(customer_id, AddressCreateRequest(**billing_address.model_dump(), address_type=AddressType.billing))
            if not data.shipping_address_id:
                await self.customer_service.add_address(customer_id, AddressCreateRequest(**shipping_address.model_dump(), address_type=AddressType.shipping))

        warehouse_id = await self._resolve_warehouse_id()

        order_items: list[OrderLineItemInput] = []
        for cart_item in active_items:
            product = await self.product_repo.get_by_id(cart_item.product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="A product in your cart is no longer available.")
            line_subtotal = cart_item.unit_price * cart_item.quantity
            tax_amount = await self._line_tax(product, line_subtotal, shipping_address.country, shipping_address.state)
            order_items.append(OrderLineItemInput(
                product_id=cart_item.product_id,
                variant_id=cart_item.variant_id,
                warehouse_id=warehouse_id,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                tax_amount=round(tax_amount, 2),
                gift_note=cart_item.gift_note,
            ))

        subtotal = sum(item.unit_price * item.quantity for item in order_items)
        shipping_amount = self._estimate_shipping(subtotal, data.shipping_method)

        order_data = OrderCreateRequest(
            customer_id=customer_id,
            cart_id=cart.id,
            currency=cart.currency,
            billing_address=billing_address,
            shipping_address=shipping_address,
            payment_method=data.payment_method,
            shipping_method=data.shipping_method,
            shipping_amount=shipping_amount,
            customer_note=data.customer_note,
            gift_note=data.gift_note,
            coupon_code=cart.coupon_code,
            items=order_items,
        )
        order = await self.order_service.create_order(order_data, created_by=None)

        cart.status = CartStatus.converted
        cart.order_id = order.id
        await self.cart_service.repo.save(cart)

        return order
