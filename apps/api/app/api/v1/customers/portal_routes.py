from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_customer, get_db
from app.models.order import OrderStatus as ModelOrderStatus
from app.models.return_request import ReturnStatus as ModelReturnStatus
from app.schemas.address import AddressCreateRequest, AddressItem, AddressListResponse
from app.schemas.customer import CustomerItem, CustomerSelfUpdateRequest
from app.schemas.invoice import InvoiceRead
from app.schemas.order import OrderDetail, OrderLineItem, OrderListResponse, OrderNoteRead, OrderRead, OrderStatusHistoryRead
from app.schemas.return_request import (
    ReturnItemRead,
    ReturnRequestCreateRequest,
    ReturnRequestDetail,
    ReturnRequestListResponse,
)
from app.schemas.shipment import CustomerShipmentTrackingRead, ShipmentItemRead
from app.schemas.shipment_tracking import ShipmentTrackingEventRead
from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService
from app.services.order_service import OrderService
from app.services.return_service import ReturnService
from app.services.shipment_service import ShipmentService
from app.services.shipment_tracking_service import ShipmentTrackingService

router = APIRouter(prefix="/customers/me", tags=["customer-portal"])


def _services(db: AsyncSession, organization_id: str):
    return (
        CustomerService(db, organization_id),
        OrderService(db, organization_id),
        ReturnService(db, organization_id),
        InvoiceService(db, organization_id),
    )


@router.get("/", response_model=CustomerItem)
async def get_my_profile(current_customer=Depends(get_current_customer)):
    return current_customer


@router.patch("/", response_model=CustomerItem)
async def update_my_profile(
    data: CustomerSelfUpdateRequest,
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    customer_service, *_ = _services(db, current_customer.organization_id)
    return await customer_service.update_customer(current_customer.id, data)


@router.get("/addresses", response_model=AddressListResponse)
async def list_my_addresses(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    customer_service, *_ = _services(db, current_customer.organization_id)
    items, total = await customer_service.list_addresses(current_customer.id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/addresses", response_model=AddressItem, status_code=status.HTTP_201_CREATED)
async def add_my_address(
    data: AddressCreateRequest,
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    customer_service, *_ = _services(db, current_customer.organization_id)
    return await customer_service.add_address(current_customer.id, data)


@router.delete("/addresses/{address_id}")
async def delete_my_address(
    address_id: str,
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    customer_service, *_ = _services(db, current_customer.organization_id)
    await customer_service.delete_address(current_customer.id, address_id)
    return {"detail": "Address deleted."}


@router.get("/orders", response_model=OrderListResponse)
async def list_my_orders(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    _, order_service, *_rest = _services(db, current_customer.organization_id)
    model_status = ModelOrderStatus(status_filter) if status_filter else None
    items, total = await order_service.list_orders(customer_id=current_customer.id, status_filter=model_status, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def _get_own_order_or_404(order_service: OrderService, order_id: str, customer_id: str):
    order = await order_service.get_order(order_id)
    if not order or order.customer_id != customer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return order


@router.get("/orders/{order_id}", response_model=OrderDetail)
async def get_my_order(order_id: str, current_customer=Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    _, order_service, *_rest = _services(db, current_customer.organization_id)
    order = await _get_own_order_or_404(order_service, order_id, current_customer.id)

    items = await order_service.get_items(order_id)
    history = await order_service.get_status_history(order_id)
    notes = [n for n in await order_service.get_notes(order_id) if n.is_customer_visible]

    detail = OrderDetail.model_validate(order)
    detail.items = [OrderLineItem.model_validate(i) for i in items]
    detail.status_history = [OrderStatusHistoryRead.model_validate(h) for h in history]
    detail.notes = [OrderNoteRead.model_validate(n) for n in notes]
    return detail


@router.get("/orders/{order_id}/tracking", response_model=list[CustomerShipmentTrackingRead])
async def get_my_order_tracking(order_id: str, current_customer=Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    _, order_service, *_rest = _services(db, current_customer.organization_id)
    await _get_own_order_or_404(order_service, order_id, current_customer.id)

    shipment_service = ShipmentService(db, current_customer.organization_id)
    tracking_service = ShipmentTrackingService(db, current_customer.organization_id)

    shipments, _total = await shipment_service.list_shipments(order_id=order_id, limit=200)
    results = []
    for shipment in shipments:
        items = await shipment_service.get_items(shipment.id)
        events = await tracking_service.get_timeline(shipment.id)
        detail = CustomerShipmentTrackingRead.model_validate(shipment)
        detail.items = [ShipmentItemRead.model_validate(i) for i in items]
        detail.tracking_events = [ShipmentTrackingEventRead.model_validate(e) for e in events]
        results.append(detail)
    return results


@router.get("/orders/{order_id}/invoice", response_model=InvoiceRead)
async def get_my_order_invoice(order_id: str, current_customer=Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    _, order_service, _return_service, invoice_service = _services(db, current_customer.organization_id)
    await _get_own_order_or_404(order_service, order_id, current_customer.id)

    invoice = await invoice_service.get_invoice_for_order(order_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No invoice has been generated for this order.")
    return invoice


@router.get("/orders/{order_id}/invoice/html", response_class=HTMLResponse)
async def get_my_order_invoice_html(order_id: str, current_customer=Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    _, order_service, _return_service, invoice_service = _services(db, current_customer.organization_id)
    await _get_own_order_or_404(order_service, order_id, current_customer.id)

    invoice = await invoice_service.get_invoice_for_order(order_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No invoice has been generated for this order.")
    return await invoice_service.render_html(invoice.id)


@router.get("/returns", response_model=ReturnRequestListResponse)
async def list_my_returns(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    *_, return_service, _invoice_service = _services(db, current_customer.organization_id)
    model_status = ModelReturnStatus(status_filter) if status_filter else None
    items, total = await return_service.list_returns(customer_id=current_customer.id, status_filter=model_status, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/returns", response_model=ReturnRequestDetail, status_code=status.HTTP_201_CREATED)
async def create_my_return(
    data: ReturnRequestCreateRequest,
    current_customer=Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    _, _order_service, return_service, _invoice_service = _services(db, current_customer.organization_id)
    return_request = await return_service.create_return_request(data, customer_id=current_customer.id)
    items = await return_service.get_items(return_request.id)
    detail = ReturnRequestDetail.model_validate(return_request)
    detail.items = [ReturnItemRead.model_validate(i) for i in items]
    return detail


@router.get("/returns/{return_id}", response_model=ReturnRequestDetail)
async def get_my_return(return_id: str, current_customer=Depends(get_current_customer), db: AsyncSession = Depends(get_db)):
    *_, return_service, _invoice_service = _services(db, current_customer.organization_id)
    return_request = await return_service.get_return(return_id)
    if not return_request or return_request.customer_id != current_customer.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found.")

    items = await return_service.get_items(return_id)
    detail = ReturnRequestDetail.model_validate(return_request)
    detail.items = [ReturnItemRead.model_validate(i) for i in items]
    return detail
