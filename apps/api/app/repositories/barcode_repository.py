from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.barcode import Barcode, BarcodeFormat
from app.models.qr_code import QRCode
from app.repositories.base_repository import BaseRepository


class BarcodeRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, barcode: Barcode) -> Barcode:
        self._add_tenant_on_create(barcode)
        self.session.add(barcode)
        await self.session.commit()
        await self.session.refresh(barcode)
        return barcode

    async def save(self, barcode: Barcode) -> Barcode:
        self.session.add(barcode)
        await self.session.commit()
        await self.session.refresh(barcode)
        return barcode

    async def get_by_id(self, barcode_id: str) -> Barcode | None:
        statement = select(Barcode).where(Barcode.id == barcode_id)
        statement = self._apply_tenant_filter(statement, Barcode)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_value(self, format_: BarcodeFormat, value: str) -> Barcode | None:
        statement = select(Barcode).where(Barcode.format == format_, Barcode.value == value)
        statement = self._apply_tenant_filter(statement, Barcode)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        product_id: str | None = None,
        variant_id: str | None = None,
        format_: BarcodeFormat | None = None,
        q: str | None = None,
    ):
        if product_id is not None:
            statement = statement.where(Barcode.product_id == product_id)
        if variant_id is not None:
            statement = statement.where(Barcode.variant_id == variant_id)
        if format_ is not None:
            statement = statement.where(Barcode.format == format_)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Barcode.value.ilike(like)))
        return statement

    async def list(
        self,
        product_id: str | None = None,
        variant_id: str | None = None,
        format_: BarcodeFormat | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Barcode]:
        statement = select(Barcode).order_by(Barcode.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, product_id, variant_id, format_, q)
        statement = self._apply_tenant_filter(statement, Barcode)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        product_id: str | None = None,
        variant_id: str | None = None,
        format_: BarcodeFormat | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(Barcode.id))
        statement = self._apply_filters(statement, product_id, variant_id, format_, q)
        statement = self._apply_tenant_filter(statement, Barcode)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, barcode_id: str) -> None:
        statement = update(Barcode).where(Barcode.id == barcode_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Barcode)
        await self.session.execute(statement)
        await self.session.commit()

    async def bulk_soft_delete(self, barcode_ids: list[str]) -> int:
        if not barcode_ids:
            return 0
        statement = update(Barcode).where(Barcode.id.in_(barcode_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Barcode)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0


class QRCodeRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, qr_code: QRCode) -> QRCode:
        self._add_tenant_on_create(qr_code)
        self.session.add(qr_code)
        await self.session.commit()
        await self.session.refresh(qr_code)
        return qr_code

    async def save(self, qr_code: QRCode) -> QRCode:
        self.session.add(qr_code)
        await self.session.commit()
        await self.session.refresh(qr_code)
        return qr_code

    async def get_by_id(self, qr_code_id: str) -> QRCode | None:
        statement = select(QRCode).where(QRCode.id == qr_code_id)
        statement = self._apply_tenant_filter(statement, QRCode)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_entity(self, entity_type: str, entity_id: str) -> QRCode | None:
        statement = select(QRCode).where(QRCode.entity_type == entity_type, QRCode.entity_id == entity_id)
        statement = self._apply_tenant_filter(statement, QRCode)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, entity_type: str | None = None):
        if entity_type is not None:
            statement = statement.where(QRCode.entity_type == entity_type)
        return statement

    async def list(self, entity_type: str | None = None, limit: int = 50, offset: int = 0) -> list[QRCode]:
        statement = select(QRCode).order_by(QRCode.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, entity_type)
        statement = self._apply_tenant_filter(statement, QRCode)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, entity_type: str | None = None) -> int:
        statement = select(func.count(QRCode.id))
        statement = self._apply_filters(statement, entity_type)
        statement = self._apply_tenant_filter(statement, QRCode)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, qr_code_id: str) -> None:
        statement = update(QRCode).where(QRCode.id == qr_code_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, QRCode)
        await self.session.execute(statement)
        await self.session.commit()
