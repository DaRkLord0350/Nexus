from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_customer, get_current_customer_optional, get_db
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.schemas.cart import (
    CartCouponRequest,
    CartDetail,
    CartGetOrCreateRequest,
    CartItemAddRequest,
    CartItemRead,
    CartItemUpdateRequest,
    CartMergeRequest,
    CartRead,
)
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


def _build_detail(cart: Cart, items: list[CartItem]) -> CartDetail:
    detail = CartDetail.model_validate(cart)
    detail.items = []
    for item in items:
        item_read = CartItemRead.model_validate(item)
        item_read.line_total = round(item.unit_price * item.quantity, 2)
        detail.items.append(item_read)
    return detail


@router.post("/", response_model=CartDetail, status_code=status.HTTP_201_CREATED)
async def get_or_create_cart(
    data: CartGetOrCreateRequest,
    organization_id: str = Query(..., description="Storefront organization id."),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db, organization_id=organization_id)
    cart = await service.get_or_create_cart(
        customer_id=current_customer.id if current_customer else None,
        session_token=data.session_token,
        currency=data.currency,
    )
    items = await service.item_repo.list_for_cart(cart.id)
    return _build_detail(cart, items)


@router.get("/{cart_id}", response_model=CartDetail)
async def get_cart(
    cart_id: str,
    organization_id: str = Query(...),
    session_token: str | None = Query(None),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db, organization_id=organization_id)
    cart, items = await service.get_cart_detail(cart_id)
    service.assert_access(cart, current_customer.id if current_customer else None, session_token)
    return _build_detail(cart, items)


@router.post("/{cart_id}/items", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    cart_id: str,
    data: CartItemAddRequest,
    organization_id: str = Query(...),
    session_token: str | None = Query(None),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db, organization_id=organization_id)
    cart = await service.get_cart(cart_id)
    service.assert_access(cart, current_customer.id if current_customer else None, session_token)
    item = await service.add_item(cart_id, data)
    item_read = CartItemRead.model_validate(item)
    item_read.line_total = round(item.unit_price * item.quantity, 2)
    return item_read


@router.patch("/{cart_id}/items/{item_id}", response_model=CartItemRead)
async def update_cart_item(
    cart_id: str,
    item_id: str,
    data: CartItemUpdateRequest,
    organization_id: str = Query(...),
    session_token: str | None = Query(None),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db, organization_id=organization_id)
    cart = await service.get_cart(cart_id)
    service.assert_access(cart, current_customer.id if current_customer else None, session_token)
    item = await service.update_item(cart_id, item_id, data)
    item_read = CartItemRead.model_validate(item)
    item_read.line_total = round(item.unit_price * item.quantity, 2)
    return item_read


@router.delete("/{cart_id}/items/{item_id}")
async def remove_cart_item(
    cart_id: str,
    item_id: str,
    organization_id: str = Query(...),
    session_token: str | None = Query(None),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db, organization_id=organization_id)
    cart = await service.get_cart(cart_id)
    service.assert_access(cart, current_customer.id if current_customer else None, session_token)
    await service.remove_item(cart_id, item_id)
    return {"detail": "Item removed from cart."}


@router.post("/{cart_id}/coupon", response_model=CartRead)
async def apply_cart_coupon(
    cart_id: str,
    data: CartCouponRequest,
    organization_id: str = Query(...),
    session_token: str | None = Query(None),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db, organization_id=organization_id)
    cart = await service.get_cart(cart_id)
    service.assert_access(cart, current_customer.id if current_customer else None, session_token)
    return await service.apply_coupon(cart_id, data.code)


@router.delete("/{cart_id}/coupon", response_model=CartRead)
async def remove_cart_coupon(
    cart_id: str,
    organization_id: str = Query(...),
    session_token: str | None = Query(None),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db, organization_id=organization_id)
    cart = await service.get_cart(cart_id)
    service.assert_access(cart, current_customer.id if current_customer else None, session_token)
    return await service.remove_coupon(cart_id)


@router.post("/merge", response_model=CartDetail)
async def merge_guest_cart(
    data: CartMergeRequest,
    organization_id: str = Query(...),
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db, organization_id=organization_id)
    cart = await service.merge_guest_cart(current_customer.id, data.session_token)
    items = await service.item_repo.list_for_cart(cart.id)
    return _build_detail(cart, items)
