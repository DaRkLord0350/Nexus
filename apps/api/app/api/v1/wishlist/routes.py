from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_customer, get_db
from app.schemas.cart import CartItemRead
from app.schemas.wishlist import WishlistItemCreateRequest, WishlistItemRead, WishlistListResponse
from app.services.wishlist_service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("/", response_model=WishlistListResponse)
async def list_wishlist(
    organization_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    service = WishlistService(db, organization_id=organization_id)
    items, total = await service.list_items(current_customer.id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=WishlistItemRead, status_code=status.HTTP_201_CREATED)
async def add_wishlist_item(
    data: WishlistItemCreateRequest,
    organization_id: str = Query(...),
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    service = WishlistService(db, organization_id=organization_id)
    return await service.add_item(current_customer.id, data)


@router.delete("/{item_id}")
async def remove_wishlist_item(
    item_id: str,
    organization_id: str = Query(...),
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    service = WishlistService(db, organization_id=organization_id)
    await service.remove_item(current_customer.id, item_id)
    return {"detail": "Removed from wishlist."}


@router.post("/{item_id}/move-to-cart", response_model=CartItemRead)
async def move_wishlist_item_to_cart(
    item_id: str,
    organization_id: str = Query(...),
    session_token: str | None = Query(None),
    quantity: int = Query(1, gt=0),
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    service = WishlistService(db, organization_id=organization_id)
    cart_item = await service.move_to_cart(current_customer.id, item_id, session_token=session_token, quantity=quantity)
    item_read = CartItemRead.model_validate(cart_item)
    item_read.line_total = round(cart_item.unit_price * cart_item.quantity, 2)
    return item_read
