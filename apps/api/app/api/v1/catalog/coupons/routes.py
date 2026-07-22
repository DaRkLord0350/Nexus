from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.coupon import (
    BulkDeleteRequest,
    CouponCreateRequest,
    CouponItem,
    CouponListResponse,
    CouponRedeemRequest,
    CouponUpdateRequest,
    CouponValidateRequest,
    CouponValidationResponse,
)
from app.services.audit_service import AuditService
from app.services.coupon_service import CouponService

router = APIRouter(prefix="/coupons", tags=["catalog-coupons"])


def _coupon_service(db: AsyncSession, current_user) -> CouponService:
    return CouponService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=CouponListResponse)
async def list_coupons(
    is_active: bool | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.coupons.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _coupon_service(db, current_user)
    await service.notify_expired_coupons()
    items, total = await service.list_coupons(is_active, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=CouponItem, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    data: CouponCreateRequest,
    current_user=Depends(require_permission("catalog.coupons.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _coupon_service(db, current_user)
    coupon = await service.create_coupon(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="Coupon", entity_id=coupon.id,
        user_id=current_user.id, after={"code": coupon.code, "discount_type": coupon.discount_type.value}, context=audit_context,
    )
    return coupon


@router.post("/validate", response_model=CouponValidationResponse)
async def validate_coupon(
    data: CouponValidateRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = _coupon_service(db, current_user)
    return await service.validate_coupon(
        data.code, data.order_amount, data.product_ids, data.category_ids, data.collection_ids,
        data.quantity, data.unit_price, data.customer_id,
    )


@router.post("/bulk-delete")
async def bulk_delete_coupons(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("catalog.coupons.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _coupon_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Coupon", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{coupon_id}", response_model=CouponItem)
async def get_coupon(coupon_id: str, current_user=Depends(require_permission("catalog.coupons.view")), db: AsyncSession = Depends(get_db)):
    service = _coupon_service(db, current_user)
    coupon = await service.get_coupon(coupon_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
    return coupon


@router.patch("/{coupon_id}", response_model=CouponItem)
async def update_coupon(
    coupon_id: str,
    data: CouponUpdateRequest,
    current_user=Depends(require_permission("catalog.coupons.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _coupon_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    coupon = await service.update_coupon(coupon_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Coupon", entity_id=coupon.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return coupon


@router.delete("/{coupon_id}")
async def delete_coupon(
    coupon_id: str,
    current_user=Depends(require_permission("catalog.coupons.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _coupon_service(db, current_user)
    await service.delete_coupon(coupon_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Coupon", entity_id=coupon_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Coupon deleted successfully."}


@router.post("/{coupon_id}/redeem")
async def redeem_coupon(
    coupon_id: str,
    data: CouponRedeemRequest,
    current_user=Depends(require_permission("catalog.coupons.view")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _coupon_service(db, current_user)
    await service.redeem_coupon(coupon_id, customer_id=data.customer_id, order_id=data.order_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Coupon", entity_id=coupon_id,
        user_id=current_user.id, after={"redeemed": True}, context=audit_context,
    )
    return {"detail": "Coupon redeemed successfully."}
