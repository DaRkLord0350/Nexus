from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.serial_number import SerialNumber, SerialStatus
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.serial_number_repository import SerialNumberRepository


class SerialNumberService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = SerialNumberRepository(session, organization_id, is_superuser)
        self.inventory_repo = InventoryRepository(session, organization_id, is_superuser)

    async def _ensure_unique(self, product_id: str, serial: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_serial(product_id, serial)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Serial '{serial}' already exists for this product.")

    async def create_serial(self, data) -> SerialNumber:
        await self._ensure_unique(data.product_id, data.serial)
        inventory = await self.inventory_repo.get_or_create_for_update(data.product_id, data.variant_id, data.warehouse_id, data.bin_id)
        await self.session.commit()

        serial_number = SerialNumber(
            inventory_id=inventory.id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            warehouse_id=data.warehouse_id,
            batch_id=data.batch_id,
            bin_id=data.bin_id,
            serial=data.serial,
            status=SerialStatus(data.status.value),
            notes=data.notes,
        )
        return await self.repo.create(serial_number)

    async def bulk_import(self, data) -> tuple[list[SerialNumber], list[str]]:
        inventory = await self.inventory_repo.get_or_create_for_update(data.product_id, data.variant_id, data.warehouse_id, data.bin_id)
        await self.session.commit()

        created: list[SerialNumber] = []
        skipped: list[str] = []
        for raw_serial in data.serials:
            serial_value = raw_serial.strip()
            if not serial_value:
                continue
            existing = await self.repo.get_by_serial(data.product_id, serial_value)
            if existing:
                skipped.append(serial_value)
                continue
            serial_number = SerialNumber(
                inventory_id=inventory.id,
                product_id=data.product_id,
                variant_id=data.variant_id,
                warehouse_id=data.warehouse_id,
                batch_id=data.batch_id,
                bin_id=data.bin_id,
                serial=serial_value,
                status=SerialStatus.available,
            )
            created.append(await self.repo.create(serial_number))
        return created, skipped

    async def update_serial(self, serial_id: str, data) -> SerialNumber:
        serial_number = await self.repo.get_by_id(serial_id)
        if not serial_number:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serial number not found.")

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "status" and value is not None:
                value = SerialStatus(value.value if hasattr(value, "value") else value)
                if value == SerialStatus.sold and serial_number.status != SerialStatus.sold:
                    serial_number.sold_at = datetime.utcnow()
            setattr(serial_number, field, value)

        return await self.repo.save(serial_number)

    async def delete_serial(self, serial_id: str) -> None:
        serial_number = await self.repo.get_by_id(serial_id)
        if not serial_number:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serial number not found.")
        await self.repo.soft_delete(serial_id)

    async def bulk_delete(self, serial_ids: list[str]) -> int:
        deleted = 0
        for serial_id in serial_ids:
            serial_number = await self.repo.get_by_id(serial_id)
            if serial_number:
                await self.repo.soft_delete(serial_id)
                deleted += 1
        return deleted

    async def get_serial(self, serial_id: str) -> SerialNumber | None:
        return await self.repo.get_by_id(serial_id)

    async def scan(self, serial: str) -> SerialNumber | None:
        return await self.repo.find_by_serial_any_product(serial)

    async def list_serials(
        self,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        batch_id: str | None = None,
        status_filter: SerialStatus | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SerialNumber], int]:
        items = await self.repo.list(product_id, warehouse_id, batch_id, status_filter, q, limit, offset)
        total = await self.repo.count(product_id, warehouse_id, batch_id, status_filter, q)
        return items, total
