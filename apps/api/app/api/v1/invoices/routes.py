from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.invoice import InvoiceStatus as ModelInvoiceStatus
from app.schemas.invoice import InvoiceListResponse, InvoiceRead, InvoiceVoidRequest
from app.services.audit_service import AuditService
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _invoice_service(db: AsyncSession, current_user) -> InvoiceService:
    return InvoiceService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("orders.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _invoice_service(db, current_user)
    model_status = ModelInvoiceStatus(status_filter) if status_filter else None
    items, total = await service.list_invoices(model_status, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(invoice_id: str, current_user=Depends(require_permission("orders.view")), db: AsyncSession = Depends(get_db)):
    service = _invoice_service(db, current_user)
    invoice = await service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return invoice


@router.get("/{invoice_id}/html", response_class=HTMLResponse)
async def render_invoice_html(invoice_id: str, current_user=Depends(require_permission("orders.view")), db: AsyncSession = Depends(get_db)):
    service = _invoice_service(db, current_user)
    return await service.render_html(invoice_id)


@router.post("/{invoice_id}/void", response_model=InvoiceRead)
async def void_invoice(
    invoice_id: str,
    data: InvoiceVoidRequest,
    current_user=Depends(require_permission("orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _invoice_service(db, current_user)
    invoice = await service.void_invoice(invoice_id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Invoice", entity_id=invoice.id,
        user_id=current_user.id, after={"status": "void", "reason": data.reason}, context=audit_context,
    )
    return invoice
