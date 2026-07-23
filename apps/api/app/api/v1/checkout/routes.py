from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_customer_optional, get_db
from app.schemas.checkout import CheckoutQuoteRequest, CheckoutQuoteResponse, CheckoutRequest
from app.schemas.order import OrderRead
from app.services.checkout_service import CheckoutService

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/quote", response_model=CheckoutQuoteResponse)
async def get_checkout_quote(
    data: CheckoutQuoteRequest,
    organization_id: str = Query(...),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CheckoutService(db, organization_id)
    return await service.get_quote(data, current_customer.id if current_customer else None)


@router.post("/", response_model=OrderRead)
async def checkout(
    data: CheckoutRequest,
    organization_id: str = Query(...),
    current_customer=Depends(get_current_customer_optional),
    db: AsyncSession = Depends(get_db),
):
    service = CheckoutService(db, organization_id)
    return await service.checkout(data, current_customer.id if current_customer else None)
