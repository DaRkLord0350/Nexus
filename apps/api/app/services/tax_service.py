from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tax_class import TaxClass
from app.models.tax_rate import TaxRate, TaxType
from app.repositories.tax_class_repository import TaxClassRepository
from app.repositories.tax_rate_repository import TaxRateRepository
from app.utils.text import slugify


class TaxService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.class_repo = TaxClassRepository(session, organization_id, is_superuser)
        self.rate_repo = TaxRateRepository(session, organization_id, is_superuser)

    # ------------------------------------------------------------------
    # Tax classes
    # ------------------------------------------------------------------
    async def _ensure_unique_code(self, code: str, exclude_id: str | None = None) -> None:
        existing = await self.class_repo.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A tax class with that code already exists.")

    async def create_tax_class(self, data, created_by: str | None = None) -> TaxClass:
        code = slugify(data.code or data.name, fallback="tax-class")
        await self._ensure_unique_code(code)

        tax_class = TaxClass(
            name=data.name, code=code, description=data.description,
            is_default=data.is_default, is_active=data.is_active, created_by=created_by,
        )
        created = await self.class_repo.create(tax_class)

        if created.is_default:
            await self.class_repo.unset_default(exclude_id=created.id)
            await self.session.commit()

        return created

    async def update_tax_class(self, tax_class_id: str, data) -> TaxClass:
        tax_class = await self.class_repo.get_by_id(tax_class_id)
        if not tax_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax class not found.")

        if data.code is not None:
            new_code = slugify(data.code, fallback="tax-class")
            await self._ensure_unique_code(new_code, exclude_id=tax_class.id)
            tax_class.code = new_code
        elif data.name is not None:
            new_code = slugify(data.name, fallback="tax-class")
            await self._ensure_unique_code(new_code, exclude_id=tax_class.id)
            tax_class.code = new_code

        changes = data.model_dump(exclude_unset=True, exclude={"code"})
        for field, value in changes.items():
            setattr(tax_class, field, value)

        saved = await self.class_repo.save(tax_class)
        if saved.is_default:
            await self.class_repo.unset_default(exclude_id=saved.id)
            await self.session.commit()
        return saved

    async def delete_tax_class(self, tax_class_id: str) -> None:
        tax_class = await self.class_repo.get_by_id(tax_class_id)
        if not tax_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax class not found.")
        await self.rate_repo.soft_delete_for_class(tax_class_id)
        await self.class_repo.soft_delete(tax_class_id)

    async def get_tax_class(self, tax_class_id: str) -> TaxClass | None:
        return await self.class_repo.get_by_id(tax_class_id)

    async def list_tax_classes(self, is_active: bool | None = None, limit: int = 100, offset: int = 0) -> tuple[list[TaxClass], int]:
        items = await self.class_repo.list(is_active, limit, offset)
        total = await self.class_repo.count(is_active)
        return items, total

    # ------------------------------------------------------------------
    # Tax rates
    # ------------------------------------------------------------------
    async def create_tax_rate(self, tax_class_id: str, data) -> TaxRate:
        if not await self.class_repo.get_by_id(tax_class_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax class not found.")

        tax_rate = TaxRate(
            tax_class_id=tax_class_id,
            country=data.country.upper(),
            state=data.state,
            rate=data.rate,
            tax_type=TaxType(data.tax_type.value),
            is_inclusive=data.is_inclusive,
            priority=data.priority,
            is_active=data.is_active,
        )
        return await self.rate_repo.create(tax_rate)

    async def update_tax_rate(self, tax_class_id: str, tax_rate_id: str, data) -> TaxRate:
        tax_rate = await self.rate_repo.get_by_id(tax_rate_id)
        if not tax_rate or tax_rate.tax_class_id != tax_class_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax rate not found.")

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "country" and value is not None:
                value = value.upper()
            if field == "tax_type" and value is not None:
                value = TaxType(value.value if hasattr(value, "value") else value)
            setattr(tax_rate, field, value)

        return await self.rate_repo.save(tax_rate)

    async def delete_tax_rate(self, tax_class_id: str, tax_rate_id: str) -> None:
        tax_rate = await self.rate_repo.get_by_id(tax_rate_id)
        if not tax_rate or tax_rate.tax_class_id != tax_class_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax rate not found.")
        await self.rate_repo.soft_delete(tax_rate_id)

    async def list_tax_rates(self, tax_class_id: str) -> list[TaxRate]:
        if not await self.class_repo.get_by_id(tax_class_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax class not found.")
        return await self.rate_repo.list_for_class(tax_class_id)

    # ------------------------------------------------------------------
    # Calculation
    # ------------------------------------------------------------------
    async def calculate_tax(self, tax_class_id: str, amount: float, country: str, state: str | None = None) -> dict:
        if not await self.class_repo.get_by_id(tax_class_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax class not found.")

        matching_rates = await self.rate_repo.list_matching(tax_class_id, country.upper(), state)
        if not matching_rates:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tax rate configured for this country/state.")

        total_rate = sum(r.rate for r in matching_rates)
        is_inclusive = any(r.is_inclusive for r in matching_rates)

        if is_inclusive:
            tax_amount = amount - (amount / (1 + total_rate / 100))
            total_amount = amount
        else:
            tax_amount = amount * (total_rate / 100)
            total_amount = amount + tax_amount

        return {
            "amount": amount,
            "tax_amount": round(tax_amount, 2),
            "total_amount": round(total_amount, 2),
            "rate": total_rate,
            "is_inclusive": is_inclusive,
            "country": country.upper(),
            "state": state,
        }
