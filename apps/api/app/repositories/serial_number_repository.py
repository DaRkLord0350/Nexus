from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.serial_number import SerialNumber, SerialStatus
from app.repositories.base_repository import BaseRepository


class SerialNumberRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, serial_number: SerialNumber) -> SerialNumber:
        self._add_tenant_on_create(serial_number)
        self.session.add(serial_number)
        await self.session.commit()
        await self.session.refresh(serial_number)
        return serial_number

    async def save(self, serial_number: SerialNumber) -> SerialNumber:
        self.session.add(serial_number)
        await self.session.commit()
        await self.session.refresh(serial_number)
        return serial_number

    async def get_by_id(self, serial_id: str) -> SerialNumber | None:
        statement = select(SerialNumber).where(SerialNumber.id == serial_id)
        statement = self._apply_tenant_filter(statement, SerialNumber)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_serial(self, product_id: str, serial: str) -> SerialNumber | None:
        statement = select(SerialNumber).where(SerialNumber.product_id == product_id, SerialNumber.serial == serial)
        statement = self._apply_tenant_filter(statement, SerialNumber)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def find_by_serial_any_product(self, serial: str) -> SerialNumber | None:
        statement = select(SerialNumber).where(SerialNumber.serial == serial)
        statement = self._apply_tenant_filter(statement, SerialNumber)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        batch_id: str | None = None,
        status: SerialStatus | None = None,
        q: str | None = None,
    ):
        if product_id is not None:
            statement = statement.where(SerialNumber.product_id == product_id)
        if warehouse_id is not None:
            statement = statement.where(SerialNumber.warehouse_id == warehouse_id)
        if batch_id is not None:
            statement = statement.where(SerialNumber.batch_id == batch_id)
        if status is not None:
            statement = statement.where(SerialNumber.status == status)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(SerialNumber.serial.ilike(like)))
        return statement

    async def list(
        self,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        batch_id: str | None = None,
        status: SerialStatus | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SerialNumber]:
        statement = select(SerialNumber).order_by(SerialNumber.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, product_id, warehouse_id, batch_id, status, q)
        statement = self._apply_tenant_filter(statement, SerialNumber)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        batch_id: str | None = None,
        status: SerialStatus | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(SerialNumber.id))
        statement = self._apply_filters(statement, product_id, warehouse_id, batch_id, status, q)
        statement = self._apply_tenant_filter(statement, SerialNumber)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, serial_id: str) -> None:
        statement = update(SerialNumber).where(SerialNumber.id == serial_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, SerialNumber)
        await self.session.execute(statement)
        await self.session.commit()
