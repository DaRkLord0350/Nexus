from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.channel import ProductChannelItem, ProductChannelsRequest
from app.services.audit_service import AuditService
from app.services.channel_service import ChannelService

router = APIRouter(prefix="/products/{product_id}/channels", tags=["catalog-product-channels"])


def _channel_service(db: AsyncSession, current_user) -> ChannelService:
    return ChannelService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=list[ProductChannelItem])
async def list_product_channels(
    product_id: str,
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _channel_service(db, current_user)
    return await service.get_product_channels(product_id)


@router.put("/")
async def set_product_channels(
    product_id: str,
    data: ProductChannelsRequest,
    current_user=Depends(require_permission("catalog.channels.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _channel_service(db, current_user)
    await service.set_product_channels(product_id, data.channel_ids)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Product", entity_id=product_id,
        user_id=current_user.id, after={"channel_ids": data.channel_ids}, context=audit_context,
    )
    return {"detail": "Product channels updated."}
