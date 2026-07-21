from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_permission
from app.schemas.audit import AuditLogItem, AuditLogListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


def _audit_service(db: AsyncSession, current_user) -> AuditService:
    return AuditService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    module: str | None = Query(None),
    action: str | None = Query(None),
    entity: str | None = Query(None),
    user_id: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("audit")),
    db: AsyncSession = Depends(get_db),
):
    audit_service = _audit_service(db, current_user)
    items, total = await audit_service.search(
        module=module, action=action, entity=entity, user_id=user_id,
        date_from=date_from, date_to=date_to, limit=limit, offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/search", response_model=AuditLogListResponse)
async def search_audit_logs(
    q: str | None = Query(None),
    module: str | None = Query(None),
    action: str | None = Query(None),
    entity: str | None = Query(None),
    user_id: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("audit")),
    db: AsyncSession = Depends(get_db),
):
    audit_service = _audit_service(db, current_user)
    items, total = await audit_service.search(
        module=module, action=action, entity=entity, user_id=user_id,
        date_from=date_from, date_to=date_to, q=q, limit=limit, offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/export")
async def export_audit_logs(
    q: str | None = Query(None),
    module: str | None = Query(None),
    action: str | None = Query(None),
    entity: str | None = Query(None),
    user_id: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user=Depends(require_permission("audit")),
    db: AsyncSession = Depends(get_db),
):
    audit_service = _audit_service(db, current_user)
    csv_text = await audit_service.export_csv(
        module=module, action=action, entity=entity, user_id=user_id,
        date_from=date_from, date_to=date_to, q=q,
    )
    await audit_service.log(
        action="export", module="audit", entity="AuditLog",
        user_id=current_user.id,
    )
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-log-export.csv"},
    )


@router.get("/{audit_log_id}", response_model=AuditLogItem)
async def get_audit_log(audit_log_id: str, current_user=Depends(require_permission("audit")), db: AsyncSession = Depends(get_db)):
    audit_service = _audit_service(db, current_user)
    record = await audit_service.repo.get_by_id(audit_log_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found.")
    return record
