from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address, AddressType
from app.models.customer import Customer
from app.repositories.address_repository import AddressRepository
from app.repositories.customer_repository import CustomerRepository
from app.utils.security import hash_password


class CustomerService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = CustomerRepository(session, organization_id, is_superuser)
        self.address_repo = AddressRepository(session, organization_id, is_superuser)

    async def _ensure_unique_email(self, email: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_email(email)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A customer with that email already exists.")

    async def create_customer(self, data, created_by: str | None = None) -> Customer:
        await self._ensure_unique_email(data.email)

        customer = Customer(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            hashed_password=hash_password(data.password) if data.password else None,
            is_guest=data.password is None,
            accepts_marketing=data.accepts_marketing,
            notes=data.notes,
            created_by=created_by,
        )
        return await self.repo.create(customer)

    async def _get_or_404(self, customer_id: str) -> Customer:
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
        return customer

    async def get_customer(self, customer_id: str) -> Customer | None:
        return await self.repo.get_by_id(customer_id)

    async def update_customer(self, customer_id: str, data) -> Customer:
        customer = await self._get_or_404(customer_id)
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(customer, field, value)
        return await self.repo.save(customer)

    async def delete_customer(self, customer_id: str) -> None:
        await self._get_or_404(customer_id)
        await self.repo.soft_delete(customer_id)

    async def restore_customer(self, customer_id: str) -> Customer | None:
        return await self.repo.restore(customer_id)

    async def bulk_delete_customers(self, customer_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(customer_ids)

    async def list_customers(
        self,
        is_active: bool | None = None,
        is_guest: bool | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Customer], int]:
        items = await self.repo.list(is_active, is_guest, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(is_active, is_guest, q)
        return items, total

    async def list_addresses(self, customer_id: str, limit: int = 50, offset: int = 0) -> tuple[list[Address], int]:
        await self._get_or_404(customer_id)
        items = await self.address_repo.list_for_customer(customer_id, limit, offset)
        total = await self.address_repo.count_for_customer(customer_id)
        return items, total

    async def add_address(self, customer_id: str, data) -> Address:
        await self._get_or_404(customer_id)
        address_type = AddressType(data.address_type.value if hasattr(data.address_type, "value") else data.address_type)

        if data.is_default:
            await self.address_repo.clear_default_for_customer(customer_id, address_type)

        address = Address(
            customer_id=customer_id,
            label=data.label,
            address_type=address_type,
            first_name=data.first_name,
            last_name=data.last_name,
            company=data.company,
            phone=data.phone,
            line1=data.line1,
            line2=data.line2,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country.upper(),
            is_default=data.is_default,
        )
        return await self.address_repo.create(address)

    async def _get_address_or_404(self, customer_id: str, address_id: str) -> Address:
        address = await self.address_repo.get_by_id(address_id)
        if not address or address.customer_id != customer_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
        return address

    async def update_address(self, customer_id: str, address_id: str, data) -> Address:
        address = await self._get_address_or_404(customer_id, address_id)
        changes = data.model_dump(exclude_unset=True)

        if changes.get("is_default"):
            new_type = AddressType(changes.get("address_type", address.address_type))
            await self.address_repo.clear_default_for_customer(customer_id, new_type)

        if "country" in changes and changes["country"]:
            changes["country"] = changes["country"].upper()
        if "address_type" in changes:
            changes["address_type"] = AddressType(changes["address_type"])

        for field, value in changes.items():
            setattr(address, field, value)
        return await self.address_repo.save(address)

    async def delete_address(self, customer_id: str, address_id: str) -> None:
        await self._get_address_or_404(customer_id, address_id)
        await self.address_repo.soft_delete(address_id)
