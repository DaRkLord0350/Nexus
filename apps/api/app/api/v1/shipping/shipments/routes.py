from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.shipment import ShipmentStatus as ModelShipmentStatus
from app.schemas.shipment import (
    ShipmentCancelRequest,
    ShipmentCreateRequest,
    ShipmentDetail,
    ShipmentFailDeliveryRequest,
    ShipmentItemRead,
    ShipmentListResponse,
    ShipmentRead,
    ShipmentUpdateRequest,
)
from app.schemas.shipment_tracking import ShipmentTrackingEventCreateRequest, ShipmentTrackingEventRead
from app.schemas.shipping_label import BulkLabelsRequest, ManifestGenerateRequest
from app.services.audit_service import AuditService
from app.services.shipment_service import ShipmentService
from app.services.shipment_tracking_service import ShipmentTrackingService
from app.services.shipping_label_service import ShippingLabelService

router = APIRouter(prefix="/shipments", tags=["shipping-shipments"])


def _tracking_service(db: AsyncSession, current_user) -> ShipmentTrackingService:
    return ShipmentTrackingService(db, current_user.organization_id, current_user.is_superuser)


def _shipment_service(db: AsyncSession, current_user) -> ShipmentService:
    return ShipmentService(db, current_user.organization_id, current_user.is_superuser)


def _label_service(db: AsyncSession, current_user) -> ShippingLabelService:
    return ShippingLabelService(db, current_user.organization_id, current_user.is_superuser)


async def _build_detail(service: ShipmentService, shipment) -> ShipmentDetail:
    items = await service.get_items(shipment.id)
    detail = ShipmentDetail.model_validate(shipment)
    detail.items = [ShipmentItemRead.model_validate(item) for item in items]
    return detail


@router.get("/", response_model=ShipmentListResponse)
async def list_shipments(
    order_id: str | None = Query(None),
    warehouse_id: str | None = Query(None),
    shipping_provider_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("shipping.shipments.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _shipment_service(db, current_user)
    model_status = ModelShipmentStatus(status_filter) if status_filter else None
    items, total = await service.list_shipments(order_id, warehouse_id, shipping_provider_id, model_status, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ShipmentDetail, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    data: ShipmentCreateRequest,
    current_user=Depends(require_permission("shipping.shipments.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _shipment_service(db, current_user)
    shipment = await service.create_shipment(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="shipping", entity="Shipment", entity_id=shipment.id,
        user_id=current_user.id, after={"shipment_number": shipment.shipment_number, "order_id": data.order_id}, context=audit_context,
    )
    return await _build_detail(service, shipment)


@router.get("/{shipment_id}", response_model=ShipmentDetail)
async def get_shipment(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.view")), db: AsyncSession = Depends(get_db)):
    service = _shipment_service(db, current_user)
    shipment = await service.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")
    return await _build_detail(service, shipment)


@router.patch("/{shipment_id}", response_model=ShipmentRead)
async def update_shipment(
    shipment_id: str,
    data: ShipmentUpdateRequest,
    current_user=Depends(require_permission("shipping.shipments.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _shipment_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    shipment = await service.update_shipment(shipment_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Shipment", entity_id=shipment.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return shipment


async def _apply_transition(service: ShipmentService, db: AsyncSession, current_user, audit_context: AuditContext, shipment_id: str, method_name: str):
    method = getattr(service, method_name)
    shipment = await method(shipment_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Shipment", entity_id=shipment.id,
        user_id=current_user.id, after={"status": shipment.status.value}, context=audit_context,
    )
    return shipment


@router.post("/{shipment_id}/label", response_model=ShipmentRead)
async def generate_shipment_label(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.manage")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_shipment_service(db, current_user), db, current_user, audit_context, shipment_id, "generate_label")


@router.post("/{shipment_id}/pickup", response_model=ShipmentRead)
async def mark_shipment_picked_up(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.manage")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_shipment_service(db, current_user), db, current_user, audit_context, shipment_id, "mark_picked_up")


@router.post("/{shipment_id}/in-transit", response_model=ShipmentRead)
async def mark_shipment_in_transit(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.manage")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_shipment_service(db, current_user), db, current_user, audit_context, shipment_id, "mark_in_transit")


@router.post("/{shipment_id}/out-for-delivery", response_model=ShipmentRead)
async def mark_shipment_out_for_delivery(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.manage")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_shipment_service(db, current_user), db, current_user, audit_context, shipment_id, "mark_out_for_delivery")


@router.post("/{shipment_id}/deliver", response_model=ShipmentRead)
async def mark_shipment_delivered(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.manage")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_shipment_service(db, current_user), db, current_user, audit_context, shipment_id, "mark_delivered")


@router.post("/{shipment_id}/return", response_model=ShipmentRead)
async def mark_shipment_returned(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.manage")), db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    return await _apply_transition(_shipment_service(db, current_user), db, current_user, audit_context, shipment_id, "mark_returned")


@router.post("/{shipment_id}/fail-delivery", response_model=ShipmentRead)
async def mark_shipment_failed_delivery(
    shipment_id: str,
    data: ShipmentFailDeliveryRequest,
    current_user=Depends(require_permission("shipping.shipments.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _shipment_service(db, current_user)
    shipment = await service.mark_failed_delivery(shipment_id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Shipment", entity_id=shipment.id,
        user_id=current_user.id, after={"status": "failed_delivery", "reason": data.reason}, context=audit_context,
    )
    return shipment


@router.post("/{shipment_id}/cancel", response_model=ShipmentRead)
async def cancel_shipment(
    shipment_id: str,
    data: ShipmentCancelRequest,
    current_user=Depends(require_permission("shipping.shipments.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _shipment_service(db, current_user)
    shipment = await service.cancel_shipment(shipment_id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Shipment", entity_id=shipment.id,
        user_id=current_user.id, after={"status": "cancelled", "reason": data.reason}, context=audit_context,
    )
    return shipment


@router.get("/{shipment_id}/tracking", response_model=list[ShipmentTrackingEventRead])
async def list_shipment_tracking(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.view")), db: AsyncSession = Depends(get_db)):
    service = _tracking_service(db, current_user)
    return await service.get_timeline(shipment_id)


@router.post("/{shipment_id}/tracking", response_model=ShipmentTrackingEventRead, status_code=status.HTTP_201_CREATED)
async def add_shipment_tracking_event(
    shipment_id: str,
    data: ShipmentTrackingEventCreateRequest,
    current_user=Depends(require_permission("shipping.shipments.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tracking_service(db, current_user)
    event = await service.add_event(shipment_id, data, source="manual")
    await AuditService(db, current_user.organization_id).log(
        action="create", module="shipping", entity="ShipmentTracking", entity_id=event.id,
        user_id=current_user.id, after={"shipment_id": shipment_id, "status": data.status}, context=audit_context,
    )
    return event


@router.get("/{shipment_id}/label", response_class=HTMLResponse)
async def get_shipment_label(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.view")), db: AsyncSession = Depends(get_db)):
    service = _label_service(db, current_user)
    return await service.render_label_html(shipment_id, generated_by=current_user.id)


@router.get("/{shipment_id}/packing-slip", response_class=HTMLResponse)
async def get_shipment_packing_slip(shipment_id: str, current_user=Depends(require_permission("shipping.shipments.view")), db: AsyncSession = Depends(get_db)):
    service = _label_service(db, current_user)
    return await service.render_packing_slip_html(shipment_id, generated_by=current_user.id)


@router.post("/bulk-labels", response_class=HTMLResponse)
async def get_bulk_shipment_labels(
    data: BulkLabelsRequest,
    current_user=Depends(require_permission("shipping.shipments.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _label_service(db, current_user)
    return await service.render_bulk_labels_html(data.shipment_ids, generated_by=current_user.id)


@router.post("/manifests", response_class=HTMLResponse)
async def generate_manifest(
    data: ManifestGenerateRequest,
    current_user=Depends(require_permission("shipping.shipments.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _label_service(db, current_user)
    html = await service.render_manifest_html(data.warehouse_id, data.shipment_ids, generated_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="shipping", entity="Manifest", entity_id=None,
        user_id=current_user.id, after={"warehouse_id": data.warehouse_id, "shipment_ids": data.shipment_ids}, context=audit_context,
    )
    return html
