from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tax_rate import TaxRate
from app.repositories.base_repository import BaseRepository


class TaxRateRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, tax_rate: TaxRate) -> TaxRate:
        self._add_tenant_on_create(tax_rate)
        self.session.add(tax_rate)
        await self.session.commit()
        await self.session.refresh(tax_rate)
        return tax_rate

    async def save(self, tax_rate: TaxRate) -> TaxRate:
        self.session.add(tax_rate)
        await self.session.commit()
        await self.session.refresh(tax_rate)
        return tax_rate

    async def get_by_id(self, tax_rate_id: str) -> TaxRate | None:
        statement = select(TaxRate).where(TaxRate.id == tax_rate_id)
        statement = self._apply_tenant_filter(statement, TaxRate)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_class(self, tax_class_id: str) -> list[TaxRate]:
        statement = select(TaxRate).where(TaxRate.tax_class_id == tax_class_id).order_by(TaxRate.priority.asc())
        statement = self._apply_tenant_filter(statement, TaxRate)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_matching(self, tax_class_id: str, country: str, state: str | None) -> list[TaxRate]:
        statement = select(TaxRate).where(
            TaxRate.tax_class_id == tax_class_id,
            TaxRate.country == country,
            TaxRate.is_active.is_(True),
        )
        statement = self._apply_tenant_filter(statement, TaxRate)
        result = await self.session.execute(statement)
        rates = result.scalars().all()
        if state:
            state_specific = [r for r in rates if r.state == state]
            if state_specific:
                return state_specific
        return [r for r in rates if r.state is None]

    async def soft_delete(self, tax_rate_id: str) -> None:
        statement = update(TaxRate).where(TaxRate.id == tax_rate_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, TaxRate)
        await self.session.execute(statement)
        await self.session.commit()

    async def soft_delete_for_class(self, tax_class_id: str) -> None:
        statement = update(TaxRate).where(TaxRate.tax_class_id == tax_class_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, TaxRate)
        await self.session.execute(statement)
        await self.session.commit()
