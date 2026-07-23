from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.schemas.address import AddressCreateRequest, AddressItem, AddressListResponse, AddressUpdateRequest
from app.schemas.customer import (
    BulkDeleteRequest,
    CustomerCreateRequest,
    CustomerItem,
    CustomerListResponse,
    CustomerUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


def _customer_service(db: AsyncSession, current_user) -> CustomerService:
    return CustomerService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    is_active: bool | None = Query(None),
    is_guest: bool | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("customers.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _customer_service(db, current_user)
    items, total = await service.list_customers(is_active, is_guest, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=CustomerItem, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreateRequest,
    current_user=Depends(require_permission("customers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _customer_service(db, current_user)
    customer = await service.create_customer(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="customers", entity="Customer", entity_id=customer.id,
        user_id=current_user.id, after={"email": customer.email}, context=audit_context,
    )
    return customer


@router.get("/{customer_id}", response_model=CustomerItem)
async def get_customer(customer_id: str, current_user=Depends(require_permission("customers.view")), db: AsyncSession = Depends(get_db)):
    service = _customer_service(db, current_user)
    customer = await service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    return customer


@router.patch("/{customer_id}", response_model=CustomerItem)
async def update_customer(
    customer_id: str,
    data: CustomerUpdateRequest,
    current_user=Depends(require_permission("customers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _customer_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    customer = await service.update_customer(customer_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="customers", entity="Customer", entity_id=customer.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user=Depends(require_permission("customers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _customer_service(db, current_user)
    await service.delete_customer(customer_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="customers", entity="Customer", entity_id=customer_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Customer deleted successfully."}


@router.post("/{customer_id}/restore", response_model=CustomerItem)
async def restore_customer(
    customer_id: str,
    current_user=Depends(require_permission("customers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _customer_service(db, current_user)
    customer = await service.restore_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    await AuditService(db, current_user.organization_id).log(
        action="restore", module="customers", entity="Customer", entity_id=customer_id,
        user_id=current_user.id, context=audit_context,
    )
    return customer


@router.post("/bulk-delete")
async def bulk_delete_customers(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("customers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _customer_service(db, current_user)
    count = await service.bulk_delete_customers(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="customers", entity="Customer", entity_id=None,
        user_id=current_user.id, after={"ids": data.ids}, context=audit_context,
    )
    return {"detail": f"{count} customer(s) deleted."}


@router.get("/{customer_id}/addresses", response_model=AddressListResponse)
async def list_customer_addresses(
    customer_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("customers.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _customer_service(db, current_user)
    items, total = await service.list_addresses(customer_id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/{customer_id}/addresses", response_model=AddressItem, status_code=status.HTTP_201_CREATED)
async def add_customer_address(
    customer_id: str,
    data: AddressCreateRequest,
    current_user=Depends(require_permission("customers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _customer_service(db, current_user)
    address = await service.add_address(customer_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="customers", entity="Address", entity_id=address.id,
        user_id=current_user.id, after={"customer_id": customer_id}, context=audit_context,
    )
    return address


@router.patch("/{customer_id}/addresses/{address_id}", response_model=AddressItem)
async def update_customer_address(
    customer_id: str,
    address_id: str,
    data: AddressUpdateRequest,
    current_user=Depends(require_permission("customers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _customer_service(db, current_user)
    address = await service.update_address(customer_id, address_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="customers", entity="Address", entity_id=address_id,
        user_id=current_user.id, context=audit_context,
    )
    return address


@router.delete("/{customer_id}/addresses/{address_id}")
async def delete_customer_address(
    customer_id: str,
    address_id: str,
    current_user=Depends(require_permission("customers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _customer_service(db, current_user)
    await service.delete_address(customer_id, address_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="customers", entity="Address", entity_id=address_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Address deleted successfully."}
