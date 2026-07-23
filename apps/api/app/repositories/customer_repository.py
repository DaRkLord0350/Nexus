from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "first_name": Customer.first_name,
    "last_name": Customer.last_name,
    "email": Customer.email,
    "created_at": Customer.created_at,
    "updated_at": Customer.updated_at,
}


class CustomerRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, customer: Customer) -> Customer:
        self._add_tenant_on_create(customer)
        self.session.add(customer)
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def save(self, customer: Customer) -> Customer:
        self.session.add(customer)
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def get_by_id(self, customer_id: str) -> Customer | None:
        statement = select(Customer).where(Customer.id == customer_id)
        statement = self._apply_tenant_filter(statement, Customer)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Customer | None:
        statement = select(Customer).where(Customer.email == email)
        statement = self._apply_tenant_filter(statement, Customer)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        is_active: bool | None = None,
        is_guest: bool | None = None,
        q: str | None = None,
    ):
        if is_active is not None:
            statement = statement.where(Customer.is_active == is_active)
        if is_guest is not None:
            statement = statement.where(Customer.is_guest == is_guest)
        if q:
            like = f"%{q}%"
            statement = statement.where(
                or_(Customer.email.ilike(like), Customer.first_name.ilike(like), Customer.last_name.ilike(like), Customer.phone.ilike(like))
            )
        return statement

    async def list(
        self,
        is_active: bool | None = None,
        is_guest: bool | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Customer]:
        column = SORTABLE_FIELDS.get(sort_by, Customer.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Customer).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, is_active, is_guest, q)
        statement = self._apply_tenant_filter(statement, Customer)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None, is_guest: bool | None = None, q: str | None = None) -> int:
        statement = select(func.count(Customer.id))
        statement = self._apply_filters(statement, is_active, is_guest, q)
        statement = self._apply_tenant_filter(statement, Customer)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, customer_id: str) -> None:
        statement = update(Customer).where(Customer.id == customer_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Customer)
        await self.session.execute(statement)
        await self.session.commit()

    async def restore(self, customer_id: str) -> Customer | None:
        statement = update(Customer).where(Customer.id == customer_id).values(deleted_at=None)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Customer.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(customer_id)

    async def bulk_soft_delete(self, customer_ids: list[str]) -> int:
        if not customer_ids:
            return 0
        statement = update(Customer).where(Customer.id.in_(customer_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Customer)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0
