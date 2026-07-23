from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.order import OrderPriority as ModelOrderPriority
from app.models.order import OrderStatus as ModelOrderStatus
from app.schemas.order import (
    BulkPriorityUpdateRequest,
    BulkTagRequest,
    OrderCancelRequest,
    OrderCreateRequest,
    OrderDetail,
    OrderHoldRequest,
    OrderLineItem,
    OrderListResponse,
    OrderNoteCreateRequest,
    OrderNoteRead,
    OrderRead,
    OrderStatusHistoryRead,
    OrderUpdateRequest,
)
from app.schemas.invoice import InvoiceRead
from app.schemas.payment import PaymentAttemptCreateRequest, PaymentAttemptRead, RefundPaymentRequest
from app.services.audit_service import AuditService
from app.services.invoice_service import InvoiceService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_service(db: AsyncSession, current_user) -> OrderService:
    return OrderService(db, current_user.organization_id, current_user.is_superuser)


async def _build_detail(service: OrderService, order) -> OrderDetail:
    items = await service.get_items(order.id)
    history = await service.get_status_history(order.id)
    notes = await service.get_notes(order.id)
    detail = OrderDetail.model_validate(order)
    detail.items = [OrderLineItem.model_validate(item) for item in items]
    detail.status_history = [OrderStatusHistoryRead.model_validate(entry) for entry in history]
    detail.notes = [OrderNoteRead.model_validate(note) for note in notes]
    return detail


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    customer_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    requires_manual_review: bool | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("orders.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _order_service(db, current_user)
    model_status = ModelOrderStatus(status_filter) if status_filter else None
    model_priority = ModelOrderPriority(priority) if priority else None
    items, total = await service.list_orders(customer_id, model_status, model_priority, requires_manual_review, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreateRequest,
    current_user=Depends(require_permission("orders.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    order = await service.create_order(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="orders", entity="Order", entity_id=order.id,
        user_id=current_user.id, after={"order_number": order.order_number, "total": order.total}, context=audit_context,
    )
    return order


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(order_id: str, current_user=Depends(require_permission("orders.view")), db: AsyncSession = Depends(get_db)):
    service = _order_service(db, current_user)
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return await _build_detail(service, order)


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: str,
    data: OrderUpdateRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    order = await service.update_order(order_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Order", entity_id=order.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return order


@router.get("/{order_id}/history", response_model=list[OrderStatusHistoryRead])
async def get_order_history(order_id: str, current_user=Depends(require_permission("orders.view")), db: AsyncSession = Depends(get_db)):
    service = _order_service(db, current_user)
    return await service.get_status_history(order_id)


@router.get("/{order_id}/notes", response_model=list[OrderNoteRead])
async def list_order_notes(order_id: str, current_user=Depends(require_permission("orders.view")), db: AsyncSession = Depends(get_db)):
    service = _order_service(db, current_user)
    return await service.get_notes(order_id)


@router.post("/{order_id}/notes", response_model=OrderNoteRead, status_code=status.HTTP_201_CREATED)
async def add_order_note(
    order_id: str,
    data: OrderNoteCreateRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    note = await service.add_note(order_id, data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="orders", entity="OrderNote", entity_id=note.id,
        user_id=current_user.id, after={"order_id": order_id}, context=audit_context,
    )
    return note


async def _apply_transition(service: OrderService, db: AsyncSession, current_user, audit_context: AuditContext, order_id: str, method_name: str):
    method = getattr(service, method_name)
    order = await method(order_id, changed_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Order", entity_id=order.id,
        user_id=current_user.id, after={"status": order.status.value}, context=audit_context,
    )
    return order


@router.post("/{order_id}/place", response_model=OrderRead)
async def place_order(order_id: str, current_user=Depends(require_permission("orders.edit")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "place_order")


@router.post("/{order_id}/confirm", response_model=OrderRead)
async def confirm_order(order_id: str, current_user=Depends(require_permission("orders.edit")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "confirm_order")


@router.post("/{order_id}/process", response_model=OrderRead)
async def process_order(order_id: str, current_user=Depends(require_permission("orders.edit")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "start_processing")


@router.post("/{order_id}/pack", response_model=OrderRead)
async def pack_order(order_id: str, current_user=Depends(require_permission("orders.edit")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "pack_order")


@router.post("/{order_id}/ready-to-ship", response_model=OrderRead)
async def ready_to_ship_order(order_id: str, current_user=Depends(require_permission("orders.edit")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "mark_ready_to_ship")


@router.post("/{order_id}/ship", response_model=OrderRead)
async def ship_order(order_id: str, current_user=Depends(require_permission("orders.fulfill")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "ship_order")


@router.post("/{order_id}/out-for-delivery", response_model=OrderRead)
async def out_for_delivery_order(order_id: str, current_user=Depends(require_permission("orders.fulfill")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "mark_out_for_delivery")


@router.post("/{order_id}/deliver", response_model=OrderRead)
async def deliver_order(order_id: str, current_user=Depends(require_permission("orders.fulfill")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "deliver_order")


@router.post("/{order_id}/partially-fulfill", response_model=OrderRead)
async def partially_fulfill_order(order_id: str, current_user=Depends(require_permission("orders.fulfill")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "mark_partially_fulfilled")


@router.post("/{order_id}/backorder", response_model=OrderRead)
async def backorder_order(order_id: str, current_user=Depends(require_permission("orders.fulfill")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_order_service(db, current_user), db, current_user, audit_context, order_id, "mark_backordered")


@router.post("/{order_id}/fail", response_model=OrderRead)
async def fail_order(
    order_id: str,
    data: OrderCancelRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    order = await service.mark_failed(order_id, changed_by=current_user.id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Order", entity_id=order.id,
        user_id=current_user.id, after={"status": "failed"}, context=audit_context,
    )
    return order


@router.post("/{order_id}/hold", response_model=OrderRead)
async def hold_order(
    order_id: str,
    data: OrderHoldRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    order = await service.hold_order(order_id, changed_by=current_user.id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Order", entity_id=order.id,
        user_id=current_user.id, after={"status": "hold"}, context=audit_context,
    )
    return order


@router.post("/{order_id}/resume", response_model=OrderRead)
async def resume_order(
    order_id: str,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    order = await service.resume_order(order_id, changed_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Order", entity_id=order.id,
        user_id=current_user.id, after={"status": order.status.value}, context=audit_context,
    )
    return order


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: str,
    data: OrderCancelRequest,
    current_user=Depends(require_permission("orders.cancel")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    order = await service.cancel_order(order_id, changed_by=current_user.id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Order", entity_id=order.id,
        user_id=current_user.id, after={"status": "cancelled", "reason": data.reason}, context=audit_context,
    )
    return order


@router.get("/{order_id}/payments", response_model=list[PaymentAttemptRead])
async def list_order_payments(order_id: str, current_user=Depends(require_permission("orders.view")), db: AsyncSession = Depends(get_db)):
    service = PaymentService(db, current_user.organization_id, current_user.is_superuser)
    return await service.list_payment_attempts(order_id)


@router.post("/{order_id}/payments", response_model=PaymentAttemptRead, status_code=status.HTTP_201_CREATED)
async def create_order_payment(
    order_id: str,
    data: PaymentAttemptCreateRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = PaymentService(db, current_user.organization_id, current_user.is_superuser)
    attempt = await service.create_payment_attempt(order_id, data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="orders", entity="PaymentAttempt", entity_id=attempt.id,
        user_id=current_user.id, after={"order_id": order_id, "status": attempt.status.value, "amount": attempt.amount}, context=audit_context,
    )
    return attempt


@router.post("/{order_id}/refund-payment", response_model=PaymentAttemptRead)
async def refund_order_payment(
    order_id: str,
    data: RefundPaymentRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = PaymentService(db, current_user.organization_id, current_user.is_superuser)
    attempt = await service.refund_payment(order_id, data.amount, reason=data.reason, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="PaymentAttempt", entity_id=attempt.id,
        user_id=current_user.id, after={"order_id": order_id, "refunded_amount": data.amount}, context=audit_context,
    )
    return attempt


@router.get("/{order_id}/invoice", response_model=InvoiceRead)
async def get_order_invoice(order_id: str, current_user=Depends(require_permission("orders.view")), db: AsyncSession = Depends(get_db)):
    service = InvoiceService(db, current_user.organization_id, current_user.is_superuser)
    invoice = await service.get_invoice_for_order(order_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No invoice has been generated for this order.")
    return invoice


@router.post("/{order_id}/invoice", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def generate_order_invoice(
    order_id: str,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = InvoiceService(db, current_user.organization_id, current_user.is_superuser)
    invoice = await service.generate_invoice(order_id, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="orders", entity="Invoice", entity_id=invoice.id,
        user_id=current_user.id, after={"order_id": order_id, "invoice_number": invoice.invoice_number}, context=audit_context,
    )
    return invoice


@router.post("/bulk-priority")
async def bulk_update_priority(
    data: BulkPriorityUpdateRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    count = await service.bulk_update_priority(data.ids, ModelOrderPriority(data.priority.value))
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Order", entity_id=None,
        user_id=current_user.id, after={"ids": data.ids, "priority": data.priority.value}, context=audit_context,
    )
    return {"detail": f"{count} order(s) updated."}


@router.post("/bulk-tags")
async def bulk_update_tags(
    data: BulkTagRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _order_service(db, current_user)
    count = await service.bulk_update_tags(data.ids, data.tags)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Order", entity_id=None,
        user_id=current_user.id, after={"ids": data.ids, "tags": data.tags}, context=audit_context,
    )
    return {"detail": f"{count} order(s) updated."}
