from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceStatus
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "invoice_number": Invoice.invoice_number,
    "total": Invoice.total,
    "created_at": Invoice.created_at,
}


class InvoiceRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, invoice: Invoice) -> Invoice:
        self._add_tenant_on_create(invoice)
        self.session.add(invoice)
        await self.session.commit()
        await self.session.refresh(invoice)
        return invoice

    async def save(self, invoice: Invoice) -> Invoice:
        self.session.add(invoice)
        await self.session.commit()
        await self.session.refresh(invoice)
        return invoice

    async def get_by_id(self, invoice_id: str) -> Invoice | None:
        statement = select(Invoice).where(Invoice.id == invoice_id)
        statement = self._apply_tenant_filter(statement, Invoice)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, invoice_number: str) -> Invoice | None:
        statement = select(Invoice).where(Invoice.invoice_number == invoice_number)
        statement = self._apply_tenant_filter(statement, Invoice)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_for_order(self, order_id: str) -> Invoice | None:
        statement = select(Invoice).where(Invoice.order_id == order_id)
        statement = self._apply_tenant_filter(statement, Invoice)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, status: InvoiceStatus | None = None, q: str | None = None):
        if status is not None:
            statement = statement.where(Invoice.status == status)
        if q:
            statement = statement.where(or_(Invoice.invoice_number.ilike(f"%{q}%")))
        return statement

    async def list(
        self,
        status: InvoiceStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Invoice]:
        column = SORTABLE_FIELDS.get(sort_by, Invoice.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Invoice).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, status, q)
        statement = self._apply_tenant_filter(statement, Invoice)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, status: InvoiceStatus | None = None, q: str | None = None) -> int:
        statement = select(func.count(Invoice.id))
        statement = self._apply_filters(statement, status, q)
        statement = self._apply_tenant_filter(statement, Invoice)
        result = await self.session.execute(statement)
        return result.scalar_one()
