from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.barcode import Barcode, BarcodeFormat
from app.models.qr_code import QRCode
from app.repositories.barcode_repository import BarcodeRepository, QRCodeRepository


class BarcodeService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = BarcodeRepository(session, organization_id, is_superuser)
        self.qr_repo = QRCodeRepository(session, organization_id, is_superuser)

    async def _ensure_unique_value(self, format_: BarcodeFormat, value: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_value(format_, value)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A barcode with that value already exists for this format.")

    async def create_barcode(self, data) -> Barcode:
        if not data.product_id and not data.variant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A barcode must be linked to a product or a variant.")
        if data.product_id and data.variant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A barcode can be linked to a product OR a variant, not both.")

        format_ = BarcodeFormat(data.format.value)
        await self._ensure_unique_value(format_, data.value)
        barcode = Barcode(
            product_id=data.product_id,
            variant_id=data.variant_id,
            value=data.value,
            format=format_,
            is_primary=data.is_primary,
        )
        return await self.repo.create(barcode)

    async def update_barcode(self, barcode_id: str, data) -> Barcode:
        barcode = await self.repo.get_by_id(barcode_id)
        if not barcode:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found.")

        new_format = BarcodeFormat(data.format.value) if data.format is not None else barcode.format
        new_value = data.value if data.value is not None else barcode.value
        if data.format is not None or data.value is not None:
            await self._ensure_unique_value(new_format, new_value, exclude_id=barcode.id)

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "format" and value is not None:
                value = BarcodeFormat(value.value if hasattr(value, "value") else value)
            setattr(barcode, field, value)

        return await self.repo.save(barcode)

    async def delete_barcode(self, barcode_id: str) -> None:
        barcode = await self.repo.get_by_id(barcode_id)
        if not barcode:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found.")
        await self.repo.soft_delete(barcode_id)

    async def bulk_delete(self, barcode_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(barcode_ids)

    async def get_barcode(self, barcode_id: str) -> Barcode | None:
        return await self.repo.get_by_id(barcode_id)

    async def lookup(self, value: str, format_: BarcodeFormat | None = None) -> Barcode | None:
        if format_ is not None:
            return await self.repo.get_by_value(format_, value)
        for candidate_format in BarcodeFormat:
            barcode = await self.repo.get_by_value(candidate_format, value)
            if barcode:
                return barcode
        return None

    async def list_barcodes(
        self,
        product_id: str | None = None,
        variant_id: str | None = None,
        format_: BarcodeFormat | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Barcode], int]:
        items = await self.repo.list(product_id, variant_id, format_, q, limit, offset)
        total = await self.repo.count(product_id, variant_id, format_, q)
        return items, total

    async def create_qr_code(self, data) -> QRCode:
        existing = await self.qr_repo.get_by_entity(data.entity_type, data.entity_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A QR code already exists for this entity.")
        qr_code = QRCode(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            value=data.value,
            image_url=data.image_url,
        )
        return await self.qr_repo.create(qr_code)

    async def update_qr_code(self, qr_code_id: str, data) -> QRCode:
        qr_code = await self.qr_repo.get_by_id(qr_code_id)
        if not qr_code:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR code not found.")
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(qr_code, field, value)
        return await self.qr_repo.save(qr_code)

    async def delete_qr_code(self, qr_code_id: str) -> None:
        qr_code = await self.qr_repo.get_by_id(qr_code_id)
        if not qr_code:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR code not found.")
        await self.qr_repo.soft_delete(qr_code_id)

    async def get_qr_code(self, qr_code_id: str) -> QRCode | None:
        return await self.qr_repo.get_by_id(qr_code_id)

    async def get_qr_code_for_entity(self, entity_type: str, entity_id: str) -> QRCode | None:
        return await self.qr_repo.get_by_entity(entity_type, entity_id)

    async def list_qr_codes(self, entity_type: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[QRCode], int]:
        items = await self.qr_repo.list(entity_type, limit, offset)
        total = await self.qr_repo.count(entity_type)
        return items, total
